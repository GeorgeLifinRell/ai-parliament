"""
SQLite-backed session store for parliament sessions.

Persists bills, amendments, debate arguments, votes, and decisions
so that sessions are auditable and replayable.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from parliament.core.bill import Bill, BillStatus
from parliament.core.amendment import Amendment, AmendmentStatus
from parliament.core.debate import DebateArgument
from parliament.core.vote import Vote, VoteChoice
from parliament.core.decision import Decision


_DEFAULT_DB_PATH = Path("parliament_sessions.db")


class SessionStore:
    """
    Persists parliamentary session data to an SQLite database.

    Usage:
        store = SessionStore()
        session_id = store.create_session(bill)
        store.save_debate_argument(session_id, argument)
        store.save_amendment(session_id, amendment)
        store.save_vote(session_id, vote)
        store.save_decision(session_id, decision)
        sessions = store.list_sessions()
    """

    def __init__(self, db_path: str | Path = _DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self._init_db()

    # ---- Initialisation ----

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id   TEXT PRIMARY KEY,
                    bill_id      TEXT NOT NULL,
                    bill_title   TEXT NOT NULL,
                    bill_json    TEXT NOT NULL,
                    created_at   TEXT NOT NULL,
                    concluded_at TEXT
                );

                CREATE TABLE IF NOT EXISTS debate_arguments (
                    id               TEXT PRIMARY KEY,
                    session_id       TEXT NOT NULL REFERENCES sessions(session_id),
                    bill_version     INTEGER NOT NULL,
                    speaker_faction  TEXT NOT NULL,
                    round_number     INTEGER NOT NULL,
                    argument         TEXT NOT NULL,
                    targeted_factions TEXT NOT NULL,
                    recorded_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS amendments (
                    id               TEXT PRIMARY KEY,
                    session_id       TEXT NOT NULL REFERENCES sessions(session_id),
                    bill_version     INTEGER NOT NULL,
                    proposer_faction TEXT NOT NULL,
                    change_summary   TEXT NOT NULL,
                    rationale        TEXT NOT NULL,
                    status           TEXT NOT NULL DEFAULT 'PENDING',
                    recorded_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS votes (
                    id           TEXT PRIMARY KEY,
                    session_id   TEXT NOT NULL REFERENCES sessions(session_id),
                    bill_version INTEGER NOT NULL,
                    faction      TEXT NOT NULL,
                    choice       TEXT NOT NULL,
                    weight       REAL NOT NULL,
                    justification TEXT NOT NULL,
                    recorded_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decisions (
                    id                    TEXT PRIMARY KEY,
                    session_id            TEXT NOT NULL REFERENCES sessions(session_id),
                    bill_version          INTEGER NOT NULL,
                    passed                INTEGER NOT NULL,
                    total_approve_weight  REAL NOT NULL,
                    total_reject_weight   REAL NOT NULL,
                    total_abstain_weight  REAL NOT NULL,
                    vetoed_by             TEXT NOT NULL,
                    coalitions            TEXT NOT NULL,
                    decision_summary      TEXT NOT NULL,
                    decided_at            TEXT NOT NULL
                );
            """)

    # ---- Session management ----

    def create_session(self, bill: Bill) -> str:
        """Create a new session for the given bill and return the session_id."""
        session_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, bill_id, bill_title, bill_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    str(bill.id),
                    bill.title,
                    bill.model_dump_json(),
                    datetime.now().isoformat(),
                ),
            )
        return session_id

    def conclude_session(self, session_id: str) -> None:
        """Mark a session as concluded."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET concluded_at = ? WHERE session_id = ?",
                (datetime.now().isoformat(), session_id),
            )

    def list_sessions(self) -> list[dict]:
        """Return a list of all sessions with basic metadata."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT session_id, bill_title, created_at, concluded_at FROM sessions ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, session_id: str) -> dict | None:
        """Return full session data for a given session_id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return dict(row) if row else None

    # ---- Debate arguments ----

    def save_debate_argument(self, session_id: str, argument: DebateArgument) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO debate_arguments
                    (id, session_id, bill_version, speaker_faction, round_number,
                     argument, targeted_factions, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(argument.id),
                    session_id,
                    argument.bill_version,
                    argument.speaker_faction,
                    argument.round_number,
                    argument.argument,
                    json.dumps(argument.targeted_factions),
                    datetime.now().isoformat(),
                ),
            )

    def get_debate_arguments(self, session_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM debate_arguments WHERE session_id = ? ORDER BY round_number, recorded_at",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---- Amendments ----

    def save_amendment(self, session_id: str, amendment: Amendment) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO amendments
                    (id, session_id, bill_version, proposer_faction,
                     change_summary, rationale, status, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(amendment.id),
                    session_id,
                    amendment.bill_version,
                    amendment.proposer_faction,
                    amendment.change_summary,
                    amendment.rationale,
                    amendment.status.value,
                    datetime.now().isoformat(),
                ),
            )

    def get_amendments(self, session_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM amendments WHERE session_id = ? ORDER BY recorded_at",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---- Votes ----

    def save_vote(self, session_id: str, vote: Vote) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO votes
                    (id, session_id, bill_version, faction, choice,
                     weight, justification, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(vote.id),
                    session_id,
                    vote.bill_version,
                    vote.faction,
                    vote.choice.value,
                    vote.weight,
                    vote.justification,
                    datetime.now().isoformat(),
                ),
            )

    def get_votes(self, session_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM votes WHERE session_id = ? ORDER BY recorded_at",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---- Decisions ----

    def save_decision(self, session_id: str, decision: Decision) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO decisions
                    (id, session_id, bill_version, passed,
                     total_approve_weight, total_reject_weight, total_abstain_weight,
                     vetoed_by, coalitions, decision_summary, decided_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(decision.id),
                    session_id,
                    decision.bill_version,
                    int(decision.passed),
                    decision.total_approve_weight,
                    decision.total_reject_weight,
                    decision.total_abstain_weight,
                    json.dumps(decision.vetoed_by),
                    json.dumps(decision.coalitions),
                    decision.decision_summary,
                    decision.decided_at.isoformat(),
                ),
            )

    def get_decisions(self, session_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE session_id = ? ORDER BY decided_at",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---- Full session export ----

    def export_session(self, session_id: str) -> dict:
        """Return the complete session data as a dictionary."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id!r} not found")
        return {
            "session": session,
            "debate_arguments": self.get_debate_arguments(session_id),
            "amendments": self.get_amendments(session_id),
            "votes": self.get_votes(session_id),
            "decisions": self.get_decisions(session_id),
        }
