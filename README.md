# job-extraction-pipeline

Turns messy freelance job postings into clean, structured data with an LLM, then checks the
model's answers against the original text. I ran it on about 8,600 data-related postings from the
Freelancer job postings dataset from Kaggle (not included here).

See [reports/summary.md](reports/summary.md) for what it found.

## How it works

```
raw CSV --prepare--> postings.jsonl --extract--> extractions.jsonl --analyze--> reports/
                      (clean, dedupe)   (LLM + checks)                (tables, charts)
```

| File | What it does |
|---|---|
| `schema.py` | The shape of the answer: project type, tools, experience level, deadline, budget, red flags. The model must fill this in. |
| `prepare.py` | Fixes broken characters and removes exact duplicate postings. |
| `extract.py` | Sends each posting to the model, 10 at a time, retries temporary errors, and saves each result as it arrives so a stopped run can resume. A posting is redone if its text, the model, the prompt or the schema has changed, and the old result moves to `extractions.old.jsonl`. Results saved before this check was added stay as they are. |
| `batch.py` | The same extraction through OpenAI's Batch API: upload every request in one file and collect the answers later, at half the price. |
| `verify.py` | Checks every claim against the posting. No second model call. |
| `analyze.py` | Counts and charts the results. |
| `api.py` | A small FastAPI service: `POST /extract` with one posting. |
| `ask.py` | Ask questions about all the postings (RAG): finds the closest postings by meaning, and the model answers from them and cites them. |

## The three ideas worth knowing

1. **Structured output.** The model is forced to answer in the shape of `JobExtraction`, so I get
   typed data, not text to parse.
2. **Null is allowed.** Most postings never state a budget or deadline. Letting the model say
   "not mentioned" stops it making a value up.
3. **Quotes as proof.** Facts that are easy to invent must come with a quote copied from the
   posting. `verify.py` checks that the quote is really there. 97.1% of postings passed every
   check, and the failures are listed in the report.

## Run it

```bash
uv sync
# put OPENAI_API_KEY=... in a .env file, and the CSV in data/raw/freelancer_job_postings.csv
uv run jobs prepare
uv run jobs extract --limit 20     # try 20 first; drop --limit for everything
uv run jobs analyze
uv run jobs serve                  # then POST to http://localhost:8000/extract

uv run jobs index                  # once: embed every posting (a few cents)
uv run jobs ask "What do clients want when they ask for a Power BI dashboard?"
```

`notebooks/try_it.ipynb` walks through all of it step by step. It shows real postings, so clear its outputs before sharing it.

A full run is about 8 million tokens and takes about 40 minutes.

## Half price with the Batch API

Nobody waits for these answers, so there's no reason to pay for fast replies. OpenAI's Batch API
takes a file of requests, works through it within 24 hours and charges half the normal price.

```bash
uv run jobs extract --batch --limit 20   # upload the requests and start a batch
uv run jobs collect                      # check on it; once it's done, save the results
```

`batch.py` sends exactly the same request as a normal run (same model, prompt and schema), so
results from either way have the same fingerprint, go through the same checks and land in the
same `extractions.jsonl`.

On 40 postings, a batch used the same tokens as a normal run for half the cost ($0.0059
against $0.0119) and finished in 3.5 minutes instead of 12 seconds. Its answers differed from
the saved run about as much as a fresh normal run does, since the model isn't fully repeatable
either way.

## Asking questions (RAG)

`jobs ask` retrieves the 8 postings closest in meaning to your question and gives them to the model, which answers only
from them and cites each by number. It sees 8 postings, not all 8,595, so it describes examples. It cannot give totals;
the analysis step does that. Extracted facts that failed a check are left out, so the model reads that posting's own
text instead.

## Other examples

* [zenrows-example](zenrows-example/) applies the same extraction and checks to company careers
  pages, and scores whether someone living in Nigeria could apply.
* [ops-example](ops-example/) turns made-up operations emails (payroll changes, 401(k) census data,
  shipment updates) into checked records, with a review list for anything that doesn't add up.

## Limits

* The checks prove a quote exists in the text, not that the model understood it correctly. I did
  not hand-label postings, so there is no accuracy score. The numbers describe the market, and are
  best read as good estimates.
* Only exact duplicates are removed. Postings with templated openings stay in.
* Project types and experience levels are the model's judgment from the text.
