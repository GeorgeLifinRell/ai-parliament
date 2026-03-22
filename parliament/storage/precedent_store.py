"""
Parliament precedent store.

Stores decision summaries so that faction agents can reason about
past parliamentary outcomes when debating and voting on new bills.
"""

from dataclasses import dataclass, field
from datetime import datetime

from parliament.core.decision import Decision


@dataclass
class PrecedentEntry:
    """A condensed record of a past parliamentary decision."""

    bill_title: str
    bill_proposal_snippet: str  # First 200 chars of proposal
    passed: bool
    decision_summary: str
    approve_coalition: list[str]
    reject_coalition: list[str]
    abstain_coalition: list[str]
    vetoed_by: list[str]
    decided_at: str

    def to_context_string(self) -> str:
        """Format as a readable paragraph for injection into LLM prompts."""
        outcome = "PASSED" if self.passed else "REJECTED"
        lines = [
            f'Past bill: "{self.bill_title}" — {outcome} on {self.decided_at[:10]}.',
            f"  Proposal: {self.bill_proposal_snippet}",
            f"  Summary: {self.decision_summary}",
        ]
        if self.approve_coalition:
            lines.append(f"  Approved by: {', '.join(self.approve_coalition)}")
        if self.reject_coalition:
            lines.append(f"  Rejected by: {', '.join(self.reject_coalition)}")
        if self.abstain_coalition:
            lines.append(f"  Abstained: {', '.join(self.abstain_coalition)}")
        if self.vetoed_by:
            lines.append(f"  Vetoed by: {', '.join(self.vetoed_by)}")
        return "\n".join(lines)


class PrecedentStore:
    """
    In-memory store of past parliamentary decisions used as precedent context.

    After each session, call ``record(bill_proposal, decision)`` to log the outcome.
    Use ``get_precedent_context()`` to retrieve a formatted string ready for
    injection into agent LLM prompts.
    """

    def __init__(self, max_entries: int = 20):
        self._entries: list[PrecedentEntry] = []
        self.max_entries = max_entries

    def record(self, bill_proposal: str, decision: Decision) -> None:
        """Record a completed decision as a precedent entry."""
        snippet = bill_proposal.strip()[:200]
        if len(bill_proposal.strip()) > 200:
            snippet += "…"

        entry = PrecedentEntry(
            bill_title=decision.bill_title,
            bill_proposal_snippet=snippet,
            passed=decision.passed,
            decision_summary=decision.decision_summary,
            approve_coalition=decision.coalitions.get("APPROVE", []),
            reject_coalition=decision.coalitions.get("REJECT", []),
            abstain_coalition=decision.coalitions.get("ABSTAIN", []),
            vetoed_by=list(decision.vetoed_by),
            decided_at=decision.decided_at.isoformat(),
        )

        self._entries.append(entry)

        # Trim to max_entries (keep most recent)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]

    def get_precedent_context(self, max_recent: int = 5) -> str:
        """
        Return a formatted string of recent precedent entries for LLM injection.

        Returns an empty string if no precedents are recorded.
        """
        if not self._entries:
            return ""

        recent = self._entries[-max_recent:]
        lines = ["=== Parliamentary Precedents (most recent first) ==="]
        for entry in reversed(recent):
            lines.append(entry.to_context_string())
            lines.append("")
        return "\n".join(lines).strip()

    def __len__(self) -> int:
        return len(self._entries)
