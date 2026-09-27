"""
Score glossary retrieval (search_glossary) against labelled test cases.

No LLM calls, so it is free to run after every retrieval or glossary change.

Usage:
    python bot/retrieval_eval.py
    python bot/retrieval_eval.py --verbose      # show hits for passing cases too
    python bot/retrieval_eval.py --category spelling
    python bot/retrieval_eval.py --no-semantic  # keyword matching only

Cases live in bot/retrieval_cases.json. Each case has:
    query        the user message
    category     direct | sentence | false-positive | spelling | paraphrase | unknown
    expect       glossary terms that must be retrieved; "a|b" means either is fine
    forbid       (optional) terms that must NOT be retrieved
    expect_none  (optional) true if nothing beyond generic terms should match
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from rag import merge_glossary, search_glossary

CASES_PATH = BOT_DIR / "retrieval_cases.json"

# Hits on these are harmless context, not a false positive, for expect_none cases.
GENERIC_TERMS = {"ns", "national service", "saf"}


def check_case(case: dict, glossary: list[dict], semantic: bool = True) -> tuple[bool, list[str], list[str]]:
    hits = [h["term"] for h in search_glossary(case["query"], glossary, semantic=semantic)]
    hit_set = {h.lower() for h in hits}
    problems: list[str] = []

    for group in case.get("expect", []):
        options = [o.strip().lower() for o in group.split("|")]
        if not any(o in hit_set for o in options):
            problems.append(f"missing {group}")

    for term in case.get("forbid", []):
        if term.lower() in hit_set:
            problems.append(f"unwanted {term}")

    if case.get("expect_none"):
        extra = [h for h in hits if h.lower() not in GENERIC_TERMS]
        if extra:
            problems.append(f"should match nothing, got {', '.join(extra)}")

    return not problems, hits, problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Glossary retrieval eval")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--category")
    parser.add_argument("--no-semantic", action="store_true", help="keyword matching only")
    args = parser.parse_args()

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]

    glossary = merge_glossary()
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for case in cases:
        ok, hits, problems = check_case(case, glossary, semantic=not args.no_semantic)
        totals[case["category"]][0] += ok
        totals[case["category"]][1] += 1
        if not ok or args.verbose:
            status = "PASS" if ok else "FAIL"
            print(f"[{status}] ({case['category']}) {case['query']}")
            if problems:
                print(f"         {'; '.join(problems)}")
            print(f"         hits: {', '.join(hits) or '(none)'}")

    print("\nBy category:")
    passed = total = 0
    for cat, (p, t) in totals.items():
        print(f"  {cat:<15} {p}/{t}")
        passed += p
        total += t
    print(f"  {'TOTAL':<15} {passed}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
