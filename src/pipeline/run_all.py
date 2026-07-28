"""
Run All — main orchestration pipeline for the World Cup 2026 Pool Optimiser.

1. Load configuration and team-strength inputs
2. Generate group-stage fixtures and score-probability matrices
3. Optimise a scoreline for each match under the configured scoring rule
4. Run the tournament Monte Carlo simulation
5. Optimise the bonus questions
6. Save CSV and JSON outputs with a release manifest

Usage:
    python -m src.pipeline.run_all
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from src.config_loader import get_groups
from src.ingest.data_validator import print_health_report, validate_and_aggregate_odds
from src.ingest.ingest_csv import load_odds_csv
from src.ingest.odds_api_client import run_ingestion
from src.model.momentum import apply_momentum
from src.model.score_matrix import generate_score_matrix
from src.model.team_strength import TeamStrength, build_default_strengths
from src.optimizer.bonus_optimizer import optimize_all_bonuses
from src.optimizer.pick_optimizer import PickResult, optimize_pick
from src.optimizer.scoring_rules import ScoringRule, TOURNAMENT_RULE
from src.simulator.tournament_sim import TournamentSimulator

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore


def generate_group_matches() -> list[dict]:
    """Generate all 72 group-stage fixtures, six per group."""
    groups = get_groups()
    matches = []
    match_num = 1

    for group_letter, teams in sorted(groups.items()):
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                matches.append(
                    {
                        "match_id": f"GS_{group_letter}_{match_num:03d}",
                        "group": group_letter,
                        "team_a": teams[i],
                        "team_b": teams[j],
                        "stage": "group",
                    }
                )
                match_num += 1

    return matches


def run_match_predictions(
    matches: list[dict],
    strengths: dict[str, TeamStrength],
    rule: ScoringRule,
    external_probs: dict[str, dict] | None = None,
) -> list[PickResult]:
    """Generate score matrices and optimise one pick for every match."""
    results = []

    for match in matches:
        team_a = match["team_a"]
        team_b = match["team_b"]

        strength_a = strengths.get(team_a)
        strength_b = strengths.get(team_b)

        if strength_a is None or strength_b is None:
            print(
                f"  ⚠ Missing strength data for {team_a} or {team_b}; "
                "skipping the fixture"
            )
            continue

        external_1x2 = None
        external_over_25 = None
        if external_probs and match["match_id"] in external_probs:
            external_data = external_probs[match["match_id"]]
            external_1x2 = external_data["1x2"]
            external_over_25 = external_data.get("over_25")
            if external_over_25 is not None and math.isnan(external_over_25):
                external_over_25 = None

        score_probs = generate_score_matrix(
            team_a=strength_a,
            team_b=strength_b,
            external_1x2=external_1x2,
            target_over_25=external_over_25,
        )

        result = optimize_pick(
            match_id=match["match_id"],
            team_a=team_a,
            team_b=team_b,
            score_probs=score_probs,
            rule=rule,
        )
        results.append(result)

    return results


def save_match_picks(picks: list[PickResult], filepath: Path) -> None:
    """Save optimised match picks to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "match_id",
                "team_a",
                "team_b",
                "pick_a",
                "pick_b",
                "expected_points",
                "confidence",
                "most_probable_a",
                "most_probable_b",
                "most_probable_prob",
                "rationale",
            ]
        )

        for pick in picks:
            writer.writerow(
                [
                    pick.match_id,
                    pick.team_a,
                    pick.team_b,
                    pick.best_pick[0],
                    pick.best_pick[1],
                    f"{pick.expected_points:.4f}",
                    f"{pick.confidence:.4f}",
                    pick.most_probable_score[0],
                    pick.most_probable_score[1],
                    f"{pick.most_probable_prob:.4f}",
                    pick.rationale,
                ]
            )


