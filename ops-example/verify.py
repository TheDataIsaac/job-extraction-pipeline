"""Check every record against its own document with plain string matching (no model call).

A record passes only if every value it claims has a quote that really is in the document, the
sample's business rules find nothing wrong, and the model did not ask for a person. Anything else
goes to review with the reason written down.

Run it as `python verify.py oyster_payroll_changes`, after extract.py.
"""

import json
import re
import sys

from extract import load_sample, read_documents, read_jsonl

# Curly quotes become straight ones, so a quote typed with ' or " still matches a document
# written with ‘ ’ or “ ”, and the other way round.
STRAIGHT_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def normalise(text: str) -> str:
    """Make quote characters and runs of spaces or line breaks the same. Nothing else changes."""
    return re.sub(r"\s+", " ", text.translate(STRAIGHT_QUOTES)).strip()


def quote_in_text(quote: str, text: str) -> bool:
    """True if the quote appears in the (already normalised) text as whole words.

    So "31" doesn't match inside "310", and "500" doesn't match inside "4,500" or "500.75".
    """
    # Not next to a letter or digit, and not next to a comma or point that joins digits.
    pattern = r"(?<!\w)(?<!\d[.,])" + re.escape(normalise(quote)) + r"(?!\w)(?![.,]\d)"
    return re.search(pattern, text) is not None


def number_in_quote(value: float, quote: str) -> bool:
    """True if the number is written in digits inside its quote. '4,500' counts as 4500."""
    numbers = re.findall(r"\d+(?:\.\d+)?", quote.replace(",", ""))
    return any(float(number) == float(value) for number in numbers)


def check_quotes(record: dict, document_text: str) -> list[str]:
    """Every value that has a matching *_quote field must be backed by that quote."""
    text = normalise(document_text)
    problems = []
    for key, quote in record.items():
        if not key.endswith("_quote"):
            continue
        field = key.removesuffix("_quote")
        if record[field] is None:
            continue
        # A blank quote would always match ("" is in every string), so it counts as no quote.
        if not quote or not quote.strip():
            problems.append(f"no quote for {field}")
        elif not quote_in_text(quote, text):
            problems.append(f"quote for {field} is not in the document")
        elif isinstance(record[field], (int, float)) and not number_in_quote(record[field], quote):
            # Catches figures written in words or misread by a scanner: a person confirms them.
            problems.append(f"{field} is not written in digits in its quote")
    return problems


def check_record(record: dict, document_text: str, schema) -> list[str]:
    """Return every reason this record needs a person. An empty list means it passed."""
    problems = check_quotes(record, document_text)
    problems += schema.rules(record)
    if record["needs_human"]:
        problems.append("flagged by the model")
    return problems


def run(sample: str) -> None:
    schema, folder = load_sample(sample)
    documents = read_documents(folder)
    rows = read_jsonl(folder / "output" / "extractions.jsonl")

    with (folder / "output" / "checked.jsonl").open("w", encoding="utf-8") as out:
        for row in rows:
            text = documents[row["document"]]
            checked = [
                {"data": record, "problems": check_record(record, text, schema)}
                for record in row["records"]
            ]
            row = {"document": row["document"], "tokens": row["tokens"], "records": checked}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{sample}: checked {len(rows)} documents")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python verify.py <sample name>")
    run(sys.argv[1])
