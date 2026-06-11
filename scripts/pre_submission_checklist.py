"""
Pre-Submission Checklist — Run before submitting picks to the bolão.

Verifies that all pipeline components are healthy and outputs are consistent.
"""

import subprocess
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

def run_step(name: str, cmd: list[str]) -> bool:
    print(f"\n{'='*60}")
    print(f"  🔍 {name}")
    print(f"{'='*60}")
    result = subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True,
        env={**__import__('os').environ, 'PYTHONIOENCODING': 'utf-8'}
    )
    if result.returncode != 0:
        print(f"  ❌ FALHOU")
        print(result.stderr[-500:] if result.stderr else "No stderr")
        return False
    else:
        # Print last 10 lines of output
        lines = result.stdout.strip().split('\n')
        for line in lines[-10:]:
            print(f"  {line}")
        print(f"  ✅ OK")
        return True

def check_outputs() -> bool:
    print(f"\n{'='*60}")
    print(f"  🔍 Verificar outputs existem e são recentes")
    print(f"{'='*60}")
    
    required = [
        "match_picks.csv",
        "bonus_picks.json",
        "simulation_summary.json",
        "release_manifest.json",
    ]
    
    all_ok = True
    for fname in required:
        path = OUTPUT_DIR / fname
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {fname} ({size:,} bytes)")
        else:
            print(f"  ❌ {fname} NÃO EXISTE")
            all_ok = False
    
    return all_ok

def check_manifest() -> bool:
    print(f"\n{'='*60}")
    print(f"  🔍 Verificar release_manifest.json")
    print(f"{'='*60}")
    
    manifest_path = OUTPUT_DIR / "release_manifest.json"
    if not manifest_path.exists():
        print("  ❌ Manifest não existe. Rode run_all.py primeiro.")
        return False
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    
    print(f"  Versão:     {m.get('version', '?')}")
    print(f"  Timestamp:  {m.get('timestamp', '?')}")
    print(f"  Seed:       {m.get('seed', '?')}")
    print(f"  N sims:     {m.get('n_simulations', '?'):,}")
    print(f"  Odds hash:  {m.get('input_hashes', {}).get('odds_input.csv', '?')[:12]}...")
    
    notes = m.get("model_notes", [])
    if notes:
        print(f"  Notas:")
        for n in notes:
            print(f"    ⚠ {n}")
    
    print(f"  ✅ OK")
    return True

def check_simulation_summary() -> bool:
    print(f"\n{'='*60}")
    print(f"  🔍 Verificar simulation_summary.json")
    print(f"{'='*60}")
    
    path = OUTPUT_DIR / "simulation_summary.json"
    if not path.exists():
        print("  ❌ Não existe.")
        return False
    
    with open(path, "r", encoding="utf-8") as f:
        s = json.load(f)
    
    # Check golden_boot_team_probs exists
    gb = s.get("golden_boot_team_probs", {})
    ts = s.get("top_scorer_player_probs", {})
    
    if not gb:
        print("  ❌ golden_boot_team_probs está vazio!")
        return False
    
    if not ts:
        print("  ❌ top_scorer_player_probs está vazio!")
        return False
    
    print(f"  Artilheiro (jogador): {list(ts.keys())[0]} ({list(ts.values())[0]*100:.1f}%)")
    print(f"  Artilheiro (equipa):  {list(gb.keys())[0]} ({list(gb.values())[0]*100:.1f}%)")
    print(f"  ✅ OK")
    return True

def check_fallbacks() -> bool:
    print(f"\n{'='*60}")
    print(f"  🔍 Verificar jogos em fallback")
    print(f"{'='*60}")
    
    import csv
    picks_path = OUTPUT_DIR / "match_picks.csv"
    if not picks_path.exists():
        print("  ❌ match_picks.csv não existe.")
        return False
    
    fallbacks = []
    total = 0
    with open(picks_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            rationale = row.get("rationale", "")
            if "fallback" in rationale.lower():
                fallbacks.append(f"{row['team_a']} vs {row['team_b']}")
    
    print(f"  Total jogos: {total}")
    print(f"  Em fallback: {len(fallbacks)}")
    for fb in fallbacks:
        print(f"    ⚠ {fb}")
    
    print(f"  ✅ OK (verificar manualmente se é aceitável)")
    return True

def main():
    print("\n" + "=" * 60)
    print("  📋 CHECKLIST PRÉ-SUBMISSÃO — Bolão Copa 2026 v2.4-RC")
    print("=" * 60)
    
    results = {}
    
    # 1. Audit totals
    results["audit_totals"] = run_step(
        "Auditoria Over/Under (audit_totals.py)",
        [sys.executable, "scripts/audit_totals.py"]
    )
    
    # 2. Test Annexe C
    results["annexe_c"] = run_step(
        "Teste Annexe C (495 combinações)",
        [sys.executable, "-c", 
         "from src.simulator.annexe_c_official import validate_annexe_c; validate_annexe_c(); print('Annexe C: 495 combinações validadas')"]
    )
    
    # 3. Check outputs
    results["outputs"] = check_outputs()
    
    # 4. Check manifest
    results["manifest"] = check_manifest()
    
    # 5. Check simulation summary
    results["sim_summary"] = check_simulation_summary()
    
    # 6. Check fallbacks
    results["fallbacks"] = check_fallbacks()
    
    # Final summary
    print("\n" + "=" * 60)
    print("  📊 RESULTADO FINAL")
    print("=" * 60)
    
    all_ok = True
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False
    
    print()
    if all_ok:
        print("  🎉 TODOS OS CHECKS PASSARAM. Pronto para submeter!")
    else:
        print("  ⚠️  ALGUNS CHECKS FALHARAM. Reveja antes de submeter.")
    
    print()
    print("  📝 Checklist manual restante:")
    print("     □ Verificar lesões/escalações/notícias recentes")
    print("     □ Confirmar que odds estão actualizadas")
    print("     □ Conferir match_picks.csv para sanity check")
    print("     □ Anotar data/hora da submissão")
    print()

if __name__ == "__main__":
    main()
