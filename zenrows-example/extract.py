"""Extract structured data from each posting with the model.

Copied from job-extraction-pipeline's extract.py. The Extractor class is unchanged. The prompt is
reworded for careers-page postings, and run_batch is trimmed: it still skips postings that are
already saved, but drops the fingerprint check, which only matters for big reruns.

Run it as `python extract.py`, or give other files: `python extract.py outputs/eval_postings.jsonl
outputs/eval_extractions.jsonl`.
"""

import asyncio
import json
import sys
from pathlib import Path

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic_settings import BaseSettings, SettingsConfigDict
from schema import JobExtraction
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from verify import check

POSTINGS = Path("outputs/postings.jsonl")
EXTRACTIONS = Path("outputs/extractions.jsonl")


class Settings(BaseSettings):
    """Read from environment variables or the .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    llm_model: str = "gpt-5.6-luna"
    concurrency: int = 10  # how many requests are in flight at once


PROMPT = """You extract structured data from a job posting on a company careers page.

Rules:
- Use only what the posting says. If something is not mentioned, use null, not_stated or an
  empty list. Never guess.
- Every quote must be copied exactly from the posting.
- Pay counts only if an amount is written in the text itself.
- Add a quote only for a field that has a real value. Do not add quotes for null, not_stated or
  empty fields.
"""

# Only retry errors that are likely to go away. A bad request would fail every time.
RETRYABLE = (APIConnectionError, APITimeoutError, RateLimitError)


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


async def run_batch(postings_file: Path, out_file: Path) -> None:
    """Extract postings and append them to out_file. Postings already in out_file are skipped,
    so the run can be stopped and restarted without paying twice."""
    extractor = Extractor(Settings())
    postings = [json.loads(line) for line in postings_file.open(encoding="utf-8")]
    done = set()
    if out_file.exists():
        done = {json.loads(line)["id"] for line in out_file.open(encoding="utf-8")}
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
            "tokens": tokens,
            "problems": check(data, posting["title"] + " " + posting["description"]),
            "data": data.model_dump(mode="json"),
        }
        out.write(json.dumps(record, ensure_ascii=False) + "\n")
        out.flush()
        print(f"{posting['id']}: {tokens} tokens, {len(record['problems'])} problems")

    with out_file.open("a", encoding="utf-8") as out:
        await asyncio.gather(*(work(p, out) for p in todo))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        asyncio.run(run_batch(POSTINGS, EXTRACTIONS))
    elif len(sys.argv) == 3:
        asyncio.run(run_batch(Path(sys.argv[1]), Path(sys.argv[2])))
    else:
        sys.exit("Usage: python extract.py [postings_file extractions_file]")
