"""
Unit tests for VotingEngine.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from parliament.core.bill import Bill, BillStatus
from parliament.core.vote import Vote, VoteChoice
from parliament.core.decision import Decision
from parliament.engine.voting import VotingEngine


# ---- Fixtures ----

def make_bill(version: int = 1) -> Bill:
    return Bill(
        id=uuid4(),
        version=version,
        title="Test Bill",
        proposal="A test proposal",
        assumptions=["a"],
        intended_outcomes=["b"],
        known_risks=["c"],
        unknowns=["d"],
        status=BillStatus.DRAFT,
    )


def make_vote(bill: Bill, faction: str, choice: VoteChoice, weight: float = 1.0) -> Vote:
    return Vote(
        id=uuid4(),
        bill_id=bill.id,
        bill_version=bill.version,
        faction=faction,
        choice=choice,
        weight=weight,
        justification="test justification",
    )


# ---- Basic pass/fail ----

def test_majority_approve_passes():
    bill = make_bill()
    engine = VotingEngine()
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE, weight=2.0),
        make_vote(bill, "Safety", VoteChoice.REJECT, weight=1.0),
    ]
    decision = engine.evaluate(bill, votes)
    assert decision.passed is True


def test_majority_reject_fails():
    bill = make_bill()
    engine = VotingEngine()
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE, weight=1.0),
        make_vote(bill, "Safety", VoteChoice.REJECT, weight=2.0),
    ]
    decision = engine.evaluate(bill, votes)
    assert decision.passed is False


def test_tie_results_in_rejection():
    bill = make_bill()
    engine = VotingEngine()
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE, weight=1.0),
        make_vote(bill, "Safety", VoteChoice.REJECT, weight=1.0),
    ]
    decision = engine.evaluate(bill, votes)
    assert decision.passed is False


def test_abstain_does_not_count_toward_approve_or_reject():
    bill = make_bill()
    engine = VotingEngine()
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE, weight=1.0),
        make_vote(bill, "Safety", VoteChoice.ABSTAIN, weight=5.0),
    ]
    decision = engine.evaluate(bill, votes)
    # Approve weight 1 > Reject weight 0, so passes despite huge abstain
    assert decision.passed is True
    assert decision.total_abstain_weight == 5.0


# ---- Veto logic ----

def test_veto_overrides_majority_approve():
    bill = make_bill()
    engine = VotingEngine(veto_factions={"Safety"})
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE, weight=10.0),
        make_vote(bill, "Safety", VoteChoice.REJECT, weight=1.0),
    ]
    decision = engine.evaluate(bill, votes)
    assert decision.passed is False
    assert "Safety" in decision.vetoed_by


def test_veto_faction_approve_does_not_trigger_veto():
    bill = make_bill()
    engine = VotingEngine(veto_factions={"Safety"})
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE, weight=1.0),
        make_vote(bill, "Safety", VoteChoice.APPROVE, weight=1.5),
    ]
    decision = engine.evaluate(bill, votes)
    assert decision.passed is True
    assert decision.vetoed_by == []


def test_multiple_vetoes():
    bill = make_bill()
    engine = VotingEngine(veto_factions={"Safety", "Compliance"})
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE, weight=10.0),
        make_vote(bill, "Safety", VoteChoice.REJECT, weight=1.5),
        make_vote(bill, "Compliance", VoteChoice.REJECT, weight=1.2),
    ]
    decision = engine.evaluate(bill, votes)
    assert decision.passed is False
    assert "Safety" in decision.vetoed_by
    assert "Compliance" in decision.vetoed_by


# ---- Legitimacy checks ----

def test_no_votes_raises():
    bill = make_bill()
    engine = VotingEngine()
    with pytest.raises(ValueError, match="No votes cast"):
        engine.evaluate(bill, [])


def test_vote_for_wrong_bill_raises():
    bill = make_bill()
    other_bill = make_bill()
    engine = VotingEngine()
    wrong_vote = make_vote(other_bill, "Efficiency", VoteChoice.APPROVE)
    with pytest.raises(ValueError, match="wrong bill"):
        engine.evaluate(bill, [wrong_vote])


def test_duplicate_faction_vote_raises():
    bill = make_bill()
    engine = VotingEngine()
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE),
        make_vote(bill, "Efficiency", VoteChoice.REJECT),
    ]
    with pytest.raises(ValueError, match="Duplicate vote"):
        engine.evaluate(bill, votes)


# ---- Weight aggregation ----

def test_weight_totals_are_correct():
    bill = make_bill()
    engine = VotingEngine()
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE, weight=1.0),
        make_vote(bill, "Safety", VoteChoice.REJECT, weight=1.5),
        make_vote(bill, "Equity", VoteChoice.ABSTAIN, weight=1.0),
    ]
    decision = engine.evaluate(bill, votes)
    assert decision.total_approve_weight == 1.0
    assert decision.total_reject_weight == 1.5
    assert decision.total_abstain_weight == 1.0


# ---- Coalition tracking ----

def test_coalitions_are_populated():
    bill = make_bill()
    engine = VotingEngine()
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE),
        make_vote(bill, "Equity", VoteChoice.APPROVE),
        make_vote(bill, "Safety", VoteChoice.REJECT),
        make_vote(bill, "Innovation", VoteChoice.ABSTAIN),
    ]
    decision = engine.evaluate(bill, votes)
    assert set(decision.coalitions["APPROVE"]) == {"Efficiency", "Equity"}
    assert decision.coalitions["REJECT"] == ["Safety"]
    assert decision.coalitions["ABSTAIN"] == ["Innovation"]


def test_empty_coalition_entries_omitted():
    bill = make_bill()
    engine = VotingEngine()
    votes = [
        make_vote(bill, "Efficiency", VoteChoice.APPROVE),
        make_vote(bill, "Safety", VoteChoice.APPROVE),
    ]
    decision = engine.evaluate(bill, votes)
    assert "REJECT" not in decision.coalitions
    assert "ABSTAIN" not in decision.coalitions


# ---- Decision immutability ----

def test_decision_is_immutable():
    from pydantic import ValidationError
    bill = make_bill()
    engine = VotingEngine()
    votes = [make_vote(bill, "Efficiency", VoteChoice.APPROVE)]
    decision = engine.evaluate(bill, votes)
    with pytest.raises((TypeError, ValidationError)):
        decision.passed = False
