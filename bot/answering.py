"""
Shared question handling for the chat bots (Discord, Telegram).

Each question: limits check -> search_glossary (keyword + embeddings, local)
-> one LLM call (OpenRouter or Gemini, see llm.py). The platform bots only
format the reply. One Answerer shared by both bots means one global limit
across both, and the embedding model is loaded once.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque

from llm import make_asker
from rag import format_context, merge_glossary, search_glossary

MAX_QUESTION_CHARS = 300
# Each question costs one LLM call, billed to whoever owns the API key. One cap across
# all users on all platforms together, so the bill can't run away.
GLOBAL_RATE_LIMIT_CALLS = 200
RATE_LIMIT_WINDOW_S = 60 * 60

log = logging.getLogger("ns_lingo_bot")


class RateLimiter:
    """At most `max_calls` in any rolling `window_s` seconds."""

    def __init__(self, max_calls: int, window_s: int):
        self.max_calls = max_calls
        self.window_s = window_s
        self._calls: deque[float] = deque()

    def wait(self) -> int:
        """0 if a call is allowed now, else seconds until the next free slot. Records nothing."""
        now = time.monotonic()
        while self._calls and now - self._calls[0] >= self.window_s:
            self._calls.popleft()
        if len(self._calls) >= self.max_calls:
            return int(self.window_s - (now - self._calls[0])) + 1
        return 0

    def record(self) -> None:
        self._calls.append(time.monotonic())


class Answerer:
    def __init__(self, ask, glossary: list[dict]):
        self.ask = ask
        self.glossary = glossary
        self.global_limiter = RateLimiter(GLOBAL_RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW_S)

    def warm_up(self) -> None:
        search_glossary("warm up", self.glossary)  # load embeddings now, not on the first question

    async def handle(self, user_key: str, question: str) -> tuple[str, list[str]] | None:
        """(answer, glossary terms used), or None for an empty question (caller shows help).

        `user_key` is platform-prefixed (e.g. "discord:123") and only used for logging.
        Refusals (too long, rate limited, errors) come back as an answer with no terms.
        """
        question = question.strip()
        if not question:
            return None
        if len(question) > MAX_QUESTION_CHARS:
            return f"That's a bit long. Please keep questions under {MAX_QUESTION_CHARS} characters.", []
        wait = self.global_limiter.wait()
        if wait:
            return f"I'm getting a lot of questions right now. Try again in {wait // 60 + 1} min.", []
        self.global_limiter.record()

        log.info("user=%s q=%r", user_key, question)
        try:
            return await asyncio.to_thread(self._answer, question)
        except Exception:
            log.exception("Failed to answer %r", question)
            return "Sorry, something went wrong on my side. Try again in a bit.", []

    def _answer(self, question: str) -> tuple[str, list[str]]:
        hits = search_glossary(question, self.glossary)
        answer = self.ask(question, format_context(hits)) or "Sorry, I couldn't come up with an answer."
        return answer, [h["term"] for h in hits]


def make_answerer() -> Answerer:
    """Answerer for whichever LLM key is in the environment, with embeddings preloaded."""
    ask, model = make_asker()
    answerer = Answerer(ask, merge_glossary())
    log.info("Model %s, %d glossary entries. Loading embedding model...", model, len(answerer.glossary))
    answerer.warm_up()
    return answerer
