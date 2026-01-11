from enum import Enum
from parliament.core.bill import Bill, BillStatus
from parliament.llm.client import LLMClient
from parliament.llm.speaker_schemas import DebateOrderSchema, VetoPowerSchema


# ANSI color codes for Speaker messages
SPEAKER_COLOR = '\033[97m'  # Bright white
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'


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
    Now backed by LLM for strategic decisions while maintaining procedural authority.
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
        self.veto_factions: set[str] = set()
        self.llm = LLMClient()

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
        Can be called manually or use determine_debate_order() for LLM-based decision.
        """
        if self.phase != Phase.DEBATE:
            raise RuntimeError("Can only set debate order during DEBATE phase")
        
        self.debate_order = factions.copy()

    def determine_debate_order(self, faction_names: list[str], faction_statements: dict[str, str]) -> list[str]:
        """
        LLM-powered strategic determination of debate speaking order.
        
        Args:
            faction_names: List of all faction names
            faction_statements: Dict of faction -> their initial statement
            
        Returns:
            Ordered list of faction names for debate
        """
        try:
            system = """
You are the Parliamentary Speaker with authority to determine debate order.

Your role is PROCEDURAL and STRATEGIC:
- You maintain order and fairness
- You determine speaking order to maximize productive debate
- You consider faction positions to arrange strategic discussion flow
- You have NO policy opinion, only procedural judgment

Consider:
- Which factions should speak early to frame the debate?
- Which opposing views should be adjacent for direct engagement?
- Which factions might build on each other's arguments?
"""

            faction_positions = "\n".join([
                f"- {name}: {stmt}" 
                for name, stmt in faction_statements.items()
            ])

            user = f"""
Bill: {self.bill.title}
Proposal: {self.bill.proposal}

Faction Statements:
{faction_positions}

Available factions: {faction_names}

Determine the optimal speaking order for debate to maximize productive discussion.

Return JSON:
{{
  "faction_order": ["Faction1", "Faction2", ...],
  "reasoning": "brief explanation of speaking order strategy"
}}
"""

            raw = self.llm.generate_json(system, user)
            parsed = DebateOrderSchema(**raw)
            
            # Validate all factions are included
            if set(parsed.faction_order) != set(faction_names):
                print(f"{DIM}[Speaker] LLM provided invalid faction order, using default{RESET}")
                return faction_names
            
            print(f"{SPEAKER_COLOR}{BOLD}[Speaker]{RESET} {DIM}Debate order reasoning: {parsed.reasoning}{RESET}")
            return parsed.faction_order
            
        except Exception as e:
            print(f"{DIM}[Speaker] LLM failed to determine debate order, using default: {e}{RESET}")
            return faction_names

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

    def assign_veto_power(self, faction: str):
        """
        Grants veto power to a specific faction for this bill.
        Speaker has authority to determine which factions receive veto power.
        Can be called manually or use determine_veto_powers() for LLM-based decision.
        
        Args:
            faction: The name of the faction to grant veto power
        """
        self.veto_factions.add(faction)

    def revoke_veto_power(self, faction: str):
        """
        Revokes veto power from a specific faction.
        
        Args:
            faction: The name of the faction to revoke veto power from
        """
        self.veto_factions.discard(faction)

    def get_veto_factions(self) -> set[str]:
        """
        Returns the set of factions with veto power for this bill.
        """
        return self.veto_factions.copy()

    def determine_veto_powers(self, faction_names: list[str], faction_ideologies: dict[str, dict]) -> set[str]:
        """
        LLM-powered strategic determination of which factions should have veto power.
        
        Args:
            faction_names: List of all faction names
            faction_ideologies: Dict of faction -> ideology (goal, priorities, red_lines)
            
        Returns:
            Set of faction names that should have veto power
        """
        try:
            system = """
You are the Parliamentary Speaker with authority to assign veto powers.

Your role is PROCEDURAL and PROTECTIVE:
- You determine which factions are FIT to hold veto power
- Veto power should protect against catastrophic outcomes
- Consider the bill's risks and which factions are best positioned to prevent harm
- You have NO policy preference, only institutional judgment

Consider:
- What are the serious risks in this bill?
- Which factions have red lines that align with preventing catastrophic outcomes?
- Which factions have the expertise/focus to recognize critical flaws?
- Veto power is SERIOUS - grant it only when needed for institutional protection
"""

            faction_info = "\n".join([
                f"- {name}:\n  Goal: {ideology['goal']}\n  Red lines: {ideology['red_lines']}"
                for name, ideology in faction_ideologies.items()
            ])

            user = f"""
Bill: {self.bill.title}
Proposal: {self.bill.proposal}

Known Risks: {self.bill.known_risks}
Unknowns: {self.bill.unknowns}

Available Factions:
{faction_info}

Determine which factions (if any) should have veto power to protect against catastrophic outcomes.

Return JSON:
{{
  "factions_with_veto": ["Faction1", "Faction2"] or [],
  "reasoning": "brief explanation of veto power assignments"
}}
"""

            raw = self.llm.generate_json(system, user)
            parsed = VetoPowerSchema(**raw)
            
            # Validate factions exist
            invalid = set(parsed.factions_with_veto) - set(faction_names)
            if invalid:
                print(f"{DIM}[Speaker] LLM suggested invalid factions for veto: {invalid}, ignoring{RESET}")
                valid_vetos = set(parsed.factions_with_veto) - invalid
            else:
                valid_vetos = set(parsed.factions_with_veto)
            
            print(f"{SPEAKER_COLOR}{BOLD}[Speaker]{RESET} {DIM}Veto power reasoning: {parsed.reasoning}{RESET}")
            
            # Apply veto assignments
            for faction in valid_vetos:
                self.assign_veto_power(faction)
            
            return valid_vetos
            
        except Exception as e:
            print(f"{DIM}[Speaker] LLM failed to determine veto powers, assigning none: {e}{RESET}")
            return set()
