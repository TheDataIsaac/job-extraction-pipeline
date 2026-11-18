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

## Part 2: how often does it get location right?

The quote check can't tell you whether an answer is right, so Part 2 measures it. It runs the
same pipeline on 50 postings from 8 companies (`eval_urls.txt`, fetched on 18 November 2026) and
compares the model's answers with true answers taken from reading each posting (`labels.csv`).
It scores two things: `remote_scope`, and the decision that matters, whether someone living in
Nigeria can apply.

For comparison, it scores two filters that only read the location label: one that looks for
"remote" or "worldwide" (roughly what a job board's remote filter does), and one that looks for
the same place words `report.py` uses (EMEA, Africa, Nigeria, worldwide, anywhere).

| File | What it does |
|---|---|
| `eval_urls.txt` | The 50 postings, picked to cover the different ways location gets written. |
| `labels.csv` | The true answers, one row per posting, with the quote that decides each one. `label_status` says whether a label is still a suggestion or has been confirmed by a person. |
| `evaluate.py` | Compares the records with the labels and writes `evaluation_report.md`. |

```bash
uv run --no-project --with-requirements requirements.txt python fetch_pages.py eval_urls.txt outputs/eval_postings.jsonl
uv run --no-project --with-requirements requirements.txt python extract.py outputs/eval_postings.jsonl outputs/eval_extractions.jsonl
uv run --no-project --with-requirements requirements.txt python evaluate.py
```

The report gives accuracy for both fields, a confusion table for `remote_scope`, every miss with
the model's quotes, and how many misses passed the checks in `verify.py`. Until every label is
confirmed, the report says its numbers are provisional.

### How the labels are decided

I drafted the labels with an LLM's help, a second model labelled all 50 again without seeing
them (they agreed on the Nigeria answer for all 50 and on `remote_scope` for 48), and I settled
the two disagreements and reviewed the rest. These are the rules all three followed.

- Go by the posting page only, not the listing page or what you know about the company. Ignore
  footers and region pickers.
- `location_label` is the location line on the posting page, copied as written.
- `anywhere`: any country, with no limit. `regions`: remote, but only from named regions (EMEA,
  the Americas) or from a band of time zones with no countries named. `countries`: remote, but
  only from named countries or states, or from countries the posting limits but doesn't name
  (`places` stays empty then). `hybrid_or_office`: regular office time, or the page names
  only an office city.
- Remote in a region or an office: remote wins, so `regions` or `countries`.
- `open_from_nigeria`: could someone living in Nigeria (GMT +1) do the job from there, going by
  the posting? `unclear` when the posting doesn't settle it.
- When the only limit is a band of time zones, Nigeria counts as in if GMT +1 is inside the band.
- `places` holds countries, regions or cities only. A time zone goes in `required_timezone`.
