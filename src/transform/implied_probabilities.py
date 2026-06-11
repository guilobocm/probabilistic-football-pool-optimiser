"""
Implied Probabilities — Convert odds to clean probabilities.

Removes bookmaker margin (overround) via normalisation.
Supports 1X2, over/under, and exact score markets.
"""

from __future__ import annotations

from typing import Optional


def decimal_odds_to_clean_probs(
    odds: dict[str, float],
) -> dict[str, float]:
    """
    Convert decimal odds to margin-free probabilities.

    1. Compute raw implied probability: q_i = 1 / odd_i
    2. Sum all q_i (= 1 + margin)
    3. Normalise: p_i = q_i / sum(q_i)

    Args:
        odds: {selection_name: decimal_odd}

    Returns:
        {selection_name: clean_probability}

    Raises:
        ValueError if any odd <= 1 or empty dict
    """
    if not odds:
        raise ValueError("Odds dictionary is empty.")

    raw_probs: dict[str, float] = {}

    for selection, odd in odds.items():
        if odd is None or odd <= 1.0:
            raise ValueError(f"Invalid decimal odd for '{selection}': {odd}")
        raw_probs[selection] = 1.0 / odd

    total = sum(raw_probs.values())

    if total <= 0:
        raise ValueError("Invalid total implied probability.")

    return {
        selection: prob / total
        for selection, prob in raw_probs.items()
    }


def overround(odds: dict[str, float]) -> float:
    """Calculate the bookmaker overround (margin) from decimal odds."""
    return sum(1.0 / odd for odd in odds.values())


def validate_overround(
    margin: float,
    min_acceptable: float = 1.00,
    max_acceptable: float = 1.20,
) -> bool:
    """Check if overround is within acceptable range."""
    return min_acceptable <= margin <= max_acceptable


def odds_1x2_to_probs(
    odd_home: float,
    odd_draw: float,
    odd_away: float,
) -> tuple[float, float, float]:
    """
    Convenience function for 1X2 market.

    Returns (p_home, p_draw, p_away) with margin removed.
    """
    clean = decimal_odds_to_clean_probs({
        "home": odd_home,
        "draw": odd_draw,
        "away": odd_away,
    })
    return clean["home"], clean["draw"], clean["away"]


def over_under_to_probs(
    odd_over: float,
    odd_under: float,
) -> tuple[float, float]:
    """
    Convert over/under odds to probabilities.

    Returns (p_over, p_under) with margin removed.
    """
    clean = decimal_odds_to_clean_probs({
        "over": odd_over,
        "under": odd_under,
    })
    return clean["over"], clean["under"]


def aggregate_probabilities(
    sources: list[dict[str, float]],
    method: str = "trimmed_mean",
    trim_pct: float = 0.1,
) -> dict[str, float]:
    """
    Aggregate probabilities from multiple sources.

    Methods:
        'mean': simple average
        'median': median value
        'trimmed_mean': remove top/bottom trim_pct before averaging

    Args:
        sources: list of {selection: probability} dicts
        method: aggregation method

    Returns:
        Aggregated {selection: probability}
    """
    if not sources:
        raise ValueError("No sources to aggregate.")

    # Collect all values per selection
    all_keys = set()
    for s in sources:
        all_keys.update(s.keys())

    aggregated: dict[str, float] = {}

    for key in all_keys:
        values = [s[key] for s in sources if key in s]

        if not values:
            continue

        if method == "mean":
            aggregated[key] = sum(values) / len(values)

        elif method == "median":
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            if n % 2 == 0:
                aggregated[key] = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
            else:
                aggregated[key] = sorted_vals[n//2]

        elif method == "trimmed_mean":
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            trim = max(1, int(n * trim_pct))
            if n > 2 * trim:
                trimmed = sorted_vals[trim:-trim]
            else:
                trimmed = sorted_vals
            aggregated[key] = sum(trimmed) / len(trimmed)

        else:
            raise ValueError(f"Unknown aggregation method: {method}")

    # Normalise
    total = sum(aggregated.values())
    if total > 0:
        aggregated = {k: v / total for k, v in aggregated.items()}

    return aggregated


def calculate_dispersion(sources: list[dict[str, float]]) -> dict[str, float]:
    """
    Calculate probability dispersion across sources.

    Low dispersion = sources agree (higher confidence)
    High dispersion = sources disagree (lower confidence, possibly news/injury)
    """
    if len(sources) < 2:
        return {}

    all_keys = set()
    for s in sources:
        all_keys.update(s.keys())

    dispersion: dict[str, float] = {}

    for key in all_keys:
        values = [s[key] for s in sources if key in s]
        if len(values) < 2:
            dispersion[key] = 0.0
            continue

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        dispersion[key] = variance ** 0.5  # std dev

    return dispersion
