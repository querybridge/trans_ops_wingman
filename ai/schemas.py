"""Pydantic contracts for tool inputs and generated outputs."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

IssueCategory = Literal["missed_window", "missing_scan", "failed_attempt", "missing_pod", "none"]
IssueType = Literal["missed_window", "missing_scan", "failed_attempt", "missing_pod", "escalation"]
RegionCode = Literal["tampa", "orlando", "jacksonville"]
ShipmentId = Field(pattern=r"^SHP-\d{5}$")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Tool inputs (validated before any tool runs) ---------------------------

class ListExceptionsInput(Strict):
    region: Optional[RegionCode] = None
    customer_id: Optional[str] = None


class ShipmentInput(Strict):
    shipment_id: str = ShipmentId
    customer_id: Optional[str] = None


class RetrieveProcedureInput(Strict):
    issue_type: IssueType
    region: Optional[RegionCode] = None
    customer_id: Optional[str] = None


# --- Generated outputs -------------------------------------------------------

class CitedStatement(Strict):
    text: str = Field(min_length=1, max_length=600)
    evidence_ids: list[str] = Field(min_length=1, max_length=10)


class Conflict(Strict):
    description: str = Field(min_length=1, max_length=600)
    evidence_ids: list[str] = Field(min_length=2, max_length=10)


class ShipmentExplanation(Strict):
    summary: str = Field(min_length=1, max_length=800)
    shipment_id: str = ShipmentId
    issue_category: IssueCategory
    observed_facts: list[CitedStatement] = Field(min_length=1, max_length=10)
    recommended_next_action: CitedStatement
    proposed_responsible_role: str = Field(min_length=1, max_length=120)
    missing_information: list[str] = Field(default_factory=list, max_length=8)
    conflicts: list[Conflict] = Field(default_factory=list, max_length=5)
    requires_review: bool


class BriefingItem(Strict):
    shipment_id: str = ShipmentId
    issue_category: IssueCategory
    summary: str = Field(min_length=1, max_length=400)
    recommended_next_action: str = Field(min_length=1, max_length=400)
    proposed_responsible_role: str = Field(min_length=1, max_length=120)
    evidence_ids: list[str] = Field(min_length=1, max_length=10)


class ManagerBriefing(Strict):
    summary: str = Field(min_length=1, max_length=1200)
    shipment_count: int = Field(ge=0)
    exception_count: int = Field(ge=0)
    items: list[BriefingItem] = Field(max_length=25)
    missing_information: list[str] = Field(default_factory=list, max_length=10)
    requires_review: bool
