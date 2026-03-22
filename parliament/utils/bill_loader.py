"""
Bill YAML loader.

Loads one or more bills from YAML files in the bills/ directory.
"""

from pathlib import Path
from uuid import uuid4

import yaml

from parliament.core.bill import Bill, BillStatus


def load_bill_from_yaml(path: str | Path) -> Bill:
    """
    Load a Bill from a YAML file.

    Expected YAML keys: title, proposal, assumptions, intended_outcomes,
    known_risks, unknowns.

    Args:
        path: Path to the YAML file.

    Returns:
        A new Bill with status DRAFT.
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    return Bill(
        id=uuid4(),
        title=data["title"],
        proposal=data["proposal"].strip(),
        assumptions=data.get("assumptions", []),
        intended_outcomes=data.get("intended_outcomes", []),
        known_risks=data.get("known_risks", []),
        unknowns=data.get("unknowns", []),
        status=BillStatus.DRAFT,
    )


def load_bills_from_dir(directory: str | Path) -> list[Bill]:
    """
    Load all YAML bill files from a directory.

    Files are sorted alphabetically before loading so the order is
    deterministic.

    Args:
        directory: Path to the bills directory.

    Returns:
        List of Bills.
    """
    directory = Path(directory)
    bill_files = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))
    return [load_bill_from_yaml(f) for f in bill_files]
