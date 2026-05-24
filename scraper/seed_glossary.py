import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = Path("data/glossary")
OUTPUT_PATH = OUTPUT_DIR / "seed.json"

HEADERS = {
    "User-Agent": "ns_lingo_nlp/1.0 (research project)"
}

SEED_URLS = [
    "https://national-service.vercel.app/lingo/",
    "https://safti.mindef.gov.sg/covid19/abbreviations/",
    "https://www.cmpb.gov.sg/life-in-ns/saf/ranks-and-drill-commands/",
    "https://defencepioneer.sg/pioneer-articles/12-saf-acronyms-you-need-to-know",
    "https://en.wikipedia.org/wiki/List_of_Singapore_abbreviations"
]

MANUAL_TERMS = [
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


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def fetch_soup(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def scrape_national_service_lingo():
    url = "https://national-service.vercel.app/lingo/"
    soup = fetch_soup(url)

    page_text = soup.get_text("\n")
    lines = [clean_text(line) for line in page_text.split("\n")]
    lines = [line for line in lines if line]
    

    entries = []

    known_terms = {
        "BMT(C)": "Basic Military Training Centre.",
        "PTP": "Physical training phase: extra BMT period for those who failed or did not attempt IPPT.",
        "IPPT": "Individual Physical Proficiency Test.",
        "SBA": "Stand by area; bunk inspection.",
        "SBO": "Skeletal battle order; helmet, LBS, and rifle.",
        "FBO": "Full battle order; helmet, LBS, field pack, and rifle.",
        "MO": "Medical officer; the person you go to in order to report sick.",
        "SOC": "Standard obstacle course.",
        "SAR 21": "Singapore Assault Rifle, 21st century.",
        "CQB": "Close quarter combat.",
        "POP": "Passing Out Parade; marks the end of basic military training.",
        "SCS": "Specialist Cadet School.",
        "OCS": "Officer Cadet School.",
        "SOL": "Stoppage of leave.",
        "Kenna": "To be subject to harsh or painful treatment.",
        "Semula": "A command meaning undo or repeat what you last did.",
        "Bobo": "Someone who cannot aim well.",
        "Wayang": "Acting differently when higher-ranking personnel are around.",
        "Saikang": "Menial or undesirable tasks.",
        "Rabak": "A messy, chaotic, or bad situation.",
        "Coy": "Company; a large military grouping.",
        "Platoon": "A military group smaller than a company.",
        "Section": "The smallest group in a company.",
        "Drop / Knock it down": "Go into the push-up position.",
        "Force prep": "Forced preparation before outfield or training.",
        "Turnout": "Being woken up suddenly for preparation or training.",
        "Act blur, live longer": "Pretending not to know something to avoid responsibility.",
        "You think, I thought, who confirm?": "Phrase used to scold someone for assuming without confirmation.",
        "PES": "Physical Employment Standard.",
        "Attend B / LD": "Light duty status.",
        "Attend C / MC": "Medical certificate; stay home and rest.",
    }

    for term, definition in known_terms.items():
        if term.lower() in page_text.lower():
            entries.append({
                "term": term,
                "definition": definition,
                "category": "ns_lingo",
                "source": url
            })

    return entries


def scrape_safti_abbreviations():
    url = "https://safti.mindef.gov.sg/covid19/abbreviations/"
    soup = fetch_soup(url)

    entries = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        for row in rows:
            cells = [
                clean_text(cell.get_text(" "))
                for cell in row.find_all(["td", "th"])
            ]

            if len(cells) < 2:
                continue

            term = cells[0]
            definition = cells[1]

            if term.lower() in {"acronym", "abbreviation", "term"}:
                continue

            entries.append({
                "term": term,
                "definition": definition,
                "category": "acronym",
                "source": url
            })

    return entries


def scrape_pioneer_terms():
    url = "https://defencepioneer.sg/pioneer-articles/12-saf-acronyms-you-need-to-know"
    soup = fetch_soup(url)

    entries = []

    paragraphs = soup.find_all(["p", "li"])

    for paragraph in paragraphs:
        text = clean_text(paragraph.get_text(" "))

        if ":" not in text:
            continue

        parts = text.split(":", 1)

        if len(parts) != 2:
            continue

        term = clean_text(parts[0])
        definition = clean_text(parts[1])

        if len(term) > 25:
            continue

        entries.append({
            "term": term,
            "definition": definition,
            "category": "saf_acronym",
            "source": url
        })

    return entries


def scrape_wikipedia_abbreviations():
    url = "https://en.wikipedia.org/wiki/List_of_Singapore_abbreviations"
    soup = fetch_soup(url)

    entries = []

    page_text = soup.get_text("\n")
    lines = [clean_text(line) for line in page_text.split("\n")]
    lines = [line for line in lines if line]

    in_military_section = False

    for line in lines:
        # flexible start
        if "SAFMI Military Institute" in line or "Troop lift" in line:
            in_military_section = True

        if not in_military_section:
            continue

        # flexible stop
        if "Science, technology and engineering" in line:
            break

        # remove bullet symbols
        line = line.lstrip("-•*").strip()

        # support hyphen, en dash, em dash
        match = re.split(r"\s[-–—]\s", line, maxsplit=1)

        if len(match) != 2:
            continue

        term, definition = match
        term = clean_text(term)
        definition = clean_text(definition)

        if not term or not definition:
            continue

        if len(term) > 40:
            continue

        entries.append({
            "term": term,
            "definition": definition,
            "category": "wikipedia_military_abbreviation",
            "source": url
        })

    return entries


def scrape_cmpb_terms():
    url = "https://www.cmpb.gov.sg/life-in-ns/saf/ranks-and-drill-commands/"
    soup = fetch_soup(url)

    entries = []

    known_terms = {
        "hentak kaki": "Malay drill command used during SAF marching drills.",
        "sedia": "Malay drill command meaning attention.",
        "senang diri": "Malay drill command meaning stand at ease.",
        "semula": "Malay drill command meaning repeat or restart.",
        "drill commands": "Commands used during SAF marching and parade drills."
    }

    page_text = clean_text(soup.get_text(" ")).lower()

    for term, definition in known_terms.items():
        if term.lower() in page_text:
            entries.append({
                "term": term,
                "definition": definition,
                "category": "drill_command",
                "source": url
            })

    return entries


def dedupe_entries(entries):
    seen = set()
    deduped = []

    for entry in entries:
        term = clean_text(entry.get("term", ""))
        definition = clean_text(entry.get("definition", ""))

        if not term or not definition:
            continue

        key = term.lower()

        if key in seen:
            continue

        seen.add(key)

        deduped.append({
            "term": term,
            "definition": definition,
            "category": entry.get("category", "unknown"),
            "source": entry.get("source", "unknown")
        })

    return sorted(deduped, key=lambda item: item["term"].lower())


def save_seed_glossary(entries):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(entries)} seed glossary entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    all_entries = []

    print("Scraping NS glossary sources...\n")

    all_entries.extend(MANUAL_TERMS)

    scrapers = [
        scrape_national_service_lingo,
        scrape_safti_abbreviations,
        scrape_pioneer_terms,
        scrape_wikipedia_abbreviations,
        scrape_cmpb_terms
    ]

    for scraper in scrapers:
        try:
            entries = scraper()
            all_entries.extend(entries)
            print(f"{scraper.__name__}: loaded {len(entries)} entries")
        except Exception as e:
            print(f"{scraper.__name__} failed: {e}")

    seed_entries = dedupe_entries(all_entries)

    save_seed_glossary(seed_entries)