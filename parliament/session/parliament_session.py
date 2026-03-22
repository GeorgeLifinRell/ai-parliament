"""
ParliamentSession — multi-bill orchestrator with precedent-aware agents.

Runs a list of bills through the full parliamentary procedure sequentially.
After each bill, the decision is stored as a precedent so later bills
benefit from institutional memory.
"""

from parliament.agents.base import BaseFactionAgent
from parliament.core.bill import Bill, BillStatus
from parliament.core.decision import Decision
from parliament.engine.amendments import accept_amendment, apply_accepted_amendments
from parliament.engine.voting import VotingEngine
from parliament.procedure.speaker import Speaker
from parliament.storage.precedent_store import PrecedentStore
from parliament.storage.session_store import SessionStore
from parliament.storage.audit_log import export_audit_log
from parliament.utils.colors import (
    header, faction_colored, vote_colored, decision_colored,
    colored, Colors,
)


class ParliamentSession:
    """
    Runs one or more bills through the full parliamentary procedure.

    Features
    --------
    - Sequential bill processing with precedent injection.
    - Persists every session event to a SessionStore (SQLite by default).
    - Exports a JSON audit log after each bill.
    - Prints coloured terminal output.

    Usage
    -----
    ::

        session = ParliamentSession(agents=agents, store=SessionStore())
        results = session.run([bill1, bill2])
    """

    def __init__(
        self,
        agents: list[BaseFactionAgent],
        store: SessionStore | None = None,
        precedent_store: PrecedentStore | None = None,
        max_debate_rounds: int = 2,
        export_logs: bool = True,
        log_dir: str = ".",
        speaker_llm=None,
    ):
        self.agents = agents
        self.store = store if store is not None else SessionStore()
        self.precedent_store = precedent_store if precedent_store is not None else PrecedentStore()
        self.max_debate_rounds = max_debate_rounds
        self.export_logs = export_logs
        self.log_dir = log_dir
        self._speaker_llm = speaker_llm  # Optional injectable LLM for Speaker (useful in tests)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(self, bills: list[Bill]) -> list[Decision]:
        """
        Process a list of bills in order and return their decisions.
        """
        decisions: list[Decision] = []
        for bill in bills:
            decision = self._run_bill(bill)
            decisions.append(decision)
        return decisions

    # ------------------------------------------------------------------ #
    # Internal orchestration
    # ------------------------------------------------------------------ #

    def _run_bill(self, bill: Bill) -> Decision:
        print(header(f"🏛️  AI PARLIAMENT — {bill.title}  🏛️", style="main"))
        print(colored("📜 Bill on the Floor:", Colors.BRIGHT_WHITE, bold=True))
        print(colored(f"   {bill.title}", Colors.BRIGHT_CYAN, bold=True))
        print(colored("─" * 60, Colors.DIM))

        session_id = self.store.create_session(bill)
        precedent_context = self.precedent_store.get_precedent_context()

        faction_names = [a.name for a in self.agents]
        faction_ideologies = {a.name: a.ideology for a in self.agents}

        speaker = Speaker(bill, max_debate_rounds=self.max_debate_rounds, llm=self._speaker_llm)

        # ---- Veto determination ----
        print(header("⚖️  SPEAKER AUTHORITY (LLM-Backed)", style="section"))
        veto_factions = speaker.determine_veto_powers(faction_names, faction_ideologies)
        if veto_factions:
            veto_display = ", ".join([faction_colored(f, f, bold=True) for f in veto_factions])
            print(f"🔨 Speaker grants veto power to: {veto_display}\n")
        else:
            print(colored("🔨 Speaker grants veto power to: None", Colors.DIM) + "\n")

        # ---- Phase: Statements ----
        print(header("💬 FACTION STATEMENTS", style="section"))
        speaker.advance_phase()

        statements: dict[str, str] = {}
        for agent in self.agents:
            stmt = agent.statement(bill, precedent_context=precedent_context)
            statements[agent.name] = stmt
            label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
            print(f"{label} {stmt}\n")

        # ---- Phase: Debate ----
        print(header("🗣️  DEBATE PHASE", style="section"))
        speaker.advance_phase()

        debate_order = speaker.determine_debate_order(faction_names, statements)
        speaker.set_debate_order(debate_order)

        all_debate_arguments = []

        for debate_round in range(1, self.max_debate_rounds + 1):
            print(header(f"Debate Round {debate_round}", style="subsection"))
            order_display = " → ".join([faction_colored(f, f, bold=True) for f in speaker.debate_order])
            print(colored("Speaker mediates turn order: ", Colors.BRIGHT_WHITE) + order_display + "\n")

            for faction_name in speaker.debate_order:
                agent = next(a for a in self.agents if a.name == faction_name)
                argument = agent.debate(
                    bill=bill,
                    round_number=debate_round,
                    all_factions=faction_names,
                    previous_arguments=all_debate_arguments,
                    precedent_context=precedent_context,
                )

                if argument:
                    all_debate_arguments.append(argument)
                    self.store.save_debate_argument(session_id, argument)

                    label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
                    if argument.targeted_factions:
                        targets = ", ".join([faction_colored(t, t) for t in argument.targeted_factions])
                        target_msg = colored(" → ", Colors.DIM) + f"[{targets}]"
                    else:
                        target_msg = colored(" → ", Colors.DIM) + colored("[All Factions]", Colors.WHITE)
                    print(f"{label}{target_msg}")
                    print(colored(f"  {argument.argument}", Colors.WHITE) + "\n")
                else:
                    label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
                    print(label + colored(" passes this round.", Colors.DIM) + "\n")

            if debate_round < self.max_debate_rounds:
                if not speaker.next_debate_round():
                    break

        # ---- Phase: Amendments ----
        print(header("✏️  AMENDMENTS", style="section"))
        speaker.advance_phase()

        all_amendments = []
        for agent in self.agents:
            amendments = agent.propose_amendments(bill, precedent_context=precedent_context)
            label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
            if amendments:
                for a in amendments:
                    print(f"{label} {colored('proposes:', Colors.BRIGHT_WHITE)}")
                    print(colored(f"  • {a.change_summary}", Colors.CYAN))
                    print(colored(f"    Reason: {a.rationale}", Colors.DIM) + "\n")
                    all_amendments.append(a)
                    self.store.save_amendment(session_id, a)
            else:
                print(f"{label} {colored('proposes no amendments.', Colors.DIM)}\n")

        # Accept all amendments for demonstration (Speaker accepts all)
        accepted_amendments = [accept_amendment(a) for a in all_amendments]
        for a in accepted_amendments:
            self.store.save_amendment(session_id, a)

        # Apply accepted amendments to the bill
        current_bill, applied = apply_accepted_amendments(
            bill, accepted_amendments
        )
        if applied:
            print(
                colored(
                    f"\n📝 {len(applied)} amendment(s) applied — bill version bumped to v{current_bill.version}",
                    Colors.BRIGHT_CYAN,
                )
            )

        # ---- Phase: Voting ----
        print(header("🗳️  VOTING", style="section"))
        speaker.advance_phase()

        votes = []
        for agent in self.agents:
            vote = agent.vote(current_bill, accepted_amendments, precedent_context=precedent_context)
            votes.append(vote)
            self.store.save_vote(session_id, vote)

            label = faction_colored(agent.name, f"[{agent.name}]", bold=True)
            vote_display = vote_colored(vote.choice.value)
            print(f"{label} votes: {vote_display}")
            print(colored(f"  Justification: {vote.justification}", Colors.DIM) + "\n")

        # ---- Final Decision ----
        print(header("⚖️  FINAL DECISION", style="section"))
        engine = VotingEngine(veto_factions=speaker.get_veto_factions())
        decision = engine.evaluate(current_bill, votes)

        self.store.save_decision(session_id, decision)
        self.store.conclude_session(session_id)

        # Update precedent store
        self.precedent_store.record(current_bill.proposal, decision)

        # Print decision
        print(colored("Bill Status: ", Colors.BRIGHT_WHITE, bold=True) + decision_colored(decision.passed))
        print(colored("Approve Weight: ", Colors.GREEN) + colored(str(decision.total_approve_weight), Colors.BRIGHT_GREEN, bold=True))
        print(colored("Reject Weight:  ", Colors.RED) + colored(str(decision.total_reject_weight), Colors.BRIGHT_RED, bold=True))
        print(colored("Abstain Weight: ", Colors.YELLOW) + colored(str(decision.total_abstain_weight), Colors.BRIGHT_YELLOW, bold=True))
        print(colored(f"\n{decision.decision_summary}", Colors.BRIGHT_WHITE))

        if decision.vetoed_by:
            veto_display = ", ".join([faction_colored(f, f, bold=True) for f in decision.vetoed_by])
            print(colored("\n🚫 Vetoed By: ", Colors.BRIGHT_RED, bold=True) + veto_display)

        if decision.coalitions:
            print(colored("\n🤝 Coalitions:", Colors.BRIGHT_WHITE, bold=True))
            for choice, factions in decision.coalitions.items():
                color = Colors.BRIGHT_GREEN if choice == "APPROVE" else (Colors.BRIGHT_RED if choice == "REJECT" else Colors.BRIGHT_YELLOW)
                factions_str = ", ".join([faction_colored(f, f) for f in factions])
                print(colored(f"  {choice}: ", color, bold=True) + factions_str)

        # Export audit log
        if self.export_logs:
            try:
                log_path = export_audit_log(session_id, self.store, output_dir=self.log_dir)
                print(colored(f"\n📋 Audit log written to: {log_path}", Colors.DIM))
            except Exception as exc:
                print(colored(f"\n⚠️  Audit log export failed: {exc}", Colors.BRIGHT_YELLOW))

        print(header("SESSION CONCLUDED", style="main"))
        return decision
