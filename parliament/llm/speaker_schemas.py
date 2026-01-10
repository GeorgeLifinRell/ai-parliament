from pydantic import BaseModel
from typing import Literal


class DebateOrderSchema(BaseModel):
    """Schema for Speaker's debate order decision"""
    faction_order: list[str]
    reasoning: str


class VetoPowerSchema(BaseModel):
    """Schema for Speaker's veto power assignments"""
    factions_with_veto: list[str]
    reasoning: str


class ForceVoteSchema(BaseModel):
    """Schema for Speaker's decision to force a vote"""
    should_force_vote: bool
    reasoning: str
