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

The project is split into five sequential stages:

| Stage | What it produces | Status |
|-------|------------------|--------|
| **1 — Scrape existing dictionaries** | `seed.json` with 292 entries from curated online dictionaries | ✅ Done |
| **2 — Forum data + frequency analysis** | Raw Reddit/HWZ text → cleaned → frequency list → candidate terms | ✅ Done |
| **3 — LLM extraction + crowdsourcing** | New candidates from forum text (LLM) and friends (crowdsourcing) → reviewed + merged into `curated.json` | 🔶 Partially done (Gemini extraction done, 59 terms in curated.json, crowdsourcing pending) |
| **4 — Model** | Fine-tuned Singlish model (adapted to NS lingo) | 🔜 Planned |
| **5 — Bot** | Discord bot (RAG + fine-tuned model) | 🔜 Planned |

---

## Pipeline (end-to-end)

```
EXISTING NS DICTIONARIES ──► seed_glossary.py ──► data/glossary/seed.json
                                                             │
SCRAPER ──► data/raw ──► clean.py ──► data/cleaned/ ───────┤
 (Reddit)    (never touch)     │         (posts + comments) │
                                │                            │
                                ▼                            ▼
                     corpus/frequency.py ──► frequency list (learning) ──► corpus/extract.py ──► data/glossary/candidates.json
                                                                                                          │
                                                                                                          ▼
                     national-service.vercel.app ──► corpus/llm_extract.py ──► manual review ──► data/glossary/curated.json
                                (Gemini API)                                 │
                                                                              │
                                                          data/glossary/seed.json (Iter 1 baseline, frozen)
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
│  main.py                hwz_scraper.py            seed_glossary.py          │
│  ────────               ─────────────             ────────────────            │
│  Scrapes Reddit         Scans EDMW titles         Scrapes existing            │
│  (public JSON API,      for NS keywords           NS dictionaries             │
│  no auth needed)        + scrapes threads                                     │
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
│  frequency.py           extract.py              llm_extract.py                          │
│  ─────────────          ──────────              ──────────────                          │
│  word / n-gram          Candidate term          Gemini-powered term extraction          │
│  counts (learning)      extraction +            from NSR website pages                  │
│                         SEA-LION annotation     (BMT + General)                         │
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

Existing NS lingo dictionaries (blog posts, media articles, community guides) are scraped
via `scraper/seed_glossary.py` and saved as `data/glossary/seed.json`. This provides a
baseline set of known terms with basic definitions.

| Source | Type |
|--------|------|
| national-service.vercel.app/lingo | Community wiki |
| SAFTI MI abbreviations page | Official |
| CMPB ranks and drill commands | Official |
| defencepioneer.sg articles | Media |
| thesmartlocal.com guide | Media |
| straitstimes.com article | Media |
| speakgoodsinglishmovement.blogspot.com | Community guide |
| shopee.sg blog | Media |

### 2. Corpus extraction (Iter 1 — MVP)

Cleaned posts and comments from `data/cleaned/` are processed to surface candidate terms
not already in the seed glossary:

- **Frequency analysis** (`corpus/frequency.py`) — tokenise, count n-grams, filter stopwords.
  Primarily for learning NLP fundamentals.
- **Candidate filtering** (`corpus/extract.py`) — filter frequency data against seed glossary
  using heuristics (all-caps acronyms, known NS hint words). Output: `candidates.json`.

### 3. LLM extraction + crowdsourcing (Iter 2)

- **LLM-assisted extraction** — two approaches:
  - `corpus/extract.py`: loads candidate terms from frequency analysis, prompts local SEA-LION model (`aisingapore/Llama-SEA-LION-v3-8B`) for structured definitions.
  - `corpus/llm_extract.py`: scrapes NSR website (national-service.vercel.app) BMT + General pages, sends each section to Gemini API (`gemini-3.1-flash-lite`) for term extraction. Outputs candidates with definitions for manual review.
- **Crowdsourcing** — collect terms directly from NS friends (term + definition + example).
- **Review workflow** — candidates go into `candidates.json`; you mark each as `reviewed` or `rejected` directly in the file; reviewed entries are extracted into `curated.json`.

### 4. Human validation (Iter 2)

Candidates from all sources are compiled for review in `candidates.json`. You mark each as:
- **reviewed** — correct NS term, included in `curated.json`
- **rejected** — not NS lingo, excluded

Output: `data/glossary/curated.json` (59 entries as of Iter 1)

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
| HWZ EDMW (keyword search) | requests + BeautifulSoup (title scan via EDMW pages) | None | ✅ Active |
| national-service.vercel.app | requests + BeautifulSoup + Gemini API for term extraction | None | ✅ Active |
| Existing NS dictionaries | Web scrape / manual copy | None | ✅ Done |
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
│   └── glossary/            # Glossary pipeline data
│       ├── seed.json                    # Baseline NS glossary terms (Iter 1, frozen)
│       ├── candidates.json              # Candidate terms from frequency analysis (reviewed + rejected)
│       ├── candidates_annotated.json   # SEA-LION annotated glossary candidates
│       └── curated.json                # Final validated glossary entries (59 terms)
│
├── scraper/
│   ├── hwz_scraper.py       # HardwareZone scraper (EDMW keyword scan + thread scrape)
│   ├── seed_glossary.py     # Scrapes existing NS dictionaries online
│   └── fetch_comments.py    # Fetches comments for scraped Reddit posts
│
├── corpus/
│   ├── frequency.py         # Word/bigram/trigram frequency analysis and candidate term generation
│   ├── extract.py           # LLM-assisted glossary annotation pipeline using SEA-LION
│   └── llm_extract.py       # Gemini-powered term extraction from NSR website pages
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
| `requests` | HTTP calls (Reddit JSON API, NSR pages) | Scraper |
| `beautifulsoup4` | HTML parsing (HWZ, NSR pages, existing dictionaries) | Scraper |
| `google-genai` | Google Gemini API client | LLM Extraction |
| `discord.py` | Discord bot framework | Bot (future) |
| `nltk` / `spaCy` | NLP (tokenisation, lemmatisation) | Corpus |
| `sentence-transformers` | Embeddings for RAG | Bot (future) |
| `datasets` | Training data management | Model |
| `transformers` | SEA-LION inference + future fine-tuning | Corpus / Model |
| `torch` | ML framework for model inference/training | Corpus / Model |
| `accelerate` | Device mapping/offloading for large models | Corpus / Model |
| `sentencepiece` | Tokenizer support for LLMs | Corpus / Model |

---

## Environments / Config

- `.env` — user-specific secrets (e.g. `GEMINI_API_KEY`)
- No Reddit API keys required — public JSON endpoints are used
- Conda environment: `ns_lingo_nlp`
