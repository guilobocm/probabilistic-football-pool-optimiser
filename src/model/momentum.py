"""
Momentum Tracker — Injects recent form (proxy for xG momentum) into Team Strength.
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def apply_momentum(
    strengths: dict, form_path: Path = PROJECT_ROOT / "data" / "recent_form.csv"
) -> None:
    """
    Reads recent form modifiers from a CSV and applies them to the TeamStrength objects.
    The form modifier is a value between -0.3 and +0.3.
    """
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
                        # Cap modifier between -0.3 and 0.3
                        modifier = max(-0.3, min(0.3, modifier))
                        strengths[team].form = modifier
                except ValueError:
                    pass
    except Exception as e:
        print(f"⚠ Erro ao aplicar momentum: {e}")
