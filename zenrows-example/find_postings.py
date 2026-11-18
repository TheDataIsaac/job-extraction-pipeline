"""Find the job posting links on a careers page, once without JavaScript and once with it."""

import re
from pathlib import Path

from fetch_pages import Settings, fetch_markdown

LISTING = "https://canonical.com/careers/all"
POSTING_LINK = r"https?://canonical\.com/careers/\d+"  # a posting is /careers/ plus a number
LINKS_FILE = Path("outputs/canonical_links.txt")


def main() -> None:
    api_key = Settings().zenrows_api_key
    LINKS_FILE.parent.mkdir(exist_ok=True)

    for js_render in (False, True):
        markdown, credits = fetch_markdown(LISTING, api_key, js_render)
        links = sorted(set(re.findall(POSTING_LINK, markdown)))
        print(f"js_render={js_render}: {len(links)} posting links, {credits} credits")

    LINKS_FILE.write_text("\n".join(links) + "\n", encoding="utf-8")
    print(f"Saved the rendered links to {LINKS_FILE}")


if __name__ == "__main__":
    main()
