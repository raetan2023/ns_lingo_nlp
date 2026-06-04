"""
LLM term extraction from NSR article pages using Gemini API (gemini-3.5-flash).
Processes BMT + General pages and outputs a unified candidates file.
"""

import json
import os
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai

GEMINI_MODEL = "gemini-3.1-flash-lite"

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

HEADERS = {"User-Agent": "ns_lingo_nlp/1.0 (research project)"}

EXTRACTION_PROMPT = """You are extracting Singapore National Service (NS) lingo terms from the text below.

A valid term must be ONE of:
- An acronym used in NS context (e.g., BMT, POP, SOC, CQB)
- A Singlish or Malay word used in camp (e.g., kena, wayang, sedia, encik)
- Slang or jargon with a specific NS meaning (e.g., shellscrape, sign extra, bookout)
- A drill command (e.g., sedia, senang diri, hormat senjata)
- A number or phrase that has specific NS significance (e.g., "1206" for the loss/damage form, "24km" for route march, "2-3" for post-field-camp cleaning days)

Do NOT extract:
- Routine activities described in plain English (e.g., "rifle cleaning", "boots cleaning", "washing of stores")
- General vocabulary that any English speaker would know

If you're confident a term is genuine NS-specific, include it in the "terms" list.
If you suspect a term might be NS-relevant but aren't completely sure, include it in the "uncertain" list instead.

Return a JSON object with exactly two keys:
{
  "terms": [{"term": "...", "definition": "..."}],
  "uncertain": [{"term": "...", "definition": "...", "reason": "why you're unsure"}]
}

If no terms found, return {"terms": [], "uncertain": []}. No other text.

Article text:
"""  # noqa: E501

# MVP scope: BMT + General pages from NSR_DISCOVERED_URLS
BMT_URLS = [
    "https://national-service.vercel.app/bmt-hub",
    "https://national-service.vercel.app/basic-military-training",
    "https://national-service.vercel.app/before-enlistment",
    "https://national-service.vercel.app/guide-on-uppes",
    "https://national-service.vercel.app/hair-requirement",
    "https://national-service.vercel.app/glasses-requirement",
    "https://national-service.vercel.app/command-school",
]

GENERAL_URLS = [
    "https://national-service.vercel.app/about",
    "https://national-service.vercel.app/apps",
    "https://national-service.vercel.app/army-shop-emart",
    "https://national-service.vercel.app/best-canteen-dishes",
    "https://national-service.vercel.app/contact",
    "https://national-service.vercel.app/faq",
    "https://national-service.vercel.app/free-time",
    "https://national-service.vercel.app/links",
    "https://national-service.vercel.app/meme-assets",
    "https://national-service.vercel.app/movies",
    "https://national-service.vercel.app/telegram-bots",
    "https://national-service.vercel.app/what-is-attend-c",
]


DELAY_BETWEEN_CALLS = 4


def fetch_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_article_sections(url):
    soup = fetch_soup(url)
    content = soup.select_one("article .nuxt-content")
    if not content:
        return []

    sections = []
    current_heading = "General"
    current_text = []

    for child in content.children:
        tag = child.name if hasattr(child, "name") else None
        if tag in ("h2", "h3"):
            if current_text:
                sections.append({"heading": current_heading, "text": " ".join(current_text).strip()})
            current_heading = child.get_text(" ", strip=True)
            current_text = []
        elif tag in ("p", "li", "blockquote", "td", "th"):
            t = child.get_text(" ", strip=True)
            if t:
                current_text.append(t)

    if current_text:
        sections.append({"heading": current_heading, "text": " ".join(current_text).strip()})

    return sections


def parse_gemini_response(content):
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if not json_match:
        return [], []

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError:
        return [], []

    terms = data.get("terms", [])
    uncertain = data.get("uncertain", [])
    return terms, uncertain


def extract_from_section(section_text):
    prompt = EXTRACTION_PROMPT + section_text
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        content = response.text
        terms, uncertain = parse_gemini_response(content)
        return terms, uncertain
    except Exception as e:
        print(f"    Gemini error: {e}")
        return [], []


def process_url(url, category):
    sections = extract_article_sections(url)
    if not sections:
        return [], []

    all_terms = []
    all_uncertain = []

    for i, section in enumerate(sections):
        text = section["text"]
        if len(text) < 30:
            continue

        if i > 0:
            time.sleep(DELAY_BETWEEN_CALLS)

        terms, uncertain = extract_from_section(text)
        for t in terms:
            t["source"] = url
            t["section"] = section["heading"]
            all_terms.append(t)
        for u in uncertain:
            u["source"] = url
            u["section"] = section["heading"]
            all_uncertain.append(u)

    return all_terms, all_uncertain


def dedupe(items):
    seen = set()
    result = []
    for item in items:
        key = item["term"].lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def main():
    all_terms = []
    all_uncertain = []

    urls = []
    for url in BMT_URLS:
        urls.append(("bmt", url))
    for url in GENERAL_URLS:
        urls.append(("general", url))

    for idx, (category, url) in enumerate(urls):
        slug = url.rstrip("/").split("/")[-1]
        print(f"[{idx+1}/{len(urls)}] [{category}/{slug}] ...", end=" ", flush=True)
        terms, uncertain = process_url(url, category)
        all_terms.extend(terms)
        all_uncertain.extend(uncertain)
        print(f"{len(terms)} terms, {len(uncertain)} uncertain")

        if idx < len(urls) - 1:
            time.sleep(DELAY_BETWEEN_CALLS)

    all_terms = dedupe(all_terms)
    all_uncertain = dedupe(all_uncertain)

    output = {
        "terms": all_terms,
        "uncertain": all_uncertain,
    }

    output_path = Path("data/glossary/candidates_nsr.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Done! {len(all_terms)} terms + {len(all_uncertain)} uncertain saved to {output_path}")
    print(f"{'='*60}")

    if all_terms:
        print("\nTerms:")
        for t in all_terms:
            print(f"  {t['term']:30s} | {t['definition'][:80]}")
    if all_uncertain:
        print("\nUncertain:")
        for u in all_uncertain:
            print(f"  {u['term']:30s} | {u['definition'][:80]}  [{u.get('reason', '')}]")


if __name__ == "__main__":
    main()
