NS Lingo NLP Project
A corpus-building and NLP exploration project focused on Singapore National Service (NS) lingo. The goal is to build a glossary of NS-specific terms and eventually a Discord bot that explains NS lingo to civilians (girlfriends, parents, future enlistees).
Project owner is a CS undergraduate in Singapore, new to NLP and AI. The project is a passion project for learning, not production software. Vibe-coding with Claude Code and OpenCode while learning NLP concepts in parallel.
Current stage: corpus building and scraping.
Tech stack: Python, conda environment, Jupyter notebooks for exploration, discord.py for the bot layer (later). 
Project structure:
data/raw — scraped data, never modify directly. data/cleaned — processed versions. data/glossary — curated schema entries. scraper/ — Reddit and HWZ scrapers. corpus/ — candidate term extraction and frequency analysis. bot/ — Discord bot, to be built later. notebooks/ — Jupyter notebooks for exploration.
Data sources: Reddit (r/NationalServiceSG, r/singapore), HardwareZone NS/SAF subforum, manual crowdsourcing from NS friends.
Corpus approach: scrape raw text, run frequency analysis, compare against standard English frequency lists to surface NS-specific candidate terms, validate with NS friends via Google Form, curate into structured glossary schema.
Glossary schema fields: term, variants (including clippings like rabak → rabz), definition, example sentences, etymology (Hokkien/Malay/SAF acronym/English military), register (informal/vulgar/formal), vocation scope (universal/BMT/infantry/naval etc), related terms, part of speech, user-facing explanation.
NLP concepts being explored: corpus linguistics, keyword extraction, lemmatisation, frequency analysis, embeddings, RAG (retrieval augmented generation).
End goal: Discord bot that takes a sentence containing NS lingo and explains it naturally in plain English or Singlish, grounded in the curated glossary to prevent hallucination.

All of the above info is subject to change