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
from collections import defaultdict, deque

from llm import make_asker
from rag import format_context, merge_glossary, search_glossary

MAX_QUESTION_CHARS = 300
# Each question costs one LLM call, billed to whoever owns the API key.
RATE_LIMIT_CALLS = 20
RATE_LIMIT_WINDOW_S = 60 * 60
# Cap across all users on all platforms together, so many people at once can't run up the bill.
GLOBAL_RATE_LIMIT_CALLS = 200
GLOBAL_KEY = "all"

log = logging.getLogger("ns_lingo_bot")


class RateLimiter:
    """At most `max_calls` per key (a user key, or GLOBAL_KEY) in any rolling `window_s` seconds."""

    def __init__(self, max_calls: int, window_s: int):
        self.max_calls = max_calls
        self.window_s = window_s
        self._calls: dict[str, deque[float]] = defaultdict(deque)

    def wait(self, key: str) -> int:
        """0 if a call is allowed now, else seconds until the next free slot. Records nothing."""
        now = time.monotonic()
        calls = self._calls[key]
        while calls and now - calls[0] >= self.window_s:
            calls.popleft()
        if len(calls) >= self.max_calls:
            return int(self.window_s - (now - calls[0])) + 1
        return 0

    def record(self, key: str) -> None:
        self._calls[key].append(time.monotonic())


class Answerer:
    def __init__(self, ask, glossary: list[dict]):
        self.ask = ask
        self.glossary = glossary
        self.limiter = RateLimiter(RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW_S)
        self.global_limiter = RateLimiter(GLOBAL_RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW_S)

    def warm_up(self) -> None:
        search_glossary("warm up", self.glossary)  # load embeddings now, not on the first question

    async def handle(self, user_key: str, question: str) -> tuple[str, list[str]] | None:
        """(answer, glossary terms used), or None for an empty question (caller shows help).

        `user_key` should be platform-prefixed (e.g. "discord:123") so IDs can't collide.
        Refusals (too long, rate limited, errors) come back as an answer with no terms.
        """
        question = question.strip()
        if not question:
            return None
        if len(question) > MAX_QUESTION_CHARS:
            return f"That's a bit long. Please keep questions under {MAX_QUESTION_CHARS} characters.", []
        # Check both limits before recording, so a refused question doesn't use up either.
        wait = self.limiter.wait(user_key)
        if wait:
            return f"You've hit the limit of {RATE_LIMIT_CALLS} questions an hour. Try again in {wait // 60 + 1} min.", []
        wait = self.global_limiter.wait(GLOBAL_KEY)
        if wait:
            return f"I'm getting a lot of questions right now. Try again in {wait // 60 + 1} min.", []
        self.limiter.record(user_key)
        self.global_limiter.record(GLOBAL_KEY)

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
