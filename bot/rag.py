"""Glossary lookup for RAG (seed + curated, curated wins on dedupe)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
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


@lru_cache(maxsize=None)
def _alias_pattern(alias: str) -> re.Pattern:
    """Match alias as a whole word/phrase (so 'mo' doesn't hit 'mono'), allowing a plural."""
    return re.compile(rf"(?<!\w){re.escape(alias)}(?:s|es)?(?!\w)")


def _normalise(text: str) -> str:
    """Lowercase and treat hyphens/underscores as spaces ('book-out' -> 'book out')."""
    return re.sub(r"\s+", " ", re.sub(r"[-_]", " ", text.lower())).strip()


def _compact(text: str) -> str:
    """Drop everything but letters/digits ('SAR 21' -> 'sar21', 'Chao Keng' -> 'chaokeng')."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _query_grams(query: str, max_n: int = 4) -> set[str]:
    """Compacted 1..max_n word windows of the query, for spacing/typo-tolerant matching."""
    words = re.findall(r"[a-z0-9]+", query.lower())
    return {
        "".join(words[i : i + n])
        for n in range(1, max_n + 1)
        for i in range(len(words) - n + 1)
    }


def _within_edits(a: str, b: str, limit: int) -> bool:
    """True if Levenshtein distance between a and b is <= limit."""
    if abs(len(a) - len(b)) > limit:
        return False
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > limit:
            return False
        prev = cur
    return prev[-1] <= limit


def _typo_limit(alias: str) -> int:
    """Allowed typos by length. Short terms (ORD, mo, SBA) must match exactly, and so
    must codes with a short part (pes b4, Attend C), where one character changes the meaning."""
    if any(len(w) <= 2 for w in re.findall(r"[a-z0-9]+", alias)):
        return 0
    n = len(_compact(alias))
    if n < 5:
        return 0
    return 1 if n < 9 else 2


def _score_entry(q_norm: str, q_grams: set[str], entry: dict) -> int:
    score = 0
    for alias in _aliases(entry):
        if _alias_pattern(alias).search(q_norm) or _alias_pattern(_normalise(alias)).search(q_norm):
            score += 10 + len(alias)
            continue
        alias_compact = _compact(alias)
        if not alias_compact:
            continue
        # Spacing variants: 'standby bed', 'chaokeng', 'SAR21', 'PES B 4'
        if alias_compact in q_grams or alias_compact + "s" in q_grams:
            score += 10 + len(alias)
            continue
        # Small typos: 'rabbak'. Scored below exact matches.
        limit = _typo_limit(alias)
        if limit and any(_within_edits(alias_compact, g, limit) for g in q_grams):
            score += 5 + len(alias)
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
    semantic: bool = True,
) -> list[dict]:
    """Return glossary entries most relevant to the user query.

    Keyword matches (exact, spacing variants, small typos) first, then up to
    SEMANTIC_MAX_HITS meaning-based matches when semantic=True.
    """
    if entries is None:
        entries = merge_glossary()

    q_norm = _normalise(query)
    q_grams = _query_grams(query)
    scored: list[tuple[int, dict]] = []
    for entry in entries:
        score = _score_entry(q_norm, q_grams, entry)
        if score > 0:
            scored.append((score, entry))

    # Boost entries matching extracted focus phrase exactly
    for focus in extract_focus_terms(query):
        for entry in entries:
            if focus == entry["term"].lower() or focus in _aliases(entry):
                scored.append((100 + len(focus), entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    ranked = [entry for _, entry in scored]
    # Keyword hits come first (precise); meaning-based hits fill in after them,
    # which is what catches paraphrases like "pretends to be sick" -> Chao Keng.
    if semantic:
        ranked.extend(semantic_search(query, entries))

    seen: set[str] = set()
    results: list[dict] = []
    for entry in ranked:
        key = entry["term"].lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(entry)
        if len(results) >= limit:
            break
    return results


# --- Semantic (embedding) search -------------------------------------------

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Cosine similarity cutoff. On the retrieval eval, real matches score ~0.55-0.77
# and unrelated entries stay under ~0.5 (e.g. "zombie parade" -> NDP 0.51).
SEMANTIC_MIN_SCORE = 0.55
SEMANTIC_MAX_HITS = 3

_embed_model = None
_embed_index: dict[tuple, object] = {}


def _entry_text(entry: dict) -> str:
    return f"{entry['term']}: {entry.get('definition', '')}"


def semantic_search(
    query: str,
    entries: list[dict],
    *,
    min_score: float = SEMANTIC_MIN_SCORE,
    max_hits: int = SEMANTIC_MAX_HITS,
) -> list[dict]:
    """Glossary entries whose meaning is close to the query, best first.

    Runs locally (no API). Returns [] if sentence-transformers isn't installed.
    """
    global _embed_model
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return []

    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL)

    texts = tuple(_entry_text(e) for e in entries)
    matrix = _embed_index.get(texts)
    if matrix is None:
        matrix = _embed_model.encode(list(texts), normalize_embeddings=True)
        _embed_index[texts] = matrix

    q = _embed_model.encode([query], normalize_embeddings=True)[0]
    scores = matrix @ q
    best = scores.argsort()[::-1][:max_hits]
    return [entries[i] for i in best if scores[i] >= min_score]


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
