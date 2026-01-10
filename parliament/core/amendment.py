from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class Amendment(BaseModel):
    """
    Constitutional model for a Bill Amendment.

    Design principles:
    - Immutable after creation
    - References a specific bill version
    - Cannot decide its own acceptance
    """

    id: UUID
    bill_id: UUID
    bill_version: int
    proposer_faction: str
    change_summary: str
    rationale: str
    accepted: bool | None = None

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
    def forbid_premature_decision(self):
        if self.accepted is not None:
            raise ValueError(
                "Amendment cannot be accepted or rejected at creation time"
            )
        return self
