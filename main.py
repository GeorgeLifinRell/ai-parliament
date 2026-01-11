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

from parliament.utils.colors import (
    header, faction_colored, vote_colored, decision_colored,
    colored, Colors
)


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
    print(header("🏛️  AI PARLIAMENT SIMULATION  🏛️", style="main"))

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

    print(colored("📜 Bill on the Floor:", Colors.BRIGHT_WHITE, bold=True))
    print(colored(f"   {bill.title}", Colors.BRIGHT_CYAN, bold=True))
    print(colored("─" * 60, Colors.DIM))

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
    # Speaker determines veto power (LLM-backed)
    # -------------------------
    print(header("⚖️  SPEAKER AUTHORITY (LLM-Backed)", style="section"))
    
    # Build ideology dict for Speaker's decision
    faction_ideologies = {agent.name: agent.ideology for agent in agents}
    faction_names = [agent.name for agent in agents]
    
    veto_factions = speaker.determine_veto_powers(faction_names, faction_ideologies)
    if veto_factions:
        veto_display = ', '.join([faction_colored(f, f, bold=True) for f in veto_factions])
        print(f"🔨 Speaker grants veto power to: {veto_display}\n")
    else:
        print(colored("🔨 Speaker grants veto power to: None", Colors.DIM) + "\n")

    # -------------------------
    # Phase: Statements
    # -------------------------
    print(header("💬 FACTION STATEMENTS", style="section"))
    
    speaker.advance_phase()  # Move to FACTION_STATEMENTS

    statements = {}
    for agent in agents:
        stmt = agent.statement(bill)
        statements[agent.name] = stmt
        faction_name = faction_colored(agent.name, f"[{agent.name}]", bold=True)
        print(f"{faction_name} {stmt}\n")

    # -------------------------
    # Phase: Debate (Speaker-mediated persuasion)
    # -------------------------
    print(header("🗣️  DEBATE PHASE", style="section"))
    
    speaker.advance_phase()  # Move to DEBATE
    
    # Speaker strategically determines debate order (LLM-backed)
    faction_names = [agent.name for agent in agents]
    debate_order = speaker.determine_debate_order(faction_names, statements)
    speaker.set_debate_order(debate_order)
    
    all_debate_arguments = []
    
    for debate_round in range(1, speaker.max_debate_rounds + 1):
        print(header(f"Debate Round {debate_round}", style="subsection"))
        
        order_display = ' → '.join([faction_colored(f, f, bold=True) for f in speaker.debate_order])
        print(colored("Speaker mediates turn order: ", Colors.BRIGHT_WHITE) + order_display + "\n")
        
        round_arguments = []
        
        # Each faction speaks in order determined by Speaker
        for faction_name in speaker.debate_order:
            agent = next(a for a in agents if a.name == faction_name)
            
            argument = agent.debate(
                bill=bill,
                round_number=debate_round,
                all_factions=faction_names,
                previous_arguments=all_debate_arguments
            )
            
            if argument:
                round_arguments.append(argument)
                all_debate_arguments.append(argument)
                
                speaker_label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
                
                if argument.targeted_factions:
                    targets = ', '.join([faction_colored(t, t) for t in argument.targeted_factions])
                    target_msg = colored(" → ", Colors.DIM) + f"[{targets}]"
                else:
                    target_msg = colored(" → ", Colors.DIM) + colored("[All Factions]", Colors.WHITE)
                
                print(f"{speaker_label}{target_msg}")
                print(colored(f"  {argument.argument}", Colors.WHITE) + "\n")
            else:
                speaker_label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
                print(speaker_label + colored(" passes this round.", Colors.DIM) + "\n")
        
        # Check if we should continue debate
        if debate_round < speaker.max_debate_rounds:
            if not speaker.next_debate_round():
                break

    # -------------------------
    # Phase: Amendments
    # -------------------------
    print(header("✏️  AMENDMENTS", style="section"))
    
    speaker.advance_phase()  # Move to AMENDMENTS

    all_amendments = []

    for agent in agents:
        amendments = agent.propose_amendments(bill)
        faction_label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
        
        if amendments:
            for a in amendments:
                print(f"{faction_label} {colored('proposes:', Colors.BRIGHT_WHITE)}")
                print(colored(f"  • {a.change_summary}", Colors.CYAN))
                print(colored(f"    Reason: {a.rationale}", Colors.DIM) + "\n")
                all_amendments.append(a)
        else:
            print(f"{faction_label} {colored('proposes no amendments.', Colors.DIM)}\n")

    # -------------------------
    # Phase: Voting
    # -------------------------
    print(header("🗳️  VOTING", style="section"))
    
    speaker.advance_phase()  # Move to VOTING

    votes = []
    for agent in agents:
        vote = agent.vote(bill, all_amendments)
        votes.append(vote)

        faction_label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
        vote_display = vote_colored(vote.choice.value)
        print(f"{faction_label} votes: {vote_display}")
        print(colored(f"  Justification: {vote.justification}", Colors.DIM) + "\n")

    # -------------------------
    # Final Decision
    # -------------------------
    print(header("⚖️  FINAL DECISION", style="section"))

    # Use Speaker's veto assignments
    engine = VotingEngine(veto_factions=speaker.get_veto_factions())
    decision = engine.evaluate(bill, votes)

    print(colored("Bill Status: ", Colors.BRIGHT_WHITE, bold=True) + decision_colored(decision.passed))
    print(colored(f"Approve Weight: ", Colors.GREEN) + colored(str(decision.total_approve_weight), Colors.BRIGHT_GREEN, bold=True))
    print(colored(f"Reject Weight: ", Colors.RED) + colored(str(decision.total_reject_weight), Colors.BRIGHT_RED, bold=True))
    print(colored(f"Abstain Weight: ", Colors.YELLOW) + colored(str(decision.total_abstain_weight), Colors.BRIGHT_YELLOW, bold=True))
    print(colored(f"\n{decision.decision_summary}", Colors.BRIGHT_WHITE))

    if decision.vetoed_by:
        veto_display = ', '.join([faction_colored(f, f, bold=True) for f in decision.vetoed_by])
        print(colored(f"\n🚫 Vetoed By: ", Colors.BRIGHT_RED, bold=True) + veto_display)

    print(header("SESSION CONCLUDED", style="main"))


if __name__ == "__main__":
    run_parliament_simulation()
