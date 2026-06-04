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
| `corpus/` | NLP corpus processing: frequency analysis and candidate term extraction |
| `data/` | All project data: raw scrapes, cleaned text, glossary entries |
| `docs/` | Project documentation (README, architecture, project map) |
| `scraper/` | Web scraping scripts (Reddit, glossary sources) |

## `data/`

| Path | Purpose |
|------|---------|
| `data/raw/` | Raw scraped output — never edit directly (gitignored) |
| `data/cleaned/` | Deduped, normalised text posts + comments |
| `data/cleaned/frequency.json` | Word/n-gram frequency analysis output |
| `data/glossary/` | Curated glossary entries in JSON schema |
| `data/glossary/seed.json` | Baseline terms scraped from existing NS dictionaries |
| `data/glossary/candidates.json` | Candidate terms surfaced by LLM-assisted extraction |

## `corpus/`

| Path | Purpose |
|------|---------|
| `corpus/frequency.py` | Tokenises text from Reddit posts, Reddit comments, and HWZ threads. Computes word/n-gram counts, filters stopwords. Primarily for learning NLP fundamentals. |
| `corpus/extract.py` | LLM-assisted candidate term extraction. Feeds cleaned comments to an LLM to identify NS-lingo terms with context and suggested definitions. |

## `scraper/`

| Path | Purpose |
|------|---------|
| `scraper/fetch_comments.py` | Fetches comments for scraped Reddit posts, flattens nested reply trees, normalises output |
| `scraper/seed_glossary.py` | Scrapes existing NS lingo dictionaries (r/NationalServiceSG wiki, Urban Dictionary, blogs) to build seed glossary |
| `scraper/hwz_scraper.py` | Scans 500 most recent EDMW pages for NS-related thread titles, then scrapes full thread content |

## `docs/`

| Path | Purpose |
|------|---------|
| `docs/README.md` | Full project overview: goals, tech stack, data sources, glossary schema, NLP concepts, iteration roadmap, crowdsourcing plan |
| `docs/ARCHITECTURE.md` | Detailed architecture: 5-stage pipeline, component diagram, glossary pipeline, data flow |
| `docs/project-map.md` | This file — maps every folder and file with descriptions |
