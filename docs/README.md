# NS Lingo NLP Project

A corpus-building and NLP exploration project focused on Singapore National Service (NS) lingo. The goal is to build a glossary of NS-specific terms and eventually a Discord bot that explains NS lingo to civilians (girlfriends, parents, future enlistees).

The project owner is a CS undergraduate in Singapore, new to NLP and AI. The project is a passion project for learning, not production software.

> **Note:** All of the info below is subject to change.

---

## Current Stage
* Corpus building and scraping.

---

## Tech Stack
* **Language:** Python
* **Environment:** Conda
* **Exploration:** Jupyter Notebooks
* **Bot Layer:** `discord.py` (to be built later)

---

## Project Structure
* `data/raw` — Scraped data, never modify directly.
* `data/cleaned` — Processed versions.
* `data/glossary` — Curated schema entries.
* `scraper/` — Reddit and HWZ scrapers.
* `corpus/` — Candidate term extraction and frequency analysis.
* `bot/` — Discord bot, to be built later.
* `notebooks/` — Jupyter notebooks for exploration.

---

## Data Sources
* Reddit (`r/NationalServiceSG`, `r/singapore`)
* HardwareZone NS/SAF subforum
* Manual crowdsourcing from NS friends

---

## Corpus Approach
1. Scrape raw text.
2. Run frequency analysis.
3. Compare against standard English frequency lists to surface NS-specific candidate terms.
4. Validate with NS friends via Google Form.
5. Curate into structured glossary schema.

---

## Glossary Schema Fields
* **term**
* **variants** (including clippings like *rabak* → *rabz*)
* **definition**
* **example sentences**
* **etymology** (Hokkien / Malay / SAF acronym / English military)
* **register** (informal / vulgar / formal)
* **vocation scope** (universal / BMT / infantry / naval etc)
* **related terms**
* **part of speech**
* **user-facing explanation**

---

## NLP Concepts Being Explored
* Corpus linguistics
* Keyword extraction
* Lemmatisation
* Frequency analysis
* Embeddings
* RAG (Retrieval-Augmented Generation)

---

## End Goal
A Discord bot that takes a sentence containing NS lingo and explains it naturally in plain English or Singlish, grounded in the curated glossary to prevent hallucination.

---

## Iteration Roadmap

| Iter | Focus | What gets built |
|------|-------|-----------------|
| **1** (MVP) | Curated dictionaries + frequency pipeline | Expand `seed_glossary.py` to scrape all major NS dictionary sources. Run frequency analysis on Reddit + HWZ data. Output: comprehensive `seed.json` |
| **2** | Human-in-the-loop enrichment | Crowdsource from NS friends. LLM-assisted term extraction from forum data. Pattern-based bootstrapping. Review workflow (candidates → verified → merged). Output: `curated.json` with full glossary schema |
| **3** | Model + Bot | Fine-tune Singlish model on curated data. Build Discord bot with RAG. |

## Crowdsourcing Plan (Iter 2)

Collect terms directly from people who've served NS. This catches vocation-specific slang and colloquialisms no dictionary covers.

**Format:** Simple template — just `term` + `definition` + optional `example`:
```
Term: _________
Definition: _________
Example: _________
```

**Collection method:** TBD -- mass forward a google sheet?

### Future data sources

- **NS Vocations Handbook (PDF)** — `https://national-service.vercel.app/ns-vocations-handbook.pdf` — comprehensive guide to SAF/SCDF/SPF vocations. Valuable for iter 2+ to extract vocation-specific terms. PDF parsing needed.
