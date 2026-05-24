import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone

HEADERS = {"User-Agent": "ns_lingo_nlp/1.0 (research project)"}

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/raw")
SUBREDDIT = "NationalServiceSG"


def load_latest_posts_file():
    files = sorted(RAW_DIR.glob(f"{SUBREDDIT}_*.json"))

    if not files:
        raise FileNotFoundError(f"No {SUBREDDIT} raw post files found in {RAW_DIR}")

    return files[-1]


def fetch_comments(permalink):
    url = f"https://www.reddit.com{permalink}.json"

    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    return resp.json()


def extract_comments(comment_listing):
    comments = []

    def walk(items):
        for item in items:
            if item.get("kind") != "t1":
                continue

            data = item.get("data", {})

            body = data.get("body", "")
            if not body or body in {"[deleted]", "[removed]"}:
                continue

            comments.append({
                "id": data.get("id"),
                "parent_id": data.get("parent_id"),
                "body": body,
                "score": data.get("score"),
                "created_utc": data.get("created_utc"),
                "author": data.get("author"),
                "permalink": data.get("permalink"),
                "depth": data.get("depth")
            })

            replies = data.get("replies")
            if isinstance(replies, dict):
                reply_items = replies.get("data", {}).get("children", [])
                walk(reply_items)

    walk(comment_listing)
    return comments


def main():
    posts_path = load_latest_posts_file()

    with open(posts_path, "r", encoding="utf-8") as f:
        posts = json.load(f)

    all_comments = []

    print(f"Loading posts from {posts_path}")

    for post in posts:
        data = post.get("data", {})
        title = data.get("title", "")
        permalink = data.get("permalink")

        if not permalink:
            continue

        print(f"Fetching comments: {title}")

        try:
            reddit_json = fetch_comments(permalink)

            # reddit_json[0] = post data
            # reddit_json[1] = comments data
            comment_listing = reddit_json[1]["data"]["children"]
            comments = extract_comments(comment_listing)

            for comment in comments:
                comment["post_id"] = data.get("id")
                comment["post_title"] = title
                comment["post_permalink"] = permalink

            all_comments.extend(comments)
            print(f"  Found {len(comments)} comments")

            time.sleep(1)

        except Exception as e:
            print(f"  Failed to fetch comments for {title}: {e}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"{SUBREDDIT}_comments_{ts}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_comments)} comments to {output_path}")


if __name__ == "__main__":
    main()