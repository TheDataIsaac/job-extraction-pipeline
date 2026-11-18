"""Ask ZenRows Crawl for the posting links on a careers page. depth=1 means the links on the
start page only."""

import re
import time

import requests
from fetch_pages import Settings
from find_postings import POSTING_LINK

START = "https://canonical.com/careers/all"
CRAWLS = "https://api.zenrows.com/v1/crawls"


def main() -> None:
    headers = {"X-API-Key": Settings().zenrows_api_key}
    body = {"url": START, "depth": 1, "max_pages": 3, "include_patterns": ["/careers/"]}
    crawl = requests.post(CRAWLS, json=body, headers=headers, timeout=60).json()

    # A crawl runs in the background, so check on it every few seconds until it ends.
    while crawl["status"] == "running":
        time.sleep(3)
        crawl = requests.get(f"{CRAWLS}/{crawl['crawl_id']}", headers=headers, timeout=60).json()

    links = [result["url"] for result in crawl.get("results", [])]
    postings = [link for link in links if re.search(POSTING_LINK, link)]
    print(f"status: {crawl['status']}, coverage: {crawl['coverage']}")
    print(f"{len(links)} links found, {len(postings)} of them are postings")
    for link in links:
        print(" ", link)


if __name__ == "__main__":
    main()
