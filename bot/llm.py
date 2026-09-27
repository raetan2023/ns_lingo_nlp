"""LLM client shared by the bot and eval scripts.

Uses OpenRouter if OPENROUTER_API_KEY is set, else Gemini direct (GEMINI_API_KEY).
Both run Gemini 3.1 Flash Lite so results stay comparable.
"""

from __future__ import annotations

import os

from eval_prompts import RAG_INSTRUCTION, SYSTEM_PROMPT

GEMINI_MODEL = "gemini-3.1-flash-lite"
OPENROUTER_MODEL = "google/gemini-3.1-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_prompt(question: str, glossary_context: str) -> str:
    return f"""{SYSTEM_PROMPT}

{RAG_INSTRUCTION}

## Glossary excerpts
{glossary_context}

## Question
{question}
"""


def make_asker():
    """Return (ask_fn, model_name) for whichever API key is configured."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        import requests

        def ask(question: str, glossary_context: str) -> str:
            resp = requests.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {openrouter_key}"},
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "user", "content": build_prompt(question, glossary_context)}
                    ],
                },
                timeout=60,
            )
            resp.raise_for_status()
            return (resp.json()["choices"][0]["message"]["content"] or "").strip()

        return ask, OPENROUTER_MODEL

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise RuntimeError("Set OPENROUTER_API_KEY or GEMINI_API_KEY in .env")

    from google import genai

    client = genai.Client(api_key=gemini_key)

    def ask(question: str, glossary_context: str) -> str:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=build_prompt(question, glossary_context),
        )
        return (response.text or "").strip()

    return ask, GEMINI_MODEL
