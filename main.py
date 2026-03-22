"""
main.py — backward-compatible entry point.

Delegates to the ParliamentSession orchestrator which now handles:
  - Amendment lifecycle (accepted amendments applied before voting)
  - Session persistence (SQLite audit trail)
  - JSON audit log export
  - Precedent-aware faction agents
  - Coalition tracking in the final decision
"""

from uuid import uuid4
import yaml

from parliament.core.bill import Bill, BillStatus

from parliament.agents.efficiency import EfficiencyAgent
from parliament.agents.safety import SafetyAgent
from parliament.agents.equity import EquityAgent
from parliament.agents.innovation import InnovationAgent
from parliament.agents.compliance import ComplianceAgent

from parliament.session.parliament_session import ParliamentSession
from parliament.storage.session_store import SessionStore


# -------------------------
# Load faction ideologies
# -------------------------

def load_factions():
    with open("parliament/config/factions.yaml", "r") as f:
        return yaml.safe_load(f)


# -------------------------
# Simulation runner
# -------------------------

def run_parliament_simulation():
    factions = load_factions()

    # Example bill
    bill = Bill(
        id=uuid4(),
        title="Deploy AI Teaching Assistant for University",
        proposal="""
Deploy a Gemini-based AI assistant for all students to:
- Answer academic questions 24/7
- Help with assignments
- Provide study guidance
""",
        assumptions=[
            "Students will not overly depend on the system",
            "AI answers will be mostly accurate"
        ],
        intended_outcomes=[
            "Reduce load on professors",
            "Improve learning access",
            "Provide 24/7 support"
        ],
        known_risks=[
            "Hallucinated answers",
            "Academic integrity issues"
        ],
        unknowns=[
            "Long-term student dependency",
            "Equity of access"
        ],
        status=BillStatus.DRAFT
    )

    # Agents
    agents = [
        EfficiencyAgent(factions["Efficiency"]),
        SafetyAgent(factions["Safety"]),
        EquityAgent(factions["Equity"]),
        InnovationAgent(factions["Innovation"]),
        ComplianceAgent(factions["Compliance"]),
    ]

    store = SessionStore()
    session = ParliamentSession(agents=agents, store=store)
    session.run([bill])


if __name__ == "__main__":
    run_parliament_simulation()

