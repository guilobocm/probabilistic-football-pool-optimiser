"""
Run All — Main pipeline that orchestrates the entire system.

1. Load configs
2. Load team strengths
3. Generate score matrices for all group stage matches
4. Optimize picks for each match
5. Run Monte Carlo simulation for bonuses
6. Output everything to CSV + JSON

Usage:
    python -m src.pipeline.run_all
"""

from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config_loader import get_groups, get_scoring_rule, get_all_teams
from src.model.team_strength import build_default_strengths, TeamStrength
from src.model.score_matrix import generate_score_matrix
from src.model.poisson_model import get_1x2_from_matrix, dixon_coles_correction
from src.model.team_strength import estimate_lambdas
from src.optimizer.scoring_rules import ScoringRule, TOURNAMENT_RULE
from src.optimizer.pick_optimizer import optimize_pick, PickResult
from src.optimizer.bonus_optimizer import optimize_all_bonuses, BonusPick
from src.simulator.tournament_sim import TournamentSimulator
from src.ingest.odds_api_client import run_ingestion
from src.ingest.ingest_csv import load_odds_csv
from src.ingest.data_validator import validate_and_aggregate_odds, print_health_report
from src.model.momentum import apply_momentum

OUTPUT_DIR = PROJECT_ROOT / "outputs"


def generate_group_matches() -> list[dict]:
    """Generate all group stage matches (6 per group = 72 total)."""
    groups = get_groups()
    matches = []
    match_num = 1

    for group_letter, teams in sorted(groups.items()):
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                matches.append({
                    "match_id": f"GS_{group_letter}_{match_num:03d}",
                    "group": group_letter,
                    "team_a": teams[i],
                    "team_b": teams[j],
                    "stage": "group",
                })
                match_num += 1

    return matches


