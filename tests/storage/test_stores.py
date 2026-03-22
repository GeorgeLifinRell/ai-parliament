"""
Unit tests for SessionStore and PrecedentStore.
"""

import json
import pytest
import tempfile
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from parliament.core.bill import Bill, BillStatus
from parliament.core.vote import Vote, VoteChoice
from parliament.core.decision import Decision
from parliament.core.amendment import Amendment, AmendmentStatus
from parliament.core.debate import DebateArgument
from parliament.storage.session_store import SessionStore
from parliament.storage.precedent_store import PrecedentStore


# ---- Helpers ----

def make_bill() -> Bill:
    return Bill(
        id=uuid4(),
        title="Test Bill",
        proposal="Test proposal",
        assumptions=["a"],
        intended_outcomes=["b"],
        known_risks=["c"],
        unknowns=["d"],
        status=BillStatus.DRAFT,
    )


def make_vote(bill: Bill) -> Vote:
    return Vote(
        id=uuid4(),
        bill_id=bill.id,
        bill_version=bill.version,
        faction="Efficiency",
        choice=VoteChoice.APPROVE,
        weight=1.0,
        justification="Looks good.",
    )


def make_decision(bill: Bill, votes: list[Vote]) -> Decision:
    return Decision(
        id=uuid4(),
        bill_id=bill.id,
        bill_version=bill.version,
        bill_title=bill.title,
        passed=True,
        total_approve_weight=1.0,
        total_reject_weight=0.0,
        total_abstain_weight=0.0,
        votes=votes,
        vetoed_by=[],
        coalitions={"APPROVE": ["Efficiency"]},
        decided_at=datetime.now(),
        decision_summary="Bill PASSED",
    )


def make_store(tmp_path: Path) -> SessionStore:
    return SessionStore(db_path=tmp_path / "test.db")


# ---- SessionStore ----

class TestSessionStore:
    def test_create_and_list_session(self, tmp_path):
        store = make_store(tmp_path)
        bill = make_bill()
        session_id = store.create_session(bill)
        sessions = store.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == session_id
        assert sessions[0]["bill_title"] == "Test Bill"
        assert sessions[0]["concluded_at"] is None

    def test_conclude_session(self, tmp_path):
        store = make_store(tmp_path)
        bill = make_bill()
        session_id = store.create_session(bill)
        store.conclude_session(session_id)
        sessions = store.list_sessions()
        assert sessions[0]["concluded_at"] is not None

    def test_save_and_retrieve_vote(self, tmp_path):
        store = make_store(tmp_path)
        bill = make_bill()
        session_id = store.create_session(bill)
        vote = make_vote(bill)
        store.save_vote(session_id, vote)
        votes = store.get_votes(session_id)
        assert len(votes) == 1
        assert votes[0]["faction"] == "Efficiency"
        assert votes[0]["choice"] == "APPROVE"

    def test_save_and_retrieve_decision(self, tmp_path):
        store = make_store(tmp_path)
        bill = make_bill()
        session_id = store.create_session(bill)
        vote = make_vote(bill)
        decision = make_decision(bill, [vote])
        store.save_decision(session_id, decision)
        decisions = store.get_decisions(session_id)
        assert len(decisions) == 1
        assert decisions[0]["passed"] == 1
        coalitions = json.loads(decisions[0]["coalitions"])
        assert "Efficiency" in coalitions["APPROVE"]

    def test_save_and_retrieve_amendment(self, tmp_path):
        store = make_store(tmp_path)
        bill = make_bill()
        session_id = store.create_session(bill)
        amendment = Amendment(
            id=uuid4(),
            bill_id=bill.id,
            bill_version=1,
            proposer_faction="Safety",
            change_summary="Add safety checks",
            rationale="Reduce risk",
        )
        store.save_amendment(session_id, amendment)
        amendments = store.get_amendments(session_id)
        assert len(amendments) == 1
        assert amendments[0]["status"] == "PENDING"

    def test_save_and_retrieve_debate_argument(self, tmp_path):
        store = make_store(tmp_path)
        bill = make_bill()
        session_id = store.create_session(bill)
        arg = DebateArgument(
            id=uuid4(),
            bill_id=bill.id,
            bill_version=1,
            speaker_faction="Safety",
            round_number=1,
            argument="We must be careful.",
            targeted_factions=["Efficiency"],
        )
        store.save_debate_argument(session_id, arg)
        args = store.get_debate_arguments(session_id)
        assert len(args) == 1
        assert args[0]["argument"] == "We must be careful."

    def test_export_session_includes_all_parts(self, tmp_path):
        store = make_store(tmp_path)
        bill = make_bill()
        session_id = store.create_session(bill)
        vote = make_vote(bill)
        store.save_vote(session_id, vote)
        decision = make_decision(bill, [vote])
        store.save_decision(session_id, decision)
        exported = store.export_session(session_id)
        assert "session" in exported
        assert "votes" in exported
        assert "decisions" in exported
        assert len(exported["votes"]) == 1

    def test_get_session_not_found_returns_none(self, tmp_path):
        store = make_store(tmp_path)
        result = store.get_session("nonexistent-id")
        assert result is None

    def test_multiple_sessions_isolated(self, tmp_path):
        store = make_store(tmp_path)
        bill1 = make_bill()
        bill2 = make_bill()
        s1 = store.create_session(bill1)
        s2 = store.create_session(bill2)
        v1 = make_vote(bill1)
        v2 = make_vote(bill2)
        store.save_vote(s1, v1)
        store.save_vote(s2, v2)
        assert len(store.get_votes(s1)) == 1
        assert len(store.get_votes(s2)) == 1


