from enum import Enum
from uuid import UUID
from pydantic import BaseModel, field_validator, model_validator, ConfigDict


class AmendmentStatus(str, Enum):
    """Lifecycle status of an amendment proposal."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Amendment(BaseModel):
    """
    Constitutional model for a Bill Amendment.

    Design principles:
    - Immutable after creation
    - References a specific bill version
    - Status starts as PENDING; accepted/rejected copies are created via model_copy()
    """

    id: UUID
    bill_id: UUID
    bill_version: int
    proposer_faction: str
    change_summary: str
    rationale: str
    status: AmendmentStatus = AmendmentStatus.PENDING

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=False
    )

    # ---- Field-level validation ----
    @field_validator("change_summary", "rationale")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must be a non-empty string")
        return value.strip()

    # ---- Model-level validation ----
    @model_validator(mode="after")
    def status_must_be_pending_at_creation(self):
        if self.status != AmendmentStatus.PENDING:
            raise ValueError(
                "Amendment status must be PENDING at creation time; "
                "use model_copy(update={'status': ...}) to advance the lifecycle"
            )
        return self