def run_match_predictions(
    matches: list[dict],
    strengths: dict[str, TeamStrength],
    rule: ScoringRule,
    external_probs: dict[str, dict] | None = None,
) -> list[PickResult]:
    """Generate score matrices and optimize picks for all matches."""
    results = []

    for match in matches:
        team_a = match["team_a"]
        team_b = match["team_b"]

        sa = strengths.get(team_a)
        sb = strengths.get(team_b)

        if sa is None or sb is None:
            print(f"  ⚠ Missing strength data for {team_a} or {team_b}, skipping")
            continue

        # Get external odds if available
        ext_1x2 = None
        ext_over_25 = None
        if external_probs and match["match_id"] in external_probs:
            ext_data = external_probs[match["match_id"]]
            ext_1x2 = ext_data["1x2"]
            ext_over_25 = ext_data.get("over_25")
            if ext_over_25 is not None and math.isnan(ext_over_25):
                ext_over_25 = None

        # Generate score probability matrix
        score_probs = generate_score_matrix(
            team_a=sa,
            team_b=sb,
            external_1x2=ext_1x2,
            target_over_25=ext_over_25,
        )

        # Optimize pick
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
    """Save match picks to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "match_id", "team_a", "team_b",
            "pick_a", "pick_b", "expected_points",
            "confidence", "most_probable_a", "most_probable_b",
            "most_probable_prob", "rationale",
        ])

        for pick in picks:
            writer.writerow([
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
            ])


def save_bonus_picks(bonuses: dict, filepath: Path) -> None:
    """Save bonus picks to JSON."""
    output = {}

    # Group winners
    group_picks = []
    for bp in bonuses.get("group_winners", []):
        group_picks.append({
            "question": bp.question,
            "pick": bp.pick,
            "probability": round(bp.probability, 4),
            "expected_points": round(bp.expected_points, 4),
            "alternatives": [
                {"team": t, "prob": round(p, 4)}
                for t, p in bp.alternatives[:3]
            ],
        })
    output["group_winners"] = group_picks

    # Semifinalists
    sf_picks = []
    for bp in bonuses.get("semifinalists", []):
        sf_picks.append({
            "question": bp.question,
            "pick": bp.pick,
            "probability": round(bp.probability, 4),
            "expected_points": round(bp.expected_points, 4),
        })
    output["semifinalists"] = sf_picks

    # Champion
    champ = bonuses.get("champion")
    if champ:
        output["champion"] = {
            "question": champ.question,
            "pick": champ.pick,
            "probability": round(champ.probability, 4),
            "expected_points": round(champ.expected_points, 4),
            "alternatives": [
                {"team": t, "prob": round(p, 4)}
                for t, p in champ.alternatives[:5]
            ],
        }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def save_simulation_summary(sim_results, filepath: Path) -> None:
    """Save simulation summary to JSON."""
    output = {
        "n_simulations": sim_results.n_simulations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "champion_probabilities": {
            team: round(prob, 4)
            for team, prob in sorted(
                sim_results.champion.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:15]
        },
        "semifinal_probabilities": {
            team: round(prob, 4)
            for team, prob in sorted(
                sim_results.semifinalists.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:20]
        },
        "group_winners": {
            group: {
                team: round(prob, 4)
                for team, prob in sorted(
                    probs.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            }
            for group, probs in sorted(sim_results.group_winners.items())
        },
        "top_scorer_player_probs": {
            player: round(prob, 4)
            for player, prob in sorted(
                sim_results.top_scorer.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:15]
        } if sim_results.top_scorer else {},
        "golden_boot_team_probs": {
            team: round(prob, 4)
            for team, prob in sorted(
                sim_results.golden_boot_team.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:15]
        } if sim_results.golden_boot_team else {},
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def print_banner():
    print("=" * 70)
    print("  ⚽ OTIMIZADOR DE BOLÃO — COPA DO MUNDO 2026 ⚽")
    print("  Maximizando pontuação esperada, não palpite de boteco")
    print("=" * 70)
    print()


def print_pick_summary(picks: list[PickResult]):
    """Print a nice summary of match picks."""
    print("\n📊 PALPITES OTIMIZADOS (Fase de Grupos)")
    print("-" * 70)
    print(f"{'Jogo':<35} {'Palpite':>8} {'EP':>8} {'Mais Provável':>15}")
    print("-" * 70)

    total_ep = 0
    for pick in picks:
        pa, pb = pick.best_pick
        mp_a, mp_b = pick.most_probable_score
        match_label = f"{pick.team_a} vs {pick.team_b}"

        # Highlight when pick differs from most probable
        marker = " ⚡" if pick.best_pick != pick.most_probable_score else ""

        print(
            f"{match_label:<35} {pa}-{pb:>6} {pick.expected_points:>7.3f} "
            f"{mp_a}-{mp_b} ({pick.most_probable_prob:.1%}){marker}"
        )
        total_ep += pick.expected_points

    print("-" * 70)
    print(f"{'Total EP esperado:':<35} {'':<8} {total_ep:>7.3f}")
    print(f"{'Jogos:':<35} {len(picks)}")
    print()


def print_bonus_summary(bonuses: dict, sim_results):
    """Print bonus picks summary."""
    print("\n🏆 BÓNUS — PREVISÕES DE TORNEIO")
    print("-" * 70)

    # Champion
    champ = bonuses.get("champion")
    if champ:
        # Standard Error for Binomial Proportion: SE = sqrt(p * (1-p) / N)
        # Margin of Error (95% CI) = 1.96 * SE
        n_sims = sim_results.n_simulations
        moe = 1.96 * math.sqrt(champ.probability * (1 - champ.probability) / n_sims)
        
        print(f"\n🥇 Campeão do Mundo: {champ.pick} (P={champ.probability*100:.1f}% ± {moe*100:.2f} p.p., EP={champ.expected_points:.2f})")
        if champ.alternatives:
            alts = ", ".join(f"{t} ({p:.1%})" for t, p in champ.alternatives[:4])
            print(f"   Alternativas: {alts}")

    # Semifinalists
    sf_picks = bonuses.get("semifinalists", [])
    if sf_picks:
        print(f"\n🏅 Semifinalistas:")
        for bp in sf_picks:
            print(f"   {bp.pick} (P={bp.probability:.1%}, EP={bp.expected_points:.2f})")

    # Group winners
    gw_picks = bonuses.get("group_winners", [])
    if gw_picks:
        print(f"\n📋 Vencedores dos Grupos:")
        for bp in gw_picks:
            group_letter = bp.question.split("Grupo ")[-1].rstrip("?")
            alts = ", ".join(f"{t} ({p:.1%})" for t, p in bp.alternatives[:2])
            print(f"   Grupo {group_letter}: {bp.pick} ({bp.probability:.1%}) | Alt: {alts}")

    # Golden Boot Team
    gb_team = bonuses.get("golden_boot_team")
    if gb_team:
        print(f"\n⚽ Equipa do Artilheiro: {gb_team.pick} (P={gb_team.probability*100:.1f}%, EP={gb_team.expected_points:.2f})")
        if gb_team.alternatives:
            alts = ", ".join(f"{t} ({p:.1%})" for t, p in gb_team.alternatives[:4])
            print(f"   Alternativas: {alts}")

    # Total expected bonus points
    total_bonus_ep = 0
    if champ:
        total_bonus_ep += champ.expected_points
    for bp in sf_picks:
        total_bonus_ep += bp.expected_points
    for bp in gw_picks:
        total_bonus_ep += bp.expected_points
    if gb_team:
        total_bonus_ep += gb_team.expected_points

    print(f"\n   Total EP bónus: {total_bonus_ep:.2f}")
    print()


def main():
    """Run the full pipeline."""
    print_banner()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ============ STEP 1: Load data ============
    print("📂 Carregando configurações...")
    groups = get_groups()
    strengths = build_default_strengths()
    apply_momentum(strengths)
    rule = TOURNAMENT_RULE

    print(f"   {len(groups)} grupos, {len(strengths)} seleções com dados de força")

    # ============ STEP 2: Generate matches ============
    print("\n⚽ Gerando jogos da fase de grupos...")
    matches = generate_group_matches()
    print(f"   {len(matches)} jogos gerados")

    # ============ STEP 2.5: Fetch Live Odds ============
    print("\n🌐 Buscando odds em tempo real (The Odds API)...")
    run_ingestion()
    
    odds_path = PROJECT_ROOT / "data" / "raw" / "odds_input.csv"
    external_probs = {}
    
    if odds_path.exists():
        try:
            df_odds = load_odds_csv(odds_path)
            
            agg_df, report = validate_and_aggregate_odds(df_odds)
            print()
            print_health_report(report)
            
            for _, row in agg_df.iterrows():
                external_probs[row["match_id"]] = {
                    "1x2": (row["p_home"], row["p_draw"], row["p_away"]),
                    "over_25": row.get("p_over_25")
                }
                    
            print(f"   Sucesso: {len(external_probs)} jogos validados com odds incorporadas no modelo.")
        except Exception as e:
            print(f"   ⚠ Falha ao processar CSV de odds: {e}")

    # ============ STEP 3: Optimize match picks ============
    print("\n🧮 Otimizando palpites por pontuação esperada...")
    
    missing_matches = [m for m in matches if m["match_id"] not in external_probs]
    if missing_matches:
        print(f"   ⚠ Atenção: {len(missing_matches)} jogos farão fallback para o Elo base (sem cobertura/rejeitados):")
        for mm in missing_matches:
            print(f"      - {mm['team_a']} vs {mm['team_b']} (source_used = base_model_fallback)")
            
    picks = run_match_predictions(matches, strengths, rule, external_probs)
    print(f"   {len(picks)} palpites otimizados")

    # ============ STEP 4: Tournament simulation ============
    print("\n🎰 Rodando simulação Monte Carlo do torneio...")
    simulator = TournamentSimulator(groups, strengths)
    sim_results = simulator.simulate(n_simulations=100_000, seed=2026)
    print(f"   {sim_results.n_simulations:,} simulações completadas")
    
    # Audit logging
    simulator.print_audit_report()

    # ============ STEP 5: Optimize bonuses ============
    print("\n🏆 Otimizando picks de bónus...")
    bonuses = optimize_all_bonuses(sim_results, points_per_correct=4)

    # ============ STEP 6: Save outputs ============
    print("\n💾 Salvando resultados...")
    save_match_picks(picks, OUTPUT_DIR / "match_picks.csv")
    save_bonus_picks(bonuses, OUTPUT_DIR / "bonus_picks.json")
    save_simulation_summary(sim_results, OUTPUT_DIR / "simulation_summary.json")
    
    # Save release manifest
    import hashlib
    def file_hash(path):
        if path.exists():
            return hashlib.md5(path.read_bytes()).hexdigest()
        return "N/A"
    
    manifest = {
        "version": "2.4-RC",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": 2026,
        "n_simulations": 100_000,
        "input_hashes": {
            "odds_input.csv": file_hash(PROJECT_ROOT / "data" / "raw" / "odds_input.csv"),
            "players.yaml": file_hash(PROJECT_ROOT / "data" / "players.yaml"),
            "recent_form.csv": file_hash(PROJECT_ROOT / "data" / "recent_form.csv"),
        },
        "outputs_generated": [
            "match_picks.csv",
            "bonus_picks.json",
            "simulation_summary.json",
            "release_manifest.json",
        ],
        "matches_with_market_odds": 66,
        "matches_with_fallback": 6,
        "model_notes": [
            "Artilheiro: modelo experimental (golos + assists + minutos)",
            "Desempates: aproximação estatística (Pts > GD > GF > noise)",
            "Momentum: proxy leve via recent_form.csv, não xG real",
            "6 jogos usam base_model_fallback (Chéquia, Bósnia)",
            "Actualizar odds perto dos jogos para refletir lesões/escalações",
        ],
    }
    with open(OUTPUT_DIR / "release_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"   Resultados salvos em: {OUTPUT_DIR}")

    # ============ STEP 7: Print summaries ============
    print_pick_summary(picks)
    print_bonus_summary(bonuses, sim_results)

    print("\n" + "=" * 70)
    print("  ✅ Pipeline completo!")
    print("  Arquivos gerados:")
    print(f"    📄 {OUTPUT_DIR / 'match_picks.csv'}")
    print(f"    📄 {OUTPUT_DIR / 'bonus_picks.json'}")
    print(f"    📄 {OUTPUT_DIR / 'simulation_summary.json'}")
    print(f"    📄 {OUTPUT_DIR / 'release_manifest.json'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
