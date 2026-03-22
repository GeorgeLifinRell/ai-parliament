"""
Unit tests for LLMFactionAgent with a mocked LLM client.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from parliament.core.bill import Bill, BillStatus
from parliament.core.amendment import Amendment, AmendmentStatus
from parliament.core.vote import VoteChoice
from parliament.agents.efficiency import EfficiencyAgent
from parliament.agents.safety import SafetyAgent


# ---- Helpers ----

IDEOLOGY = {
    "goal": "Minimize cost",
    "priorities": ["speed", "cost"],
    "red_lines": ["unnecessary complexity"],
}

SAFETY_IDEOLOGY = {
    "goal": "Prevent harm",
    "priorities": ["risk", "safety"],
    "red_lines": ["unbounded risk"],
}


def make_bill() -> Bill:
    return Bill(
        id=uuid4(),
        title="Test Bill",
        proposal="A test proposal",
        assumptions=["a"],
        intended_outcomes=["b"],
        known_risks=["c"],
        unknowns=["d"],
        status=BillStatus.DRAFT,
    )


def make_mock_llm(return_value: dict) -> MagicMock:
    mock = MagicMock()
    mock.generate_json.return_value = return_value
    return mock


# ---- Statement ----

def test_statement_returns_summary():
    mock_llm = make_mock_llm({"summary": "We support this bill for cost reasons."})
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    result = agent.statement(bill)
    assert result == "We support this bill for cost reasons."


def test_statement_gracefully_degrades_on_llm_failure():
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = RuntimeError("LLM down")
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    result = agent.statement(bill)
    assert isinstance(result, str)
    assert len(result) > 0


def test_statement_includes_precedent_context_in_prompt():
    mock_llm = make_mock_llm({"summary": "ok"})
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    agent.statement(bill, precedent_context="Past: Bill X was REJECTED.")
    call_kwargs = mock_llm.generate_json.call_args
    system_prompt = call_kwargs[0][0]
    assert "Past: Bill X was REJECTED." in system_prompt


# ---- Debate ----

def test_debate_returns_argument():
    mock_llm = make_mock_llm({"argument": "We should pass this.", "targeted_factions": ["Safety"]})
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    argument = agent.debate(bill, round_number=1, all_factions=["Efficiency", "Safety", "Equity"])
    assert argument is not None
    assert argument.argument == "We should pass this."
    assert argument.targeted_factions == ["Safety"]
    assert argument.speaker_faction == "Efficiency"


def test_debate_returns_none_on_llm_failure():
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = RuntimeError("LLM down")
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    result = agent.debate(bill, round_number=1, all_factions=["Efficiency", "Safety"])
    assert result is None


def test_debate_argument_links_to_bill():
    mock_llm = make_mock_llm({"argument": "Debate point.", "targeted_factions": []})
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    argument = agent.debate(bill, round_number=2, all_factions=["Efficiency"])
    assert argument.bill_id == bill.id
    assert argument.bill_version == bill.version
    assert argument.round_number == 2


# ---- Amendments ----

def test_propose_amendments_returns_list():
    mock_llm = make_mock_llm([{"change_summary": "Simplify scope", "rationale": "Reduce cost"}])
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    amendments = agent.propose_amendments(bill)
    assert len(amendments) == 1
    assert amendments[0].change_summary == "Simplify scope"
    assert amendments[0].proposer_faction == "Efficiency"
    assert amendments[0].status == AmendmentStatus.PENDING


def test_propose_amendments_returns_empty_list_on_llm_failure():
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = RuntimeError("LLM down")
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    result = agent.propose_amendments(bill)
    assert result == []


def test_propose_amendments_empty_when_llm_returns_empty():
    mock_llm = make_mock_llm([])
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    result = agent.propose_amendments(bill)
    assert result == []


# ---- Voting ----

def test_vote_returns_approve():
    mock_llm = make_mock_llm({"choice": "APPROVE", "justification": "Looks good."})
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    vote = agent.vote(bill, [])
    assert vote.choice == VoteChoice.APPROVE
    assert vote.faction == "Efficiency"
    assert vote.weight == 1.0


def test_vote_returns_reject():
    mock_llm = make_mock_llm({"choice": "REJECT", "justification": "Too risky."})
    agent = SafetyAgent(SAFETY_IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    vote = agent.vote(bill, [])
    assert vote.choice == VoteChoice.REJECT
    assert vote.faction == "Safety"
    assert vote.weight == 1.5


def test_vote_abstains_gracefully_on_llm_failure():
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = RuntimeError("LLM down")
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    vote = agent.vote(bill, [])
    assert vote.choice == VoteChoice.ABSTAIN
    assert "LLM failure" in vote.justification


def test_vote_includes_amendment_context_in_prompt():
    mock_llm = make_mock_llm({"choice": "APPROVE", "justification": "Fine."})
    agent = EfficiencyAgent(IDEOLOGY, llm=mock_llm)
    bill = make_bill()
    amendment = Amendment(
        id=uuid4(),
        bill_id=bill.id,
        bill_version=1,
        proposer_faction="Safety",
        change_summary="Add safety checks",
        rationale="Reduce risk",
    )
    agent.vote(bill, [amendment])
    call_kwargs = mock_llm.generate_json.call_args
    user_prompt = call_kwargs[0][1]
    assert "Add safety checks" in user_prompt
