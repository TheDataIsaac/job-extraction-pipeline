# Ops example: messy operations emails into checked records

A folder of emails and notes goes in; records a team can use come out, plus a list of the ones a
person needs to look at and why. It uses the same three ideas as the main pipeline: the model
fills in a fixed form, every value it gives comes with a quote from the document, and plain
Python checks those quotes before anything is trusted.

**All documents in `samples/` are made up.** Each sample's `ABOUT.md` names the public job
posting that inspired it and lists what each document is meant to test.

| Sample | What goes in | One record is |
|---|---|---|
| `oyster_payroll_changes` | Client emails to a payroll team | One payroll change for one employee |
| `nova_401k_census` | Payroll data sent to a 401(k) administrator | One employee's census row |
| `christie_lites_shipments` | Branch, driver and carrier shipment updates | One job's shipment status |

## How it works

```
documents/ --extract.py--> extractions.jsonl --verify.py--> checked.jsonl --report.py--> records.csv
            (one model call               (quotes and                       review.csv
             per document)                 business rules)                  summary.md
```

| File | What it does |
|---|---|
| `extract.py` | Sends each `.txt` or `.eml` file in the sample's `documents/` folder to the model, which fills in that sample's form. A document can give several records (two employees in one email) or none (a party invite). Each result is saved as soon as it arrives, and documents already saved are skipped, so a stopped run carries on where it left off. |
| `verify.py` | Checks every record against its own document. No second model call. |
| `report.py` | Writes the passed records, the review list and a summary. |
| `run.py` | Runs all three for one sample. |
| `samples/<name>/schema.py` | That sample's form (a Pydantic model), extra instructions for the model, and its business rules. |

## The checks

A record goes to `records.csv` only if all of these hold. Otherwise it goes to `review.csv` with
every reason listed.

1. **Every value has a quote, and the quote is in the document.** Each field such as `amount`
   has a partner `amount_quote`. The quote must appear word for word in the document. Only
   spacing, line breaks and curly versus straight quote marks are ignored.
2. **Numbers appear in digits in their quote.** If the model says 2500 but the quote says
   "two thousand five hundred", or a scan says "1,7l6.00", a person confirms it.
3. **Business rules.** A few plain checks per sample, in `schema.py`: an amount with no
   currency, a termination date before the hire date, a delayed shipment with no reason, and
   so on.
4. **The model didn't ask for a person.** The model sets `needs_human` with a reason when it
   sees two possible values, a missing attachment or numbers that disagree.

## Run it

You need [uv](https://docs.astral.sh/uv/) and an OpenAI key in the `.env` file at the top of the
repo (`OPENAI_API_KEY=...`). From the top of the repo:

```bash
uv sync
uv run python ops-example/run.py oyster_payroll_changes
```

Swap in `nova_401k_census` or `christie_lites_shipments` for the other samples. Each run is 12
model calls of about 1,200 tokens each. To start a sample over, delete its `output/` folder.
The steps also run one at a time: `extract.py`, then `verify.py`, then `report.py`, each with the
sample name.

## What the output means

Each sample's `output/` folder holds the results of a real run:

- `records.csv`: records that passed every check, ready to use.
- `review.csv`: records a person must check, with the reasons in the first column and the
  model's own note in `needs_human_reason`. The quotes are there too, so the reviewer can see
  what the model read.
- `summary.md`: how many documents, records, passes and reviews, and the count for each reason.
- `extractions.jsonl` and `checked.jsonl`: the raw model answers and the check results.

## Limits

- The quote check proves the text is in the document, not that the model read it correctly.
  A quote of "1 March" backs a date of 2027-03-01, but the code can't tell if the year is right.
- A short quote from a table cell, like "8", shows the number is in the document, not that it
  sits in that row and column.
- In a thread with a correction, the quote could come from the old, replaced text ("1 Feb"
  instead of the later "1 March") and still pass.
- Dates, currency codes and choices like `bonus` are the model's reading of the quote. Only
  numbers are compared with their quote.
- The model's `needs_human` flag depends on the model noticing a problem. In the rehire email
  it didn't, and only the termination-before-hire rule caught it.
- 36 invented documents, written to include the messy cases, are a demo, not a measure of
  accuracy. Real documents would need a labelled set to score it.
- Files are read as plain text. Real `.eml` files with attachments, HTML bodies or scanned PDFs
  would need a step that turns them into text first.
