"""Glossary lookup for RAG (seed + curated, curated wins on dedupe)."""

from __future__ import annotations

import json
import re
from pathlib import Path

SEED_PATH = Path("data/glossary/seed.json")
CURATED_PATH = Path("data/glossary/curated.json")

EXTRACT_PATTERNS = [
    re.compile(r"what does (.+?) mean", re.I),
    re.compile(r"explain (.+?)(?:\s+to|\s+for|\?|$)", re.I),
    re.compile(r"what is (.+?)(?:\?|$)", re.I),
    re.compile(r"translate .+?:\s*(.+)$", re.I),
]


def load_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def merge_glossary() -> list[dict]:
    """Curated entries override seed entries with the same normalised term."""
    by_term: dict[str, dict] = {}

    for entry in load_json(SEED_PATH):
        term = entry.get("term", "").strip()
        if not term:
            continue
        key = term.lower()
        by_term[key] = {
            "term": term,
            "definition": entry.get("definition", ""),
            "variants": entry.get("variants", []),
            "source_file": "seed",
        }

    for entry in load_json(CURATED_PATH):
        term = entry.get("term", "").strip()
        if not term:
            continue
        key = term.lower()
        by_term[key] = {
            "term": term,
            "definition": entry.get("definition", ""),
            "variants": entry.get("variants", []),
            "related_terms": entry.get("related_terms", []),
            "source_file": "curated",
        }

    return list(by_term.values())


def _aliases(entry: dict) -> list[str]:
    names = [entry["term"].lower()]
    names.extend(v.lower() for v in entry.get("variants", []) if v)
    return names


def _score_entry(query: str, entry: dict) -> int:
    q = query.lower()
    score = 0
    for alias in _aliases(entry):
        if alias in q:
            score += 10 + len(alias)
        elif len(alias) > 3 and alias in q.replace("?", ""):
            score += 5
    definition = entry.get("definition", "").lower()
    if definition and any(word in definition for word in q.split() if len(word) > 4):
        score += 1
    return score


def extract_focus_terms(query: str) -> list[str]:
    """Pull likely target term(s) from a question."""
    found: list[str] = []
    for pattern in EXTRACT_PATTERNS:
        match = pattern.search(query)
        if match:
            phrase = match.group(1).strip(" .?!")
            if phrase:
                found.append(phrase.lower())
    return found


def search_glossary(
    query: str,
    entries: list[dict] | None = None,
    *,
    limit: int = 8,
) -> list[dict]:
    """Return glossary entries most relevant to the user query."""
    if entries is None:
        entries = merge_glossary()

    scored: list[tuple[int, dict]] = []
    for entry in entries:
        score = _score_entry(query, entry)
        if score > 0:
            scored.append((score, entry))

    # Boost entries matching extracted focus phrase exactly
    for focus in extract_focus_terms(query):
        for entry in entries:
            if focus == entry["term"].lower() or focus in _aliases(entry):
                scored.append((100 + len(focus), entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    seen: set[str] = set()
    results: list[dict] = []
    for _, entry in scored:
        key = entry["term"].lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(entry)
        if len(results) >= limit:
            break
    return results


def format_context(entries: list[dict]) -> str:
    if not entries:
        return "(No matching glossary entries found.)"
    blocks = []
    for entry in entries:
        lines = [f"term: {entry['term']}", f"definition: {entry['definition']}"]
        if entry.get("variants"):
            lines.append(f"variants: {', '.join(entry['variants'])}")
        if entry.get("related_terms"):
            lines.append(f"related_terms: {', '.join(entry['related_terms'])}")
        lines.append(f"source: {entry.get('source_file', 'unknown')}")
        blocks.append("\n".join(lines))
    return "\n\n---\n\n".join(blocks)
