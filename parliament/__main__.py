"""
parliament CLI entry-point.

Usage
-----
Run a single bill from a YAML file::

    python -m parliament run --bill bills/ai_teaching_assistant.yaml

Run all bills in a directory::

    python -m parliament run --bills-dir bills/

List all past sessions::

    python -m parliament list-sessions

Export a session audit log::

    python -m parliament replay --session-id <id>
"""

import argparse
import sys
from pathlib import Path


def _build_agents(factions_config: dict) -> list:
    from parliament.agents.efficiency import EfficiencyAgent
    from parliament.agents.safety import SafetyAgent
    from parliament.agents.equity import EquityAgent
    from parliament.agents.innovation import InnovationAgent
    from parliament.agents.compliance import ComplianceAgent

    return [
        EfficiencyAgent(factions_config["Efficiency"]),
        SafetyAgent(factions_config["Safety"]),
        EquityAgent(factions_config["Equity"]),
        InnovationAgent(factions_config["Innovation"]),
        ComplianceAgent(factions_config["Compliance"]),
    ]


def cmd_run(args: argparse.Namespace) -> int:
    import yaml
    from parliament.session.parliament_session import ParliamentSession
    from parliament.storage.session_store import SessionStore
    from parliament.utils.bill_loader import load_bill_from_yaml, load_bills_from_dir

    # Load faction config
    config_path = Path(args.factions_config)
    if not config_path.exists():
        print(f"[ERROR] Factions config not found: {config_path}", file=sys.stderr)
        return 1

    with open(config_path, "r", encoding="utf-8") as fh:
        factions = yaml.safe_load(fh)

    # Load bill(s)
    if args.bill:
        bill_path = Path(args.bill)
        if not bill_path.exists():
            print(f"[ERROR] Bill file not found: {bill_path}", file=sys.stderr)
            return 1
        bills = [load_bill_from_yaml(bill_path)]
    elif args.bills_dir:
        bills_dir = Path(args.bills_dir)
        if not bills_dir.is_dir():
            print(f"[ERROR] Bills directory not found: {bills_dir}", file=sys.stderr)
            return 1
        bills = load_bills_from_dir(bills_dir)
        if not bills:
            print(f"[ERROR] No YAML bills found in {bills_dir}", file=sys.stderr)
            return 1
    else:
        print("[ERROR] Provide --bill <file> or --bills-dir <dir>", file=sys.stderr)
        return 1

    agents = _build_agents(factions)
    db_path = Path(args.db) if args.db else Path("parliament_sessions.db")
    store = SessionStore(db_path=db_path)
    log_dir = Path(args.log_dir) if args.log_dir else Path(".")

    session = ParliamentSession(
        agents=agents,
        store=store,
        max_debate_rounds=args.debate_rounds,
        export_logs=not args.no_logs,
        log_dir=str(log_dir),
    )
    session.run(bills)
    return 0


def cmd_list_sessions(args: argparse.Namespace) -> int:
    from parliament.storage.session_store import SessionStore

    db_path = Path(args.db) if args.db else Path("parliament_sessions.db")
    if not db_path.exists():
        print("No session database found. Run a parliament session first.")
        return 0

    store = SessionStore(db_path=db_path)
    sessions = store.list_sessions()

    if not sessions:
        print("No sessions recorded yet.")
        return 0

    print(f"\n{'Session ID':<38}  {'Bill Title':<40}  {'Created At':<20}  {'Concluded'}")
    print("-" * 110)
    for s in sessions:
        concluded = "✓" if s["concluded_at"] else "…"
        print(f"{s['session_id']:<38}  {s['bill_title']:<40}  {s['created_at'][:19]:<20}  {concluded}")
    print()
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    import json
    from parliament.storage.session_store import SessionStore
    from parliament.storage.audit_log import export_audit_log

    db_path = Path(args.db) if args.db else Path("parliament_sessions.db")
    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}", file=sys.stderr)
        return 1

    store = SessionStore(db_path=db_path)
    log_dir = Path(args.log_dir) if args.log_dir else Path(".")

    log_path = export_audit_log(args.session_id, store=store, output_dir=log_dir)
    print(f"Audit log exported: {log_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parliament",
        description="AI Parliament — constrained multi-agent governance system",
    )
    parser.add_argument(
        "--db",
        metavar="PATH",
        help="Path to the SQLite session database (default: parliament_sessions.db)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- run ----
    run_parser = subparsers.add_parser("run", help="Run a parliament session")
    bill_group = run_parser.add_mutually_exclusive_group()
    bill_group.add_argument("--bill", metavar="PATH", help="Path to a single bill YAML file")
    bill_group.add_argument(
        "--bills-dir", metavar="DIR", help="Directory of bill YAML files to process in order"
    )
    run_parser.add_argument(
        "--factions-config",
        metavar="PATH",
        default="parliament/config/factions.yaml",
        help="Path to factions YAML config (default: parliament/config/factions.yaml)",
    )
    run_parser.add_argument(
        "--debate-rounds",
        metavar="N",
        type=int,
        default=2,
        help="Maximum debate rounds per bill (default: 2)",
    )
    run_parser.add_argument(
        "--no-logs",
        action="store_true",
        help="Disable JSON audit log export",
    )
    run_parser.add_argument(
        "--log-dir",
        metavar="DIR",
        help="Directory for audit log files (default: current directory)",
    )

    # ---- list-sessions ----
    subparsers.add_parser("list-sessions", help="List all recorded parliament sessions")

    # ---- replay ----
    replay_parser = subparsers.add_parser(
        "replay", help="Export a session audit log by session ID"
    )
    replay_parser.add_argument(
        "--session-id", required=True, metavar="ID", help="Session ID to export"
    )
    replay_parser.add_argument(
        "--log-dir",
        metavar="DIR",
        help="Directory for the exported log file (default: current directory)",
    )

    parsed = parser.parse_args(argv)

    if parsed.command == "run":
        return cmd_run(parsed)
    elif parsed.command == "list-sessions":
        return cmd_list_sessions(parsed)
    elif parsed.command == "replay":
        return cmd_replay(parsed)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
