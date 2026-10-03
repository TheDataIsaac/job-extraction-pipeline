"""Clean the raw CSV and remove duplicate postings."""

import csv
import json
import re
from pathlib import Path

csv.field_size_limit(10**9)

# Some bullet characters were damaged in the dataset and show up as the replacement character.
BROKEN_BULLET = "�"


def clean_text(text: str) -> str:
    text = text.replace(BROKEN_BULLET, "-")
    return re.sub(r"\s+", " ", text).strip()


def prepare(raw_csv: Path, out_file: Path) -> tuple[int, int]:
    """Write one cleaned posting per line. Returns (rows read, postings kept)."""
    seen: set[str] = set()
    kept = 0
    rows_read = 0
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with (
        raw_csv.open(encoding="utf-8", errors="replace", newline="") as f,
        out_file.open("w", encoding="utf-8") as out,
    ):
        for row in csv.DictReader(f):
            rows_read += 1
            description = clean_text(row["job_description"])
            key = description.lower()
            if key in seen:  # exact duplicate of a posting we already have
                continue
            seen.add(key)
            posting = {
                "id": row["projectId"],
                "title": clean_text(row["job_title"]),
                "description": description,
                "country": row["client_country"],
                "currency": row["currency"],
                "rate_type": row["rate_type"],
            }
            out.write(json.dumps(posting, ensure_ascii=False) + "\n")
            kept += 1
    return rows_read, kept
