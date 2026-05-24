import json
import re
from collections import Counter
from pathlib import Path

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/cleaned")
OUTPUT_PATH = OUTPUT_DIR / "frequency.json"

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "is", "it", "for",
    "on", "with", "this", "that", "i", "you", "he", "she", "they", "we",
    "my", "your", "me", "are", "was", "be", "as", "at", "from", "but",
    "if", "so", "not", "have", "has", "had", "do", "does", "did"
}


def tokenize(text):
    text = text.lower()
    return re.findall(r"[a-zA-Z0-9']+", text)


def load_reddit_text():
    texts = []

    for path in RAW_DIR.glob("NationalServiceSG_*.json"):
        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        for post in posts:
            data = post.get("data", {})
            title = data.get("title", "")
            body = data.get("selftext", "")
            texts.append(title)
            texts.append(body)

    return texts


def count_words(texts):
    counter = Counter()

    for text in texts:
        tokens = tokenize(text)

        for token in tokens:
            if token not in STOPWORDS and len(token) > 1:
                counter[token] += 1

    return counter


def save_frequency(counter):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = [
        {"term": word, "count": count}
        for word, count in counter.most_common(100)
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved frequency results to {OUTPUT_PATH}")


if __name__ == "__main__":
    texts = load_reddit_text()
    counter = count_words(texts)

    print("Top terms:")
    for word, count in counter.most_common(30):
        print(f"{word}: {count}")

    save_frequency(counter)