import pytest
from uuid import uuid4
from parliament.core.amendment import Amendment


def test_empty_change_summary_fails():
    with pytest.raises(ValueError):
        Amendment(
            id=uuid4(),
            bill_id=uuid4(),
            bill_version=1,
            proposer_faction="Safety",
            change_summary="   ",
            rationale="Reduce catastrophic risk"
        )

def test_amendment_cannot_self_accept():
    with pytest.raises(ValueError):
        Amendment(
            id=uuid4(),
            bill_id=uuid4(),
            bill_version=1,
            proposer_faction="Equity",
            change_summary="Add fairness constraint",
            rationale="Prevent unequal outcomes",
            accepted=True
        )

def test_amendment_is_immutable():
    amendment = Amendment(
        id=uuid4(),
        bill_id=uuid4(),
        bill_version=1,
        proposer_faction="Efficiency",
        change_summary="Reduce scope",
        rationale="Lower operational cost"
    )

    with pytest.raises(TypeError):
        amendment.change_summary = "New text"

def test_accepted_defaults_to_none():
    amendment = Amendment(
        id=uuid4(),
        bill_id=uuid4(),
        bill_version=1,
        proposer_faction="Innovation",
        change_summary="Enable experimental feature",
        rationale="Long-term upside"
    )

    assert amendment.accepted is None
