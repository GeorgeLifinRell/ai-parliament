from uuid import uuid4
from parliament.agents.base import BaseFactionAgent
from parliament.llm.client import LLMClient
from parliament.llm.schemas import StatementSchema, AmendmentSchema, VoteSchema
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
