"""
Data Validator — ensure external odds are sufficiently reliable before ingestion.

Filters:
- Overround limit, such as a maximum of 110%
- Minimum number of bookmakers per match
- Optional outlier detection

Outputs:
- Cleaned and aggregated probabilities dataframe
- Data-quality report dictionary
"""

import numpy as np
import pandas as pd


def validate_and_aggregate_odds(
    df_odds: pd.DataFrame,
    max_overround: float = 1.10,
    min_bookmakers: int = 3,
    expected_matches: int = 72,
    max_std_dev: float = 0.15,
) -> tuple[pd.DataFrame, dict]:
    """
    Validate odds data and return aggregated probabilities and a health report.

    Expected columns:
    match_id, source, market, selection, decimal_odd, source_type
    """
    report = {
        "expected_matches": expected_matches,
        "raw_rows": len(df_odds),
        "matches_found": df_odds["match_id"].nunique() if not df_odds.empty else 0,
        "matches_complete_1x2": 0,
        "bookmakers_dropped_overround": 0,
        "matches_dropped_low_volume": 0,
        "matches_dropped_high_std": 0,
        "matches_dropped_timestamp": 0,
        "median_bookmakers_per_match": 0,
        "mean_std_dev": 0.0,
        "valid_matches": 0,
        "unmapped_teams": [],
    }

    if df_odds.empty:
        return pd.DataFrame(), report

    # Filter to the 1X2 market.
    df_1x2 = df_odds[df_odds["market"] == "1x2"].copy()

    # Calculate implied probabilities for each row.
    df_1x2["implied_prob"] = 1.0 / df_1x2["decimal_odd"]

    # Pivot home, draw, and away outcomes side by side for each match and source.
    # The selection column normally contains team_a, draw, or team_b.
    try:
        df_pivot = df_1x2.pivot(
            index=["match_id", "source"],
            columns="selection",
            values="implied_prob",
        ).reset_index()
    except Exception:
        # Remove duplicates before retrying malformed or repeated rows.
        df_1x2 = df_1x2.drop_duplicates(
            subset=["match_id", "source", "selection", "market"]
        )
        pivot_index = (
            ["match_id", "source", "last_update"]
            if "last_update" in df_1x2.columns
            else ["match_id", "source"]
        )
        df_pivot = df_1x2.pivot(
            index=pivot_index,
            columns="selection",
            values="implied_prob",
        ).reset_index()

    # Filter by timestamp when source timestamps are available.
    if "last_update" in df_pivot.columns:
        try:
            now = pd.Timestamp.utcnow()
            df_pivot["last_update_dt"] = pd.to_datetime(
                df_pivot["last_update"], utc=True
            )
            age = now - df_pivot["last_update_dt"]

            # Use a conservative 48-hour window for pre-tournament market data.
            df_pivot = df_pivot[age <= pd.Timedelta(hours=48)].copy()

            remaining_matches = df_pivot["match_id"].nunique()
            report["matches_dropped_timestamp"] = (
                report["matches_found"] - remaining_matches
            )
        except Exception:
            # If timestamp parsing fails, continue without the age filter.
            pass

    # Ensure all outcome columns exist.
    for col in ["team_a", "draw", "team_b"]:
        if col not in df_pivot.columns:
            df_pivot[col] = np.nan

    # Drop rows missing any 1X2 outcome.
    df_complete = df_pivot.dropna(subset=["team_a", "draw", "team_b"]).copy()
    report["matches_complete_1x2"] = df_complete["match_id"].nunique()

    # Calculate and filter bookmaker overround.
    df_complete["overround"] = (
        df_complete["team_a"] + df_complete["draw"] + df_complete["team_b"]
    )
    df_valid = df_complete[df_complete["overround"] <= max_overround].copy()
    report["bookmakers_dropped_overround"] = len(df_complete) - len(df_valid)

    # Enforce minimum source coverage per match.
    bookie_counts = df_valid.groupby("match_id").size()
    report["median_bookmakers_per_match"] = (
        int(bookie_counts.median()) if not bookie_counts.empty else 0
    )

    valid_match_ids = bookie_counts[bookie_counts >= min_bookmakers].index
    df_final = df_valid[df_valid["match_id"].isin(valid_match_ids)].copy()
    report["matches_dropped_low_volume"] = len(bookie_counts) - len(valid_match_ids)

    # Check cross-bookmaker dispersion.
    if not df_final.empty:
        std_df = (
            df_final.groupby("match_id")
            .agg({"team_a": "std", "draw": "std", "team_b": "std"})
            .fillna(0)
        )
        std_df["max_std"] = std_df[["team_a", "draw", "team_b"]].max(axis=1)
        report["mean_std_dev"] = float(std_df["max_std"].mean())

        valid_std_ids = std_df[std_df["max_std"] <= max_std_dev].index
        report["matches_dropped_high_std"] = len(df_final["match_id"].unique()) - len(
            valid_std_ids
        )
        df_final = df_final[df_final["match_id"].isin(valid_std_ids)].copy()

    report["valid_matches"] = df_final["match_id"].nunique()

    if df_final.empty:
        return pd.DataFrame(), report

    # Aggregate 1X2 probabilities by match.
    agg_df = (
        df_final.groupby("match_id")
        .agg({"team_a": "mean", "draw": "mean", "team_b": "mean"})
        .reset_index()
    )

    agg_df["total"] = agg_df["team_a"] + agg_df["draw"] + agg_df["team_b"]
    agg_df["p_home"] = agg_df["team_a"] / agg_df["total"]
    agg_df["p_draw"] = agg_df["draw"] / agg_df["total"]
    agg_df["p_away"] = agg_df["team_b"] / agg_df["total"]
    agg_df = agg_df[["match_id", "p_home", "p_draw", "p_away"]]

    # Process Over/Under 2.5 markets when available.
    df_totals = df_odds[df_odds["market"] == "totals"].copy()
    if not df_totals.empty:
        df_totals["implied_prob"] = 1.0 / df_totals["decimal_odd"]
        df_tot_pivot = df_totals.pivot_table(
            index=["match_id", "source"],
            columns="selection",
            values="implied_prob",
            aggfunc="first",
        ).reset_index()

        if "over" in df_tot_pivot.columns and "under" in df_tot_pivot.columns:
            df_tot_complete = df_tot_pivot.dropna(subset=["over", "under"]).copy()
            df_tot_complete["tot_overround"] = (
                df_tot_complete["over"] + df_tot_complete["under"]
            )
            df_tot_valid = df_tot_complete[
                df_tot_complete["tot_overround"] <= max_overround
            ].copy()

            if not df_tot_valid.empty:
                agg_tot = (
                    df_tot_valid.groupby("match_id")
                    .agg({"over": "mean", "under": "mean"})
                    .reset_index()
                )
                agg_tot["tot_sum"] = agg_tot["over"] + agg_tot["under"]
                agg_tot["p_over_25"] = agg_tot["over"] / agg_tot["tot_sum"]
                agg_df = pd.merge(
                    agg_df,
                    agg_tot[["match_id", "p_over_25"]],
                    on="match_id",
                    how="left",
                )

    if "p_over_25" not in agg_df.columns:
        agg_df["p_over_25"] = np.nan

    return agg_df, report


def print_health_report(report: dict) -> None:
    """Print a formatted data-quality report."""
    print("📋 DATA-QUALITY REPORT")
    print(f"  Expected matches: {report.get('expected_matches', 72)}")
    print(f"  Matches found: {report['matches_found']}")
    print(f"  Matches with complete 1X2 markets: {report['matches_complete_1x2']}")
    print(f"  Matches accepted after filtering: {report['valid_matches']}")
    print(
        "  Matches rejected for stale timestamps (>48 h): "
        f"{report.get('matches_dropped_timestamp', 0)}"
    )
    print(
        "  Matches rejected for insufficient coverage (<3 sources): "
        f"{report['matches_dropped_low_volume']}"
    )
    print(
        "  Matches rejected for high dispersion (standard deviation >0.15): "
        f"{report['matches_dropped_high_std']}"
    )
    print(
        "  Bookmakers rejected for excessive overround (>110%): "
        f"{report['bookmakers_dropped_overround']}"
    )
    print(f"  Unmapped teams: {report.get('unmapped_teams', [])}")
    print(f"  Median sources per match: {report['median_bookmakers_per_match']}")
    print(f"  Mean cross-source dispersion: {report['mean_std_dev']:.4f}")
    print("=" * 40)
