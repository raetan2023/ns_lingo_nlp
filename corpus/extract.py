import json
from pathlib import Path

FREQUENCY_PATH = Path("data/cleaned/frequency.json")
SEED_PATH = Path("data/glossary/seed.json")
OUTPUT_PATH = Path("data/glossary/candidates.json")

NOISE_WORDS = {
    "https", "http", "www", "com",
    "now", "how", "need", "will", "anyone", "know",
    "training", "questions", "appointment",
    "like", "also", "can", "get", "one", "two",
    "about", "after", "before", "then", "than",
    "what", "when", "where", "why", "who"
}

KNOWN_NS_HINTS = {
    "pes", "bmt", "ippt", "ocs", "scs", "pcc",
    "ord", "nsf", "nsmen", "ict", "rt", "ptp",
    "mc", "mo", "sba", "soc", "sitest", "tekong",
    "encik", "wayang", "keng", "chao", "outfield"
}


def load_json(path):
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_candidate(term, count):
    term_lower = term.lower()

    if term_lower in NOISE_WORDS:
        return False

    if count < 2:
        return False

    if term_lower in KNOWN_NS_HINTS:
        return True

    if term.isupper() and len(term) <= 6:
        return True

    if len(term_lower) <= 2:
        return False

    return False


def build_candidates():
    frequency_data = load_json(FREQUENCY_PATH)
    seed_data = load_json(SEED_PATH)

    seed_terms = {entry["term"].lower() for entry in seed_data}

    candidates = []

    for item in frequency_data:
        term = item["term"]
        count = item["count"]
        term_lower = term.lower()

        if not is_candidate(term, count):
            continue

        candidates.append({
            "term": term_lower,
            "count": count,
            "source": "frequency",
            "in_seed_glossary": term_lower in seed_terms,
            "status": "candidate",
            "notes": ""
        })

    return candidates


def save_candidates(candidates):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(candidates)} candidates to {OUTPUT_PATH}")


if __name__ == "__main__":
    candidates = build_candidates()

    print("Candidate terms:")
    for item in candidates:
        print(f"- {item['term']} ({item['count']})")

    save_candidates(candidates)