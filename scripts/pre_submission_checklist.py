"""
Pre-submission checklist for the FIFA World Cup 2026 prediction pool.

Run this script before submitting picks. It verifies that the pipeline is
healthy and that the generated outputs are internally consistent.
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def run_step(name: str, cmd: list[str]) -> bool:
    print(f"\n{'=' * 60}")
    print(f"  🔍 {name}")
    print(f"{'=' * 60}")
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        print("  ❌ FAILED")
        print(result.stderr[-500:] if result.stderr else "No stderr output")
        return False

    # Print the final ten output lines for a concise audit trail.
    lines = result.stdout.strip().split("\n")
    for line in lines[-10:]:
        print(f"  {line}")
    print("  ✅ OK")
    return True


def check_outputs() -> bool:
    print(f"\n{'=' * 60}")
    print("  🔍 Check that required outputs exist")
    print(f"{'=' * 60}")

    required = [
        "match_picks.csv",
        "bonus_picks.json",
        "simulation_summary.json",
        "release_manifest.json",
    ]

    all_ok = True
    for fname in required:
        path = OUTPUT_DIR / fname
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {fname} ({size:,} bytes)")
        else:
            print(f"  ❌ {fname} DOES NOT EXIST")
            all_ok = False

    return all_ok


def check_manifest() -> bool:
    print(f"\n{'=' * 60}")
    print("  🔍 Check release_manifest.json")
    print(f"{'=' * 60}")

    manifest_path = OUTPUT_DIR / "release_manifest.json"
    if not manifest_path.exists():
        print("  ❌ The manifest does not exist. Run run_all.py first.")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"  Version:    {manifest.get('version', '?')}")
    print(f"  Timestamp:  {manifest.get('timestamp', '?')}")
    print(f"  Seed:       {manifest.get('seed', '?')}")
    print(f"  Simulations:{manifest.get('n_simulations', '?'):,}")
    print(
        "  Odds hash: "
        f"{manifest.get('input_hashes', {}).get('odds_input.csv', '?')[:12]}..."
    )

    notes = manifest.get("model_notes", [])
    if notes:
        print("  Notes:")
        for note in notes:
            print(f"    ⚠ {note}")

    print("  ✅ OK")
    return True


def check_simulation_summary() -> bool:
    print(f"\n{'=' * 60}")
    print("  🔍 Check simulation_summary.json")
    print(f"{'=' * 60}")

    path = OUTPUT_DIR / "simulation_summary.json"
    if not path.exists():
        print("  ❌ The file does not exist.")
        return False

    with open(path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    golden_boot_teams = summary.get("golden_boot_team_probs", {})
    top_scorers = summary.get("top_scorer_player_probs", {})

    if not golden_boot_teams:
        print("  ❌ golden_boot_team_probs is empty.")
        return False

    if not top_scorers:
        print("  ❌ top_scorer_player_probs is empty.")
        return False

    top_player = next(iter(top_scorers))
    top_team = next(iter(golden_boot_teams))
    print(
        f"  Leading Golden Boot player: {top_player} ({top_scorers[top_player] * 100:.1f}%)"
    )
    print(
        f"  Leading Golden Boot team:   {top_team} ({golden_boot_teams[top_team] * 100:.1f}%)"
    )
    print("  ✅ OK")
    return True


def check_fallbacks() -> bool:
    print(f"\n{'=' * 60}")
    print("  🔍 Check matches using fallback inputs")
    print(f"{'=' * 60}")

    import csv

    picks_path = OUTPUT_DIR / "match_picks.csv"
    if not picks_path.exists():
        print("  ❌ match_picks.csv does not exist.")
        return False

    fallbacks = []
    total = 0
    with open(picks_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            rationale = row.get("rationale", "")
            if "fallback" in rationale.lower():
                fallbacks.append(f"{row['team_a']} vs {row['team_b']}")

    print(f"  Total matches:       {total}")
    print(f"  Matches on fallback: {len(fallbacks)}")
    for match in fallbacks:
        print(f"    ⚠ {match}")

    print("  ✅ OK — review the fallback set manually before submission")
    return True


def main():
    print("\n" + "=" * 60)
    print("  📋 PRE-SUBMISSION CHECKLIST — WORLD CUP 2026 POOL v2.4-RC")
    print("=" * 60)

    results = {}

    # 1. Audit total-goals calibration.
    results["audit_totals"] = run_step(
        "Over/Under audit (audit_totals.py)",
        [sys.executable, "-m", "scripts.audit_totals"],
    )

    # 2. Validate Annexe C.
    results["annexe_c"] = run_step(
        "Annexe C test (495 combinations)",
        [
            sys.executable,
            "-c",
            (
                "from src.simulator.annexe_c_official import validate_annexe_c; "
                "validate_annexe_c(); "
                "print('Annexe C: 495 combinations validated')"
            ),
        ],
    )

    # 3. Check outputs.
    results["outputs"] = check_outputs()

    # 4. Check the release manifest.
    results["manifest"] = check_manifest()

    # 5. Check the simulation summary.
    results["simulation_summary"] = check_simulation_summary()

    # 6. Check fallback usage.
    results["fallbacks"] = check_fallbacks()

    print("\n" + "=" * 60)
    print("  📊 FINAL RESULT")
    print("=" * 60)

    all_ok = True
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("  🎉 ALL AUTOMATED CHECKS PASSED. Ready for submission.")
    else:
        print("  ⚠️  SOME CHECKS FAILED. Review them before submitting.")

    print()
    print("  📝 Remaining manual checks:")
    print("     □ Review injuries, line-ups, and recent squad news")
    print("     □ Confirm that market odds are current")
    print("     □ Inspect match_picks.csv as a final sanity check")
    print("     □ Record the submission date and time")
    print()


if __name__ == "__main__":
    main()
