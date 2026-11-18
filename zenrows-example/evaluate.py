"""Measure how often the extraction gets a job's location right.

Compares the model's records with the true answers in labels.csv, which come from reading each
posting. Two simple filters that only read the location label are scored the same way, for
comparison. Prints the results and saves them to evaluation_report.md.
"""

import csv
import json
from collections import Counter
from pathlib import Path

from report import INCLUDES_NIGERIA, open_from_nigeria

LABELS = Path("labels.csv")
EXTRACTIONS = Path("outputs/eval_extractions.jsonl")
REPORT = Path("evaluation_report.md")
SCOPES = ["anywhere", "regions", "countries", "hybrid_or_office", "not_stated"]
NIGERIA_ANSWERS = ["yes", "no", "unclear"]


def label_says_remote(location_label: str) -> bool:
    """Baseline 1: trust the word "remote" in the label, the way a job board's filter does."""
    label = location_label.lower()
    return "remote" in label or "worldwide" in label


def label_names_a_place(location_label: str) -> bool:
    """Baseline 2: report.py's own words for places that include Nigeria (EMEA, Africa, ...),
    looked for in the label instead of in the model's answers."""
    label = location_label.lower()
    return any(word in label for word in INCLUDES_NIGERIA)


def yes_no(answer: bool) -> str:
    return "yes" if answer else "no"


def share(part: int, whole: int) -> str:
    return f"{part} of {whole} ({part / whole:.0%})"


def quote_for(data: dict, field: str) -> str:
    """The model's quote for one field, or a note that it gave none."""
    quotes = [item["quote"] for item in data["evidence"] if item["field"] == field]
    if not quotes:
        return "(no quote)"
    return " ".join(quotes[0].split())  # a line break inside the quote would break the list


def read_labels() -> dict:
    """Read labels.csv, stopping on a value that isn't one of the allowed answers.
    A typo such as "Yes" would otherwise drop out of the scores without a word."""
    with LABELS.open(encoding="utf-8") as file:
        labels = {row["id"]: row for row in csv.DictReader(file)}
    for row in labels.values():
        if row["remote_scope"] not in SCOPES:
            raise SystemExit(f"{row['id']}: unknown remote_scope {row['remote_scope']!r}")
        if row["open_from_nigeria"] not in NIGERIA_ANSWERS:
            raise SystemExit(f"{row['id']}: unknown open_from_nigeria {row['open_from_nigeria']!r}")
    return labels


def main() -> None:
    labels = read_labels()
    records = {}
    for line in EXTRACTIONS.open(encoding="utf-8"):
        record = json.loads(line)
        records[record["id"]] = record

    ids = [posting_id for posting_id in labels if posting_id in records]
    missing = [posting_id for posting_id in labels if posting_id not in records]
    confirmed = sum(labels[i]["label_status"] == "confirmed" for i in ids)

    lines = ["# Location evaluation", ""]
    lines.append(f"{len(ids)} postings. {confirmed} of {len(ids)} labels confirmed by Isaac.")
    if confirmed < len(ids):
        lines.append("")
        lines.append("**Provisional: scored against suggested labels, not yet reviewed by Isaac.**")
    if missing:
        lines.append("")
        lines.append(f"Labelled but no model record (extraction failed): {', '.join(missing)}")

    # remote_scope: one of five fixed answers, so it is either right or wrong.
    scope_wrong = {
        i for i in ids if records[i]["data"]["remote_scope"] != labels[i]["remote_scope"]
    }
    pairs = Counter((labels[i]["remote_scope"], records[i]["data"]["remote_scope"]) for i in ids)
    scope_right = len(ids) - len(scope_wrong)
    lines += ["", "## remote_scope", "", f"Correct: {share(scope_right, len(ids))}", ""]
    lines += ["Rows are the true answer, columns are the model's answer.", ""]
    lines.append("| true \\ model | " + " | ".join(SCOPES) + " |")
    lines.append("|---" * (len(SCOPES) + 1) + "|")
    for true in SCOPES:
        counts = [str(pairs[(true, model)]) for model in SCOPES]
        lines.append(f"| {true} | " + " | ".join(counts) + " |")

    # Can someone in Nigeria apply? Postings labelled "unclear" have no right answer to score.
    decided = [i for i in ids if labels[i]["open_from_nigeria"] != "unclear"]
    unclear = [i for i in ids if labels[i]["open_from_nigeria"] == "unclear"]
    true_yes = sum(labels[i]["open_from_nigeria"] == "yes" for i in decided)
    schema = {i: yes_no(open_from_nigeria(records[i]["data"])) for i in ids}
    nigeria_wrong = {i for i in decided if schema[i] != labels[i]["open_from_nigeria"]}
    # Each way of answering, scored on the same postings.
    answers = {
        "Schema filter (`open_from_nigeria` in report.py)": schema,
        'Baseline 1: "remote" or "worldwide" in the location label': {
            i: yes_no(label_says_remote(labels[i]["location_label"])) for i in ids
        },
        "Baseline 2: report.py's place words in the location label": {
            i: yes_no(label_names_a_place(labels[i]["location_label"])) for i in ids
        },
        'For scale: answering "no" every time': {i: "no" for i in ids},
    }
    lines += ["", "## Can someone living in Nigeria apply?", ""]
    lines.append(
        f"{len(decided)} postings are labelled yes or no ({true_yes} yes, "
        f"{len(decided) - true_yes} no). {len(unclear)} are labelled unclear and left out."
    )
    lines.append("")
    for name, answer in answers.items():
        right = sum(answer[i] == labels[i]["open_from_nigeria"] for i in decided)
        lines.append(f"- {name}: {share(right, len(decided))}")

    # A miss is a wrong remote_scope, a wrong Nigeria answer, or both.
    misses = [i for i in ids if i in scope_wrong or i in nigeria_wrong]
    passed = [i for i in ids if not records[i]["problems"]]
    passed_but_wrong = [i for i in passed if i in misses]
    lines += ["", "## Did the checks catch the misses?", ""]
    lines.append(f"- Passed every check in verify.py: {share(len(passed), len(ids))}")
    lines.append(
        f"- Passed every check but still a miss: {len(passed_but_wrong)} of {len(misses)} misses"
    )

    lines += ["", f"## Every miss ({len(misses)})", ""]
    for i in misses:
        data, label = records[i]["data"], labels[i]
        model_places = ", ".join(data["eligible_locations"]) or "none"
        scope_quote = quote_for(data, "remote_scope")
        places_quote = quote_for(data, "eligible_locations")
        lines += [
            f"### {i}",
            "",
            f"- Posting: {label['url']}",
            f"- Location label: {label['location_label']}",
            f"- remote_scope: model `{data['remote_scope']}`, true `{label['remote_scope']}`",
            f"- Nigeria: model {schema[i]}, true {label['open_from_nigeria']}",
            f"- Places: model {model_places}, true {label['places'] or 'none'}",
            f'- The model quoted for remote_scope: "{scope_quote}"',
            f'- The model quoted for places: "{places_quote}"',
            f"- Check problems: {records[i]['problems'] or 'none'}",
            f"- Label note: {label['note'] or 'none'}",
            "",
        ]

    lines += [f"## Labelled unclear ({len(unclear)})", ""]
    for i in unclear:
        lines.append(f"- {i}: the schema filter says {schema[i]}. {labels[i]['note']}")

    report = "\n".join(lines) + "\n"
    print(report)
    REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
