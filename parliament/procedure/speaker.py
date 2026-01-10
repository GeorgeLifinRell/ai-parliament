from enum import Enum
from parliament.core.bill import Bill, BillStatus


class Phase(str, Enum):
    INTRODUCTION = "INTRODUCTION"
    FACTION_STATEMENTS = "FACTION_STATEMENTS"
    AMENDMENTS = "AMENDMENTS"
    VOTING = "VOTING"
    DECISION = "DECISION"


class Speaker:
    """
    The Speaker enforces parliamentary procedure.
    It has authority but no opinion.
    """

    def __init__(self, bill: Bill, max_rounds: int = 3):
        if bill.status != BillStatus.DRAFT:
            raise ValueError("Only draft bills may enter parliament")

        self.bill = bill
        self.phase = Phase.INTRODUCTION
        self.round = 0
        self.max_rounds = max_rounds

    # ---- Phase control ----

    def allow_action(self, action: str) -> bool:
        """
        Validates whether an action is allowed in the current phase.
        """
        allowed = {
            Phase.INTRODUCTION: {"introduce"},
            Phase.FACTION_STATEMENTS: {"statement"},
            Phase.AMENDMENTS: {"amend"},
            Phase.VOTING: {"vote"},
            Phase.DECISION: set(),
        }

        return action in allowed[self.phase]

    def advance_phase(self):
        """
        Advances to the next phase in order.
        """
        if self.phase == Phase.DECISION:
            raise RuntimeError("Parliament has concluded")

        phase_order = list(Phase)
        idx = phase_order.index(self.phase)
        self.phase = phase_order[idx + 1]

        if self.phase == Phase.FACTION_STATEMENTS:
            self.round += 1
            if self.round > self.max_rounds:
                self.force_vote()

    def force_vote(self):
        """
        Ends debate and moves directly to voting.
        """
        self.phase = Phase.VOTING

    def conclude(self):
        """
        Locks parliament after decision.
        """
        if self.phase != Phase.VOTING:
            raise RuntimeError("Cannot conclude before voting")

        self.phase = Phase.DECISION
