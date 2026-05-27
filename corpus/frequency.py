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
    "like", "also", "anyone", "know", "get", "got",
    "https", "http", "www", "com"
}

CUSTOM_STOPWORDS = {
    "any", "go", "there", "before", "may", "only", "now", "time",
    "hi", "all", "need", "should", "one", "thanks", "please",
    "think", "want", "see", "say", "mean", "able", "might",
    "about", "because", "after", "first", "their", "them",
    "would", "already", "quite", "really", "still", "then",
    "than", "here", "more", "some", "which", "even", "other",
    "things", "thing", "much", "very", "same", "next", "most",
    "last", "once", "went", "receive", "received", "posted",
    "heard", "called", "around", "through", "into", "out",
    "back", "yes", "no", "oh", "bro", "guys", "im", "i'm",
    "ll", "ve", "re", "don", "dont", "its", "etc",
    "am", "up", "too", "by", "during", "yet", "likely",
    "people", "help", "sure", "everyone", "call", "possible",
    "since", "those", "though", "few", "long", "way",
    "better", "true", "usually", "unless", "anything",
    "discord", "server", "faq", "mods", "reddit",
    "message", "compose", "questions", "discussions",
    "join", "our", "read", "frequently", "asked",
    "issues", "contact", "website", "web", "portal",
    "elon", "musk", "donald", "trump"
}

NS_KEEPWORDS = {
    "ns", "pes", "bmt", "ippt", "ptp", "bp", "pcc", "cmpb",
    "pop", "ocs", "scs", "coy", "tekong", "encik", "bmtc",
    "saf", "scdf", "c9", "b1", "b4", "mono", "vocation",
    "enlistment", "enlisting", "enlist", "unit", "intake",
    "admin", "combat", "camp", "army", "medical", "command"
}


def tokenize(text):
    text = text.lower()
    return re.findall(r"[a-zA-Z0-9']+", text)


def make_ngrams(tokens, n):
    return [
        " ".join(tokens[i:i + n])
        for i in range(len(tokens) - n + 1)
    ]


def is_clean_token(token):
    if len(token) <= 1:
        return False

    if token.isdigit():
        return False

    if token in NS_KEEPWORDS:
        return True

    if token in STOPWORDS:
        return False

    if token in CUSTOM_STOPWORDS:
        return False

    return True


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


def load_hwz_texts():
    texts = []

    for path in RAW_DIR.glob("hwz_ns_threads_*.json"):
        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        for post in posts:
            texts.append(post.get("thread_title", ""))
            texts.append(post.get("body", ""))

    return texts


def count_frequencies(texts):
    word_counter = Counter()
    bigram_counter = Counter()
    trigram_counter = Counter()

    for text in texts:
        tokens = tokenize(text)

        clean_tokens = [
            token for token in tokens
            if is_clean_token(token)
        ]

        word_counter.update(clean_tokens)
        bigram_counter.update(make_ngrams(clean_tokens, 2))
        trigram_counter.update(make_ngrams(clean_tokens, 3))

    return word_counter, bigram_counter, trigram_counter


def format_counter(counter, limit=100):
    return [
        {"term": term, "count": count}
        for term, count in counter.most_common(limit)
    ]


def save_frequency(word_counter, bigram_counter, trigram_counter):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {
        "words": format_counter(word_counter, 100),
        "bigrams": format_counter(bigram_counter, 100),
        "trigrams": format_counter(trigram_counter, 100),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved frequency results to {OUTPUT_PATH}")


if __name__ == "__main__":
    post_texts = load_post_texts()
    comment_texts = load_comment_texts()
    hwz_texts = load_hwz_texts()

    texts = post_texts + comment_texts + hwz_texts

    word_counter, bigram_counter, trigram_counter = count_frequencies(texts)

    print(f"Loaded {len(post_texts)} post text fields")
    print(f"Loaded {len(comment_texts)} comments")
    print(f"Loaded {len(hwz_texts)} HWZ post text fields")

    print("\nTop words:")
    for word, count in word_counter.most_common(20):
        print(f"{word}: {count}")

    print("\nTop bigrams:")
    for phrase, count in bigram_counter.most_common(20):
        print(f"{phrase}: {count}")

    print("\nTop trigrams:")
    for phrase, count in trigram_counter.most_common(20):
        print(f"{phrase}: {count}")

    save_frequency(word_counter, bigram_counter, trigram_counter)