# ---- PrecedentStore ----

class TestPrecedentStore:
    def _make_decision(self, title: str, passed: bool) -> Decision:
        bill = make_bill()
        vote = make_vote(bill)
        return Decision(
            id=uuid4(),
            bill_id=bill.id,
            bill_version=1,
            bill_title=title,
            passed=passed,
            total_approve_weight=1.0,
            total_reject_weight=0.0,
            total_abstain_weight=0.0,
            votes=[vote],
            coalitions={"APPROVE": ["Efficiency"]},
            decided_at=datetime.now(),
            decision_summary="test",
        )

    def test_empty_store_returns_empty_context(self):
        store = PrecedentStore()
        assert store.get_precedent_context() == ""

    def test_record_increments_count(self):
        store = PrecedentStore()
        d = self._make_decision("Bill A", passed=True)
        store.record("proposal", d)
        assert len(store) == 1

    def test_context_contains_bill_title(self):
        store = PrecedentStore()
        d = self._make_decision("My Important Bill", passed=True)
        store.record("proposal text", d)
        context = store.get_precedent_context()
        assert "My Important Bill" in context

    def test_context_contains_outcome(self):
        store = PrecedentStore()
        d_pass = self._make_decision("Pass Bill", passed=True)
        d_fail = self._make_decision("Fail Bill", passed=False)
        store.record("x", d_pass)
        store.record("y", d_fail)
        context = store.get_precedent_context()
        assert "PASSED" in context
        assert "REJECTED" in context

    def test_max_entries_respected(self):
        store = PrecedentStore(max_entries=3)
        for i in range(5):
            d = self._make_decision(f"Bill {i}", passed=True)
            store.record("p", d)
        assert len(store) == 3

    def test_max_recent_limits_context_output(self):
        store = PrecedentStore()
        for i in range(10):
            d = self._make_decision(f"Bill {i}", passed=True)
            store.record("p", d)
        context = store.get_precedent_context(max_recent=2)
        # Only the 2 most recent should appear
        assert "Bill 9" in context
        assert "Bill 8" in context
        assert "Bill 7" not in context
