"""
The Odds API client — fetch live football odds automatically.

Connects to api.the-odds-api.com to retrieve 1X2 and total-goals markets for
FIFA World Cup matches. Set THE_ODDS_API_KEY in the environment or .env file.

Documentation: https://the-odds-api.com/liveapi/guides/v4/
"""

import csv
import os
from pathlib import Path
from typing import Any

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from src.config_loader import get_groups, load_team_aliases

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT_KEY = "soccer_fifa_world_cup"
MARKETS = "h2h,totals"
REGIONS = "eu,uk"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_CSV = PROJECT_ROOT / "data" / "raw" / "odds_input.csv"


def get_api_key() -> str | None:
    """Return The Odds API key from the environment."""
    return os.getenv("THE_ODDS_API_KEY")


def match_team_to_canonical(api_team_name: str, alias_map: dict[str, str]) -> str:
    """Resolve an API team label to the repository's canonical team name."""
    key = api_team_name.lower().strip()
    return alias_map.get(key, api_team_name)


def identify_match_id(
    team_a: str,
    team_b: str,
    groups: dict[str, list[str]],
) -> str | None:
    """Return the group-stage match identifier for two teams in the same group."""
    match_num = 1
    for group_letter, teams in sorted(groups.items()):
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                candidate_a, candidate_b = teams[i], teams[j]
                if (team_a == candidate_a and team_b == candidate_b) or (
                    team_a == candidate_b and team_b == candidate_a
                ):
                    return f"GS_{group_letter}_{match_num:03d}"
                match_num += 1
    return None


def fetch_live_odds() -> list[dict[str, Any]]:
    """Fetch live odds from The Odds API."""
    api_key = get_api_key()
    if not api_key:
        print("⚠ THE_ODDS_API_KEY is not configured; skipping API ingestion.")
        return []

    print(f"🌐 Fetching live odds from The Odds API (sport: {SPORT_KEY})...")

    url = f"{ODDS_API_BASE}/sports/{SPORT_KEY}/odds"
    params = {
        "apiKey": api_key,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": "decimal",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Received {len(data)} matches from the API.")
        return data
    except requests.exceptions.RequestException as exc:
        print(f"❌ Could not fetch odds from the API: {exc}")
        return []


def parse_and_save_odds(api_data: list[dict[str, Any]]) -> None:
    """Parse an API response and save it in the repository's CSV schema."""
    if not api_data:
        return

    alias_map = load_team_aliases()
    groups = get_groups()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    records = []

    for game in api_data:
        home_api = game.get("home_team", "")
        away_api = game.get("away_team", "")

        home = match_team_to_canonical(home_api, alias_map)
        away = match_team_to_canonical(away_api, alias_map)

        match_id = identify_match_id(home, away, groups)
        if not match_id:
            continue

        for bookmaker in game.get("bookmakers", []):
            source = bookmaker["key"]
            for market in bookmaker.get("markets", []):
                if market["key"] == "h2h":
                    for outcome in market.get("outcomes", []):
                        selection_api = outcome["name"]
                        price = outcome["price"]

                        if selection_api == "Draw":
                            selection = "draw"
                        else:
                            selection_canonical = match_team_to_canonical(
                                selection_api,
                                alias_map,
                            )
                            if selection_canonical == home:
                                selection = "team_a"
                            elif selection_canonical == away:
                                selection = "team_b"
                            else:
                                continue

                        records.append(
                            {
                                "match_id": match_id,
                                "source": f"api_{source}",
                                "market": "1x2",
                                "selection": selection,
                                "decimal_odd": price,
                                "source_type": "api",
                            }
                        )

                elif market["key"] == "totals":
                    for outcome in market.get("outcomes", []):
                        selection_api = outcome["name"]
                        price = outcome["price"]
                        point = outcome.get("point")

                        if point == 2.5:
                            records.append(
                                {
                                    "match_id": match_id,
                                    "source": f"api_{source}",
                                    "market": "totals",
                                    "selection": selection_api.lower(),
                                    "decimal_odd": price,
                                    "source_type": "api",
                                }
                            )

    if not records:
        print("⚠ No API fixtures matched the configured group-stage schedule.")
        return

    fieldnames = [
        "match_id",
        "source",
        "market",
        "selection",
        "decimal_odd",
        "source_type",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"💾 Saved {len(records)} odds records to {OUTPUT_CSV.name}.")


def run_ingestion() -> None:
    """Fetch, normalise, and save the latest supported odds markets."""
    data = fetch_live_odds()
    if data:
        parse_and_save_odds(data)


if __name__ == "__main__":
    run_ingestion()
