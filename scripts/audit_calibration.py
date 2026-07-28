import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.model.lambda_calibrator import calibrate_lambdas
from src.model.poisson_model import dixon_coles_correction, get_1x2_from_matrix

import numpy as np

# Representative cases: team labels, Elo lambdas, and market P(A win), P(draw), P(B win).
TEST_CASES = [
    # Leading favourites against underdogs
    ("Argentina", "Curaçao", 3.1, 0.4, (0.85, 0.10, 0.05)),
    ("France", "Haiti", 2.9, 0.5, (0.80, 0.15, 0.05)),
    ("Spain", "Cape Verde", 2.8, 0.6, (0.75, 0.18, 0.07)),

    # Strong teams against mid-tier opposition
    ("Brazil", "Scotland", 2.2, 0.8, (0.60, 0.25, 0.15)),
    ("England", "Ghana", 2.0, 0.9, (0.55, 0.28, 0.17)),
    ("Germany", "Ecuador", 1.9, 1.0, (0.50, 0.30, 0.20)),

    # Balanced or traditionally competitive fixtures
    ("Mexico", "South Korea", 1.4, 1.3, (0.38, 0.32, 0.30)),
    ("Portugal", "Colombia", 1.6, 1.4, (0.42, 0.30, 0.28)),
    ("Netherlands", "Sweden", 1.5, 1.4, (0.40, 0.31, 0.29)),
    ("Japan", "Switzerland", 1.2, 1.3, (0.33, 0.33, 0.34)),

    # Large Elo-market disagreements
    # Elo favours Team A, while the market is approximately balanced.
    ("United States", "Paraguay", 2.1, 0.9, (0.40, 0.30, 0.30)),
    # Elo is approximately balanced, while the market strongly favours Team A.
    ("Belgium", "Iran", 1.3, 1.2, (0.65, 0.22, 0.13)),

    # Market underdog with a comparatively stronger Elo prior
    ("Australia", "Türkiye", 1.5, 1.1, (0.20, 0.25, 0.55)),

    # Very low- and high-scoring priors
    # Low total: 1.0 + 0.9 = 1.9 expected goals.
    ("Senegal", "Iraq", 1.0, 0.9, (0.45, 0.35, 0.20)),
    # High total: 2.5 + 2.0 = 4.5 expected goals.
    ("Austria", "Jordan", 2.5, 2.0, (0.55, 0.20, 0.25)),
]


def top_5_scores(matrix):
    flat = matrix.flatten()
    indices = np.argsort(flat)[-5:][::-1]
    results = []
    for idx in indices:
        i, j = np.unravel_index(idx, matrix.shape)
        results.append(f"{i}-{j} ({matrix[i, j] * 100:.1f}%)")
    return " | ".join(results)


def run_audit():
    print("=" * 120)
    print("🔎 CALIBRATION SENSITIVITY AUDIT (total-goals prior weight = 0.05)")
    print("=" * 120)

    for team_a, team_b, la_elo, lb_elo, market_1x2 in TEST_CASES:
        prior_total = la_elo + lb_elo

        # Calculate the Elo-prior matrix.
        elo_mat = dixon_coles_correction(la_elo, lb_elo, -0.10, 10)
        elo_mat = elo_mat / np.sum(elo_mat)
        elo_1x2 = get_1x2_from_matrix(elo_mat)

        # Calibrate the lambdas against the market probabilities.
        la_cal, lb_cal = calibrate_lambdas(market_1x2, la_elo, lb_elo, -0.10, 10)
        final_total = la_cal + lb_cal

        # Calculate the calibrated matrix.
        cal_mat = dixon_coles_correction(la_cal, lb_cal, -0.10, 10)
        cal_mat = cal_mat / np.sum(cal_mat)
        cal_1x2 = get_1x2_from_matrix(cal_mat)

        print(f"\n⚽ {team_a} vs {team_b}")
        print(
            f"  [ELO PRIOR] La={la_elo:.2f}, Lb={lb_elo:.2f} | "
            f"P_Elo={elo_1x2[0] * 100:.1f}% / {elo_1x2[1] * 100:.1f}% / {elo_1x2[2] * 100:.1f}%"
        )
        print(
            f"  [MARKET]                           | "
            f"P_Mkt={market_1x2[0] * 100:.1f}% / {market_1x2[1] * 100:.1f}% / {market_1x2[2] * 100:.1f}%"
        )
        print(
            f"  [CALIBRATED] La={la_cal:.2f}, Lb={lb_cal:.2f} | "
            f"P_Cal={cal_1x2[0] * 100:.1f}% / {cal_1x2[1] * 100:.1f}% / {cal_1x2[2] * 100:.1f}%"
        )
        print(
            f"  [TOTALS] Prior goals={prior_total:.2f} -> "
            f"Final goals={final_total:.2f} (delta: {final_total - prior_total:+.2f})"
        )
        print(f"  [TOP 5 BEFORE] {top_5_scores(elo_mat)}")
        print(f"  [TOP 5 AFTER]  {top_5_scores(cal_mat)}")


if __name__ == "__main__":
    run_audit()
