"""
Audit Totals — demonstrate that Over/Under market integration actively shifts
 the model's expected total-goals distribution.
"""

import csv
import sys
from pathlib import Path

# Add the project root to the import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.ingest.data_validator import validate_and_aggregate_odds
from src.ingest.ingest_csv import load_odds_csv
from src.model.lambda_calibrator import calibrate_lambdas
from src.model.momentum import apply_momentum
from src.model.poisson_model import dixon_coles_correction
from src.model.team_strength import build_default_strengths, estimate_lambdas


def get_match_mapping():
    picks_path = PROJECT_ROOT / "outputs" / "match_picks.csv"
    mapping = {}
    with open(picks_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["match_id"]] = (row["team_a"], row["team_b"])
    return mapping


def calculate_over_25(matrix: dict) -> float:
    """Calculate P(Over 2.5) from a score-probability matrix."""
    return sum(prob for (g_a, g_b), prob in matrix.items() if g_a + g_b > 2.5)


def main():
    print("=" * 80)
    print("🔎 OVER/UNDER MARKET AUDIT (TOTAL GOALS)")
    print("=" * 80)

    # 1. Load odds.
    odds_path = PROJECT_ROOT / "data" / "raw" / "odds_input.csv"
    if not odds_path.exists():
        print("Error: odds_input.csv was not found. Run the main pipeline first.")
        return

    df_odds = load_odds_csv(odds_path)
    agg_df, _ = validate_and_aggregate_odds(df_odds)

    # 2. Load team strengths and apply the momentum adjustment.
    strengths = build_default_strengths()
    apply_momentum(strengths)

    # 3. Analyse each match.
    mapping = get_match_mapping()

    count_market = 0
    for _, row in agg_df.iterrows():
        match_id = row["match_id"]

        teams = mapping.get(match_id)
        if not teams:
            continue
        team_a, team_b = teams

        sa = strengths.get(team_a)
        sb = strengths.get(team_b)

        if not sa or not sb:
            continue

        target_1x2 = (row["p_home"], row["p_draw"], row["p_away"])
        p_over25_market = row.get("p_over_25")

        # Get the base lambdas.
        la_prior, lb_prior = estimate_lambdas(sa, sb, avg_goals=2.65)

        # Matrix before calibration, using the base Elo prior.
        import numpy as np

        mat_before_np = dixon_coles_correction(la_prior, lb_prior, rho=-0.10)

        # Convert the matrix to a dictionary for aggregation.
        from src.model.poisson_model import score_matrix_to_dict

        mat_before = score_matrix_to_dict(mat_before_np)
        p_over25_before = calculate_over_25(mat_before)

        # Report cases where the market supplied a valid Over 2.5 probability.
        if p_over25_market is not None and not np.isnan(p_over25_market):
            la_cal, lb_cal = calibrate_lambdas(
                target_1x2=target_1x2,
                initial_la=la_prior,
                initial_lb=lb_prior,
                rho=-0.10,
                target_over_25=p_over25_market,
            )

            mat_after_np = dixon_coles_correction(la_cal, lb_cal, rho=-0.10)
            mat_after = score_matrix_to_dict(mat_after_np)
            p_over25_after = calculate_over_25(mat_after)

            print(f"\n⚽ {team_a} vs {team_b}")
            print(f"  P_over25_market       = {p_over25_market * 100:.1f}%")
            print(f"  P_over25_model_before = {p_over25_before * 100:.1f}%")
            print(f"  P_over25_model_after  = {p_over25_after * 100:.1f}%")
            print("  source_used           = market_totals")
            count_market += 1
        else:
            # Fall back to 1X2-only calibration.
            la_cal, lb_cal = calibrate_lambdas(
                target_1x2=target_1x2,
                initial_la=la_prior,
                initial_lb=lb_prior,
                rho=-0.10,
                target_over_25=None,
            )
            mat_after_np = dixon_coles_correction(la_cal, lb_cal, rho=-0.10)
            mat_after = score_matrix_to_dict(mat_after_np)
            p_over25_after = calculate_over_25(mat_after)

            print(f"\n⚽ {team_a} vs {team_b}")
            print("  P_over25_market       = N/A")
            print(f"  P_over25_model_before = {p_over25_before * 100:.1f}%")
            print(
                f"  P_over25_model_after  = {p_over25_after * 100:.1f}% (via 1X2 drift)"
            )
            print("  source_used           = fallback_prior")

    print(
        f"\n✅ Complete. {count_market} matches were calibrated directly "
        "against the Over/Under market."
    )


if __name__ == "__main__":
    main()
