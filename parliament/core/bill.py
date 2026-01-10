from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BillStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_DELIBERATION = "IN_DELIBERATION"
    PASSED = "PASSED"
    REJECTED = "REJECTED"


class Bill(BaseModel):
    """
    Constitutional model for a Bill.

    Design principles:
    - Immutable after creation
    - Strict validation (invalid bills are rejected early)
    - No historical state stored here (history belongs in audit logs)
    """

    id: UUID
    version: int = Field(default=1, frozen=True)
    title: str
    proposal: str
    assumptions: list[str]
    intended_outcomes: list[str]
    known_risks: list[str]
    unknowns: list[str]
    status: BillStatus = BillStatus.DRAFT

    # ---- Model-level guarantees ----
    model_config = ConfigDict(
        frozen=True,              # Enforce immutability
        extra="forbid",           # No undeclared fields allowed
        validate_assignment=False
    )

    # ---- Field-level validation ----
    @field_validator("title", "proposal")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must be a non-empty string")
        return value.strip()

    @field_validator("version")
    @classmethod
    def version_must_start_at_one(cls, value: int) -> int:
        if value != 1:
            raise ValueError("Bill version must start at 1")
        return value
