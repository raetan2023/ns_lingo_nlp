"""
NS Lingo Discord bot: explains Singapore NS slang, grounded in the glossary.

People can ask it three ways:
    /ns question:<text>     slash command
    @bot <question>         mention it in a channel
    a direct message to the bot

Each question: search_glossary (keyword + embeddings, local) -> one LLM call
(OpenRouter or Gemini, see llm.py) -> reply. Setup: docs/discord-bot.md

Usage:
    python bot/discord_bot.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

import discord
from discord import app_commands
from dotenv import load_dotenv

from llm import make_asker
from rag import format_context, merge_glossary, search_glossary

REPO_ROOT = BOT_DIR.parent
DISCORD_MAX_CHARS = 2000
MAX_QUESTION_CHARS = 300
# Each question costs one LLM call, billed to whoever owns the API key.
RATE_LIMIT_CALLS = 20
RATE_LIMIT_WINDOW_S = 60 * 60

HELP_TEXT = (
    "Ask me about NS lingo! For example:\n"
    "- `what does rabak mean?`\n"
    "- `kena extra after SBA then cannot book out`\n"
    "- `what do you call someone who pretends to be sick?`\n"
    "Use `/ns`, mention me, or DM me."
)

log = logging.getLogger("ns_lingo_bot")


class RateLimiter:
    """At most `max_calls` per user in any rolling `window_s` seconds."""

    def __init__(self, max_calls: int, window_s: int):
        self.max_calls = max_calls
        self.window_s = window_s
        self._calls: dict[int, deque[float]] = defaultdict(deque)

    def check(self, user_id: int) -> int:
        """Record a call and return 0 if allowed, else seconds until the next free slot."""
        now = time.monotonic()
        calls = self._calls[user_id]
        while calls and now - calls[0] >= self.window_s:
            calls.popleft()
        if len(calls) >= self.max_calls:
            return int(self.window_s - (now - calls[0])) + 1
        calls.append(now)
        return 0


def answer_question(question: str, glossary: list[dict], ask) -> str:
    """Retrieve glossary context, ask the LLM, and format a Discord-sized reply."""
    hits = search_glossary(question, glossary)
    answer = ask(question, format_context(hits)) or "Sorry, I couldn't come up with an answer."
    footer = f"\n-# Glossary: {', '.join(h['term'] for h in hits)}" if hits else ""
    room = DISCORD_MAX_CHARS - len(footer)
    if len(answer) > room:
        answer = answer[: room - 1] + "…"
    return answer + footer


class NSLingoBot(discord.Client):
    def __init__(self, ask, glossary: list[dict], guild_id: int | None = None):
        # No privileged intents needed: Discord still sends message content for
        # DMs and for messages that mention the bot.
        super().__init__(
            intents=discord.Intents.default(),
            # Never let a reply ping @everyone, roles or users, whatever the LLM writes.
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.ask = ask
        self.glossary = glossary
        self.guild_id = guild_id
        self.limiter = RateLimiter(RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW_S)
        self.tree = app_commands.CommandTree(self)
        self._register_commands()

    def _register_commands(self) -> None:
        @self.tree.command(name="ns", description="Ask what some NS lingo means")
        @app_commands.describe(question="e.g. what does rabak mean? / kena extra after SBA")
        async def ns(interaction: discord.Interaction, question: str) -> None:
            await interaction.response.defer(thinking=True)
            reply = await self.handle(interaction.user.id, question)
            quoted = f"> {question[:MAX_QUESTION_CHARS]}\n"
            await interaction.followup.send((quoted + reply)[:DISCORD_MAX_CHARS])

    async def setup_hook(self) -> None:
        if self.guild_id:
            # Guild sync shows /ns immediately; global sync can take up to an hour.
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id %s)", self.user, self.user.id)

    async def handle(self, user_id: int, question: str) -> str:
        question = question.strip()
        if not question:
            return HELP_TEXT
        if len(question) > MAX_QUESTION_CHARS:
            return f"That's a bit long. Please keep questions under {MAX_QUESTION_CHARS} characters."
        wait = self.limiter.check(user_id)
        if wait:
            return f"You've hit the limit of {RATE_LIMIT_CALLS} questions an hour. Try again in {wait // 60 + 1} min."

        log.info("user=%s q=%r", user_id, question)
        try:
            return await asyncio.to_thread(answer_question, question, self.glossary, self.ask)
        except Exception:
            log.exception("Failed to answer %r", question)
            return "Sorry, something went wrong on my side. Try again in a bit."

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        is_dm = message.guild is None
        if not is_dm and self.user not in message.mentions:
            return

        question = re.sub(rf"<@!?{self.user.id}>", "", message.content).strip()
        async with message.channel.typing():
            reply = await self.handle(message.author.id, question)
        await message.reply(reply, mention_author=False)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    load_dotenv(REPO_ROOT / ".env")

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("DISCORD_BOT_TOKEN not set in .env (see docs/discord-bot.md)")
        return 1
    guild_id = os.getenv("DISCORD_GUILD_ID")

    ask, model = make_asker()
    glossary = merge_glossary()
    log.info("Model %s, %d glossary entries. Loading embedding model...", model, len(glossary))
    search_glossary("warm up", glossary)  # load embeddings now, not on the first question

    bot = NSLingoBot(ask, glossary, int(guild_id) if guild_id else None)
    bot.run(token, log_handler=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
