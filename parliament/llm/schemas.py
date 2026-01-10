from pydantic import BaseModel
from typing import Literal


class StatementSchema(BaseModel):
    summary: str


class DebateSchema(BaseModel):
    argument: str
    targeted_factions: list[str] = []


class AmendmentSchema(BaseModel):
    change_summary: str
    rationale: str


class VoteSchema(BaseModel):
    choice: Literal["APPROVE", "REJECT", "ABSTAIN"]
    justification: str
