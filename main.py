from uuid import uuid4
import yaml

from parliament.core.bill import Bill, BillStatus
from parliament.procedure.speaker import Speaker
from parliament.engine.voting import VotingEngine

from parliament.agents.efficiency import EfficiencyAgent
from parliament.agents.safety import SafetyAgent
from parliament.agents.equity import EquityAgent
from parliament.agents.innovation import InnovationAgent
from parliament.agents.compliance import ComplianceAgent


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
    print("\n=== AI PARLIAMENT SIMULATION ===\n")

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

    print(f"Bill: {bill.title}")
    print("-" * 60)

    # Agents
    agents = [
        EfficiencyAgent(factions["Efficiency"]),
        SafetyAgent(factions["Safety"]),
        EquityAgent(factions["Equity"]),
        InnovationAgent(factions["Innovation"]),
        ComplianceAgent(factions["Compliance"]),
    ]

    speaker = Speaker(bill)

    # -------------------------
    # Phase: Statements
    # -------------------------
    print("\n--- FACTION STATEMENTS ---\n")

    statements = {}
    for agent in agents:
        stmt = agent.statement(bill)
        statements[agent.name] = stmt
        print(f"[{agent.name}] {stmt}")

    # -------------------------
    # Phase: Amendments
    # -------------------------
    print("\n--- AMENDMENTS ---\n")

    all_amendments = []

    for agent in agents:
        amendments = agent.propose_amendments(bill)
        if amendments:
            for a in amendments:
                print(f"[{agent.name}] proposes:")
                print(f"  - {a.change_summary}")
                print(f"    Reason: {a.rationale}")
                all_amendments.append(a)
        else:
            print(f"[{agent.name}] proposes no amendments.")

    # -------------------------
    # Phase: Voting
    # -------------------------
    print("\n--- VOTING ---\n")

    votes = []
    for agent in agents:
        vote = agent.vote(bill, all_amendments)
        votes.append(vote)

        print(f"[{agent.name}] votes: {vote.choice}")
        print(f"  Justification: {vote.justification}")

    # -------------------------
    # Final Decision
    # -------------------------
    print("\n--- FINAL DECISION ---\n")

    engine = VotingEngine(veto_factions={"Safety", "Compliance"})
    decision = engine.evaluate(bill, votes)

    print(f"Bill Passed: {decision.passed}")
    print(f"Approve Weight: {decision.total_approve_weight}")
    print(f"Reject Weight: {decision.total_reject_weight}")
    print(f"Abstain Weight: {decision.total_abstain_weight}")
    print(f"Summary: {decision.decision_summary}")

    if decision.vetoed_by:
        print(f"Vetoed By: {decision.vetoed_by}")

    print("\n=== END OF SESSION ===\n")


if __name__ == "__main__":
    run_parliament_simulation()
