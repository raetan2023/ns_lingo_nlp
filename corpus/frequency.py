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
    "if", "so", "not", "have", "has", "had", "do", "does", "did",
    "what", "when", "where", "why", "how", "who", "can", "will", "just",
    "like", "also", "anyone", "know", "get", "got", "still", "really",
    "https", "http", "www", "com"
}


def tokenize(text):
    text = text.lower()
    return re.findall(r"[a-zA-Z0-9']+", text)


def load_post_texts():
    texts = []

    for path in RAW_DIR.glob("NationalServiceSG_*.json"):
        if "comments" in path.name:
            continue

        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        for post in posts:
            data = post.get("data", {})
            texts.append(data.get("title", ""))
            texts.append(data.get("selftext", ""))

    return texts


def load_comment_texts():
    texts = []

    for path in RAW_DIR.glob("NationalServiceSG_comments_*.json"):
        with open(path, "r", encoding="utf-8") as f:
            comments = json.load(f)

        for comment in comments:
            texts.append(comment.get("body", ""))

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
        for word, count in counter.most_common(200)
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved frequency results to {OUTPUT_PATH}")


if __name__ == "__main__":
    post_texts = load_post_texts()
    comment_texts = load_comment_texts()

    texts = post_texts + comment_texts
    counter = count_words(texts)

    print(f"Loaded {len(post_texts)} post text fields")
    print(f"Loaded {len(comment_texts)} comments")
    print("\nTop terms:")

    for word, count in counter.most_common(40):
        print(f"{word}: {count}")

    save_frequency(counter)