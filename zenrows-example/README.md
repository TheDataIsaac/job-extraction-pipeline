# ZenRows example: careers pages into records you can filter

The same extraction and checks as the main pipeline, adapted to full-time jobs on company
careers pages. ZenRows fetches each posting as markdown, the model fills in a fixed form with a
quote for each main answer, plain Python checks the quotes are really on the page, and a small
filter answers one question: could someone living in Nigeria apply?

It was run on eight postings from Canonical and PostHog on 16 November 2026 (`urls.txt`).

| File | What it does |
|---|---|
| `find_postings.py` | Fetches Canonical's listing page with and without JavaScript and counts the posting links. |
| `try_crawl.py` | The same question asked through ZenRows Crawl, for comparison. |
| `fetch_pages.py` | Fetches each posting in `urls.txt` as markdown and cuts it down to the posting. |
| `schema.py` | The form the model fills in. `remote_scope` has five fixed answers. |
| `extract.py` | Sends each posting to the model and saves the records. |
| `verify.py` | Checks every quote and pay number against the posting. No second model call. |
| `report.py` | Prints the records and runs the Nigeria filter. |

## Run it

You need Python 3.11 or later, [uv](https://docs.astral.sh/uv/), a ZenRows key and an OpenAI
key. Put `ZENROWS_API_KEY` and `OPENAI_API_KEY` in a `.env` file in this folder, then run:

```bash
uv run --no-project --with-requirements requirements.txt python find_postings.py
uv run --no-project --with-requirements requirements.txt python fetch_pages.py
uv run --no-project --with-requirements requirements.txt python extract.py
uv run --no-project --with-requirements requirements.txt python report.py
```

Results go to `outputs/`. The checks prove a quote exists in the posting, not that the model
read it correctly, so a few records still need a person to read them.
