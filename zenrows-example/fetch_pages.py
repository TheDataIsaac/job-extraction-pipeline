"""Fetch each job posting through ZenRows as markdown, clean it, and save it to postings.jsonl."""

import json
import re
from pathlib import Path

import requests
from pydantic_settings import BaseSettings, SettingsConfigDict

URLS = Path("urls.txt")
POSTINGS = Path("outputs/postings.jsonl")
MIN_LENGTH = 1500  # a cleaned posting shorter than this probably needs JavaScript to load

# The posting ends at the first heading that starts with one of these. "apply" is the
# application form. PostHog's team goals section names staff, and the posting doesn't need it.
STOP_HEADINGS = ("apply", "your team's mission")


class Settings(BaseSettings):
    """Read from environment variables or the .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    zenrows_api_key: str


def fetch_markdown(url: str, api_key: str, js_render: bool) -> tuple[str, int]:
    """Fetch one page as markdown. Returns the markdown and the credits ZenRows charged."""
    params = {"apikey": api_key, "url": url, "response_type": "markdown"}
    if js_render:
        params["js_render"] = "true"  # load the page in a real browser first
    response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=120)
    response.raise_for_status()
    return response.text, int(response.headers.get("X-Request-Credits", 0))


def clean(markdown: str) -> tuple[str, str]:
    """Keep only the posting: from the first top-level heading down to a stop heading.
    Returns the title and the cleaned text."""
    lines = markdown.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if start is None:
        return "", ""

    kept = []
    for line in lines[start:]:
        heading = line.lstrip("#* ").lower()  # "### **Apply**" becomes "apply**"
        if line.startswith("#") and heading.startswith(STOP_HEADINGS):
            break
        kept.append(line)

    text = "\n".join(kept)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)  # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links: keep the words, drop the URL
    text = text.replace("**", "")  # bold markers would get in the way of quote matching
    text = re.sub(r"^\s*[-*]\s*$", "", text, flags=re.MULTILINE)  # bullets left empty
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return lines[start].lstrip("# ").strip(), text


def posting_id(url: str) -> str:
    """'https://canonical.com/careers/5143074' becomes 'canonical-5143074'."""
    company = url.split("//")[1].removeprefix("www.").split(".")[0]
    slug = url.rstrip("/").rsplit("/", 1)[-1].strip("-")
    return f"{company}-{slug}"


def main() -> None:
    api_key = Settings().zenrows_api_key
    urls = [line.strip() for line in URLS.read_text().splitlines() if line.startswith("http")]
    POSTINGS.parent.mkdir(exist_ok=True)

    total_credits = 0
    with POSTINGS.open("w", encoding="utf-8") as out:
        for url in urls:
            try:
                # Try a plain fetch first (1 credit). Only pay for a browser (5 credits)
                # when the plain page comes back without the posting in it.
                markdown, credits = fetch_markdown(url, api_key, js_render=False)
                title, text = clean(markdown)
                js_render = len(text) < MIN_LENGTH
                if js_render:
                    markdown, more = fetch_markdown(url, api_key, js_render=True)
                    title, text = clean(markdown)
                    credits += more
            except requests.RequestException as error:
                print(f"{url} failed: {error}")
                continue

            posting = {
                "id": posting_id(url),
                "url": url,
                "title": title,
                "description": text,
                "js_render": js_render,
                "credits": credits,
            }
            out.write(json.dumps(posting, ensure_ascii=False) + "\n")
            total_credits += credits
            rendered = " (needed JavaScript)" if js_render else ""
            print(f"{posting['id']}: {len(text)} characters, {credits} credits{rendered}")

    print(f"{len(urls)} pages, {total_credits} credits in total")


if __name__ == "__main__":
    main()
