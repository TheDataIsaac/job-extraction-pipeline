"""Extract postings through OpenAI's Batch API: the same requests as extract.py, at half price.

A normal run sends requests one by one and waits for each answer. With the Batch API you upload
one file holding every request. OpenAI works through it when it has spare capacity, within 24
hours (usually much sooner), and charges half the normal price. That suits this project: nobody
is waiting for the answers, so there's no reason to pay for speed.

It takes two steps, because the answers don't come back straight away:
1. submit: write one request per posting to a JSONL file, upload it and start the batch.
2. collect: check on the batch. Once it's done, download the answers, check them and add them
   to extractions.jsonl, exactly like a normal run.
"""

import json
from pathlib import Path

from openai import OpenAI

# The helper `responses.parse` uses to turn the Pydantic model into the JSON schema it sends.
# Using it here means a batch request asks for exactly the same structure as a normal one.
# It's an internal part of the openai package, so a future version could move it.
from openai.lib._parsing._responses import type_to_text_format_param

from job_extraction.extract import Settings, drop_stale, fingerprint, messages, to_record
from job_extraction.schema import JobExtraction

# Remembers which batch is running, between submit and collect.
BATCH_FILE = Path("data/batch.json")
REQUESTS_FILE = Path("data/batch_requests.jsonl")


def request_line(posting: dict, model: str) -> str:
    """One line of the upload file: a Responses API request, labelled with the posting's id."""
    body = {
        "model": model,
        "reasoning": {"effort": "none"},
        "input": messages(posting["title"], posting["description"]),
        "text": {"format": type_to_text_format_param(JobExtraction)},
    }
    request = {"custom_id": posting["id"], "method": "POST", "url": "/v1/responses", "body": body}
    return json.dumps(request, ensure_ascii=False)


def submit(postings_file: Path, out_file: Path, limit: int | None) -> None:
    """Start a batch for every posting that isn't in out_file yet (or whose input changed)."""
    if BATCH_FILE.exists():
        print(f"A batch is already running. Collect it first: {BATCH_FILE}")
        return

    settings = Settings()
    postings = [json.loads(line) for line in postings_file.open(encoding="utf-8")]
    if limit:
        postings = postings[:limit]
    fingerprints = {p["id"]: fingerprint(settings.llm_model, p) for p in postings}
    done = drop_stale(out_file, fingerprints)
    todo = [p for p in postings if p["id"] not in done]
    if not todo:
        print("Nothing to do: every posting is already extracted.")
        return

    with REQUESTS_FILE.open("w", encoding="utf-8") as requests:
        for posting in todo:
            requests.write(request_line(posting, settings.llm_model) + "\n")

    client = OpenAI(api_key=settings.openai_api_key)
    with REQUESTS_FILE.open("rb") as requests:
        uploaded = client.files.create(file=requests, purpose="batch")
    batch = client.batches.create(
        input_file_id=uploaded.id, endpoint="/v1/responses", completion_window="24h"
    )

    # The fingerprints are saved with the batch, so collect can stamp each result with the
    # input it came from, like a normal run does.
    saved = {"batch_id": batch.id, "fingerprints": {p["id"]: fingerprints[p["id"]] for p in todo}}
    BATCH_FILE.write_text(json.dumps(saved), encoding="utf-8")
    print(f"Started batch {batch.id} with {len(todo)} postings. Run `jobs collect` to check on it.")


def output_text(body: dict) -> str | None:
    """The model's answer text from a Responses API reply, or None if it refused."""
    for item in body["output"]:
        if item["type"] == "message":
            for part in item["content"]:
                if part["type"] == "output_text":
                    return part["text"]
    return None


def collect(postings_file: Path, out_file: Path) -> None:
    """If the batch has finished, add its results to out_file."""
    if not BATCH_FILE.exists():
        print("No batch is running. Start one with `jobs extract --batch`.")
        return
    saved = json.loads(BATCH_FILE.read_text(encoding="utf-8"))
    client = OpenAI(api_key=Settings().openai_api_key)
    batch = client.batches.retrieve(saved["batch_id"])
    counts = batch.request_counts
    print(f"Batch {batch.id}: {batch.status} ({counts.completed} done, {counts.failed} failed)")
    if batch.status not in ("completed", "failed", "expired", "cancelled"):
        return  # still working; run collect again later
    # A batch that expired or was cancelled can still hold answers it finished, and those are
    # already paid for, so they're saved like the rest.

    postings = {}
    for line in postings_file.open(encoding="utf-8"):
        posting = json.loads(line)
        postings[posting["id"]] = posting

    added = failed = 0
    results = client.files.content(batch.output_file_id).text if batch.output_file_id else ""
    with out_file.open("a", encoding="utf-8") as out:
        for line in results.splitlines():
            result = json.loads(line)
            posting_id = result["custom_id"]
            try:
                body = result["response"]["body"]  # response is None if the request failed
                text = output_text(body)  # None if the model refused
                data = JobExtraction.model_validate_json(text)
                tokens = body["usage"]["total_tokens"]
                fingerprint = saved["fingerprints"][posting_id]
                record = to_record(postings[posting_id], fingerprint, data, tokens)
            except Exception:  # noqa: BLE001 - one bad answer shouldn't lose all the others
                print(f"{posting_id} failed")
                failed += 1
                continue
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            added += 1

    # Requests that failed before reaching the model are in a separate error file.
    failed += counts.failed
    BATCH_FILE.unlink()  # collected, so running collect again won't add the results twice
    print(f"Added {added} results to {out_file}. Failed: {failed} (a normal run can redo them).")