def save_bonus_picks(bonuses: dict, filepath: Path) -> None:
    """Save bonus picks to JSON."""
    output = {}

    group_picks = []
    for bonus_pick in bonuses.get("group_winners", []):
        group_picks.append(
            {
                "question": bonus_pick.question,
                "pick": bonus_pick.pick,
                "probability": round(bonus_pick.probability, 4),
                "expected_points": round(bonus_pick.expected_points, 4),
                "alternatives": [
                    {"team": team, "prob": round(probability, 4)}
                    for team, probability in bonus_pick.alternatives[:3]
                ],
            }
        )
    output["group_winners"] = group_picks

    semifinal_picks = []
    for bonus_pick in bonuses.get("semifinalists", []):
        semifinal_picks.append(
            {
                "question": bonus_pick.question,
                "pick": bonus_pick.pick,
                "probability": round(bonus_pick.probability, 4),
                "expected_points": round(bonus_pick.expected_points, 4),
            }
        )
    output["semifinalists"] = semifinal_picks

    champion = bonuses.get("champion")
    if champion:
        output["champion"] = {
            "question": champion.question,
            "pick": champion.pick,
            "probability": round(champion.probability, 4),
            "expected_points": round(champion.expected_points, 4),
            "alternatives": [
                {"team": team, "prob": round(probability, 4)}
                for team, probability in champion.alternatives[:5]
            ],
        }

    golden_boot_team = bonuses.get("golden_boot_team")
    if golden_boot_team:
        output["golden_boot_team"] = {
            "question": golden_boot_team.question,
            "pick": golden_boot_team.pick,
            "probability": round(golden_boot_team.probability, 4),
            "expected_points": round(golden_boot_team.expected_points, 4),
            "alternatives": [
                {"team": team, "prob": round(probability, 4)}
                for team, probability in golden_boot_team.alternatives[:5]
            ],
        }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def save_simulation_summary(sim_results, filepath: Path) -> None:
    """Save the main tournament-simulation probabilities to JSON."""
    output = {
        "n_simulations": sim_results.n_simulations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "champion_probabilities": {
            team: round(probability, 4)
            for team, probability in sorted(
                sim_results.champion.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:15]
        },
        "semifinal_probabilities": {
            team: round(probability, 4)
            for team, probability in sorted(
                sim_results.semifinalists.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:20]
        },
        "group_winners": {
            group: {
                team: round(probability, 4)
                for team, probability in sorted(
                    probabilities.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            }
            for group, probabilities in sorted(sim_results.group_winners.items())
        },
        "top_scorer_player_probs": (
            {
                player: round(probability, 4)
                for player, probability in sorted(
                    sim_results.top_scorer.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:15]
            }
            if sim_results.top_scorer
            else {}
        ),
        "golden_boot_team_probs": (
            {
                team: round(probability, 4)
                for team, probability in sorted(
                    sim_results.golden_boot_team.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:15]
            }
            if sim_results.golden_boot_team
            else {}
        ),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def print_banner() -> None:
    print("=" * 70)
    print("  ⚽ WORLD CUP 2026 PREDICTION-POOL OPTIMISER ⚽")
    print("  Maximising expected points rather than blindly selecting the modal score")
    print("=" * 70)
    print()


def print_pick_summary(picks: list[PickResult]) -> None:
    """Print a concise summary of the optimised group-stage picks."""
    print("\n📊 OPTIMISED PICKS (GROUP STAGE)")
    print("-" * 78)
    print(f"{'Match':<38} {'Pick':>8} {'EP':>8} {'Modal score':>18}")
    print("-" * 78)

    total_ep = 0.0
    for pick in picks:
        pick_a, pick_b = pick.best_pick
        modal_a, modal_b = pick.most_probable_score
        match_label = f"{pick.team_a} vs {pick.team_b}"
        marker = " ⚡" if pick.best_pick != pick.most_probable_score else ""

        print(
            f"{match_label:<38} {pick_a}-{pick_b:>6} "
            f"{pick.expected_points:>7.3f} "
            f"{modal_a}-{modal_b} ({pick.most_probable_prob:.1%}){marker}"
        )
        total_ep += pick.expected_points

    print("-" * 78)
    print(f"{'Total expected points:':<38} {'':<8} {total_ep:>7.3f}")
    print(f"{'Matches:':<38} {len(picks)}")
    print()


def print_bonus_summary(bonuses: dict, sim_results) -> None:
    """Print the optimised bonus picks and their expected values."""
    print("\n🏆 BONUS PICKS — TOURNAMENT OUTCOMES")
    print("-" * 78)

    champion = bonuses.get("champion")
    if champion:
        n_simulations = sim_results.n_simulations
        margin_of_error = 1.96 * math.sqrt(
            champion.probability * (1 - champion.probability) / n_simulations
        )
        print(
            f"\n🥇 World champion: {champion.pick} "
            f"(P={champion.probability * 100:.1f}% ± "
            f"{margin_of_error * 100:.2f} p.p., "
            f"EP={champion.expected_points:.2f})"
        )
        if champion.alternatives:
            alternatives = ", ".join(
                f"{team} ({probability:.1%})"
                for team, probability in champion.alternatives[:4]
            )
            print(f"   Alternatives: {alternatives}")

    semifinal_picks = bonuses.get("semifinalists", [])
    if semifinal_picks:
        print("\n🏅 Semi-finalists:")
        for bonus_pick in semifinal_picks:
            print(
                f"   {bonus_pick.pick} "
                f"(P={bonus_pick.probability:.1%}, "
                f"EP={bonus_pick.expected_points:.2f})"
            )

    group_winner_picks = bonuses.get("group_winners", [])
    if group_winner_picks:
        print("\n📋 Group winners:")
        for bonus_pick in group_winner_picks:
            group_letter = bonus_pick.question.split("Group ")[-1].rstrip("?")
            alternatives = ", ".join(
                f"{team} ({probability:.1%})"
                for team, probability in bonus_pick.alternatives[:2]
            )
            print(
                f"   Group {group_letter}: {bonus_pick.pick} "
                f"({bonus_pick.probability:.1%}) | Alternatives: {alternatives}"
            )

    golden_boot_team = bonuses.get("golden_boot_team")
    if golden_boot_team:
        print(
            f"\n⚽ Golden Boot team: {golden_boot_team.pick} "
            f"(P={golden_boot_team.probability * 100:.1f}%, "
            f"EP={golden_boot_team.expected_points:.2f})"
        )
        if golden_boot_team.alternatives:
            alternatives = ", ".join(
                f"{team} ({probability:.1%})"
                for team, probability in golden_boot_team.alternatives[:4]
            )
            print(f"   Alternatives: {alternatives}")

    total_bonus_ep = 0.0
    if champion:
        total_bonus_ep += champion.expected_points
    for bonus_pick in semifinal_picks:
        total_bonus_ep += bonus_pick.expected_points
    for bonus_pick in group_winner_picks:
        total_bonus_ep += bonus_pick.expected_points
    if golden_boot_team:
        total_bonus_ep += golden_boot_team.expected_points

    print(f"\n   Total bonus EP: {total_bonus_ep:.2f}")
    print()


def file_hash(path: Path) -> str:
    """Return the legacy MD5 input hash used by the release manifest."""
    if path.exists():
        return hashlib.md5(path.read_bytes()).hexdigest()
    return "N/A"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="World Cup 2026 Pool Optimiser")
    parser.add_argument("--output-dir", type=Path, help="Directory to save outputs")
    parser.add_argument("--skip-live-ingestion", action="store_true", help="Skip fetching live odds")
    parser.add_argument("--num-simulations", type=int, default=100000, help="Number of Monte Carlo simulations")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed for simulations")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the complete modelling and optimisation pipeline."""
    args = build_parser().parse_args(argv)
    
    if args.num_simulations <= 0:
        print("Error: --num-simulations must be strictly positive.")
        return 1

    project_root = Path(__file__).resolve().parent.parent.parent
    
    if args.output_dir:
        output_dir = args.output_dir.resolve()
    else:
        output_dir = project_root / "outputs"
        
    print_banner()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("📂 Loading configuration and team-strength data...")
    groups = get_groups()
    strengths = build_default_strengths()
    apply_momentum(strengths)
    rule = TOURNAMENT_RULE
    print(
        f"   Loaded {len(groups)} groups and strength data for "
        f"{len(strengths)} teams"
    )

    print("\n⚽ Generating group-stage fixtures...")
    matches = generate_group_matches()
    print(f"   Generated {len(matches)} fixtures")

    print("\n🌐 Fetching current market odds from The Odds API...")
    if not args.skip_live_ingestion:
        run_ingestion()
    else:
        print("   ⏭ Skipped live ingestion as requested")

    odds_path = project_root / "data" / "raw" / "odds_input.csv"
    external_probs = {}

    if odds_path.exists():
        try:
            df_odds = load_odds_csv(odds_path)
            aggregated_odds, report = validate_and_aggregate_odds(df_odds)
            print()
            print_health_report(report)

            for _, row in aggregated_odds.iterrows():
                external_probs[row["match_id"]] = {
                    "1x2": (row["p_home"], row["p_draw"], row["p_away"]),
                    "over_25": row.get("p_over_25"),
                }

            print(
                f"   Success: incorporated validated odds for "
                f"{len(external_probs)} matches"
            )
        except Exception as exc:
            print(f"   ⚠ Could not process the odds CSV: {exc}")

    print("\n🧮 Optimising picks by expected points...")
    missing_matches = [
        match for match in matches if match["match_id"] not in external_probs
    ]
    if missing_matches:
        print(
            f"   ⚠ {len(missing_matches)} matches will use the base-Elo fallback "
            "because market coverage was absent or rejected:"
        )
        for match in missing_matches:
            print(
                f"      - {match['team_a']} vs {match['team_b']} "
                "(source_used = base_model_fallback)"
            )

    picks = run_match_predictions(matches, strengths, rule, external_probs)
    print(f"   Generated {len(picks)} optimised picks")

    print("\n🎰 Running the tournament Monte Carlo simulation...")
    simulator = TournamentSimulator(groups, strengths)
    simulation_results = simulator.simulate(n_simulations=args.num_simulations, seed=args.seed)
    print(f"   Completed {simulation_results.n_simulations:,} simulations")
    simulator.print_audit_report()

    print("\n🏆 Optimising bonus picks...")
    bonuses = optimize_all_bonuses(simulation_results, points_per_correct=4)

    print("\n💾 Saving outputs...")
    save_match_picks(picks, output_dir / "match_picks.csv")
    save_bonus_picks(bonuses, output_dir / "bonus_picks.json")
    save_simulation_summary(
        simulation_results,
        output_dir / "simulation_summary.json",
    )

    manifest = {
        "version": "2.4-RC",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "n_simulations": args.num_simulations,
        "input_hashes": {
            "odds_input.csv": file_hash(
                project_root / "data" / "raw" / "odds_input.csv"
            ),
            "players.yaml": file_hash(project_root / "data" / "players.yaml"),
            "recent_form.csv": file_hash(
                project_root / "data" / "recent_form.csv"
            ),
        },
        "outputs_generated": [
            "match_picks.csv",
            "bonus_picks.json",
            "simulation_summary.json",
            "release_manifest.json",
        ],
        "matches_with_market_odds": len(external_probs),
        "matches_with_fallback": len(missing_matches),
        "model_notes": [
            "The Golden Boot model is experimental and uses goals, assists, and minutes",
            "Tie-breaks use a statistical approximation: points, goal difference, goals scored, then noise",
            "Momentum is a lightweight recent_form.csv proxy rather than observed xG",
            "Refresh odds near kick-off to reflect injuries, line-ups, and squad news",
        ],
    }
    with open(output_dir / "release_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"   Outputs saved to: {output_dir}")

    print_pick_summary(picks)
    print_bonus_summary(bonuses, simulation_results)

    print("\n" + "=" * 70)
    print("  ✅ Pipeline complete")
    print("  Generated files:")
    print(f"    📄 {output_dir / 'match_picks.csv'}")
    print(f"    📄 {output_dir / 'bonus_picks.json'}")
    print(f"    📄 {output_dir / 'simulation_summary.json'}")
    print(f"    📄 {output_dir / 'release_manifest.json'}")
    
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
