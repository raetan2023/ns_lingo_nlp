import json
import re
from pathlib import Path
import torch

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

FREQUENCY_PATH = Path("data/cleaned/frequency.json")
SEED_PATH = Path("data/glossary/seed.json")
OUTPUT_PATH = Path("data/glossary/candidates.json")
ANNOTATED_OUTPUT_PATH = Path("data/glossary/candidates_annotated.json")

MODEL_NAME = "aisingapore/Llama-SEA-LION-v3-8B"
MAX_CANDIDATES = 93

NOISE_WORDS = {
    "https", "http", "www", "com",
    "now", "how", "need", "will", "anyone", "know",
    "training", "questions", "appointment",
    "like", "also", "can", "get", "one", "two",
    "about", "after", "before", "then", "than",
    "what", "when", "where", "why", "who",
    "first", "only", "time", "course", "asking",
    "use", "there", "go", "may", "no", "yes",
    "website", "reddit", "discord", "server", "faq",
    "message", "compose", "mods", "contact", "issues",
    "elon", "musk", "donald", "trump"
}

KNOWN_NS_HINTS = {
    "pes", "bmt", "ippt", "ocs", "scs", "pcc",
    "ord", "nsf", "nsmen", "ict", "rt", "ptp",
    "mc", "mo", "sba", "soc", "sitest", "tekong",
    "encik", "wayang", "keng", "chao", "outfield",
    "pop", "oot", "mono", "intake", "guard", "duty",
    "coy", "bmtc", "cmpb", "saf", "scdf", "c9",
    "b1", "b4", "bp", "admin", "combat", "camp",
    "vocation", "enlistment", "remedial", "command"
}

KNOWN_NS_PHRASES = {
    "mono intake",
    "pes status",
    "pes bp",
    "pes b1",
    "pes b4",
    "pes c9",
    "guard duty",
    "sign extra",
    "outfield training",
    "stay in",
    "stay out",
    "combat ration",
    "bmt training",
    "medical review",
    "combat unit",
    "command school",
    "remedial training",
    "remedial training company",
    "pcc appointment",
    "water parade",
    "pasir ris camp",
    "nstc jalan bahar"
}


def load_json(path):
    if not path.exists():
        return [] if path != FREQUENCY_PATH else {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_seed_terms(seed_data):
    seed_terms = set()

    for entry in seed_data:
        term = entry.get("term", "")
        if term:
            seed_terms.add(term.lower())

    return seed_terms


def is_noisy_phrase(term_lower):
    words = term_lower.split()

    if len(words) < 2:
        return False

    if all(word in NOISE_WORDS for word in words):
        return True

    if any(word.startswith("2f") for word in words):
        return True

    if any("jrsw" in word for word in words):
        return True

    return False


def is_candidate(term, count):
    term_lower = term.lower()

    if count < 2:
        return False

    if term_lower in NOISE_WORDS:
        return False

    if term_lower in KNOWN_NS_HINTS:
        return True

    if term_lower in KNOWN_NS_PHRASES:
        return True

    if " " in term_lower:
        if is_noisy_phrase(term_lower):
            return False

        words = term_lower.split()

        if any(word in KNOWN_NS_HINTS for word in words):
            return True

        if count >= 3:
            return True

        return False

    if len(term_lower) <= 2:
        return False

    return False


def build_candidates():
    frequency_data = load_json(FREQUENCY_PATH)
    seed_data = load_json(SEED_PATH)
    seed_terms = get_seed_terms(seed_data)

    candidates = []
    seen_terms = set()

    frequency_sections = [
        ("word", frequency_data.get("words", [])),
        ("bigram", frequency_data.get("bigrams", [])),
        ("trigram", frequency_data.get("trigrams", [])),
    ]

    for term_type, items in frequency_sections:
        for item in items:
            term = item.get("term", "")
            count = item.get("count", 0)
            term_lower = term.lower()

            if not term_lower:
                continue

            if term_lower in seen_terms:
                continue

            if not is_candidate(term, count):
                continue

            seen_terms.add(term_lower)

            candidates.append({
                "term": term_lower,
                "term_type": term_type,
                "count": count,
                "source": "frequency_analysis",
                "in_seed_glossary": term_lower in seed_terms,
                "status": "unreviewed",
                "definition": "",
                "example_sentences": [],
                "notes": ""
            })

    return candidates


def save_candidates(candidates):
    save_json(OUTPUT_PATH, candidates)
    print(f"Saved {len(candidates)} candidates to {OUTPUT_PATH}")


def load_llm():
    print(f"Loading model: {MODEL_NAME}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",
        torch_dtype=torch.float16
    )

    return pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer
    )


def build_prompt(candidate):
    term = candidate["term"]

    return f"""<|system|>
You are an expert on Singapore National Service (NS) terminology, SAF slang, and Singaporean military culture.

Use Singapore military context only.

You must return ONLY valid JSON.

Choose exactly ONE value for:
- register
- part_of_speech
- confidence

Do not copy placeholder text.

<|user|>
Define this Singapore NS term:

{term}

Return JSON in this exact schema:

{{
  "definition": "short clear definition",
  "register": "formal",
  "part_of_speech": "noun",
  "confidence": "high",
  "review_needed": false
}}

Rules:
- definition must be concise
- use Singapore NS/SAF meaning only
- do not explain the JSON
- do not output markdown
- register must be one of:
  ["formal", "informal", "slang"]
- part_of_speech must be one of:
  ["noun", "verb", "acronym", "phrase"]
- confidence must be one of:
  ["low", "medium", "high"]
- review_needed must be true or false

Examples:
- PES = Physical Employment Standards
- BMT = Basic Military Training
- IPPT = Individual Physical Proficiency Test

<|assistant|>
"""


def extract_json_from_text(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def annotate_candidate(generator, candidate):
    prompt = build_prompt(candidate)

    result = generator(
        prompt,
        max_new_tokens=300,
        min_new_tokens=30,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        return_full_text=True,
        pad_token_id=generator.tokenizer.eos_token_id
    )[0]

    full_text = result["generated_text"]
    output = full_text[len(prompt):].strip()

    print("RAW OUTPUT:")
    print(repr(output))

    parsed = extract_json_from_text(output)

    if parsed is None:
        return {
            **candidate,
            "llm_annotation_status": "failed_parse",
            "llm_raw_output": output
        }

    return {
        **candidate,
        "definition": parsed.get("definition", ""),
        "register": parsed.get("register", "unknown"),
        "part_of_speech": parsed.get("part_of_speech", "unknown"),
        "confidence": parsed.get("confidence", "low"),
        "review_needed": parsed.get("review_needed", True),
        "llm_annotation_status": "parsed",
        "llm_raw_output": output
    }


def annotate_candidates(candidates):
    generator = load_llm()
    selected = candidates[:MAX_CANDIDATES]

    annotated = []

    for candidate in selected:
        print(f"Annotating: {candidate['term']}")
        annotated.append(annotate_candidate(generator, candidate))

    return annotated


if __name__ == "__main__":
    candidates = build_candidates()

    print("Candidate terms:")
    for item in candidates:
        print(f"- {item['term']} ({item['term_type']}, {item['count']})")

    save_candidates(candidates)

    annotated_candidates = annotate_candidates(candidates)
    save_json(ANNOTATED_OUTPUT_PATH, annotated_candidates)

    print(f"Saved annotated candidates to {ANNOTATED_OUTPUT_PATH}")