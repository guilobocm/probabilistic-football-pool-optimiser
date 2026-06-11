"""
The Odds API Client — Fetches live betting odds automatically.

Connects to api.the-odds-api.com to get live 1x2 odds for World Cup matches.
Requires an API key (set THE_ODDS_API_KEY in .env).

Docs: https://the-odds-api.com/liveapi/guides/v4/
"""

import os
import csv
from pathlib import Path
from typing import Any

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.config_loader import load_team_aliases, get_groups

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT_KEY = "soccer_fifa_world_cup"
MARKETS = "h2h,totals"  # 1x2 market and over/under 2.5
REGIONS = "eu,uk"  # Bookmaker regions to average

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_CSV = PROJECT_ROOT / "data" / "raw" / "odds_input.csv"


def get_api_key() -> str | None:
    """Get the API key from environment variables."""
    return os.getenv("THE_ODDS_API_KEY")


def match_team_to_canonical(api_team_name: str, alias_map: dict[str, str]) -> str:
    """Resolve an API team name to our canonical name."""
    key = api_team_name.lower().strip()
    return alias_map.get(key, api_team_name)


def identify_match_id(team_a: str, team_b: str, groups: dict[str, list[str]]) -> str | None:
    """
    Find the match_id (e.g., GS_A_001) for two teams if they are in the same group.
    Returns None if they don't play each other in the group stage.
    """
    # A bit brute-force, but perfectly fine for 72 matches
    match_num = 1
    for group_letter, teams in sorted(groups.items()):
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                ta, tb = teams[i], teams[j]
                if (team_a == ta and team_b == tb) or (team_a == tb and team_b == ta):
                    return f"GS_{group_letter}_{match_num:03d}"
                match_num += 1
    return None


def fetch_live_odds() -> list[dict[str, Any]]:
    """Fetch live odds from The Odds API."""
    api_key = get_api_key()
    if not api_key:
        print("⚠ THE_ODDS_API_KEY não configurada. Ingestão pulada.")
        return []

    print(f"🌐 Buscando odds ao vivo da API (Sport: {SPORT_KEY})...")
    
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
        print(f"✅ Recebidos {len(data)} jogos da API.")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar odds da API: {e}")
        return []


def parse_and_save_odds(api_data: list[dict[str, Any]]) -> None:
    """Parse API data and save to our CSV format."""
    if not api_data:
        return

    alias_map = load_team_aliases()
    groups = get_groups()
    
    # Prepara o diretório e ficheiro
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    
    records = []

    for game in api_data:
        home_api = game.get("home_team", "")
        away_api = game.get("away_team", "")
        
        home = match_team_to_canonical(home_api, alias_map)
        away = match_team_to_canonical(away_api, alias_map)
        
        match_id = identify_match_id(home, away, groups)
        if not match_id:
            # Not a group stage match or teams not found
            continue

        # Extract bookmakers
        bookmakers = game.get("bookmakers", [])
        for bookie in bookmakers:
            source = bookie["key"]
            markets = bookie.get("markets", [])
            for m in markets:
                if m["key"] == "h2h":
                    outcomes = m.get("outcomes", [])
                    for outcome in outcomes:
                        sel_api = outcome["name"]
                        price = outcome["price"]
                        
                        # Map selection name to 'team_a', 'team_b', 'draw'
                        if sel_api == 'Draw':
                            selection = 'draw'
                        else:
                            sel_canon = match_team_to_canonical(sel_api, alias_map)
                            if sel_canon == home:
                                selection = 'team_a'
                            elif sel_canon == away:
                                selection = 'team_b'
                            else:
                                continue # Unknown selection
                                
                        records.append({
                            "match_id": match_id,
                            "source": f"api_{source}",
                            "market": "1x2",
                            "selection": selection,
                            "decimal_odd": price,
                            "source_type": "api"
                        })
                elif m["key"] == "totals":
                    outcomes = m.get("outcomes", [])
                    for outcome in outcomes:
                        sel_api = outcome["name"] # Over or Under
                        price = outcome["price"]
                        point = outcome.get("point")
                        
                        if point == 2.5:
                            selection = sel_api.lower() # over or under
                            records.append({
                                "match_id": match_id,
                                "source": f"api_{source}",
                                "market": "totals",
                                "selection": selection,
                                "decimal_odd": price,
                                "source_type": "api"
                            })

    if not records:
        print("⚠ Nenhum jogo da API correspondente à fase de grupos foi encontrado.")
        return

    # Guarda no CSV (sobrescreve o ficheiro para ter as odds mais frescas)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["match_id", "source", "market", "selection", "decimal_odd", "source_type"])
        writer.writeheader()
        writer.writerows(records)
        
    print(f"💾 Salvos {len(records)} registos de odds no arquivo {OUTPUT_CSV.name}.")


def run_ingestion() -> None:
    """Main execution block for ingestion."""
    data = fetch_live_odds()
    if data:
        parse_and_save_odds(data)

if __name__ == "__main__":
    run_ingestion()
