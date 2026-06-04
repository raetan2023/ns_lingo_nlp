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

# URLs actively scraped by the real HTML parsers below
SCRAPED_URLS = [
    "https://national-service.vercel.app/lingo/",
    "https://national-service.vercel.app/army-dictionary",
    "https://national-service.vercel.app/commands",
    "https://safti.mindef.gov.sg/covid19/abbreviations/",
    "https://defencepioneer.sg/pioneer-articles/12-saf-acronyms-you-need-to-know",
    "https://en.wikipedia.org/wiki/List_of_Singapore_abbreviations",
    "http://speakgoodsinglishmovement.blogspot.com/2010/04/handy-ns-lingo-guide.html",
    "https://defencepioneer.sg/pioneer-articles/15jan25_news1",
]

# Pages auto-discovered on national-service.vercel.app
# User to verify before building parsers for these
NSR_DISCOVERED_URLS = {
    "lingo_dictionary": [
        "https://national-service.vercel.app/army-dictionary",
        "https://national-service.vercel.app/lingo",
        "https://national-service.vercel.app/commands",
    ],
    "bmt": [
        "https://national-service.vercel.app/bmt-hub",
        "https://national-service.vercel.app/basic-military-training",
        "https://national-service.vercel.app/before-enlistment",
        "https://national-service.vercel.app/guide-on-uppes",
        "https://national-service.vercel.app/hair-requirement",
        "https://national-service.vercel.app/glasses-requirement",
        "https://national-service.vercel.app/command-school",
        "https://national-service.vercel.app/bmt",
    ],
    "scs": [
        "https://national-service.vercel.app/scs-hub",
        "https://national-service.vercel.app/scs-tips",
        "https://national-service.vercel.app/specialist-cadet-school",
    ],
    "ranks_pes_vocations": [
        "https://national-service.vercel.app/ranks",
        "https://national-service.vercel.app/pes",
        "https://national-service.vercel.app/vocations",
        "https://national-service.vercel.app/transport-vocation",
        "https://national-service.vercel.app/storeman-non-combat",
    ],
    "songs": [
        "https://national-service.vercel.app/when-the-whistle-blows-song",
        "https://national-service.vercel.app/left-toe-right-toe-song",
        "https://national-service.vercel.app/infantry-song",
        "https://national-service.vercel.app/purple-light-song",
        "https://national-service.vercel.app/training-to-be-soldiers-song",
        "https://national-service.vercel.app/hentak-kaki-song",
        "https://national-service.vercel.app/army-life-song",
        "https://national-service.vercel.app/bmt-roar-pop-song",
        "https://national-service.vercel.app/songs",
    ],
    "finance": [
        "https://national-service.vercel.app/nsf-allowance",
        "https://national-service.vercel.app/saving-money",
        "https://national-service.vercel.app/financial-advice",
    ],
    "general": [
        "https://national-service.vercel.app/about",
        "https://national-service.vercel.app/apps",
        "https://national-service.vercel.app/army-shop-emart",
        "https://national-service.vercel.app/best-canteen-dishes",
        "https://national-service.vercel.app/contact",
        "https://national-service.vercel.app/faq",
        "https://national-service.vercel.app/free-time",
        "https://national-service.vercel.app/links",
        "https://national-service.vercel.app/movies",
        "https://national-service.vercel.app/telegram-bots",
        "https://national-service.vercel.app/what-is-attend-c",
    ],
    "tools_reference": [
        "https://national-service.vercel.app/ord-countdown",
        "https://national-service.vercel.app/ippt",
        "https://national-service.vercel.app/dates",
    ],
}

