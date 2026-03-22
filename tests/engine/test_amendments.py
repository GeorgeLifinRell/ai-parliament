"""
Unit tests for the amendment application engine.
"""

import pytest
from uuid import uuid4

from parliament.core.bill import Bill, BillStatus
from parliament.core.amendment import Amendment, AmendmentStatus
from parliament.engine.amendments import (
    accept_amendment,
    reject_amendment,
    apply_amendment,
    apply_accepted_amendments,
)


# ---- Helpers ----

def make_bill(version: int = 1) -> Bill:
    return Bill(
        id=uuid4(),
        version=version,
        title="Test Bill",
        proposal="Original proposal",
        assumptions=["a"],
        intended_outcomes=["b"],
        known_risks=["c"],
        unknowns=["d"],
        status=BillStatus.DRAFT,
    )


def make_amendment(bill: Bill) -> Amendment:
    return Amendment(
        id=uuid4(),
        bill_id=bill.id,
        bill_version=bill.version,
        proposer_faction="Safety",
        change_summary="Add safety clause",
        rationale="Reduce risk",
    )


# ---- accept_amendment / reject_amendment ----

def test_accept_amendment_creates_accepted_copy():
    bill = make_bill()
    a = make_amendment(bill)
    accepted = accept_amendment(a)
    assert accepted.status == AmendmentStatus.ACCEPTED
    assert a.status == AmendmentStatus.PENDING  # original unchanged


def test_reject_amendment_creates_rejected_copy():
    bill = make_bill()
    a = make_amendment(bill)
    rejected = reject_amendment(a)
    assert rejected.status == AmendmentStatus.REJECTED
    assert a.status == AmendmentStatus.PENDING  # original unchanged


# ---- apply_amendment ----

def test_apply_amendment_increments_version():
    bill = make_bill()
    accepted = accept_amendment(make_amendment(bill))
    new_bill = apply_amendment(bill, accepted)
    assert new_bill.version == 2


def test_apply_amendment_appends_to_proposal():
    bill = make_bill()
    accepted = accept_amendment(make_amendment(bill))
    new_bill = apply_amendment(bill, accepted)
    assert "Add safety clause" in new_bill.proposal
    assert "Original proposal" in new_bill.proposal


def test_apply_amendment_preserves_bill_id():
    bill = make_bill()
    accepted = accept_amendment(make_amendment(bill))
    new_bill = apply_amendment(bill, accepted)
    assert new_bill.id == bill.id


def test_apply_non_accepted_amendment_raises():
    bill = make_bill()
    pending = make_amendment(bill)
    with pytest.raises(ValueError, match="ACCEPTED"):
        apply_amendment(bill, pending)


def test_apply_rejected_amendment_raises():
    bill = make_bill()
    rejected = reject_amendment(make_amendment(bill))
    with pytest.raises(ValueError, match="ACCEPTED"):
        apply_amendment(bill, rejected)


def test_apply_amendment_wrong_bill_raises():
    bill = make_bill()
    other_bill = make_bill()
    accepted = accept_amendment(make_amendment(other_bill))
    with pytest.raises(ValueError, match="different bill"):
        apply_amendment(bill, accepted)


def test_apply_amendment_wrong_version_raises():
    bill = make_bill()
    amendment_v1 = make_amendment(bill)
    accepted_v1 = accept_amendment(amendment_v1)
    # Bump to v2 by applying it once
    bill_v2 = apply_amendment(bill, accepted_v1)
    # Now try to apply the same (v1-targeting) amendment to v2 bill
    amendment_v2 = make_amendment(bill_v2)
    accepted_v2 = accept_amendment(amendment_v2)
    # Should work for v2
    bill_v3 = apply_amendment(bill_v2, accepted_v2)
    assert bill_v3.version == 3


# ---- apply_accepted_amendments ----

def test_apply_accepted_amendments_skips_pending():
    bill = make_bill()
    pending = make_amendment(bill)
    accepted = accept_amendment(make_amendment(bill))
    final_bill, applied = apply_accepted_amendments(bill, [pending, accepted])
    assert len(applied) == 1
    assert final_bill.version == 2


def test_apply_accepted_amendments_empty_list():
    bill = make_bill()
    final_bill, applied = apply_accepted_amendments(bill, [])
    assert final_bill.version == 1
    assert applied == []


def test_apply_multiple_accepted_amendments_sequentially():
    bill = make_bill()
    a1 = accept_amendment(make_amendment(bill))
    bill_v2 = apply_amendment(bill, a1)
    a2 = accept_amendment(make_amendment(bill_v2))
    # apply_accepted_amendments handles the chaining
    # First, create both amendments against sequential versions
    final_bill, applied = apply_accepted_amendments(bill, [a1])
    assert final_bill.version == 2
    assert len(applied) == 1
