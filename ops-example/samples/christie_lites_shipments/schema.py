"""The form the model fills in for each shipment update about a rental job.

Every value can be null, and every value has a *_quote field that verify.py checks against the
document. The documents in this folder are made up (see ABOUT.md).
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class Status(StrEnum):
    SHIPPED = "shipped"
    DELAYED = "delayed"
    DELIVERED = "delivered"
    RETURNED = "returned"
    OTHER = "other"


class Record(BaseModel):
    """The latest status of one job's shipment."""

    order_number: str | None = Field(
        description="Our job or order number, digits only. Not a carrier tracking or PRO number."
    )
    order_number_quote: str | None
    branch: str | None = Field(description="Our branch city the gear ships from or returns to.")
    branch_quote: str | None
    ship_date: date | None
    ship_date_quote: str | None
    delivery_date: date | None = Field(description="Actual delivery date, or the expected one.")
    delivery_date_quote: str | None
    carrier: str | None
    carrier_quote: str | None
    item_count: int | None = Field(description="Number of cases or pieces.")
    item_count_quote: str | None
    status: Status | None
    status_quote: str | None
    delay_reason: str | None
    delay_reason_quote: str | None
    needs_human: bool
    needs_human_reason: str | None


class Extraction(BaseModel):
    records: list[Record]


INSTRUCTIONS = """This sample: shipment updates from branch warehouses, drivers and carriers at a
stage-lighting rental company.
- One record per job number. An email about two jobs gives two records.
- "Today", "tomorrow" and weekdays count from the date the message was sent.
- delay_reason is the cause of a delay (weather, road closure, carrier problem) and only for
  delayed shipments. "Running late" is not a cause: use null.
- A message with no shipment update (training reminders, social events) gives no records.
"""


def rules(record: dict) -> list[str]:
    """Business checks that need no model: what shipment tracking can't use as it is."""
    problems = []
    if record["order_number"] is None:
        problems.append("no job number")
    # Dates are saved as YYYY-MM-DD text, and that format sorts in date order.
    shipped, delivered = record["ship_date"], record["delivery_date"]
    if shipped and delivered and delivered < shipped:
        problems.append("delivery date before ship date")
    if record["status"] == "delayed" and record["delay_reason"] is None:
        problems.append("delayed with no reason")
    if record["status"] == "shipped" and record["item_count"] is None:
        problems.append("shipped with no item count")
    return problems
