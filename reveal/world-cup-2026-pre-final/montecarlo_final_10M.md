# 🎲 Análise de Sensibilidade — Poisson Independente 90min
*(**10,000,000** simulações por jogo)*


## 🏆 FINAL: Spain vs Argentina

- Seed independente: 2026
- λ(Spain) = 1.2241
- λ(Argentina) = 1.1351

### Resultado em 90 min (Poisson Puro)

| Resultado | Probabilidade |
|---|---|
| Spain vence | 38.21% |
| Empate | 27.92% |
| Argentina vence | 33.87% |

### Top 10 Placares

| # | Placar | Frequência (Esperada) | Probabilidade |
|---|---|---|---|
| 1 | 1-1 | 1,312,274 | 13.12% |
| 2 | 1-0 | 1,157,298 | 11.57% |
| 3 | 0-1 | 1,072,493 | 10.72% |
| 4 | 0-0 | 946,207 | 9.46% |
| 5 | 2-1 | 803,965 | 8.04% |
| 6 | 1-2 | 744,712 | 7.45% |
| 7 | 2-0 | 706,572 | 7.07% |
| 8 | 0-2 | 608,482 | 6.08% |
| 9 | 2-2 | 457,004 | 4.57% |
| 10 | 3-1 | 327,563 | 3.28% |

### Bolão Clássico

**Palpite ótimo: 1-0** (EP = 1.10)

| # | Placar | EP |
|---|---|---|
| 1 | 1-0 | 1.10 |
| 2 | 2-1 | 1.06 |
| 3 | 3-2 | 1.00 |
| 4 | 0-1 | 0.99 |
| 5 | 4-3 | 0.98 |

### Bolão 50-35-20

**Palpite ótimo: 2-0** (EP = 13.31)

| # | Placar | EP |
|---|---|---|
| 1 | 2-0 | 13.31 |
| 2 | 1-0 | 12.78 |
| 3 | 3-0 | 12.25 |
| 4 | 2-1 | 11.80 |
| 5 | 0-2 | 11.80 |


## 🥉 3° LUGAR: France vs England

- Seed independente: 2027
- λ(France) = 1.5118
- λ(England) = 1.1601

### Resultado em 90 min (Poisson Puro)

| Resultado | Probabilidade |
|---|---|
| France vence | 45.35% |
| Empate | 25.50% |
| England vence | 29.15% |

### Top 10 Placares

| # | Placar | Frequência (Esperada) | Probabilidade |
|---|---|---|---|
| 1 | 1-1 | 1,210,794 | 12.11% |
| 2 | 1-0 | 1,044,262 | 10.44% |
| 3 | 2-1 | 915,372 | 9.15% |
| 4 | 0-1 | 802,570 | 8.03% |
| 5 | 2-0 | 790,522 | 7.91% |
| 6 | 1-2 | 703,560 | 7.04% |
| 7 | 0-0 | 692,347 | 6.92% |
| 8 | 2-2 | 530,475 | 5.30% |
| 9 | 0-2 | 464,536 | 4.65% |
| 10 | 3-1 | 462,554 | 4.63% |

### Bolão Clássico

**Palpite ótimo: 1-0** (EP = 1.24)

| # | Placar | EP |
|---|---|---|
| 1 | 1-0 | 1.24 |
| 2 | 2-1 | 1.23 |
| 3 | 3-2 | 1.16 |
| 4 | 4-3 | 1.14 |
| 5 | 5-4 | 1.13 |

### Bolão 50-35-20

**Palpite ótimo: 2-0** (EP = 15.29)

| # | Placar | EP |
|---|---|---|
| 1 | 2-0 | 15.29 |
| 2 | 3-0 | 14.43 |
| 3 | 1-0 | 14.30 |
| 4 | 2-1 | 14.06 |
| 5 | 4-0 | 13.43 |


---
📐 **Nota sobre Incerteza**: A margem de erro da simulação de Monte Carlo (10,000,000 iterações) é de ±0.0310%. Contudo, esta métrica reflete apenas o ruído de amostragem. Ela não inclui as incertezas epistêmicas do modelo (pesos das heurísticas, calibração, lesões, etc).


## Rastreabilidade e Metadados

- **Data de Geração**: `2026-07-16T17:15:00Z`
- **Git SHA (Completo)**: `fa8eb5a11c7de56acea790173012cef46ffb28fd`
- **Working Tree Suja?**: `Não`
- **Python**: `3.13.14`
- **NumPy**: `2.5.1`
- **Hash `real_results.yaml`**: `3960009b3c93b9656884500043f26e0b2eb7ab8ce4e81a2aed3645646af517fc`
- **Hash `scoring_rules.yaml`**: `29f31432014f49f32b80a7f7bdb577d3cc6275f4de6f5ded666473d03234cae1`
- **Hash `scoring_rules.py`**: `88b77c05b858b76908b5858e06551309899b2dc947ce0389accaeb783ab53bd8`
- **Hash `uv.lock`**: `32adea6b2fcd763cfd13e116bd87d165688bcdfb5ce83b67465012d044b46d1e`

### Regras Utilizadas
- **classic_rule**: `{"diff_win":3,"exact_draw":4,"exact_win":4,"trend_draw":2,"trend_win":2,"winner_and_one_team_goals":0}`
- **rule_50_35_20**: `{"diff_win":0,"exact_draw":50,"exact_win":50,"trend_draw":20,"trend_win":20,"winner_and_one_team_goals":35}`
