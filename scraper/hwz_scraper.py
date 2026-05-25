import json
import re
import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "ns_lingo_nlp/1.0 (research project)"}
RAW_DIR = Path("data/raw")
FORUM_URL = "https://forums.hardwarezone.com.sg"
EDMW_URL = f"{FORUM_URL}/forums/eat-drink-man-woman.16"
REVIEW_FILE = RAW_DIR / "hwz_matches_review.json"

MAX_PAGES = 50
MAX_REPLIES_PER_THREAD = 500
DELAY_SECONDS = 3

NS_KEYWORDS = {
    "bmt", "ippt", "ocs", "scs", "pcc", "ord", "nsf", "nsmen",
    "ict", "rt", "ptp", "mc", "mo", "sba", "soc", "sitest",
    "ns", "saf", "pns", "bmtc", "sbar",
    "tekong", "encik", "coy", "platoon", "section",
    "wayang", "chao keng", "keng", "geng", "rabak", "rabbak", "rabz",
    "saikang", "bobo", "siam", "peng",
    "outfield", "pop", "oot",
    "mono intake", "guard duty", "sign extra", "stay in", "stay out",
    "combat ration", "medical review", "pes status",
    "force prep", "knock it down", "turnout", "act blur",
    "duty", "guard", "intake", "pes",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]


def fetch_soup(url, retries=3):
    for attempt in range(retries):
        try:
            headers = {**HEADERS, "User-Agent": USER_AGENTS[attempt % len(USER_AGENTS)]}
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(DELAY_SECONDS * (attempt + 1))
            else:
                raise


def find_thread_pages(soup):
    last_page = 1
    page_links = soup.select(".pageNav-main a")
    for link in page_links:
        text = link.get_text(strip=True)
        if text.isdigit():
            num = int(text)
            if num > last_page:
                last_page = num
    return last_page


def extract_reply_count(item):
    meta_cell = item.select_one(".structItem-cell--meta")
    if not meta_cell:
        return 0

    dd = meta_cell.select_one("dd")
    if not dd:
        return 0

    text = dd.get_text(strip=True)
    text = re.sub(r"[^0-9]", "", text)
    return int(text) if text else 0


def search_thread_titles(start_page=1, count=MAX_PAGES):
    matching_threads = []
    skipped_big = 0
    end_page = start_page + count - 1

    for page in range(start_page, end_page + 1):
        url = EDMW_URL if page == 1 else f"{EDMW_URL}/page-{page}"

        try:
            soup = fetch_soup(url)
            thread_items = soup.select(".structItem--thread")

            for item in thread_items:
                title_el = item.select_one(".structItem-title a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                thread_url = title_el.get("href", "")

                if thread_url.startswith("/"):
                    thread_url = FORUM_URL + thread_url

                title_lower = title.lower()
                found_keywords = {
                    kw for kw in NS_KEYWORDS
                    if re.search(r'\b' + re.escape(kw) + r'\b', title_lower)
                }

                if not found_keywords:
                    continue

                replies = extract_reply_count(item)

                if replies > MAX_REPLIES_PER_THREAD:
                    skipped_big += 1
                    continue

                matching_threads.append({
                    "title": title,
                    "url": thread_url,
                    "author": item.get("data-author", ""),
                    "matched_keywords": list(found_keywords),
                    "source_page": page,
                    "replies": replies,
                })

            print(f"Page {page}/{end_page}: {len(matching_threads)} matches, {skipped_big} skipped (megathreads)")

            time.sleep(DELAY_SECONDS)

        except Exception as e:
            print(f"Page {page} failed: {e}")
            time.sleep(DELAY_SECONDS * 2)

    if skipped_big:
        print(f"\nSkipped {skipped_big} megathreads (> {MAX_REPLIES_PER_THREAD} replies)")

    return matching_threads


def scrape_thread(thread_info):
    url = thread_info["url"]
    all_posts = []

    try:
        soup = fetch_soup(url)
        total_pages = find_thread_pages(soup)

        for page in range(1, total_pages + 1):
            if page > 1:
                page_url = f"{url.rstrip('/')}/page-{page}"
                soup = fetch_soup(page_url)

            posts = soup.select("article.message--post")
            for post in posts:
                body_el = post.select_one(".bbWrapper")
                if not body_el:
                    continue

                body = body_el.get_text(strip=True)
                if not body or len(body) < 10:
                    continue

                author_el = post.select_one(".message-name .username")
                author = author_el.get_text(strip=True) if author_el else ""

                time_el = post.select_one("time")
                timestamp = time_el.get("datetime", "") if time_el else ""

                all_posts.append({
                    "author": author,
                    "body": body,
                    "timestamp": timestamp,
                    "thread_title": thread_info["title"],
                    "thread_url": thread_info["url"],
                })

            if page < total_pages:
                time.sleep(DELAY_SECONDS)

    except Exception as e:
        print(f"  Failed: {thread_info['title'][:60]} — {e}")

    return all_posts


def cmd_scan():
    start_page = 1
    count = MAX_PAGES
    if len(sys.argv) > 2:
        try:
            start_page = int(sys.argv[2])
            count = int(sys.argv[3]) if len(sys.argv) > 3 else MAX_PAGES
        except ValueError:
            pass

    end_page = start_page + count - 1
    print(f"=== Stage 1: Scanning EDMW pages {start_page}–{end_page} ===")
    matches = search_thread_titles(start_page, count)
    print(f"\nFound {len(matches)} NS-related threads\n")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_FILE, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)

    print(f"Saved candidate list to {REVIEW_FILE}")
    print("Edit this file to remove any unwanted threads (delete their entries),")
    print("then run: python scraper/hwz_scraper.py scrape")
    return matches


def cmd_scrape():
    if not REVIEW_FILE.exists():
        print(f"No review file found at {REVIEW_FILE}")
        print("Run 'python scraper/hwz_scraper.py scan' first")
        return

    with open(REVIEW_FILE, "r", encoding="utf-8") as f:
        matches = json.load(f)

    if not matches:
        print("No threads to scrape (review file is empty)")
        return

    print(f"=== Stage 2: Scraping {len(matches)} approved threads ===")
    all_posts = []
    for i, thread in enumerate(matches, 1):
        print(f"[{i}/{len(matches)}] Scraping: {thread['title'][:70]}")
        posts = scrape_thread(thread)
        all_posts.extend(posts)
        print(f"  -> {len(posts)} posts")
        time.sleep(DELAY_SECONDS)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = RAW_DIR / f"hwz_ns_threads_{ts}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    print(f"\n=== Done ===")
    print(f"Extracted {len(all_posts)} total posts from {len(matches)} threads")
    print(f"Saved to {output_path}")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "scan":
            cmd_scan()
        elif sys.argv[1] == "scrape":
            cmd_scrape()
        else:
            print("Usage:")
            print("  python scraper/hwz_scraper.py scan [start_page] [page_count]")
            print("  python scraper/hwz_scraper.py scrape")
            print()
            print("Examples:")
            print("  python scraper/hwz_scraper.py scan           # pages 1-50")
            print("  python scraper/hwz_scraper.py scan 51 100    # pages 51-150")
    else:
        cmd_scan()
        print(f"\nReview the threads in {REVIEW_FILE}, delete any unwanted entries,")
        print("then run: python scraper/hwz_scraper.py scrape")


if __name__ == "__main__":
    main()
