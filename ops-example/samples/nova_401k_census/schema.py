"""The form the model fills in for each employee row of a 401(k) plan census.

Every value can be null, and every value has a *_quote field that verify.py checks against the
document. The documents in this folder are made up (see ABOUT.md).
"""

from datetime import date

from pydantic import BaseModel, Field


class Record(BaseModel):
    """One employee's census row for the plan year."""

    plan_sponsor: str | None = Field(description="The employer that sponsors the 401(k) plan.")
    plan_sponsor_quote: str | None
    employee_name: str | None = Field(description="First name then last name.")
    employee_name_quote: str | None
    hire_date: date | None
    hire_date_quote: str | None
    termination_date: date | None
    termination_date_quote: str | None
    hours_worked_ytd: float | None
    hours_worked_ytd_quote: str | None
    gross_compensation_ytd: float | None = Field(description="US dollars, as a plain number.")
    gross_compensation_ytd_quote: str | None
    deferral_percent: float | None = Field(
        description="6 for 6%. Null if no percentage is written, e.g. 'not enrolled'."
    )
    deferral_percent_quote: str | None
    needs_human: bool
    needs_human_reason: str | None


class Extraction(BaseModel):
    records: list[Record]


INSTRUCTIONS = """This sample: payroll data that plan sponsors send to a 401(k) administrator to
build the annual census.
- One record per employee the document gives census data for, even a single fact such as a
  termination date. Leave the rest null.
- Dates in these documents are US style: 03/02/2026 is 2 March 2026.
- Copy numbers exactly as the document writes them. If a scan has garbled a number, do not fix it
  silently: give your best reading and set needs_human.
- A document with no employee census data (an invoice question, scheduling) gives no records.
"""


def rules(record: dict) -> list[str]:
    """Business checks that need no model: what a census file can't go out without."""
    problems = []
    if record["employee_name"] is None:
        problems.append("no employee name")
    if record["hours_worked_ytd"] is None:
        problems.append("no hours worked")
    if record["gross_compensation_ytd"] is None:
        problems.append("no gross compensation")
    # Dates are saved as YYYY-MM-DD text, and that format sorts in date order.
    hired, left = record["hire_date"], record["termination_date"]
    if hired and left and left < hired:
        problems.append("termination date before hire date")
    if record["deferral_percent"] is not None and record["deferral_percent"] > 100:
        problems.append("deferral over 100%")
    return problems
