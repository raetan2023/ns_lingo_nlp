"""
Evaluate Gemini with glossary RAG on the standard 8 NS prompts.

Backend: OpenRouter if OPENROUTER_API_KEY is set in .env, else Gemini direct
(GEMINI_API_KEY). Both run Gemini 3.1 Flash Lite so results stay comparable.

Usage:
    conda activate ns_lingo_nlp
    python bot/rag_eval.py
    python bot/rag_eval.py --prompt "What does rabak mean in NS?"

Outputs:
    bot/rag_eval_results.txt
    bot/rag_eval_results.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from dotenv import load_dotenv

from eval_prompts import DEFAULT_NS_PROMPTS, RAG_INSTRUCTION, SYSTEM_PROMPT
from rag import format_context, merge_glossary, search_glossary

OUTPUT_JSON = BOT_DIR / "rag_eval_results.json"
OUTPUT_TXT = BOT_DIR / "rag_eval_results.txt"
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


def run_eval(prompts: list[str]) -> dict:
    ask, model = make_asker()
    glossary = merge_glossary()
    rows = []

    for prompt in prompts:
        hits = search_glossary(prompt, glossary)
        context = format_context(hits)
        answer = ask(prompt, context)
        rows.append(
            {
                "prompt": prompt,
                "glossary_hits": [h["term"] for h in hits],
                "glossary_context": context,
                "response": answer,
            }
        )
        print(f"  {prompt[:55]}... -> {len(hits)} hits")

    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "mode": "gemini + glossary RAG",
        "prompts": prompts,
        "results": rows,
    }


def write_outputs(payload: dict) -> None:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    lines = [
        f"Gemini + RAG eval — {payload['run_at']}",
        f"Model: {payload['model']}",
        "",
    ]
    for i, row in enumerate(payload["results"], start=1):
        lines.append("=" * 72)
        lines.append(f"[{i}] {row['prompt']}")
        lines.append("=" * 72)
        lines.append(f"Glossary hits: {', '.join(row['glossary_hits']) or '(none)'}")
        lines.append("-" * 72)
        lines.append("CONTEXT:")
        lines.append(row["glossary_context"])
        lines.append("-" * 72)
        lines.append("ANSWER:")
        lines.append(row["response"])
        lines.append("")

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_TXT}")


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Gemini + glossary RAG eval")
    parser.add_argument("--prompt", action="append", dest="prompts")
    args = parser.parse_args()
    prompts = args.prompts or DEFAULT_NS_PROMPTS

    print(f"Running {len(prompts)} prompts with Gemini + RAG...")
    payload = run_eval(prompts)
    write_outputs(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
