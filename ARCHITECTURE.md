# Architecture — NS Lingo NLP Project

## Overview

Corpus-building and NLP exploration project for Singapore National Service (NS) lingo. Raw text is scraped from public sources, processed into candidate terms, validated with NS friends, and curated into a structured glossary. End goal is a Discord bot that explains NS lingo to civilians.

---
git p
## Data Pipeline (top to bottom)

```
scraper/ ──► data/raw ──► corpus/ ──► data/cleaned ──► data/glossary ──► bot/
                 │                      │
                 ▼                      ▼
          (never modify)        (processed versions)
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         scraper/                                     │
│  reddit_scraper.py    hwz_scraper.py    manual_crowdsource.py       │
│  ────────────────     ─────────────     ────────────────────         │
│  Public JSON API      requests +        Google Form / CSV            │
│  (no auth needed)     BeautifulSoup     ingest                        │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ raw JSON / HTML
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         data/                                        │
│  raw/          — scraped output, never touch                        │
│  cleaned/      — deduped, normalised, tokenised                     │
│  glossary/     — curated schema entries (see schema below)          │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ cleaned text
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         corpus/                                      │
│  frequency.py           extract.py           compare.py             │
│  ─────────────          ──────────           ──────────             │
│  word / n-gram          candidate term       diff against           │
│  counts                 extraction           standard English       │
│                                               freq lists            │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ candidate terms (CSV/JSON)
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Validation (manual step)                          │
│  Google Form → NS friends confirm/reject candidates                 │
│  Output: curated glossary entries                                   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ confirmed entries
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         bot/ (future)                                 │
│  discord_bot.py        rag_engine.py        glossary_loader.py      │
│  ──────────────        ─────────────        ──────────────────      │
│  slash commands        retrieval-           loads curated           │
│  + message hook        augmented            glossary into           │
│                        generation           vector store            │
│                                             + cache                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Glossary Schema

| Field | Description | Example |
|-------|-------------|---------|
| `term` | The main term | `rabak` |
| `variants` | Alternate spellings / clippings | `rabz` |
| `definition` | Dictionary-style definition | "Disorderly, chaotic, or messed up" |
| `example_sentences` | Usage in context | "Sgt chao keng rabak already" |
| `etymology` | Origin of the term | Hokkien; `rah bak` (literally "meat mash") |
| `register` | Informality level | `informal` / `vulgar` / `formal` |
| `vocation_scope` | Which NS vocations use it | `universal` / `BMT` / `infantry` / `naval` / `airforce` |
| `related_terms` | Cross-references | `chao keng`, `geng` |
| `part_of_speech` | Grammatical category | `adjective` / `verb` / `noun` / `interjection` |
| `user_facing_explanation` | Plain-English or Singlish explanation for civilians | "It means someone is acting disorderly or things are in chaos." |

---

## Data Sources

| Source | Method | Auth? | Status |
|--------|--------|-------|--------|
| r/NationalServiceSG | Public JSON API | None | ✅ Active |
| r/singapore | Public JSON API | None | ✅ Active |
| HWZ NS/SAF subforum | requests + BeautifulSoup | None | 🔜 Planned |
| Manual crowdsourcing | Google Form → CSV | Google API | 🔜 Planned |

---

## Project Structure

```
ns_lingo_nlp/
├── .env                     # Environment variables
├── main.py                  # Entry point (currently Reddit scraper)
├── requirements.txt         # Python dependencies
├── README.md                # Project overview
├── architecture.md          # This file
│
├── data/
│   ├── raw/                 # Raw scraped data (never edit)
│   ├── cleaned/             # Normalised / tokenised text
│   └── glossary/            # Curated glossary entries
│
├── scraper/
│   ├── reddit_scraper.py    # Reddit JSON API scraper
│   ├── hwz_scraper.py       # HardwareZone scraper (future)
│   └── manual_ingest.py     # Google Form → glossary loader
│
├── corpus/
│   ├── frequency.py         # Word / n-gram frequency analysis
│   ├── extract.py           # Candidate term extraction
│   └── compare.py           # Compare against standard English freq lists
│
├── bot/                     # (future)
│   ├── discord_bot.py
│   ├── rag_engine.py
│   └── glossary_loader.py
│
└── notebooks/               # Jupyter notebooks for exploration
```

---

## Dependencies

| Package | Purpose | Stage |
|---------|---------|-------|
| `python-dotenv` | Load `.env` variables | Core |
| `requests` | HTTP calls (Reddit JSON API) | Scraper |
| `beautifulsoup4` | HTML parsing (HWZ) | Scraper |
| `discord.py` | Discord bot framework | Bot (future) |
| `nltk` / `spaCy` | NLP (tokenisation, lemmatisation) | Corpus |
| `sentence-transformers` | Embeddings for RAG | Bot (future) |

---

## Environments / Config

- `.env` — user-specific secrets (e.g. `ANTHROPIC_API_KEY`, `REDDIT_USER_AGENT`)
- No Reddit API keys required — public JSON endpoints are used
- Conda environment: `ns_lingo_nlp`
