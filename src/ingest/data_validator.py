"""
Data Validator — Ensures external odds are high quality before ingestion.

Filters:
- Overround limit (e.g. max 110%)
- Minimum bookmakers per match
- Outlier detection (optional)

Outputs:
- Cleaned and aggregated probabilities dataframe
- Health report dictionary
"""

import pandas as pd
import numpy as np


def validate_and_aggregate_odds(
    df_odds: pd.DataFrame,
    max_overround: float = 1.10,
    min_bookmakers: int = 3,
    expected_matches: int = 72,
    max_std_dev: float = 0.15,
) -> tuple[pd.DataFrame, dict]:
    """
    Validates odds data and returns aggregated probabilities + health report.
    
    Expects df_odds to have columns:
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

    # Filter to 1x2 market
    df_1x2 = df_odds[df_odds["market"] == "1x2"].copy()
    
    # Calculate implied probabilities for each row
    df_1x2["implied_prob"] = 1.0 / df_1x2["decimal_odd"]

    # Pivot to get home, draw, away side-by-side per match and source
    # selection is typically 'team_a', 'draw', 'team_b'
    try:
        df_pivot = df_1x2.pivot(
            index=["match_id", "source"],
            columns="selection",
            values="implied_prob"
        ).reset_index()
    except Exception as e:
        # Duplicates or malformed data
        df_1x2 = df_1x2.drop_duplicates(subset=["match_id", "source", "selection", "market"])
        df_pivot = df_1x2.pivot(
            index=["match_id", "source", "last_update"] if "last_update" in df_1x2.columns else ["match_id", "source"],
            columns="selection",
            values="implied_prob"
        ).reset_index()

    # Filter by timestamp if available (e.g., must be within 24h)
    if "last_update" in df_pivot.columns:
        # Assuming last_update is ISO format or datetime
        try:
            now = pd.Timestamp.utcnow()
            # Handle potential string format from API
            df_pivot["last_update_dt"] = pd.to_datetime(df_pivot["last_update"], utc=True)
            age = now - df_pivot["last_update_dt"]
            
            # Drop sources older than 48 hours
            # We use 48h as conservative given World Cup odds don't move as wildly before tournament
            old_rows = df_pivot[age > pd.Timedelta(hours=48)]
            df_pivot = df_pivot[age <= pd.Timedelta(hours=48)].copy()
            
            # Count matches that were completely dropped due to timestamp
            remaining_matches = df_pivot["match_id"].nunique()
            report["matches_dropped_timestamp"] = report["matches_found"] - remaining_matches
            
        except Exception as e:
            # If timestamp parsing fails, ignore timestamp filter
            pass

    # Ensure columns exist
    for col in ["team_a", "draw", "team_b"]:
        if col not in df_pivot.columns:
            df_pivot[col] = np.nan

    # Drop rows missing any outcome
    df_complete = df_pivot.dropna(subset=["team_a", "draw", "team_b"]).copy()
    report["matches_complete_1x2"] = df_complete["match_id"].nunique()

    # Calculate overround
    df_complete["overround"] = df_complete["team_a"] + df_complete["draw"] + df_complete["team_b"]
    
    # Filter overround
    df_valid = df_complete[df_complete["overround"] <= max_overround].copy()
    report["bookmakers_dropped_overround"] = len(df_complete) - len(df_valid)

    # Count bookmakers per match
    bookie_counts = df_valid.groupby("match_id").size()
    report["median_bookmakers_per_match"] = int(bookie_counts.median()) if not bookie_counts.empty else 0

    valid_match_ids = bookie_counts[bookie_counts >= min_bookmakers].index
    df_final = df_valid[df_valid["match_id"].isin(valid_match_ids)].copy()
    
    report["matches_dropped_low_volume"] = len(bookie_counts) - len(valid_match_ids)
    # Standard Deviation Check
    if not df_final.empty:
        std_df = df_final.groupby("match_id").agg({
            "team_a": "std", "draw": "std", "team_b": "std"
        }).fillna(0)
        std_df["max_std"] = std_df[["team_a", "draw", "team_b"]].max(axis=1)
        report["mean_std_dev"] = float(std_df["max_std"].mean())
        
        valid_std_ids = std_df[std_df["max_std"] <= max_std_dev].index
        report["matches_dropped_high_std"] = len(df_final["match_id"].unique()) - len(valid_std_ids)
        df_final = df_final[df_final["match_id"].isin(valid_std_ids)].copy()
        
    report["valid_matches"] = df_final["match_id"].nunique()

    # Aggregate by match
    if df_final.empty:
        return pd.DataFrame(), report

    agg_df = df_final.groupby("match_id").agg({
        "team_a": "mean",
        "draw": "mean",
        "team_b": "mean"
    }).reset_index()

    agg_df["total"] = agg_df["team_a"] + agg_df["draw"] + agg_df["team_b"]
    agg_df["p_home"] = agg_df["team_a"] / agg_df["total"]
    agg_df["p_draw"] = agg_df["draw"] / agg_df["total"]
    agg_df["p_away"] = agg_df["team_b"] / agg_df["total"]
    
    agg_df = agg_df[["match_id", "p_home", "p_draw", "p_away"]]

    # Process totals (over/under 2.5) if available
    df_totals = df_odds[df_odds["market"] == "totals"].copy()
    if not df_totals.empty:
        df_totals["implied_prob"] = 1.0 / df_totals["decimal_odd"]
        df_tot_pivot = df_totals.pivot_table(
            index=["match_id", "source"],
            columns="selection",
            values="implied_prob",
            aggfunc="first"
        ).reset_index()
        
        if "over" in df_tot_pivot.columns and "under" in df_tot_pivot.columns:
            df_tot_complete = df_tot_pivot.dropna(subset=["over", "under"]).copy()
            df_tot_complete["tot_overround"] = df_tot_complete["over"] + df_tot_complete["under"]
            df_tot_valid = df_tot_complete[df_tot_complete["tot_overround"] <= max_overround].copy()
            
            if not df_tot_valid.empty:
                agg_tot = df_tot_valid.groupby("match_id").agg({
                    "over": "mean",
                    "under": "mean"
                }).reset_index()
                
                agg_tot["tot_sum"] = agg_tot["over"] + agg_tot["under"]
                agg_tot["p_over_25"] = agg_tot["over"] / agg_tot["tot_sum"]
                
                # Merge into agg_df
                agg_df = pd.merge(agg_df, agg_tot[["match_id", "p_over_25"]], on="match_id", how="left")

    if "p_over_25" not in agg_df.columns:
        agg_df["p_over_25"] = np.nan

    return agg_df, report


def print_health_report(report: dict) -> None:
    """Prints a formatted health report."""
    print("📋 DATA QUALITY REPORT")
    print(f"  Jogos esperados: {report.get('expected_matches', 72)}")
    print(f"  Jogos encontrados: {report['matches_found']}")
    print(f"  Jogos com 1X2 completo: {report['matches_complete_1x2']}")
    print(f"  Jogos aceitos após filtros: {report['valid_matches']}")
    print(f"  Jogos rejeitados por timestamp velho (>48h): {report.get('matches_dropped_timestamp', 0)}")
    print(f"  Jogos rejeitados por baixa cobertura (<3): {report['matches_dropped_low_volume']}")
    print(f"  Jogos rejeitados por alta divergência (STD>0.15): {report['matches_dropped_high_std']}")
    print(f"  Casas rejeitadas por overround (>110%): {report['bookmakers_dropped_overround']}")
    print(f"  Seleções não mapeadas: {report.get('unmapped_teams', [])}")
    print(f"  Mediana de fontes por jogo: {report['median_bookmakers_per_match']}")
    print(f"  Desvio médio entre fontes: {report['mean_std_dev']:.4f}")
    print("=" * 40)
