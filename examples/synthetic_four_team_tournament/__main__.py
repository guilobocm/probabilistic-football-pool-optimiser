import csv
from pathlib import Path
from src.pool_optimizer.scoring import ScoringRule
from src.pool_optimizer.poisson_baseline import generate_probability_matrix
from src.pool_optimizer.optimizer import get_expected_points_matrix, find_optimal_prediction
from src.pool_optimizer.simulation import simulate_matches
from src.pool_optimizer.traceability import get_traceability_metadata
import json

def load_teams(filepath: str):
    teams = {}
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams[row['team']] = {
                'attack': float(row['attack_strength']),
                'defense': float(row['defense_strength'])
            }
    return teams

def main():
    data_path = Path("data/sample/teams.csv")
    teams = load_teams(str(data_path))
    
    # Define a scoring rule: 3 for exact, 1 for outcome, 2 for outcome + goal diff
    rule = ScoringRule(exact_score=3, correct_outcome=1, correct_goal_difference=2)
    
    print("--- Synthetic Tournament ---")
    team_names = list(teams.keys())
    
    for i in range(len(team_names)):
        for j in range(i + 1, len(team_names)):
            home = team_names[i]
            away = team_names[j]
            
            prob_matrix = generate_probability_matrix(
                teams[home]['attack'], teams[home]['defense'],
                teams[away]['attack'], teams[away]['defense']
            )
            
            ep_matrix = get_expected_points_matrix(prob_matrix, rule)
            opt_home, opt_away = find_optimal_prediction(ep_matrix)
            
            print(f"Match: {home} vs {away}")
            print(f"Optimal Prediction (Max Expected Points): {opt_home} - {opt_away}")
            
            # Show a quick simulation
            sims = simulate_matches(prob_matrix, num_simulations=10)
            print(f"Sample from 10 Monte Carlo sims: {sims[:3]}...")
            print("-" * 30)
            
    print("\n--- Traceability Metadata ---")
    metadata = get_traceability_metadata(str(data_path))
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()
