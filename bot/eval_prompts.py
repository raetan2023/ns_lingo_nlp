"""Shared NS evaluation prompts."""

SYSTEM_PROMPT = """You are an expert on Singapore National Service (NS), SAF slang, and Singaporean military culture.

Answer using Singapore NS/SAF context only. Be concise and accurate.
If the glossary excerpts do not support an answer, say you don't know — do not invent definitions."""

RAG_INSTRUCTION = """Use the glossary excerpts below as the primary source of truth.
Prefer these definitions over general knowledge when they apply.
If excerpts conflict with your prior knowledge, follow the glossary."""

DEFAULT_NS_PROMPTS = [
    "What does rabak mean in NS?",
    "Explain pes b4 to someone who never served NS.",
    "What is bookout in National Service?",
    "Translate this NS sentence to plain English: Sgt say mono intake very jialat.",
    "What does ORD mean in Singapore NS?",
    "Explain what PES A means for enlistment.",
    "What is remedial training in NS?",
    "What does stand by area mean in army camp?",
]
