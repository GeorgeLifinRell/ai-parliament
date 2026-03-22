"""
JSON audit log export for parliamentary sessions.

Writes a human-readable audit record for any completed session.
"""

import json
from datetime import datetime
from pathlib import Path

from parliament.storage.session_store import SessionStore


def export_audit_log(
    session_id: str,
    store: SessionStore | None = None,
    output_dir: str | Path = ".",
) -> Path:
    """
    Export a full session as a JSON audit log file.

    The file is named ``session_<session_id[:8]>_<timestamp>.json``
    and written to *output_dir*.

    Args:
        session_id: The session to export.
        store: An optional SessionStore instance; a default one is used if not provided.
        output_dir: Directory where the file is written (default: current directory).

    Returns:
        Path to the written file.
    """
    if store is None:
        store = SessionStore()

    data = store.export_session(session_id)
    data["exported_at"] = datetime.now().isoformat()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"session_{session_id[:8]}_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)

    return filename
