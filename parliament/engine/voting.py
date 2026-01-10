from parliament.core.vote import Vote, VoteChoice
from parliament.core.decision import Decision
from parliament.core.bill import Bill
from uuid import uuid4
from datetime import datetime


class VotingEngine:
    """
    Aggregates votes and produces a Decision.
    """

    def __init__(self, veto_factions: set[str] | None = None):
        self.veto_factions = veto_factions or set()

    def evaluate(self, bill: Bill, votes: list[Vote]) -> Decision:
        if not votes:
            raise ValueError("No votes cast")

        seen_factions: set[str] = set()

        approve_weight = 0.0
        reject_weight = 0.0
        abstain_weight = 0.0
        vetoed_by: list[str] = []

        for vote in votes:
            # ---- Legitimacy checks ----
            if vote.bill_id != bill.id:
                raise ValueError("Vote references wrong bill")

            if vote.bill_version != bill.version:
                raise ValueError("Vote references wrong bill version")

            if vote.faction in seen_factions:
                raise ValueError(f"Duplicate vote from faction {vote.faction}")

            seen_factions.add(vote.faction)

            # ---- Veto logic ----
            if vote.faction in self.veto_factions and vote.choice == VoteChoice.REJECT:
                vetoed_by.append(vote.faction)

            # ---- Weight aggregation ----
            if vote.choice == VoteChoice.APPROVE:
                approve_weight += vote.weight
            elif vote.choice == VoteChoice.REJECT:
                reject_weight += vote.weight
            elif vote.choice == VoteChoice.ABSTAIN:
                abstain_weight += vote.weight

        # ---- Final decision ----
        if vetoed_by:
            passed = False
            summary = f"Bill REJECTED - Vetoed by: {', '.join(vetoed_by)}"
        elif approve_weight > reject_weight:
            passed = True
            summary = f"Bill PASSED - Approve: {approve_weight}, Reject: {reject_weight}"
        else:
            passed = False
            summary = f"Bill REJECTED - Approve: {approve_weight}, Reject: {reject_weight}"

        return Decision(
            id=uuid4(),
            bill_id=bill.id,
            bill_version=bill.version,
            bill_title=bill.title,
            passed=passed,
            total_approve_weight=approve_weight,
            total_reject_weight=reject_weight,
            total_abstain_weight=abstain_weight,
            votes=votes,
            vetoed_by=vetoed_by,
            decided_at=datetime.now(),
            decision_summary=summary
        )
