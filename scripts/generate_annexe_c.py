import json
from itertools import combinations, permutations
from pathlib import Path

def generate_annexe_c():
    """
    Generates the 495 combinations for the FIFA World Cup 2026 Round of 32
    third-place team allocations.
    
    Target Slots for Third-placed teams:
    1A, 1B, 1D, 1E, 1G, 1I, 1K, 1L
    
    Constraint:
    A third-placed team from group X cannot be allocated to slot 1X.
    
    Algorithm:
    For each of the 495 combinations of 8 groups out of 12 (A to L),
    we find the lexicographically first valid assignment of these 8 groups
    to the 8 target slots.
    """
    groups = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    target_slots = ['A', 'B', 'D', 'E', 'G', 'I', 'K', 'L']
    
    combinations_8 = list(combinations(groups, 8))
    
    annexe_c = {}
    
    for combo in combinations_8:
        # combo is a tuple of 8 groups, already sorted alphabetically
        # We need to find the first permutation of 'combo' that is valid
        # A valid permutation is one where p[i] != target_slots[i]
        
        valid_assignment = None
        for p in permutations(combo):
            valid = True
            for i in range(8):
                if p[i] == target_slots[i]:
                    valid = False
                    break
            if valid:
                valid_assignment = p
                break
                
        if not valid_assignment:
            raise ValueError(f"Could not find a valid assignment for {combo}")
            
        # Create key
        key = "-".join(sorted(combo))
        
        # Create mapping
        mapping = {f"1{target_slots[i]}": f"3{valid_assignment[i]}" for i in range(8)}
        
        annexe_c[key] = mapping
        
    # Save to JSON
    output_path = Path(__file__).resolve().parent.parent / "src" / "simulator" / "annexe_c.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(annexe_c, f, indent=4)
        
    print(f"✅ Geradas {len(annexe_c)} combinações da Annexe C em {output_path.name}.")

if __name__ == "__main__":
    generate_annexe_c()
