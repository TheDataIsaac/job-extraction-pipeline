"""Check an extraction against the posting text with string matching (no model call).

Copied from job-extraction-pipeline's verify.py. Only the list of claimed fields changed to
match the full-time schema.
"""

import re

from schema import JobExtraction, RemoteScope, Seniority


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower().strip()


def check(extraction: JobExtraction, posting_text: str) -> list[str]:
    """Return a list of problems. An empty list means the extraction passed."""
    text = _normalise(posting_text)
    problems = []

    # A blank quote would always match ("" is in every string), so it is treated as no quote.
    evidence = [e for e in extraction.evidence if e.quote.strip()]
    quoted = {e.field for e in evidence}
    for item in evidence:
        if _normalise(item.quote) not in text:
            problems.append(f"quote for {item.field} is not in the posting")

    # A claimed fact with no quote at all is also a problem.
    claims = {
        "seniority": extraction.seniority != Seniority.NOT_STATED,
        "remote_scope": extraction.remote_scope != RemoteScope.NOT_STATED,
        "eligible_locations": bool(extraction.eligible_locations),
        "required_timezone": extraction.required_timezone is not None,
        "stated_pay": extraction.stated_pay is not None,
    }
    for field, claimed in claims.items():
        if claimed and field not in quoted:
            problems.append(f"{field} has no supporting quote")

    # The pay has to appear in the text, digits included. Each number must match whole,
    # with no digit right before or after it, so "15" does not match inside "150".
    if extraction.stated_pay:
        digits = re.findall(r"\d+", extraction.stated_pay)
        if digits and not all(re.search(rf"(?<!\d){d}(?!\d)", text) for d in digits):
            problems.append("stated_pay numbers are not in the posting")

    return problems
