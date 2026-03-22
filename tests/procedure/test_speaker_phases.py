"""
Unit tests for Speaker phase transitions (with mocked LLM).
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from parliament.core.bill import Bill, BillStatus
from parliament.procedure.speaker import Speaker, Phase


# ---- Helpers ----

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


def make_speaker(bill: Bill | None = None, max_debate_rounds: int = 2) -> Speaker:
    """Return a Speaker with a mocked LLM so no network calls are made."""
    if bill is None:
        bill = make_bill()
    mock_llm = MagicMock()
    mock_llm.generate_json.return_value = {
        "faction_order": [],
        "factions_with_veto": [],
        "reasoning": "mocked",
    }
    return Speaker(bill, max_debate_rounds=max_debate_rounds, llm=mock_llm)


# ---- Initialisation ----

def test_speaker_starts_in_introduction():
    speaker = make_speaker()
    assert speaker.phase == Phase.INTRODUCTION


def test_speaker_rejects_non_draft_bill():
    bill = make_bill()
    in_deliberation_bill = bill.model_copy(update={"status": BillStatus.IN_DELIBERATION})
    with pytest.raises(ValueError, match="Only draft bills"):
        Speaker(in_deliberation_bill)


# ---- Phase transitions ----

def test_full_phase_sequence():
    speaker = make_speaker()
    expected = [
        Phase.INTRODUCTION,
        Phase.FACTION_STATEMENTS,
        Phase.DEBATE,
        Phase.AMENDMENTS,
        Phase.VOTING,
        Phase.DECISION,
    ]
    assert speaker.phase == expected[0]
    for next_phase in expected[1:]:
        speaker.advance_phase()
        assert speaker.phase == next_phase


def test_advance_beyond_decision_raises():
    speaker = make_speaker()
    for _ in range(5):  # advance to DECISION
        speaker.advance_phase()
    with pytest.raises(RuntimeError, match="concluded"):
        speaker.advance_phase()


def test_force_vote_jumps_to_voting():
    speaker = make_speaker()
    speaker.advance_phase()  # FACTION_STATEMENTS
    speaker.force_vote()
    assert speaker.phase == Phase.VOTING


# ---- Action gating ----

def test_action_allowed_in_correct_phase():
    speaker = make_speaker()
    assert speaker.allow_action("introduce") is True
    assert speaker.allow_action("vote") is False


def test_vote_allowed_only_in_voting_phase():
    speaker = make_speaker()
    for _ in range(4):  # advance to VOTING
        speaker.advance_phase()
    assert speaker.phase == Phase.VOTING
    assert speaker.allow_action("vote") is True
    assert speaker.allow_action("statement") is False


# ---- Debate round management ----

def test_debate_round_advances():
    speaker = make_speaker(max_debate_rounds=3)
    speaker.advance_phase()  # FACTION_STATEMENTS
    speaker.advance_phase()  # DEBATE
    assert speaker.debate_round == 0
    assert speaker.next_debate_round() is True
    assert speaker.debate_round == 1
    assert speaker.next_debate_round() is True
    assert speaker.debate_round == 2
    # At max_debate_rounds, returns False
    assert speaker.next_debate_round() is False


def test_set_debate_order_outside_debate_phase_raises():
    speaker = make_speaker()
    speaker.advance_phase()  # FACTION_STATEMENTS
    with pytest.raises(RuntimeError, match="DEBATE phase"):
        speaker.set_debate_order(["A", "B"])


def test_set_debate_order_during_debate_phase():
    speaker = make_speaker()
    speaker.advance_phase()  # FACTION_STATEMENTS
    speaker.advance_phase()  # DEBATE
    speaker.set_debate_order(["Safety", "Efficiency"])
    assert speaker.debate_order == ["Safety", "Efficiency"]


def test_next_debate_round_outside_debate_raises():
    speaker = make_speaker()
    speaker.advance_phase()  # FACTION_STATEMENTS
    with pytest.raises(RuntimeError, match="DEBATE phase"):
        speaker.next_debate_round()


# ---- Veto power management ----

def test_veto_assignment_and_retrieval():
    speaker = make_speaker()
    speaker.assign_veto_power("Safety")
    speaker.assign_veto_power("Compliance")
    assert speaker.get_veto_factions() == {"Safety", "Compliance"}


def test_veto_revocation():
    speaker = make_speaker()
    speaker.assign_veto_power("Safety")
    speaker.revoke_veto_power("Safety")
    assert len(speaker.get_veto_factions()) == 0


def test_get_veto_factions_returns_copy():
    speaker = make_speaker()
    speaker.assign_veto_power("Safety")
    copy = speaker.get_veto_factions()
    copy.add("Intruder")
    assert "Intruder" not in speaker.get_veto_factions()


def test_duplicate_veto_assignment_is_idempotent():
    speaker = make_speaker()
    speaker.assign_veto_power("Safety")
    speaker.assign_veto_power("Safety")
    assert len(speaker.get_veto_factions()) == 1


# ---- LLM-backed methods return defaults on failure ----

def test_determine_debate_order_falls_back_to_default():
    bill = make_bill()
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = RuntimeError("LLM down")
    speaker = Speaker(bill, llm=mock_llm)
    speaker.advance_phase()  # FACTION_STATEMENTS
    speaker.advance_phase()  # DEBATE
    faction_names = ["Safety", "Efficiency", "Equity"]
    order = speaker.determine_debate_order(faction_names, {})
    assert set(order) == set(faction_names)


def test_determine_veto_powers_falls_back_to_empty():
    bill = make_bill()
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = RuntimeError("LLM down")
    speaker = Speaker(bill, llm=mock_llm)
    factions = ["Safety", "Efficiency"]
    ideologies = {f: {"goal": "test", "red_lines": []} for f in factions}
    result = speaker.determine_veto_powers(factions, ideologies)
    assert result == set()
