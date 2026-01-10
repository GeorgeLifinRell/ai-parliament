from enum import Enum
from parliament.core.bill import Bill, BillStatus


class Phase(str, Enum):
    INTRODUCTION = "INTRODUCTION"
    FACTION_STATEMENTS = "FACTION_STATEMENTS"
    DEBATE = "DEBATE"
    AMENDMENTS = "AMENDMENTS"
    VOTING = "VOTING"
    DECISION = "DECISION"


class Speaker:
    """
    The Speaker enforces parliamentary procedure.
    It has authority but no opinion.
    """

    def __init__(self, bill: Bill, max_debate_rounds: int = 2, max_rounds: int = 3):
        if bill.status != BillStatus.DRAFT:
            raise ValueError("Only draft bills may enter parliament")

        self.bill = bill
        self.phase = Phase.INTRODUCTION
        self.round = 0
        self.max_rounds = max_rounds
        self.max_debate_rounds = max_debate_rounds
        self.debate_round = 0
        self.debate_order: list[str] = []

    # ---- Phase control ----

    def allow_action(self, action: str) -> bool:
        """
        Validates whether an action is allowed in the current phase.
        """
        allowed = {
            Phase.INTRODUCTION: {"introduce"},
            Phase.FACTION_STATEMENTS: {"statement"},
            Phase.DEBATE: {"debate"},
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

    def set_debate_order(self, factions: list[str]):
        """
        Establishes speaking order for debate.
        Speaker has authority to determine turn order.
        """
        if self.phase != Phase.DEBATE:
            raise RuntimeError("Can only set debate order during DEBATE phase")
        
        self.debate_order = factions.copy()

    def next_debate_round(self) -> bool:
        """
        Advances to the next debate round.
        Returns True if debate continues, False if debate should end.
        """
        if self.phase != Phase.DEBATE:
            raise RuntimeError("Can only advance debate rounds during DEBATE phase")
        
        self.debate_round += 1
        
        if self.debate_round >= self.max_debate_rounds:
            return False
        
        return True
