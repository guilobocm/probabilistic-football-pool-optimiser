import sys
import json
import subprocess
from pathlib import Path


def test_run_all_and_outputs_schema(tmp_path):
    """
    Smoke test to execute the main pipeline and verify that it completes
    successfully, producing the three expected output files with the correct
    basic schema.
    """
    project_root = Path(__file__).resolve().parent.parent
    import os

    env = os.environ.copy()
    env.pop("THE_ODDS_API_KEY", None)

    output_dir = tmp_path / "outputs"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.pipeline.run_all",
            "--output-dir",
            str(output_dir),
            "--skip-live-ingestion",
            "--num-simulations",
            "100",
            "--seed",
            "2026",
        ],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    # Check it passed successfully
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Check that outputs are created in tmp_path
    assert output_dir.exists(), "Outputs directory not created."

    match_picks = output_dir / "match_picks.csv"
    bonus_picks = output_dir / "bonus_picks.json"
    sim_summary = output_dir / "simulation_summary.json"

    assert match_picks.exists(), "match_picks.csv missing."
    assert bonus_picks.exists(), "bonus_picks.json missing."
    assert sim_summary.exists(), "simulation_summary.json missing."

    # Schema check for bonus_picks.json
    with open(bonus_picks, "r", encoding="utf-8") as f:
        bonus_data = json.load(f)
    assert isinstance(bonus_data, dict), "Bonus picks should be a dictionary."
    assert "champion" in bonus_data, "Missing champion in bonus picks."
    assert "semifinalists" in bonus_data, "Missing semifinalists in bonus picks."
    assert "group_winners" in bonus_data, "Missing group_winners in bonus picks."

    # Schema check for simulation_summary.json
    with open(sim_summary, "r", encoding="utf-8") as f:
        sim_data = json.load(f)
    assert isinstance(sim_data, dict), "Sim summary should be a dictionary."
    assert "champion_probabilities" in sim_data, (
        "Missing champion_probabilities in sim summary."
    )
    assert "semifinal_probabilities" in sim_data, (
        "Missing semifinal_probabilities in sim summary."
    )

    # Check that match picks is not empty
    with open(match_picks, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) > 1, "match_picks.csv is empty or missing headers."
    assert "team_a,team_b,pick_a,pick_b" in lines[0] or "match" in lines[0].lower(), (
        "match_picks.csv has invalid header."
    )