MANUAL_TERMS = [
    {"term": "ORD", "definition": "Operationally Ready Date", "category": "acronym", "source": "manual_seed"},
    {"term": "PES", "definition": "Physical Employment Standard", "category": "acronym", "source": "manual_seed"},
    {"term": "IPPT", "definition": "Individual Physical Proficiency Test", "category": "acronym", "source": "manual_seed"},
    {"term": "SCS", "definition": "Specialist Cadet School", "category": "acronym", "source": "manual_seed"},
    {"term": "OCS", "definition": "Officer Cadet School", "category": "acronym", "source": "manual_seed"},
    # From cmpb.gov.sg (site doesn't expose structured data)
    {"term": "hentak kaki", "definition": "Malay drill command used during SAF marching drills.", "category": "drill_command", "source": "https://www.cmpb.gov.sg/life-in-ns/saf/ranks-and-drill-commands/"},
    {"term": "sedia", "definition": "Malay drill command meaning attention.", "category": "drill_command", "source": "https://www.cmpb.gov.sg/life-in-ns/saf/ranks-and-drill-commands/"},
    {"term": "senang diri", "definition": "Malay drill command meaning stand at ease.", "category": "drill_command", "source": "https://www.cmpb.gov.sg/life-in-ns/saf/ranks-and-drill-commands/"},
    {"term": "semula", "definition": "Malay drill command meaning repeat or restart.", "category": "drill_command", "source": "https://www.cmpb.gov.sg/life-in-ns/saf/ranks-and-drill-commands/"},
    {"term": "drill commands", "definition": "Commands used during SAF marching and parade drills.", "category": "drill_command", "source": "https://www.cmpb.gov.sg/life-in-ns/saf/ranks-and-drill-commands/"},
    # From thesmartlocal.com (WordPress, no clean parse target)
    {"term": "Stand by Universe", "definition": "Command to unpack and clear everything from the bunk for inspection.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "Bobo King", "definition": "Someone who cannot shoot or aim properly.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "Whole lot knock it down", "definition": "Entire group ordered to do push-ups.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "Charlie Mike", "definition": "Continue Mission; the exercise or mission is not yet over.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "Eye-power", "definition": "Watching others work instead of helping.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "One time good one", "definition": "Do it once and do it well so you don't have to repeat.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "Reveille", "definition": "Morning wake-up call played on a bugle or speaker.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "Draw arms", "definition": "Collect weapons from the armskote (armoury).", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "1206", "definition": "Form signed when equipment is damaged or lost; payment deducted from salary.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "IA IA IA", "definition": "Immediate Action; shouted to indicate a weapon jam during firing.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    {"term": "Paradise now", "definition": "Declaration that the exercise is over.", "category": "media_article", "source": "https://thesmartlocal.com/read/read-army-english-phrases-ns/"},
    # From straitstimes.com (React SPA, cannot scrape)
    {"term": "Stand by bed", "definition": "Clean the bunk spotlessly for inspection.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    # Stand by universe already defined above from TSL
    {"term": "Fall in", "definition": "Command to assemble in formation.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    {"term": "Kiss the ground", "definition": "Command to get into push-up position.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    {"term": "Bobo shooter", "definition": "Someone who cannot shoot or aim properly.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    {"term": "Mangkuk", "definition": "Bowl; used to describe someone clumsy.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    {"term": "CAT 1", "definition": "Weather status that halts outdoor training due to lightning/heavy rain.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    {"term": "Change parade", "definition": "Punishment requiring recruits to switch between uniforms repeatedly.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    {"term": "Water parade", "definition": "Hydration break during training.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    {"term": "Sign extra", "definition": "Punishment requiring weekend stay-in at camp for extra duties.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    {"term": "Never mind", "definition": "Sarcastic phrase used by superiors; they mind a lot.", "category": "media_article", "source": "https://www.straitstimes.com/singapore/celebrating-ns50-stand-by-universe-and-other-ns-men-lingo"},
    # From shopee.sg/blog (WordPress, no clean parse target)
    {"term": "Kena Stun", "definition": "Rifle or rifle parts taken by a superior because you weren't careful.", "category": "media_article", "source": "https://shopee.sg/blog/nsf-phrases-singaporean-understand/"},
    {"term": "Bo Bo Shooter", "definition": "Someone who cannot shoot or aim properly.", "category": "media_article", "source": "https://shopee.sg/blog/nsf-phrases-singaporean-understand/"},
    {"term": "Chao Keng", "definition": "Feigning sickness to avoid training or duties.", "category": "media_article", "source": "https://shopee.sg/blog/nsf-phrases-singaporean-understand/"},
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

    entries = []
    content = soup.find("div", class_="nuxt-content")
    if not content:
        return entries

    for p in content.find_all("p"):
        strong = p.find("strong")
        if not strong:
            continue

        term = clean_text(strong.get_text(" "))
        if not term:
            continue

        # get everything after the <br> as the definition
        br = strong.find_next("br")
        if br:
            parts = []
            node = br.next_sibling
            while node:
                if isinstance(node, str):
                    text = node.strip()
                    if text:
                        parts.append(text)
                elif node.name == "br":
                    pass
                else:
                    text = node.get_text(" ", strip=True)
                    if text:
                        parts.append(text)
                node = node.next_sibling
            definition = clean_text(" ".join(parts))
        else:
            definition = ""

        if not definition:
            continue

        entries.append({
            "term": term,
            "definition": definition,
            "category": "ns_lingo",
            "source": url
        })

    return entries


def scrape_nsr_army_dictionary():
    url = "https://national-service.vercel.app/army-dictionary"
    soup = fetch_soup(url)
    entries = []
    content = soup.find("div", class_="nuxt-content")
    if not content:
        return entries
    for p in content.find_all("p"):
        strong = p.find("strong")
        if not strong:
            continue
        term = clean_text(strong.get_text(" "))
        if not term:
            continue
        br = strong.find_next("br")
        if not br:
            continue
        parts = []
        node = br.next_sibling
        while node:
            if isinstance(node, str):
                text = node.strip()
                if text:
                    parts.append(text)
            elif node.name == "br":
                pass
            else:
                text = node.get_text(" ", strip=True)
                if text:
                    parts.append(text)
            node = node.next_sibling
        definition = clean_text(" ".join(parts))
        if not definition:
            continue
        entries.append({
            "term": term,
            "definition": definition,
            "category": "ns_lingo",
            "source": url
        })
    return entries


def scrape_nsr_commands():
    url = "https://national-service.vercel.app/commands"
    soup = fetch_soup(url)
    entries = []
    content = soup.find("div", class_="nuxt-content")
    if not content:
        return entries
    for table in content.find_all("table"):
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            term = clean_text(cells[0].get_text(" "))
            definition = clean_text(cells[1].get_text(" "))
            if not term or not definition:
                continue
            entries.append({
                "term": term,
                "definition": definition,
                "category": "drill_command",
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


def scrape_sgsm_terms():
    url = "http://speakgoodsinglishmovement.blogspot.com/2010/04/handy-ns-lingo-guide.html"
    soup = fetch_soup(url)

    entries = []

    post_body = soup.find("div", class_="post-body")
    if not post_body:
        return entries

    bold_spans = post_body.find_all("span", style=re.compile(r"font-weight:\s*bold", re.I))

    for span in bold_spans:
        text = clean_text(span.get_text(" "))
        if not text:
            continue

        term = text.split(" - ")[0].split(" – ")[0].strip() if " - " in text or " – " in text else text.strip()

        if not term or len(term) > 40:
            continue

        # definition is the text following this span until the next bold span
        definition_parts = []
        node = span.next_sibling
        while node:
            if isinstance(node, str):
                definition_parts.append(node.strip())
            elif node.name == "br":
                pass
            elif node.name == "span" and node.get("style") and "bold" in node.get("style", "").lower():
                break
            elif node.name in ("div", "h2", "h3"):
                break
            else:
                text = node.get_text(" ", strip=True)
                if text:
                    definition_parts.append(text)
            node = node.next_sibling

        definition = clean_text(" ".join(definition_parts))
        if not definition:
            continue

        entries.append({
            "term": term,
            "definition": definition,
            "category": "community_guide",
            "source": url
        })

    return entries


def scrape_pioneer_2025_terms():
    url = "https://defencepioneer.sg/pioneer-articles/15jan25_news1"
    soup = fetch_soup(url)

    entries = []

    for h3 in soup.find_all("h3"):
        text = clean_text(h3.get_text(" "))
        # matches patterns like "1) Knock it down", "10) Paradise now"
        match = re.match(r"\d+\)\s*(.+)", text)
        if not match:
            continue

        term = match.group(1).strip()
        if not term or len(term) > 40:
            continue

        # get definition from the next sibling paragraph
        definition_parts = []
        node = h3.find_next_sibling()
        while node and node.name != "h3":
            if node.name == "p":
                text = clean_text(node.get_text(" "))
                if text:
                    definition_parts.append(text)
            node = node.find_next_sibling()

        definition = clean_text(" ".join(definition_parts))
        if not definition:
            continue

        entries.append({
            "term": term,
            "definition": definition,
            "category": "media_article",
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
        scrape_nsr_army_dictionary,
        scrape_nsr_commands,
        scrape_safti_abbreviations,
        scrape_pioneer_terms,
        scrape_wikipedia_abbreviations,
        scrape_sgsm_terms,
        scrape_pioneer_2025_terms,
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