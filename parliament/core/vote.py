from uuid import UUID
from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator


class VoteChoice(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"


class Vote(BaseModel):
    """
    Constitutional model for a single vote.

    Design principles:
    - Immutable
    - One faction, one bill version, one choice
    - Justified and weighted
    """

    id: UUID
    bill_id: UUID
    bill_version: int
    faction: str
    choice: VoteChoice
    weight: float
    justification: str

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=False
    )

    @field_validator("justification", "faction")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must be a non-empty string")
        return value.strip()

    @field_validator("weight")
    @classmethod
    def positive_weight(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Weight must be a positive number")
        return value
