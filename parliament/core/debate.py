from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DebateArgument(BaseModel):
    """
    Constitutional model for a debate argument.

    Design principles:
    - Immutable after creation
    - References a specific bill version
    - Can target specific factions or address all
    - Speaker mediates order, agents provide content
    """

    id: UUID
    bill_id: UUID
    bill_version: int
    speaker_faction: str
    round_number: int
    argument: str
    targeted_factions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=False
    )

    @field_validator("argument", "speaker_faction")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must be a non-empty string")
        return value.strip()

    @field_validator("round_number")
    @classmethod
    def positive_round(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Round number must be positive")
        return value
