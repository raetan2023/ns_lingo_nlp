"""
Run the Discord and Telegram bots together in one process.

Sharing a process means the embedding model is loaded once (the e2-micro server has
1GB RAM) and the global rate limit covers both platforms. Starts whichever bots have
a token in .env: DISCORD_BOT_TOKEN, TELEGRAM_BOT_TOKEN.

Usage:
    python bot/run_bots.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from dotenv import load_dotenv

from answering import make_answerer
from discord_bot import NSLingoBot
from telegram_bot import build_application

REPO_ROOT = BOT_DIR.parent

log = logging.getLogger("ns_lingo_bot")


async def run(discord_token: str | None, guild_id: str | None, telegram_token: str | None) -> None:
    answerer = make_answerer()
    discord_bot = NSLingoBot(answerer, int(guild_id) if guild_id else None) if discord_token else None
    telegram_app = build_application(telegram_token, answerer) if telegram_token else None

    if telegram_app:
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        log.info("Telegram bot polling as @%s", telegram_app.bot.username)
    try:
        if discord_bot:
            await discord_bot.start(discord_token)  # runs until the process is stopped
        else:
            await asyncio.Event().wait()
    finally:
        if telegram_app:
            await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
        if discord_bot:
            await discord_bot.close()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # otherwise logs every Telegram poll
    load_dotenv(REPO_ROOT / ".env")

    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not discord_token and not telegram_token:
        print("Set DISCORD_BOT_TOKEN and/or TELEGRAM_BOT_TOKEN in .env (see docs/)")
        return 1

    try:
        asyncio.run(run(discord_token, os.getenv("DISCORD_GUILD_ID"), telegram_token))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
