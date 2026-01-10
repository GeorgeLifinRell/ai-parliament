from uuid import uuid4
from parliament.agents.base import BaseFactionAgent
from parliament.llm.client import LLMClient
from parliament.llm.schemas import StatementSchema, DebateSchema, AmendmentSchema, VoteSchema
from parliament.core.debate import DebateArgument
from parliament.core.amendment import Amendment
from parliament.core.vote import Vote, VoteChoice


class LLMFactionAgent(BaseFactionAgent):
    def __init__(self, name: str, ideology: dict, weight: float):
        super().__init__(name, ideology)
        self.llm = LLMClient()
        self.weight = weight

    def statement(self, bill):
        try:
            system = f"You represent the {self.name} faction. Goal: {self.ideology['goal']}"
            user = f"""
Bill:
{bill.proposal}

Return JSON:
{{ "summary": "short position statement" }}
"""

            raw = self.llm.generate_json(system, user)
            return StatementSchema(**raw).summary
        except Exception as e:
            return f"[{self.name}] Unable to generate structured statement due to LLM failure."

    def debate(self, bill, round_number: int, all_factions: list[str], previous_arguments: list = None):
        """
        Generate a debate argument to persuade other factions.
        
        Args:
            bill: The bill being debated
            round_number: Current debate round
            all_factions: List of all faction names in parliament
            previous_arguments: List of DebateArgument from previous rounds
        
        Returns:
            DebateArgument or None if LLM fails
        """
        try:
            other_factions = [f for f in all_factions if f != self.name]
            
            system = f"""
You are the {self.name} faction in a parliamentary debate.

Goal: {self.ideology['goal']}
Priorities: {self.ideology['priorities']}
Red lines: {self.ideology['red_lines']}

Your task is to persuade other factions to support (or reject) this bill based on your ideology.
Make compelling arguments that appeal to other factions' concerns.
"""

            previous_context = ""
            if previous_arguments and round_number > 1:
                previous_context = "\n\nPrevious debate arguments:\n"
                for arg in previous_arguments:
                    previous_context += f"[{arg.speaker_faction}]: {arg.argument}\n"

            user = f"""
Bill:
{bill.proposal}
{previous_context}

Round {round_number}: Make a persuasive argument.

You can target specific factions or address everyone.
Available factions to convince: {other_factions}

Return JSON:
{{
  "argument": "your persuasive argument (2-3 sentences)",
  "targeted_factions": ["Faction1", "Faction2"] or [] for everyone
}}

Be strategic and persuasive based on your faction's ideology.
"""

            raw = self.llm.generate_json(system, user)
            parsed = DebateSchema(**raw)
            
            return DebateArgument(
                id=uuid4(),
                bill_id=bill.id,
                bill_version=bill.version,
                speaker_faction=self.name,
                round_number=round_number,
                argument=parsed.argument,
                targeted_factions=parsed.targeted_factions
            )
            
        except Exception as e:
            # Graceful degradation - faction passes on this debate round
            return None

    def propose_amendments(self, bill):
        try:
            system = f"You represent the {self.name} faction."
            user = f"""
Bill:
{bill.proposal}

If changes are needed, return JSON list:
[
  {{ "change_summary": "...", "rationale": "..." }}
]

If no amendments needed, return [].
"""

            raw = self.llm.generate_json(system, user)

            amendments = []
            for item in raw:
                parsed = AmendmentSchema(**item)
                amendments.append(
                    Amendment(
                        id=uuid4(),
                        bill_id=bill.id,
                        bill_version=bill.version,
                        proposer_faction=self.name,
                        change_summary=parsed.change_summary,
                        rationale=parsed.rationale
                    )
                )

            return amendments
        except Exception as e:
            return []

    def vote(self, bill, amendments):
        try:
            system = f"""
You are the {self.name} faction.

Goal: {self.ideology['goal']}
Priorities: {self.ideology['priorities']}
Red lines: {self.ideology['red_lines']}

You must vote strictly according to your faction's ideology.
"""

            user = f"""
Bill:
{bill.proposal}

Amendments proposed:
{[a.change_summary for a in amendments]}

You must return ONLY valid JSON matching this exact schema:

{{
  "choice": "APPROVE" | "REJECT" | "ABSTAIN",
  "justification": string
}}

Rules:
- choice MUST be one of: APPROVE, REJECT, ABSTAIN (uppercase)
- No extra fields
- No markdown
- No explanation outside JSON
"""

            raw = self.llm.generate_json(system, user)
            parsed = VoteSchema(**raw)

            return Vote(
                id=uuid4(),
                bill_id=bill.id,
                bill_version=bill.version,
                faction=self.name,
                choice=VoteChoice(parsed.choice),
                weight=self.weight,
                justification=parsed.justification
            )

        except Exception as e:
            return Vote(
                id=uuid4(),
                bill_id=bill.id,
                bill_version=bill.version,
                faction=self.name,
                choice=VoteChoice.ABSTAIN,
                weight=self.weight,
                justification=f"LLM failure prevented informed decision: {e}"
            )
