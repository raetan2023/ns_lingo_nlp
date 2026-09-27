"""
Compare answers from keyword RAG vs the full glossary in the prompt.

Runs every case in bot/retrieval_cases.json through the LLM twice:
    rag   top keyword hits from search_glossary (what rag_eval.py does)
    full  every glossary entry in the prompt (~10k tokens)

An answer "passes" if it names an expected term (spacing/case ignored), or, for
expect_none cases, if it says it doesn't know. This is a rough automatic check;
read bot/answer_eval_results.txt for the real picture.

Cost on google/gemini-3.1-flash-lite: about $0.10 per full run of 40 cases.

Usage:
    python bot/answer_eval.py
    python bot/answer_eval.py --mode full --category paraphrase
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from dotenv import load_dotenv

from rag import format_context, merge_glossary, search_glossary
from llm import make_asker

CASES_PATH = BOT_DIR / "retrieval_cases.json"
OUTPUT_JSON = BOT_DIR / "answer_eval_results.json"
OUTPUT_TXT = BOT_DIR / "answer_eval_results.txt"
MODES = ("rag", "full")

DONT_KNOW = re.compile(
    r"don'?t know|do not know|not (?:in|found in|covered|listed|mentioned)|no (?:information|definition|entry)|not sure|unable to",
    re.I,
)


def _compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _names_term(answer: str, term: str) -> bool:
    # 'Attend B / LD (light duty)' -> also accept just 'Attend B'
    candidates = {term, re.split(r"\s*[/(]", term)[0]}
    compact_answer = _compact(answer)
    return any(_compact(c) and _compact(c) in compact_answer for c in candidates)


def grade(case: dict, answer: str) -> bool:
    if case.get("expect_none"):
        return bool(DONT_KNOW.search(answer))
    return all(
        any(_names_term(answer, opt.strip()) for opt in group.split("|"))
        for group in case.get("expect", [])
    )


def run(cases: list[dict], modes: list[str]) -> dict:
    ask, model = make_asker()
    glossary = merge_glossary()
    full_context = format_context(glossary)

    def answer(case: dict, mode: str) -> dict:
        context = full_context if mode == "full" else format_context(search_glossary(case["query"], glossary))
        text = ask(case["query"], context)
        return {"mode": mode, "answer": text, "pass": grade(case, text)}

    jobs = [(i, mode) for i in range(len(cases)) for mode in modes]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda job: answer(cases[job[0]], job[1]), jobs))

    rows = [{**case, "answers": {}} for case in cases]
    for (i, mode), res in zip(jobs, results):
        rows[i]["answers"][mode] = res
    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "modes": modes,
        "full_context_chars": len(full_context),
        "results": rows,
    }


def summarise(payload: dict) -> list[str]:
    modes = payload["modes"]
    totals: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for row in payload["results"]:
        for mode in modes:
            t = totals[row["category"]][mode]
            t[0] += row["answers"][mode]["pass"]
            t[1] += 1

    lines = [f"{'category':<15}" + "".join(f"{m:>10}" for m in modes)]
    grand = {m: [0, 0] for m in modes}
    for cat, by_mode in totals.items():
        cells = []
        for m in modes:
            p, t = by_mode[m]
            grand[m][0] += p
            grand[m][1] += t
            cells.append(f"{p}/{t}".rjust(10))
        lines.append(f"{cat:<15}" + "".join(cells))
    lines.append(f"{'TOTAL':<15}" + "".join(f"{grand[m][0]}/{grand[m][1]}".rjust(10) for m in modes))
    return lines


def write_outputs(payload: dict) -> None:
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        f"Answer eval: {payload['run_at']}",
        f"Model: {payload['model']}",
        f"Full glossary context: {payload['full_context_chars']} chars",
        "",
        *summarise(payload),
        "",
    ]
    for i, row in enumerate(payload["results"], start=1):
        lines.append("=" * 72)
        lines.append(f"[{i}] ({row['category']}) {row['query']}")
        expect = "should say it doesn't know" if row.get("expect_none") else ", ".join(row.get("expect", []))
        lines.append(f"Expect: {expect}")
        for mode in payload["modes"]:
            res = row["answers"][mode]
            lines.append(f"--- {mode} [{'PASS' if res['pass'] else 'FAIL'}]")
            lines.append(res["answer"])
        lines.append("")

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="RAG vs full-glossary answer eval")
    parser.add_argument("--mode", choices=MODES, action="append", dest="modes")
    parser.add_argument("--category")
    args = parser.parse_args()

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]
    modes = args.modes or list(MODES)

    print(f"Running {len(cases)} cases x {len(modes)} modes...")
    payload = run(cases, modes)
    write_outputs(payload)
    print("\n".join(summarise(payload)))
    print(f"\nWrote {OUTPUT_TXT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
