import requests
import json
from pathlib import Path
from datetime import datetime, timezone

HEADERS = {"User-Agent": "ns_lingo_nlp/1.0 (research project)"}
SUBREDDITS = ["NationalServiceSG", "singapore"]
DATA_DIR = Path("data/raw")

def get_posts(subreddit, sort="hot", limit=25):
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["data"]["children"]

def get_comments(permalink):
    url = f"https://www.reddit.com{permalink}.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def save_posts(subreddit, posts):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = DATA_DIR / f"{subreddit}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    return path

if __name__ == "__main__":
    for sub in SUBREDDITS:
        print(f"\n=== r/{sub} ===")
        posts = get_posts(sub, sort="hot", limit=10)
        path = save_posts(sub, posts)
        print(f"Saved to {path}")
        for post in posts:
            d = post["data"]
            print(f"  [{d['score']:>4}] {d['title']}")
