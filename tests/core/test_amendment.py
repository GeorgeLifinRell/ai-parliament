import pytest
from uuid import uuid4
from pydantic import ValidationError
from parliament.core.amendment import Amendment, AmendmentStatus


def _make_amendment(**overrides) -> Amendment:
    defaults = dict(
        id=uuid4(),
        bill_id=uuid4(),
        bill_version=1,
        proposer_faction="Safety",
        change_summary="Add rollback mechanism",
        rationale="Reduce catastrophic risk",
    )
    defaults.update(overrides)
    return Amendment(**defaults)


def test_empty_change_summary_fails():
    with pytest.raises(ValueError):
        _make_amendment(change_summary="   ")


def test_amendment_must_start_pending():
    """Amendment status must be PENDING at creation time."""
    with pytest.raises(ValueError):
        _make_amendment(status=AmendmentStatus.ACCEPTED)

    with pytest.raises(ValueError):
        _make_amendment(status=AmendmentStatus.REJECTED)


def test_amendment_is_immutable():
    amendment = _make_amendment()
    with pytest.raises((TypeError, ValidationError)):
        amendment.change_summary = "New text"


def test_status_defaults_to_pending():
    amendment = _make_amendment()
    assert amendment.status == AmendmentStatus.PENDING


def test_accept_creates_new_object():
    from parliament.engine.amendments import accept_amendment
    original = _make_amendment()
    accepted = accept_amendment(original)
    assert accepted.status == AmendmentStatus.ACCEPTED
    assert original.status == AmendmentStatus.PENDING  # unchanged


def test_reject_creates_new_object():
    from parliament.engine.amendments import reject_amendment
    original = _make_amendment()
    rejected = reject_amendment(original)
    assert rejected.status == AmendmentStatus.REJECTED
    assert original.status == AmendmentStatus.PENDING  # unchanged

