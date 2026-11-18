"""The structure the model must fill in for each posting.

Adapted from job-extraction-pipeline's schema.py, which was built for freelance gigs. The
freelance fields (project type, deliverables, deadline, budget, red flags) are swapped for
full-time ones: seniority, where you can work from, time zone and pay. The ideas stay the same:
fields that can be missing are nullable, and facts that are easy to invent carry a quote from
the posting that verify.py checks.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Seniority(StrEnum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD_OR_MANAGER = "lead_or_manager"
    NOT_STATED = "not_stated"


class RemoteScope(StrEnum):
    ANYWHERE = "anywhere"  # can be done from any country
    REGIONS = "regions"  # remote, but only from named regions such as EMEA or the Americas
    COUNTRIES = "countries"  # remote, but only from named countries
    HYBRID_OR_OFFICE = "hybrid_or_office"  # needs regular time in an office
    NOT_STATED = "not_stated"


class Evidence(BaseModel):
    """A quote copied word for word from the posting, supporting one field."""

    field: Literal[
        "seniority", "remote_scope", "eligible_locations", "required_timezone", "stated_pay"
    ]
    quote: str = Field(description="Exact text from the posting. Do not paraphrase.")


class JobExtraction(BaseModel):
    seniority: Seniority = Field(
        description="Only what the posting says. Use not_stated if it does not say."
    )
    tools: list[str] = Field(
        description="Tools, languages or technologies named in the text, lowercase."
    )
    remote_scope: RemoteScope = Field(
        description="Where the person can work from, as the posting states it."
    )
    eligible_locations: list[str] = Field(
        description="Regions, countries or cities the posting says the person can work from. "
        "Empty if it names none."
    )
    required_timezone: str | None = Field(
        description="A time zone the person must work in, e.g. 'US Pacific'. Null if none."
    )
    stated_pay: str | None = Field(
        description="Pay written in the text, e.g. '$120,000 - $150,000'. Null if none."
    )
    evidence: list[Evidence] = Field(
        description="One quote for each of seniority, remote_scope, eligible_locations, "
        "required_timezone and stated_pay that is not null, not_stated or empty."
    )
