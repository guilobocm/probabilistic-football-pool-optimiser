"""Momentum tracker — apply recent form as a lightweight proxy for xG momentum."""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def apply_momentum(
    strengths: dict,
    form_path: Path = PROJECT_ROOT / "data" / "recent_form.csv",
) -> None:
    """Read recent-form modifiers from CSV and apply them to team strengths."""
    if not form_path.exists():
        return

    try:
        with open(form_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                team = row["team_name"].strip()
                try:
                    modifier = float(row["form_modifier"])
                    if team in strengths:
                        modifier = max(-0.3, min(0.3, modifier))
                        strengths[team].form = modifier
                except ValueError:
                    pass
    except Exception as exc:
        print(f"⚠ Could not apply the momentum adjustment: {exc}")
