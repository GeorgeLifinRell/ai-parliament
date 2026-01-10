from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from .vote import Vote


class Decision(BaseModel):
    """
    Constitutional model for a final Decision on a Bill.

    Design principles:
    - Immutable record of parliamentary outcome
    - Contains all votes that led to the decision
    - Tracks veto power usage
    - Auditable and explainable
    """

    id: UUID
    bill_id: UUID
    bill_version: int
    bill_title: str
    passed: bool
    total_approve_weight: float
    total_reject_weight: float
    total_abstain_weight: float
    votes: list[Vote]
    vetoed_by: list[str] = []  # List of faction names that used veto power
    decided_at: datetime
    decision_summary: str

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=False
    )

    @field_validator("bill_title", "decision_summary")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must be a non-empty string")
        return value.strip()

    @field_validator("total_approve_weight", "total_reject_weight", "total_abstain_weight")
    @classmethod
    def non_negative_weight(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Weight totals must be non-negative")
        return value

    @field_validator("votes")
    @classmethod
    def must_have_votes(cls, value: list[Vote]) -> list[Vote]:
        if not value:
            raise ValueError("Decision must include at least one vote")
        return value
