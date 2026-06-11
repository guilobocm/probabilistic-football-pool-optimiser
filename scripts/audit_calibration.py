import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.model.lambda_calibrator import calibrate_lambdas
from src.model.poisson_model import dixon_coles_correction, get_1x2_from_matrix

import numpy as np

# A list of 20 representative games (Elo La, Elo Lb, Market P(H), P(D), P(A))
TEST_CASES = [
    # Top Favoritos vs Zebras
    ("Argentina", "Curaçao", 3.1, 0.4, (0.85, 0.10, 0.05)),
    ("França", "Haiti", 2.9, 0.5, (0.80, 0.15, 0.05)),
    ("Espanha", "Cabo Verde", 2.8, 0.6, (0.75, 0.18, 0.07)),
    
    # Fortes vs Médios
    ("Brasil", "Escócia", 2.2, 0.8, (0.60, 0.25, 0.15)),
    ("Inglaterra", "Gana", 2.0, 0.9, (0.55, 0.28, 0.17)),
    ("Alemanha", "Equador", 1.9, 1.0, (0.50, 0.30, 0.20)),
    
    # Equilibrados / Clássicos
    ("México", "Coreia do Sul", 1.4, 1.3, (0.38, 0.32, 0.30)),
    ("Portugal", "Colômbia", 1.6, 1.4, (0.42, 0.30, 0.28)),
    ("Holanda", "Suécia", 1.5, 1.4, (0.40, 0.31, 0.29)),
    ("Japão", "Suíça", 1.2, 1.3, (0.33, 0.33, 0.34)),
    
    # Jogos com grande divergência de Elo vs Mercado (Apostas contra Elo)
    # Elo diz que A é favorito, Mercado diz que é Equilibrado
    ("EUA", "Paraguai", 2.1, 0.9, (0.40, 0.30, 0.30)), 
    # Elo diz Equilibrado, Mercado diz Favorito A
    ("Bélgica", "Irã", 1.3, 1.2, (0.65, 0.22, 0.13)),
    
    # Underdogs extremos pelo Mercado, mas Elo mais alto
    ("Austrália", "Turquia", 1.5, 1.1, (0.20, 0.25, 0.55)),
    
    # Jogos com altíssima ou baixíssima propensão de golo (Under/Over)
    # Baixo golo (Elo = 1.0 vs 0.9 = 1.9 total)
    ("Senegal", "Iraque", 1.0, 0.9, (0.45, 0.35, 0.20)),
    # Alto golo (Elo = 2.5 vs 2.0 = 4.5 total)
    ("Áustria", "Jordânia", 2.5, 2.0, (0.55, 0.20, 0.25)),
]

def top_5_scores(matrix):
    flat = matrix.flatten()
    indices = np.argsort(flat)[-5:][::-1]
    results = []
    for idx in indices:
        i, j = np.unravel_index(idx, matrix.shape)
        results.append(f"{i}-{j} ({matrix[i, j]*100:.1f}%)")
    return " | ".join(results)

def run_audit():
    print("="*120)
    print("🔎 AUDITORIA DE SENSIBILIDADE DA CALIBRAÇÃO (Total Goals Prior w=0.05)")
    print("="*120)
    
    for team_a, team_b, la_elo, lb_elo, market_1x2 in TEST_CASES:
        prior_total = la_elo + lb_elo
        
        # Calculate Elo matrix
        elo_mat = dixon_coles_correction(la_elo, lb_elo, -0.10, 10)
        elo_mat = elo_mat / np.sum(elo_mat)
        elo_1x2 = get_1x2_from_matrix(elo_mat)
        
        # Calibrate
        la_cal, lb_cal = calibrate_lambdas(market_1x2, la_elo, lb_elo, -0.10, 10)
        final_total = la_cal + lb_cal
        
        # Calculate Final matrix
        cal_mat = dixon_coles_correction(la_cal, lb_cal, -0.10, 10)
        cal_mat = cal_mat / np.sum(cal_mat)
        cal_1x2 = get_1x2_from_matrix(cal_mat)
        
        print(f"\n⚽ {team_a} vs {team_b}")
        print(f"  [ELO BASE] La={la_elo:.2f}, Lb={lb_elo:.2f} | P_Elo={elo_1x2[0]*100:.1f}% / {elo_1x2[1]*100:.1f}% / {elo_1x2[2]*100:.1f}%")
        print(f"  [MERCADO]                        | P_Mkt={market_1x2[0]*100:.1f}% / {market_1x2[1]*100:.1f}% / {market_1x2[2]*100:.1f}%")
        print(f"  [CALIBR.]  La={la_cal:.2f}, Lb={lb_cal:.2f} | P_Cal={cal_1x2[0]*100:.1f}% / {cal_1x2[1]*100:.1f}% / {cal_1x2[2]*100:.1f}%")
        print(f"  [TOTAIS]   Prior Goals={prior_total:.2f} -> Final Goals={final_total:.2f} (Delta: {final_total - prior_total:+.2f})")
        print(f"  [TOP 5 Antes]  {top_5_scores(elo_mat)}")
        print(f"  [TOP 5 Depois] {top_5_scores(cal_mat)}")
        
if __name__ == "__main__":
    run_audit()
