"""The structure the model must fill in for each posting.

Fields that can be missing are nullable, and facts that are easy to invent carry a quote from the posting
that verify.py checks.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ProjectType(StrEnum):
    DATA_ANALYSIS = "data_analysis"
    DASHBOARD_BI = "dashboard_bi"
    MACHINE_LEARNING = "machine_learning"
    DATA_ENTRY = "data_entry"
    WEB_SCRAPING = "web_scraping"
    SOFTWARE_DEV = "software_dev"
    WRITING_RESEARCH = "writing_research"
    OTHER = "other"


class ExperienceLevel(StrEnum):
    ENTRY = "entry"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    NOT_STATED = "not_stated"


class RedFlag(StrEnum):
    OFF_PLATFORM_CONTACT = "off_platform_contact"  # asks to talk by email, WhatsApp, Telegram...
    FREE_WORK_REQUESTED = "free_work_requested"  # wants a free sample or trial task
    VAGUE_BRIEF = "vague_brief"  # too little detail to know what is wanted


class Evidence(BaseModel):
    """A quote copied word for word from the posting, supporting one field."""

    field: Literal["experience_level", "timeline_days", "stated_budget", "red_flags"]
    quote: str = Field(description="Exact text from the posting. Do not paraphrase.")


class JobExtraction(BaseModel):
    project_type: ProjectType
    deliverables: list[str] = Field(
        description="What the client wants delivered, as short noun phrases. Empty if unclear."
    )
    tools: list[str] = Field(
        description="Tools, languages or technologies named in the text, lowercase."
    )
    experience_level: ExperienceLevel = Field(
        description="Only what the posting says. Use not_stated if it does not say."
    )
    timeline_days: int | None = Field(
        description="Deadline or duration converted to days. Null if the posting gives none."
    )
    is_urgent: bool = Field(description="True only if the text asks for fast delivery.")
    is_ongoing: bool = Field(description="True for long-term or repeat work, false for one-off.")
    stated_budget: str | None = Field(
        description="A budget written in the text, e.g. '$50' or '100 euros'. Null if none."
    )
    red_flags: list[RedFlag]
    evidence: list[Evidence] = Field(
        description="One quote for each of experience_level, timeline_days, stated_budget and "
        "red_flags that is not null, not_stated or empty."
    )
