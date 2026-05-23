import json
from pathlib import Path

RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")

KEEP_FIELDS = {
    "id", "subreddit", "title", "selftext", "permalink", "url",
    "score", "upvote_ratio", "num_comments", "created_utc",
    "author", "over_18", "stickied",
}


def clean_post(post: dict) -> dict:
    data = post.get("data", {})
    return {k: data.get(k) for k in KEEP_FIELDS}


def main():
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(RAW_DIR.glob("*.json"))
    if not raw_files:
        print("No raw JSON files found in data/raw/")
        return

    for raw_path in raw_files:
        with open(raw_path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        cleaned = [clean_post(p) for p in posts]

        out_name = raw_path.stem + "_cleaned.json"
        out_path = CLEANED_DIR / out_name

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)

        raw_size = raw_path.stat().st_size
        clean_size = out_path.stat().st_size
        print(f"{raw_path.name}: {len(posts)} posts, {raw_size//1024}KB -> {clean_size//1024}KB")


if __name__ == "__main__":
    main()
