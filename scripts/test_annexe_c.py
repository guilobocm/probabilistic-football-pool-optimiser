import json
import random
from pathlib import Path


def run_tests():
    annexe_path = (
        Path(__file__).resolve().parent.parent / "src" / "simulator" / "annexe_c.json"
    )

    with open(annexe_path, "r", encoding="utf-8") as f:
        annexe_c = json.load(f)

    print("Running automated tests for Annexe C...\n")

    # 3. annexe_c.json has 495 entries.
    assert len(annexe_c) == 495, f"Error: Has {len(annexe_c)} entries instead of 495."
    print("✅ Rule 3: Contains exactly 495 entries.")

    target_slots = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]

    for key, mapping in annexe_c.items():
        # 4. Each entry has exactly 8 slots
        assert sorted(list(mapping.keys())) == sorted(target_slots), (
            f"Error in key {key}: Invalid slots."
        )

        # 5. Each entry uses exactly 8 distinct third-place teams
        thirds_used = list(mapping.values())
        assert len(set(thirds_used)) == 8, (
            f"Error in key {key}: Third-place teams are not unique."
        )

        # 6. No slot receives a third-place team from the same group as the corresponding winner
        for slot, third in mapping.items():
            winner_group = slot[1]
            third_group = third[1]
            assert winner_group != third_group, (
                f"Error in key {key}: Slot {slot} plays against {third} (same group!)."
            )

    print("✅ Rule 4: Each entry has exactly the required 8 slots.")
    print("✅ Rule 5: Each entry uses exactly 8 distinct third-place teams.")
    print("✅ Rule 6: No slot receives a third-place team from the winner's group.")
    print("✅ Rule 8: All 495 combinations passed the automatic validations.\n")

    print(
        "For Rule 7, we need to compare with the official PDF. Here are 10 randomly generated combinations:"
    )
    keys = list(annexe_c.keys())
    random.seed(42)
    sample_keys = random.sample(keys, 10)
    for k in sample_keys:
        print(f"[{k}] -> {annexe_c[k]}")


if __name__ == "__main__":
    run_tests()
