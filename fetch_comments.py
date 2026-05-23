import json
import time
from pathlib import Path

import requests

HEADERS = {"User-Agent": "ns_lingo_nlp/1.0 (research project)"}
RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")
COMMENT_LIMIT = 100

KEEP_COMMENT_FIELDS = {
    "id", "body", "score", "author", "created_utc",
    "permalink", "parent_id", "depth",
    "subreddit", "link_id", "is_submitter", "stickied",
}


def dedup_posts(raw_dir: Path) -> dict[str, list[dict]]:
    seen = set()
    posts_by_sub = {}
    for f in sorted(raw_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            for post in json.load(fh):
                pid = post["data"]["id"]
                sub = post["data"]["subreddit"]
                if pid not in seen:
                    seen.add(pid)
                    posts_by_sub.setdefault(sub, []).append(post["data"])
    return posts_by_sub


def fetch_comments(permalink: str) -> list[dict]:
    url = f"https://www.reddit.com{permalink}.json?limit={COMMENT_LIMIT}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    if len(data) < 2:
        return []
    comment_listing = data[1]
    return comment_listing["data"]["children"]


def flatten_comments(children: list[dict], depth: int = 0) -> list[dict]:
    flat = []
    for child in children:
        if child["kind"] != "t1":
            continue
        cd = child["data"]
        cd["depth"] = depth
        flat.append(cd)
        replies = cd.get("replies")
        if replies and isinstance(replies, dict):
            reply_children = replies["data"]["children"]
            flat.extend(flatten_comments(reply_children, depth + 1))
    return flat


def clean_comment(comment: dict) -> dict:
    cleaned = {}
    for k in KEEP_COMMENT_FIELDS:
        cleaned[k] = comment.get(k)
    if cleaned["body"] == "[removed]" or cleaned["body"] == "[deleted]":
        return None
    return cleaned


def main():
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    posts_by_sub = dedup_posts(RAW_DIR)
    total_posts = sum(len(v) for v in posts_by_sub.values())
    print(f"Found {total_posts} unique posts across {len(posts_by_sub)} subreddits")

    for sub, posts in posts_by_sub.items():
        all_comments = []
        seen_ids = set()
        for i, post in enumerate(posts, 1):
            permalink = post["permalink"]
            print(f"  [{i}/{len(posts)}] Fetching comments for {post['id']} (r/{sub})")
            try:
                children = fetch_comments(permalink)
                flat = flatten_comments(children)
                for c in flat:
                    cleaned = clean_comment(c)
                    if cleaned and cleaned["id"] not in seen_ids:
                        seen_ids.add(cleaned["id"])
                        all_comments.append(cleaned)
                print(f"    Got {len(flat)} raw -> {len([c for c in flat if clean_comment(c)])} cleaned")
            except Exception as e:
                print(f"    FAILED: {e}")
            time.sleep(2)

        out_path = CLEANED_DIR / f"{sub}_comments.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_comments, f, indent=2, ensure_ascii=False)
        print(f"  r/{sub}: {len(all_comments)} total comments saved to {out_path}")
        print()


if __name__ == "__main__":
    main()
