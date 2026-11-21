"""The form the model fills in for each payroll change sent in by a client company.

Every value can be null, and every value has a *_quote field that verify.py checks against the
email. The documents in this folder are made up (see ABOUT.md).
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class ChangeType(StrEnum):
    SALARY_CHANGE = "salary_change"
    BONUS = "bonus"
    EXPENSE = "expense"
    UNPAID_LEAVE = "unpaid_leave"
    TERMINATION = "termination"
    OTHER = "other"


class Record(BaseModel):
    """One payroll change for one employee."""

    employee_name: str | None
    employee_name_quote: str | None
    client_company: str | None = Field(description="The company the employee works for.")
    client_company_quote: str | None
    country: str | None = Field(description="The country the employee works in.")
    country_quote: str | None
    change_type: ChangeType | None
    change_type_quote: str | None
    amount: float | None = Field(
        description="The money amount as a plain number, e.g. 3600 for 'EUR 3,600'. For a "
        "salary change, the new salary."
    )
    amount_quote: str | None
    currency: str | None = Field(description="Three-letter code, e.g. EUR, only if written.")
    currency_quote: str | None
    effective_date: date | None
    effective_date_quote: str | None
    pay_period: str | None = Field(description="The payroll run it belongs to, as written.")
    pay_period_quote: str | None
    country_note: str | None = Field(
        description="A country-specific payroll or tax instruction, in a few words."
    )
    country_note_quote: str | None
    needs_human: bool
    needs_human_reason: str | None


class Extraction(BaseModel):
    records: list[Record]


INSTRUCTIONS = """This sample: emails from client companies to an employer-of-record payroll team.
- One record per payroll change per employee. An email about two employees gives two records.
- An email with no payroll change for a named employee (an invitation, a question, an
  announcement) gives no records.
- amount is money only. Days of leave are not an amount. A termination has no amount unless a
  payment is written.
- currency is null unless the email writes it. A symbol counts when it names one currency
  (€ is EUR, £ is GBP, ₹ is INR). A bare number does not: do not work it out from the country.
"""

MONEY_CHANGES = {"salary_change", "bonus", "expense"}


def rules(record: dict) -> list[str]:
    """Business checks that need no model: what payroll can't process without."""
    problems = []
    if record["employee_name"] is None:
        problems.append("no employee name")
    if record["change_type"] in MONEY_CHANGES and record["amount"] is None:
        problems.append("money change with no amount")
    if record["amount"] is not None and record["currency"] is None:
        problems.append("amount with no currency")
    if record["effective_date"] is None and record["pay_period"] is None:
        problems.append("no effective date or pay period")
    return problems
