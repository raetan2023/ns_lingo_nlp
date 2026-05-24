# Architecture — NS Lingo NLP Project

## Overview

Corpus-building and NLP exploration project for Singapore National Service (NS) lingo.
Raw text is scraped from public sources and cross-referenced with existing NS dictionaries.
Candidate terms are pre-annotated via LLM, validated with NS friends, and curated into a
structured glossary. The curated glossary is used to fine-tune a Singlish language model
for understanding NS lingo in context. End goal is a Discord bot that explains NS lingo
to civilians, grounded in the curated glossary to prevent hallucination.

---

## Stages

The project is split into three sequential stages:

| Stage | What it produces | Status |
|-------|------------------|--------|
| **1 — Corpus & Glossary** | Cleaned text + curated glossary entries | 🔜 In progress |
| **2 — Model** | Fine-tuned Singlish model (adapted to NS lingo) | 🔜 Planned |
| **3 — Bot** | Discord bot (RAG + fine-tuned model) | 🔜 Planned |

---

## Pipeline (end-to-end)

```
EXISTING NS DICTIONARIES ──► seed_glossary.py ──► data/glossary/seed.json
                                                            │
SCRAPER ──► data/raw ──► clean.py ──► data/cleaned/ ───────┤
 (Reddit)    (never touch)     │         (posts + comments) │
                               │                            │
                               ▼                            ▼
                    corpus/frequency.py ──► frequency list (learning)
                    corpus/extract.py   ──► candidate terms + LLM pre-annotation
                                                    │
                                                    ▼
                                          Google Form / CSV
                                          Human validation (me + NS friends)
                                                    │
                                                    ▼
                                          data/glossary/curated.json
                                                    │
                    ┌───────────────────────────────┘
                    │
                    ▼
          fine_tune/prepare_data.py ──► training dataset (glossary pairs + NS comments)
                    │
                    ▼
          fine_tune/train.py ──► fine-tuned Singlish model
                    │
                    ▼
          bot/ ──► Discord bot (RAG over glossary + fine-tuned model)
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         scraper/                                                      │
│  reddit_scraper.py    hwz_scraper.py    seed_glossary.py    manual_ingest.py          │
│  ────────────────     ─────────────     ────────────────    ────────────────────      │
│  Public JSON API      requests +        Scrapes existing    Google Form / CSV          │
│  (no auth needed)     BeautifulSoup     NS dictionaries     ingest                     │
└───────────────────────┬──────────────────────────────────────────────────────────────┘
                        │ raw JSON / HTML
                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         data/                                                          │
│  raw/          — scraped output, never touch                                          │
│  cleaned/      — deduped, normalised text (posts + comments)                          │
│  glossary/     — curated schema entries (seed, candidates, final)                     │
└───────────────────────┬──────────────────────────────────────────────────────────────┘
                        │ cleaned text
                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         corpus/                                                       │
│  frequency.py           extract.py                                                     │
│  ─────────────          ──────────                                                     │
│  word / n-gram          candidate term extraction (LLM-assisted)                      │
│  counts (learning)      + pre-annotation into glossary schema                         │
└───────────────────────┬──────────────────────────────────────────────────────────────┘
                        │ candidate terms (JSON / CSV)
                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    Validation (manual step)                                            │
│  Google Form / CSV → NS friends confirm/reject candidates                             │
│  Output: curated glossary entries → data/glossary/curated.json                       │
└───────────────────────┬──────────────────────────────────────────────────────────────┘
                        │ confirmed entries
                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         fine_tune/                                                     │
│  prepare_data.py        train.py                                                       │
│  ────────────────       ─────────                                                      │
│  Converts curated       Fine-tunes a pre-trained Singlish model (e.g.                  │
│  glossary + NS          singlish-bert or a small LLM) to understand                    │
│  comments into          NS lingo. Uses:                                                │
│  training pairs         • term-definition pairs → classification                        │
│                         • NS-lingo sentences → masked language modelling               │
│                         • glossary QA pairs → generation                               │
└───────────────────────┬──────────────────────────────────────────────────────────────┘
                        │ fine-tuned model
                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         bot/ (future)                                                   │
│  discord_bot.py        rag_engine.py        glossary_loader.py                         │
│  ──────────────        ─────────────        ──────────────────                         │
│  slash commands        retrieval-           loads curated                               │
│  + message hook        augmented            glossary into                               │
│                        generation           vector store                                │
│                                             + cache                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Glossary Schema

| Field | Description | Example |
|-------|-------------|---------|
| `term` | The main term | `rabak` |
| `variants` | Alternate spellings / clippings | `rabz` |
| `definition` | Dictionary-style definition | "Disorderly, chaotic, or messed up" |
| `example_sentences` | Usage in context extracted from corpus | "Sgt chao keng rabak already" |
| `etymology` | Origin of the term | Hokkien; `rah bak` (literally "meat mash") |
| `register` | Informality level | `informal` / `vulgar` / `formal` |
| `vocation_scope` | Which NS vocations use it | `universal` / `BMT` / `infantry` / `naval` / `airforce` |
| `related_terms` | Cross-references | `chao keng`, `geng` |
| `part_of_speech` | Grammatical category | `adjective` / `verb` / `noun` / `interjection` |
| `user_facing_explanation` | Plain-English or Singlish explanation for civilians | "It means someone is acting disorderly or things are in chaos." |

---

## Glossary Pipeline Detail

### 1. Seed (existing dictionaries)

Existing NS lingo dictionaries (e.g. r/NationalServiceSG wiki, Urban Dictionary entries,
blog posts) are scraped via `scraper/seed_glossary.py` and saved as
`data/glossary/seed.json`. This provides a baseline set of known terms with basic
definitions, so we can focus on finding gaps and adding real-world example sentences.

### 2. Corpus extraction

Cleaned posts and comments from `data/cleaned/` are processed by `corpus/extract.py` to
surface candidate terms not already in the seed glossary. Two methods:

- **Frequency analysis** (`corpus/frequency.py`) — tokenise, count, filter stopwords.
  Primarily for learning NLP fundamentals (tokenisation, stopwords, n-grams).
- **LLM-assisted extraction** (`corpus/extract.py`) — feed cleaned comments to an LLM
  to identify likely NS-lingo terms with context and suggested definitions.

### 3. Pre-annotation

For each candidate term the LLM generates a first-pass glossary entry following the schema
above. Example sentences are pulled directly from the Reddit corpus for authenticity.

### 4. Human validation

Candidates are compiled into a Google Form or CSV. You and your NS friends mark each as:
- **Verified** — correct, move to curated glossary
- **Needs edits** — adjust definition / register / etymology
- **Reject** — not NS lingo

Output: `data/glossary/curated.json`

### 5. Fine-tuning (Stage 2)

The curated glossary + cleaned NS comments are converted into training examples:

| Training type | Input | Target | Purpose |
|---------------|-------|--------|---------|
| Term classification | "Sgt is damn rabak today" | Predict `rabak` | Teach model to spot NS terms |
| Definition retrieval | "What does rabak mean?" | "Disorderly, chaotic..." | QA pairs for generation |
| MLM (masked language) | "Sgt is damn [MASK] today" | `rabak` | Adapt Singlish model to NS context |

The fine-tuned model is used alongside RAG in the bot — the model provides contextual
understanding, while RAG grounds explanations in the curated glossary to prevent
hallucination.

---

## Data Sources

| Source | Method | Auth? | Status |
|--------|--------|-------|--------|
| r/NationalServiceSG | Public JSON API | None | ✅ Active |
| HWZ NS/SAF subforum | requests + BeautifulSoup | None | 🔜 Planned |
| Existing NS dictionaries | Web scrape / manual copy | None | 🔜 Planned |
| Manual crowdsourcing | Google Form → CSV | Google API | 🔜 Planned |

---

## Project Structure

```
ns_lingo_nlp/
├── .env                     # Environment variables
├── main.py                  # Entry point (Reddit scraper)
├── clean.py                 # Strips unnecessary fields from raw posts
├── fetch_comments.py        # Fetches comments for scraped posts
├── requirements.txt         # Python dependencies
├── README.md                # Project overview
├── ARCHITECTURE.md          # This file
│
├── data/
│   ├── raw/                 # Raw scraped data (never edit)
│   ├── cleaned/             # Deduped, normalised text (posts + comments)
│   └── glossary/            # Curated glossary entries
│       ├── seed.json        # Baseline terms from existing dictionaries
│       └── curated.json     # Final validated entries
│
├── scraper/
│   ├── reddit_scraper.py    # Reddit JSON API scraper
│   ├── hwz_scraper.py       # HardwareZone scraper (future)
│   ├── seed_glossary.py     # Scrapes existing NS dictionaries online
│   └── manual_ingest.py     # Google Form → glossary loader
│
├── corpus/
│   ├── frequency.py         # Word / n-gram frequency analysis (learning)
│   ├── extract.py           # Candidate term extraction + LLM pre-annotation
│   └── compare.py           # Compare against standard English freq lists
│
├── fine_tune/
│   ├── prepare_data.py      # Converts glossary + NS comments → training examples
│   └── train.py             # Fine-tunes a pre-trained Singlish model
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
| `beautifulsoup4` | HTML parsing (HWZ, existing dictionaries) | Scraper |
| `discord.py` | Discord bot framework | Bot (future) |
| `nltk` / `spaCy` | NLP (tokenisation, lemmatisation) | Corpus |
| `sentence-transformers` | Embeddings for RAG | Bot (future) |
| `transformers` | Fine-tuning Singlish model | Model |
| `datasets` | Training data management | Model |
| `torch` | ML framework | Model |

---

## Environments / Config

- `.env` — user-specific secrets (e.g. `ANTHROPIC_API_KEY`, `REDDIT_USER_AGENT`)
- No Reddit API keys required — public JSON endpoints are used
- Conda environment: `ns_lingo_nlp`
