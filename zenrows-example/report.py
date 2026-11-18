"""Show the typed records, which checks failed, and one filter the records make possible."""

import json
from collections import Counter
from pathlib import Path

POSTINGS = Path("outputs/postings.jsonl")
EXTRACTIONS = Path("outputs/extractions.jsonl")
RESULTS = Path("outputs/results.json")

# Words that mean a region includes Nigeria. EMEA is Europe, the Middle East and Africa.
INCLUDES_NIGERIA = ("emea", "africa", "nigeria", "worldwide", "anywhere")


def open_from_nigeria(data: dict) -> bool:
    """Can someone living in Nigeria apply, going only by the extracted fields?"""
    if data["remote_scope"] == "anywhere":
        return True
    if data["remote_scope"] in ("regions", "countries"):
        places = " ".join(data["eligible_locations"]).lower()
        return any(word in places for word in INCLUDES_NIGERIA)
    return False


def main() -> None:
    postings = {}
    for line in POSTINGS.open(encoding="utf-8"):
        posting = json.loads(line)
        postings[posting["id"]] = posting
    records = [json.loads(line) for line in EXTRACTIONS.open(encoding="utf-8")]
    records.sort(key=lambda r: r["id"])

    for record in records:
        data = record["data"]
        print(f"\n{record['id']}  ({postings[record['id']]['title']})")
        print(f"  remote_scope: {data['remote_scope']}   locations: {data['eligible_locations']}")
        print(f"  timezone: {data['required_timezone']}   pay: {data['stated_pay']}")
        print(f"  seniority: {data['seniority']}   problems: {record['problems'] or 'none'}")

    # Only trust records that passed every check. The others need a person to look.
    passed = [r for r in records if not r["problems"]]
    open_ids = [r["id"] for r in passed if open_from_nigeria(r["data"])]
    results = {
        "postings": len(records),
        "passed_every_check": len(passed),
        "problems": dict(Counter(p for r in records for p in r["problems"])),
        "remote_scope": dict(Counter(r["data"]["remote_scope"] for r in records)),
        "open_from_nigeria": open_ids,
        "zenrows_credits": sum(p["credits"] for p in postings.values()),
        "pages_needing_javascript": sum(p["js_render"] for p in postings.values()),
        "openai_tokens": sum(r["tokens"] for r in records),
    }
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\n" + json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
