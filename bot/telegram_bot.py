"""
NS Lingo Telegram bot: explains Singapore NS slang, grounded in the glossary.

People can ask it:
    a private chat message          any text
    /ns <question>                  in private chats or groups
    a reply to one of its messages  in groups
    @bot <question>                 in groups, only if privacy mode is off (see docs)

Same answers and limits as the Discord bot (answering.py). Setup: docs/telegram-bot.md

Usage:
    python bot/telegram_bot.py          Telegram only
    python bot/run_bots.py              Discord + Telegram in one process (what the server runs)
"""

from __future__ import annotations

import html
import logging
import os
import re
import sys
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction, ChatType, ParseMode
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from answering import Answerer, make_answerer

REPO_ROOT = BOT_DIR.parent
TELEGRAM_MAX_CHARS = 4096

HELP_TEXT = (
    "Ask me about NS lingo! For example:\n"
    "- what does rabak mean?\n"
    "- kena extra after SBA then cannot book out\n"
    "- what do you call someone who pretends to be sick?\n\n"
    "Message me here, or in a group use /ns <question> or reply to one of my messages."
)

log = logging.getLogger("ns_lingo_bot")


def to_html(answer: str) -> str:
    """Escape the LLM's text for Telegram HTML, keeping its **bold** and *italic*."""
    text = html.escape(answer, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    return text


def format_reply(answer: str, terms: list[str]) -> str:
    footer = f"\n\n<i>Glossary: {html.escape(', '.join(terms), quote=False)}</i>" if terms else ""
    body = to_html(answer)
    room = TELEGRAM_MAX_CHARS - len(footer)
    if len(body) > room:
        # Cut the plain text instead, so a tag is never split.
        body = html.escape(answer[: room - 200], quote=False) + "…"
    return body + footer


def build_application(token: str, answerer: Answerer) -> Application:
    async def reply(update: Update, question: str) -> None:
        message = update.effective_message
        await message.chat.send_action(ChatAction.TYPING)
        result = await answerer.handle(f"telegram:{update.effective_user.id}", question)
        if result is None:
            await message.reply_text(HELP_TEXT)
            return
        try:
            await message.reply_text(format_reply(*result), parse_mode=ParseMode.HTML)
        except BadRequest:
            # Telegram rejected the HTML; send it plain rather than not at all.
            answer, terms = result
            plain = answer + (f"\n\nGlossary: {', '.join(terms)}" if terms else "")
            await message.reply_text(plain[:TELEGRAM_MAX_CHARS])

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(HELP_TEXT)

    async def ns_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await reply(update, " ".join(context.args))

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        if message.chat.type == ChatType.PRIVATE:
            await reply(update, message.text)
            return
        # Groups: only answer replies to the bot, or messages that @mention it.
        mention = f"@{context.bot.username}"
        replied_to = message.reply_to_message
        if replied_to and replied_to.from_user and replied_to.from_user.id == context.bot.id:
            await reply(update, message.text)
        elif mention.lower() in message.text.lower():
            await reply(update, re.sub(re.escape(mention), "", message.text, flags=re.I))

    async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        log.error("Telegram update failed", exc_info=context.error)

    # Concurrent updates so one slow LLM call doesn't hold up everyone else.
    app = Application.builder().token(token).concurrent_updates(True).build()
    app.add_handler(CommandHandler(["start", "help"], help_command))
    app.add_handler(CommandHandler("ns", ns_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    return app


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # otherwise logs every poll
    load_dotenv(REPO_ROOT / ".env")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN not set in .env (see docs/telegram-bot.md)")
        return 1

    build_application(token, make_answerer()).run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
