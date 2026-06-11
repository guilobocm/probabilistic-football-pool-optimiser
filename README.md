# World Cup 2026 Pool Optimizer

This project is an educational probabilistic optimizer for a recreational World Cup prediction pool. It maximizes expected points under custom scoring rules using scoreline probability matrices, Monte Carlo simulation, FIFA 2026 bracket logic, calibration inputs, and transparent fallback handling. It is not a betting system.

## Methodology

The model works in several layers:
1. **Priors**: Base Elo ratings are used to estimate baseline strengths.
2. **Calibration (Optional)**: Market probabilities can be ingested via CSV to override base priors and align with realistic expectations.
3. **Score Matrices**: A Poisson-based model (with Dixon-Coles corrections) maps win/draw/loss probabilities to an exact 9x9 matrix of scoreline probabilities.
4. **Optimization**: For each group stage match, it simulates the expected points (EP) for every possible scoreline pick under the specific scoring rules of the pool.
5. **Monte Carlo Simulation**: Simulates the entire tournament (including the 495 possible combinations of best third-placed teams under FIFA Annexe C regulations) 100,000 times to determine optimal "Bonus Picks" (e.g. Champion, Semifinalists, Golden Boot team).

## Structure
- `src/`: Core logic (model, optimizer, simulator).
- `scripts/`: Utilities for pipeline auditing and checklist verification.
- `data/sample/`: Example input datasets (players, recent form).
- `outputs/sample/`: Example outputs (match picks, bonus picks, simulation summary).
- `config/`: Configuration files mapping teams, scoring rules, and tournament structure.

## Disclaimer
This project is for educational and recreational purposes only. It is not designed to provide financial advice.
