"""Write the checked records out for people: records.csv, review.csv and summary.md.

records.csv holds the records that passed every check. review.csv holds the rest, each with the
reasons a person needs to look. summary.md gives the counts.

Run it as `python report.py oyster_payroll_changes`, after verify.py.
"""

import csv
import sys
from collections import Counter
from pathlib import Path

from extract import load_sample, read_documents, read_jsonl


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    # utf-8-sig adds a marker that tells Excel the file is UTF-8, so names like Wiśniewska and
    # symbols like ₹ show correctly when someone double-clicks the file.
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, sample: str, counts: dict, reasons: Counter, empty: list[str]):
    lines = [
        f"# Summary: {sample}",
        "",
        "Every document in this sample is made up. See ABOUT.md.",
        "",
        "| | Count |",
        "|---|---|",
    ]
    lines += [f"| {label} | {number} |" for label, number in counts.items()]
    lines += ["", "## Why records went to review", ""]
    if reasons:
        lines += ["A record can have more than one reason.", ""]
        lines += ["| Reason | Records |", "|---|---|"]
        lines += [f"| {reason} | {number} |" for reason, number in reasons.most_common()]
    else:
        lines.append("None.")
    lines += ["", "## Documents that gave no record", ""]
    lines += [f"- {name}" for name in empty] or ["None."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(sample: str) -> None:
    schema, folder = load_sample(sample)
    output = folder / "output"
    rows = read_jsonl(output / "checked.jsonl")
    fields = list(schema.Record.model_fields)

    passed, review = [], []
    reasons = Counter()
    for row in rows:
        for number, record in enumerate(row["records"], start=1):
            line = {"document": row["document"], "record": number, **record["data"]}
            if record["problems"]:
                review.append({"reasons": "; ".join(record["problems"]), **line})
                reasons.update(record["problems"])
            else:
                passed.append(line)

    write_csv(output / "records.csv", passed, ["document", "record", *fields])
    write_csv(output / "review.csv", review, ["reasons", "document", "record", *fields])

    empty = [row["document"] for row in rows if not row["records"]]
    counts = {
        "Documents in the folder": len(read_documents(folder)),
        "Documents read by the model": len(rows),
        "Documents that gave no record": len(empty),
        "Records": len(passed) + len(review),
        "Passed every check (records.csv)": len(passed),
        "Sent to review (review.csv)": len(review),
        "Tokens used": f"{sum(row['tokens'] for row in rows):,}",
    }
    write_summary(output / "summary.md", sample, counts, reasons, empty)
    print(f"{sample}: {len(passed)} passed, {len(review)} sent to review. See {output}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python report.py <sample name>")
    run(sys.argv[1])
