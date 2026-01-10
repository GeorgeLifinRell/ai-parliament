from pydantic import BaseModel, ConfigDict
from uuid import UUID


class Decision(BaseModel):
    bill_id: UUID
    bill_version: int
    passed: bool
    approve_weight: float
    reject_weight: float
    abstentions: int
    vetoed_by: list[str]

    model_config = ConfigDict(
        frozen=True,
        extra="forbid"
    )
