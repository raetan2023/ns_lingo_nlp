# NS Lingo NLP Project

A corpus-building and NLP exploration project focused on Singapore National Service (NS) lingo. The goal is to build a glossary of NS-specific terms and eventually a Discord bot that explains NS lingo to civilians (girlfriends, parents, future enlistees).

The project owner is a CS undergraduate in Singapore, new to NLP and AI. The project is a passion project for learning, not production software.

> **Note:** All of the info below is subject to change.

---

## Current Stage
* Glossary validation complete for MVP; fine-tuning prep next.

## Google Doc
https://docs.google.com/document/d/12e5w7t01ktPG1FdnyjvCXDvqB_FRq2o2jgoGjcZszCo/edit?usp=sharing

For the current pipeline mental model (two parallel glossary paths, file roles, merge workflow), see [ARCHITECTURE.md](ARCHITECTURE.md) and [glossary-pipeline.md](glossary-pipeline.md).

### Latest updates from Google Doc
27/05/26
Keon:
Improved corpus/frequency.py — Refined stopword filtering and NS-specific term handling by adding custom stopwords + NS keepwords to reduce noisy Reddit/HWZ terms. Frequency analysis now outputs separate word, bigram, and trigram sections for cleaner candidate extraction and NLP experimentation.
Built and debugged corpus/extract.py — Implemented an LLM-assisted glossary candidate extraction + pre-annotation pipeline:
Loads candidate terms from frequency.json
Filters likely NS-related terms using heuristics + known NS phrases
Uses SEA-LION (aisingapore/Llama-SEA-LION-v3-8B) to generate structured glossary annotations:
definitions
register classification
part-of-speech labels
confidence estimates
Parses and saves structured JSON annotations into candidates_annotated.json
Set up SEA-LION inference workflow — Initially tested locally in VS Code, then migrated inference to Google Colab GPU (Tesla T4) due to 8B model memory limitations. Successfully configured:
Hugging Face transformers pipeline
GPU inference workflow
Colab upload/download workflow
JSON parsing + annotation validation
Completed large-scale annotation runs — Successfully ran SEA-LION annotation on all 93 extracted NS glossary candidates:
Parsed: 93
Failed: 0
Verified the end-to-end glossary candidate annotation pipeline works successfully.
Identified early hallucination and ambiguity cases — Observed incorrect or overly generic annotations (e.g. PES ambiguity, incorrect SAF expansions, non-NS phrases), confirming the need for:
human validation/review stage
stronger Singapore NS context grounding
candidate filtering improvements
Established current NLP pipeline architecture:
Reddit/HWZ comments
→ frequency analysis
→ candidate extraction
→ SEA-LION annotation
→ structured glossary dataset
→ human validation (next step)


For next time:
Set up the validation step — Google Form or CSV for NS friends to review and correct SEA-LION annotated candidates.
Install transformers/torch and start preparing the fine-tuning pipeline once the glossary is validated.
04/06/26
Rae: 
1. Gemini Integration
Installed google-genai SDK
Use Gemini 3.1 Flash-Lite in   corpus/llm_extract.py 
Added rate-limit delays (4s between API calls)
Fixed .env: removed quotes from GEMINI_API_KEY
2. LLM Term Extraction
Ran extraction on all 19 BMT + General NSR pages (~4 min runtime)
Results: 86 terms + 32 uncertain (vs Ollama's 12 + 17 — massive improvement)
Extract included Singlish/Malay (kena, blur, paiseh, liao, wayang), NS slang (shellscrape, black tape, bookout, admin time), numbers (11B, 1206, 2-3), acronyms (CFC, CPL, RSM)
3. Seed.json Expansion
Manually reviewed and approved all 118 candidates (86 terms + 32 uncertain)
Cross-referenced against existing seed: 19 duplicates found
Merged 86 new terms into seed.json
292 entries total (was 206)

4. Git Sync
Committed our changes (seed.json + Gemini rewrite + cleanups)
Pulled Keon's 2 upstream commits (SEA-LION annotations, README edit)
Resolved merge conflicts on candidates.json (accepted Keon's version) and docs/README.md (merged both)
Pushed to origin/master at 7afe71a

20/06/26
Rae:
Reviewed all terms in candidate.json
Clean up comments in candidate.json
Move 59 reviewed terms to curated.json
Updates docs folder
Next steps:
Review Keon annotated candidates on SEA-LION
Install transformers/torch and start preparing the fine-tuning pipeline

13/07/26
Rae:
1. Curated cleanup — human review round complete; 42 entries in lean schema
2. Deleted noise/redundant terms (b4, b4 expect, activities admin, month-batch duplicates)
3. Added variants (intake, nsti), related_terms (pes family, ns fit), separate ns fit record
4. Stripped workflow fields (review_status, annotation_status, confidence, count, etc.)
5. Removed merge_curated.py — one-time merge workflow complete
6. Next: build fine_tune/prepare_data.py

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
