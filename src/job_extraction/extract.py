"""Extract structured data from each posting with the model."""

import asyncio
import hashlib
import json
from pathlib import Path

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic_settings import BaseSettings, SettingsConfigDict
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from job_extraction.schema import JobExtraction
from job_extraction.verify import check


class Settings(BaseSettings):
    """Read from environment variables or the .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    llm_model: str = "gpt-5.6-luna"
    concurrency: int = 10  # how many requests are in flight at once


PROMPT = """You extract structured data from a freelance job posting.

Rules:
- Use only what the posting says. If something is not mentioned, use null, not_stated or an
  empty list. Never guess.
- Every quote must be copied exactly from the posting.
- A budget counts only if a price is written in the text itself.
- Pick the single best project_type.
- Add a quote only for a field that has a real value. Do not add quotes for null, not_stated or
  empty fields.
"""

# Only retry errors that are likely to go away. A bad request would fail every time.
RETRYABLE = (APIConnectionError, APITimeoutError, RateLimitError)

SCHEMA = json.dumps(JobExtraction.model_json_schema(), sort_keys=True)


class EmptyReply(Exception):
    """The model answered but gave no usable data, for example because it refused."""


class Extractor:
    def __init__(self, settings: Settings) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=90)
        self.model = settings.llm_model
        self.semaphore = asyncio.Semaphore(settings.concurrency)

    @retry(
        retry=retry_if_exception_type(RETRYABLE),
        wait=wait_exponential(min=2, max=30),
        stop=stop_after_attempt(5),
    )
    async def extract(self, title: str, description: str) -> tuple[JobExtraction, int]:
        """Extract one posting. Returns the data and the number of tokens used."""
        async with self.semaphore:
            response = await self.client.responses.parse(
                model=self.model,
                reasoning={"effort": "none"},
                input=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": f"Title: {title}\n\n{description}"},
                ],
                text_format=JobExtraction,
            )
        if response.output_parsed is None:
            raise EmptyReply
        return response.output_parsed, response.usage.total_tokens


def fingerprint(model: str, posting: dict) -> str:
    """A code that changes when the posting, model, prompt or schema changes."""
    parts = [model, PROMPT, SCHEMA, posting["title"], posting["description"]]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def drop_stale(out_file: Path, fingerprints: dict[str, str]) -> set[str]:
    """Move saved results whose input has changed into a side file, so they can be redone.
    Returns the IDs that are still good."""
    if not out_file.exists():
        return set()

    kept = []
    stale = []
    for line in out_file.open(encoding="utf-8"):
        record = json.loads(line)
        saved = record.get("fingerprint")
        current = fingerprints.get(record["id"])
        # Results saved before fingerprints existed have nothing to compare, so they stay.
        # So do postings outside this run (see --limit).
        if saved is None or current is None or saved == current:
            kept.append(record)
        else:
            stale.append(record)

    if stale:
        print(f"{len(stale)} saved results are out of date and will be redone")
        # The replacements don't exist yet and the run could still fail, so keep the old
        # results in a side file rather than delete what was paid for.
        with out_file.with_suffix(".old.jsonl").open("a", encoding="utf-8") as old:
            for record in stale:
                old.write(json.dumps(record, ensure_ascii=False) + "\n")
        temp_file = out_file.with_suffix(".tmp")
        with temp_file.open("w", encoding="utf-8") as out:
            for record in kept:
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
        temp_file.replace(out_file)

    return {record["id"] for record in kept}


async def run_batch(postings_file: Path, out_file: Path, limit: int | None) -> None:
    """Extract postings and append them to out_file. Postings already in out_file are skipped,
    so the run can be stopped and restarted without paying twice. A posting is redone if its
    text, the model, the prompt or the schema has changed since it was saved. Results saved
    before fingerprints were added can't be compared, so they are kept as they are."""
    extractor = Extractor(Settings())
    postings = [json.loads(line) for line in postings_file.open(encoding="utf-8")]
    if limit:
        postings = postings[:limit]

    fingerprints = {p["id"]: fingerprint(extractor.model, p) for p in postings}
    done = drop_stale(out_file, fingerprints)
    todo = [p for p in postings if p["id"] not in done]
    print(f"{len(done)} already done, {len(todo)} to go")

    async def work(posting: dict, out) -> None:
        try:
            data, tokens = await extractor.extract(posting["title"], posting["description"])
        except Exception as error:  # noqa: BLE001 - one bad posting should not stop the whole run
            print(f"{posting['id']} failed: {type(error).__name__}")
            return
        record = {
            "id": posting["id"],
            "fingerprint": fingerprints[posting["id"]],
            "tokens": tokens,
            "problems": check(data, posting["title"] + " " + posting["description"]),
            "data": data.model_dump(mode="json"),
        }
        out.write(json.dumps(record, ensure_ascii=False) + "\n")
        out.flush()

    with out_file.open("a", encoding="utf-8") as out:
        tasks = [work(p, out) for p in todo]
        for i, finished in enumerate(asyncio.as_completed(tasks), 1):
            await finished
            if i % 100 == 0:
                print(f"{i}/{len(todo)}")
