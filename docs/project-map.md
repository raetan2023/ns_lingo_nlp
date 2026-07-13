# Project Map

## Top-level files

| Path | Purpose |
|------|---------|
| `.env` | Environment variables (secrets: API keys, Reddit user agent). Not committed. |
| `.gitignore` | Git ignore rules (venv, .env, `__pycache__`, data/raw) |
| `clean.py` | Strips unnecessary fields from raw Reddit JSON posts down to 13 useful fields |
| `fetch_comments.py` | Fetches comments for all unique scraped posts via Reddit JSON API, flattens reply trees, cleans output |
| `imports_check.ipynb` | Jupyter notebook to verify Python imports are working |
| `main.py` | Entry point: orchestrates Reddit scraping pipeline |
| `requirements.txt` | Python dependencies (python-dotenv, requests, beautifulsoup4) |
| `workflow.py` | Git workflow helper: `python workflow.py start` (pull + checkout master), `python workflow.py finish` (add, commit, push, optional merge) |

## Top-level directories

| Path | Purpose |
|------|---------|
| `.git/` | Git version control data |
| `.ipynb_checkpoints/` | Jupyter notebook auto-save checkpoints (not tracked) |
| `anaconda_projects/` | Anaconda Navigator project metadata (project_filebrowser.db) |
| `corpus/` | NLP corpus processing: frequency analysis, LLM extraction, curated merge |
| `data/` | All project data: raw scrapes, cleaned text, glossary entries |
| `docs/` | Project documentation (README, architecture, project map, glossary pipeline) |
| `scraper/` | Web scraping scripts (Reddit, glossary sources, HWZ) |

## `data/`

| Path | Purpose |
|------|---------|
| `data/raw/` | Raw scraped output — never edit directly (gitignored) |
| `data/cleaned/` | Deduped, normalised text posts + comments |
| `data/cleaned/frequency.json` | Word/n-gram frequency analysis output |
| `data/glossary/` | Glossary pipeline data (see [glossary-pipeline.md](glossary-pipeline.md)) |
| `data/glossary/seed.json` | Frozen baseline dictionary (292 terms). Dictionaries + Gemini NSR merge. Do not add forum candidates here. |
| `data/glossary/candidates.json` | Forum frequency candidates (93 terms). Triage file: `reviewed` or `rejected`. Definitions empty. |
| `data/glossary/candidates_annotated.json` | Same 93 terms with SEA-LION annotations (definitions, register, POS, confidence). Awaiting human validation. |
| `data/glossary/candidates_nsr.json` | Ephemeral Gemini intermediate output from `llm_extract.py` — not always in repo. Merges into `seed.json` after review. |
| `data/glossary/curated.json` | Forum-validated glossary (42 entries). Lean schema: `term`, `definition`, `variants`, `register`, `part_of_speech`, `source`, `definition_source`, `related_terms`, `example_sentences`, `notes`. |

## `corpus/`

| Path | Purpose |
|------|---------|
| `corpus/frequency.py` | Tokenises Reddit posts, comments, and HWZ threads. Computes word/bigram/trigram counts, filters stopwords. Outputs `frequency.json`. |
| `corpus/extract.py` | Loads frequency candidates, filters NS-related phrases, annotates with SEA-LION (`aisingapore/Llama-SEA-LION-v3-8B`). Outputs `candidates.json` and `candidates_annotated.json`. |
| `corpus/llm_extract.py` | Gemini-powered term extraction from national-service.vercel.app BMT + General pages. Outputs `candidates_nsr.json` for manual merge into `seed.json`. |

## `scraper/`

| Path | Purpose |
|------|---------|
| `scraper/fetch_comments.py` | Fetches comments for scraped Reddit posts, flattens nested reply trees, normalises output |
| `scraper/seed_glossary.py` | Scrapes existing NS lingo dictionaries (wikis, blogs, official pages) to build `seed.json` |
| `scraper/hwz_scraper.py` | Scans 500 most recent EDMW pages for NS-related thread titles, then scrapes full thread content |

## `docs/`

| Path | Purpose |
|------|---------|
| `docs/README.md` | Full project overview: goals, tech stack, data sources, glossary schema, NLP concepts, iteration roadmap, progress log |
| `docs/ARCHITECTURE.md` | System design: three-layer mental model, two parallel pipelines, stages, fine-tuning readiness |
| `docs/glossary-pipeline.md` | Focused guide: glossary file roles, review workflow, merge policy |
| `docs/project-map.md` | This file — maps every folder and file with descriptions |
