"""
Integration tests for ParliamentSession with mocked LLM agents.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from parliament.core.bill import Bill, BillStatus
from parliament.core.vote import VoteChoice
from parliament.agents.efficiency import EfficiencyAgent
from parliament.agents.safety import SafetyAgent
from parliament.session.parliament_session import ParliamentSession
from parliament.storage.session_store import SessionStore
from parliament.storage.precedent_store import PrecedentStore


# ---- Helpers ----

IDEOLOGY = {"goal": "test", "priorities": [], "red_lines": []}


def make_bill(title: str = "Test Bill") -> Bill:
    return Bill(
        id=uuid4(),
        title=title,
        proposal="A test proposal",
        assumptions=["a"],
        intended_outcomes=["b"],
        known_risks=["c"],
        unknowns=["d"],
        status=BillStatus.DRAFT,
    )


def make_approving_agent(name: str, weight: float = 1.0) -> EfficiencyAgent:
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = _approving_llm_response(name)
    return EfficiencyAgent(IDEOLOGY, llm=mock_llm)


def _approving_llm_response(faction_name: str):
    """Returns different mock responses based on the prompt content."""
    call_count = {"n": 0}

    def side_effect(system, user):
        call_count["n"] += 1
        # Statement
        if '"summary"' in user:
            return {"summary": f"{faction_name} supports this bill."}
        # Debate
        if '"argument"' in user:
            return {"argument": f"{faction_name} argues for approval.", "targeted_factions": []}
        # Amendment
        if '"change_summary"' in user:
            return []
        # Vote
        if '"choice"' in user:
            return {"choice": "APPROVE", "justification": f"{faction_name} approves."}
        # Speaker: veto
        if "factions_with_veto" in str(user):
            return {"factions_with_veto": [], "reasoning": "no veto"}
        # Speaker: debate order
        if "faction_order" in str(user):
            return {"faction_order": [], "reasoning": "default order"}
        return {}

    return side_effect


def make_mock_speaker_llm() -> MagicMock:
    mock = MagicMock()
    mock.generate_json.side_effect = lambda s, u: (
        {"factions_with_veto": [], "reasoning": "test"}
        if "factions_with_veto" in u
        else {"faction_order": [], "reasoning": "test"}
    )
    return mock


def make_session(
    agents,
    store,
    precedent_store=None,
    max_debate_rounds=1,
) -> ParliamentSession:
    """Create a ParliamentSession with a mocked Speaker LLM."""
    return ParliamentSession(
        agents=agents,
        store=store,
        precedent_store=precedent_store,
        max_debate_rounds=max_debate_rounds,
        export_logs=False,
        speaker_llm=make_mock_speaker_llm(),
    )


# ---- Single-bill session ----

def test_session_returns_one_decision_for_one_bill():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = SessionStore(db_path=Path(tmpdir) / "test.db")
        bill = make_bill()

        # Use agents that abstain on LLM failure (safe default)
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = RuntimeError("no llm")
        agents = [
            EfficiencyAgent(IDEOLOGY, llm=mock_llm),
            SafetyAgent(IDEOLOGY, llm=mock_llm),
        ]

        session = make_session(agents=agents, store=store)
        decisions = session.run([bill])
        assert len(decisions) == 1


def test_session_persists_data_to_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = SessionStore(db_path=Path(tmpdir) / "test.db")
        bill = make_bill()

        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = RuntimeError("no llm")
        agents = [EfficiencyAgent(IDEOLOGY, llm=mock_llm)]

        session = make_session(agents=agents, store=store)
        session.run([bill])

        sessions = store.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["bill_title"] == "Test Bill"
        assert sessions[0]["concluded_at"] is not None


# ---- Multi-bill session ----

def test_session_processes_multiple_bills():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = SessionStore(db_path=Path(tmpdir) / "test.db")
        bills = [make_bill(f"Bill {i}") for i in range(3)]

        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = RuntimeError("no llm")
        agents = [EfficiencyAgent(IDEOLOGY, llm=mock_llm)]

        session = make_session(agents=agents, store=store)
        decisions = session.run(bills)
        assert len(decisions) == 3

        sessions = store.list_sessions()
        assert len(sessions) == 3


# ---- Precedent tracking ----

def test_precedents_accumulate_across_bills():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = SessionStore(db_path=Path(tmpdir) / "test.db")
        precedent_store = PrecedentStore()
        bills = [make_bill(f"Bill {i}") for i in range(2)]

        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = RuntimeError("no llm")
        agents = [EfficiencyAgent(IDEOLOGY, llm=mock_llm)]

        session = make_session(agents=agents, store=store, precedent_store=precedent_store)
        session.run(bills)
        assert len(precedent_store) == 2


def test_precedent_context_injected_into_agent_prompts():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = SessionStore(db_path=Path(tmpdir) / "test.db")
        precedent_store = PrecedentStore()

        # Pre-seed a precedent
        bill_a = make_bill("Prior Bill")

        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = RuntimeError("no llm")
        agents = [EfficiencyAgent(IDEOLOGY, llm=mock_llm)]

        session_a = make_session(agents=agents, store=store, precedent_store=precedent_store)
        session_a.run([bill_a])
        assert len(precedent_store) == 1

        # On next session, the agent's LLM should receive the precedent context
        mock_llm2 = MagicMock()
        mock_llm2.generate_json.return_value = {"summary": "ok"}
        agents2 = [EfficiencyAgent(IDEOLOGY, llm=mock_llm2)]

        session_b = make_session(agents=agents2, store=store, precedent_store=precedent_store)
        session_b.run([make_bill("Next Bill")])

        # Verify that the first statement call included the precedent context
        call_args = mock_llm2.generate_json.call_args_list
        # First call is the statement — system prompt should contain precedent
        first_system = call_args[0][0][0]
        assert "Prior Bill" in first_system
