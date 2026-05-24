import json
from pathlib import Path

SEED_URLS = [
    "https://national-service.vercel.app/lingo/",
    "https://safti.mindef.gov.sg/covid19/abbreviations/",
    "https://www.cmpb.gov.sg/life-in-ns/saf/ranks-and-drill-commands/"
]

# starter seed glossary
SEED_TERMS = [
    {
        "term": "ORD",
        "definition": "Operationally Ready Date",
        "category": "acronym",
        "source": "manual_seed"
    },
    {
        "term": "PES",
        "definition": "Physical Employment Standard",
        "category": "acronym",
        "source": "manual_seed"
    },
    {
        "term": "IPPT",
        "definition": "Individual Physical Proficiency Test",
        "category": "acronym",
        "source": "manual_seed"
    },
    {
        "term": "SCS",
        "definition": "Specialist Cadet School",
        "category": "acronym",
        "source": "manual_seed"
    },
    {
        "term": "OCS",
        "definition": "Officer Cadet School",
        "category": "acronym",
        "source": "manual_seed"
    }
]

OUTPUT_DIR = Path("data/glossary")
OUTPUT_PATH = OUTPUT_DIR / "seed.json"


def save_seed_glossary():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(SEED_TERMS, f, indent=2, ensure_ascii=False)

    print(f"Saved seed glossary to {OUTPUT_PATH}")


if __name__ == "__main__":
    print("NS Glossary Seed Sources:")
    for url in SEED_URLS:
        print("-", url)

    save_seed_glossary()