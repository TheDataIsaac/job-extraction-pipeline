"""Check an extraction against the posting text with string matching (no model call)."""

import re

from job_extraction.schema import ExperienceLevel, JobExtraction


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower().strip()


def check(extraction: JobExtraction, posting_text: str) -> list[str]:
    """Return a list of problems. An empty list means the extraction passed."""
    text = _normalise(posting_text)
    problems = []

    quoted = {e.field for e in extraction.evidence}
    for item in extraction.evidence:
        if _normalise(item.quote) not in text:
            problems.append(f"quote for {item.field} is not in the posting")

    # A claimed fact with no quote at all is also a problem.
    claims = {
        "experience_level": extraction.experience_level != ExperienceLevel.NOT_STATED,
        "timeline_days": extraction.timeline_days is not None,
        "stated_budget": extraction.stated_budget is not None,
        "red_flags": bool(extraction.red_flags),
    }
    for field, claimed in claims.items():
        if claimed and field not in quoted:
            problems.append(f"{field} has no supporting quote")

    # The budget has to appear in the text, digits included.
    if extraction.stated_budget:
        digits = re.findall(r"\d+", extraction.stated_budget)
        if digits and not all(d in text for d in digits):
            problems.append("stated_budget numbers are not in the posting")

    return problems
