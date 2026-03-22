"""
Amendment application engine.

Applies accepted amendments to produce new bill versions.
The original bill remains immutable; a new versioned Bill is returned.
"""

from parliament.core.amendment import Amendment, AmendmentStatus
from parliament.core.bill import Bill


def accept_amendment(amendment: Amendment) -> Amendment:
    """
    Return a new Amendment with status ACCEPTED.
    Does not mutate the original (frozen model).
    """
    return amendment.model_copy(update={"status": AmendmentStatus.ACCEPTED})


def reject_amendment(amendment: Amendment) -> Amendment:
    """
    Return a new Amendment with status REJECTED.
    Does not mutate the original (frozen model).
    """
    return amendment.model_copy(update={"status": AmendmentStatus.REJECTED})


def apply_amendment(bill: Bill, amendment: Amendment) -> Bill:
    """
    Apply an accepted amendment to a bill, returning a new bill version.

    The new bill's version is incremented by 1.
    The change_summary is appended to the proposal to reflect the amendment.

    Args:
        bill: The current bill.
        amendment: An amendment with status ACCEPTED.

    Returns:
        A new immutable Bill with an incremented version.

    Raises:
        ValueError: If the amendment is not ACCEPTED or references a different bill.
    """
    if amendment.status != AmendmentStatus.ACCEPTED:
        raise ValueError(
            f"Only ACCEPTED amendments can be applied; "
            f"got status={amendment.status.value}"
        )
    if amendment.bill_id != bill.id:
        raise ValueError("Amendment references a different bill")
    if amendment.bill_version != bill.version:
        raise ValueError(
            f"Amendment targets bill version {amendment.bill_version}, "
            f"but current version is {bill.version}"
        )

    updated_proposal = (
        f"{bill.proposal.strip()}\n\n"
        f"[Amendment v{bill.version + 1} by {amendment.proposer_faction}]: "
        f"{amendment.change_summary}"
    )

    return bill.model_copy(
        update={
            "version": bill.version + 1,
            "proposal": updated_proposal,
        }
    )


def apply_accepted_amendments(bill: Bill, amendments: list[Amendment]) -> tuple[Bill, list[Amendment]]:
    """
    Apply all ACCEPTED amendments to the bill sequentially.

    Returns:
        (updated_bill, list_of_accepted_amendments)
    """
    current_bill = bill
    accepted = []
    for amendment in amendments:
        if amendment.status == AmendmentStatus.ACCEPTED:
            current_bill = apply_amendment(current_bill, amendment)
            accepted.append(amendment)
    return current_bill, accepted
