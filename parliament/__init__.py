"""
AI Parliament - Constrained Multi-Agent Governance System

A research-grade multi-agent architecture where institutions constrain intelligence.
"""

# Core models (immutable constitutional data models)
from .core import (
    Bill,
    BillStatus,
    Amendment,
    Vote,
    VoteChoice,
    Decision,
)

# Agents (LLM-powered faction agents)
from .agents.base import BaseFactionAgent
from .agents.llm_base import LLMFactionAgent
from .agents.efficiency import EfficiencyAgent
from .agents.safety import SafetyAgent
from .agents.equity import EquityAgent
from .agents.innovation import InnovationAgent
from .agents.compliance import ComplianceAgent

# Procedure layer (phase enforcement)
from .procedure.speaker import Speaker, Phase

# Voting engine (mechanical aggregation)
from .engine.voting import VotingEngine

# LLM layer (robust client)
from .llm.client import LLMClient
from .llm.schemas import StatementSchema, AmendmentSchema, VoteSchema

__version__ = "0.1.0"

__all__ = [
    # Core models
    "Bill",
    "BillStatus",
    "Amendment",
    "Vote",
    "VoteChoice",
    "Decision",
    
    # Agents
    "BaseFactionAgent",
    "LLMFactionAgent",
    "EfficiencyAgent",
    "SafetyAgent",
    "EquityAgent",
    "InnovationAgent",
    "ComplianceAgent",
    
    # Procedure
    "Speaker",
    "Phase",
    
    # Engine
    "VotingEngine",
    
    # LLM
    "LLMClient",
    "StatementSchema",
    "AmendmentSchema",
    "VoteSchema",
]
