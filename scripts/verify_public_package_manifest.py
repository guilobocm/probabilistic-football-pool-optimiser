"""Verify that the files distributed in the public package match their declared hashes."""

import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_sha256(path: Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest_path = PROJECT_ROOT / "postmortem" / "provenance" / "public_package_manifest.json"
    package_root = manifest_path.parent.parent
    
    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path.relative_to(PROJECT_ROOT)}")
        return 1

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in manifest: {e}")
        return 1

    copied_artifacts = manifest.get("copied_artifacts", {})
    if not isinstance(copied_artifacts, dict) or not copied_artifacts:
        print("Error: No copied_artifacts object found in manifest.")
        return 1

    errors = 0
    print("=== Verifying Public Package Manifest ===")
    
    for relative_path, expected_hash in copied_artifacts.items():
        if ".." in relative_path or relative_path.startswith("/"):
            print(f"❌ INVALID PATH: {relative_path} (path traversal detected)")
            errors += 1
            continue
            
        if not isinstance(expected_hash, str) or len(expected_hash) != 64 or not all(c in "0123456789abcdefABCDEF" for c in expected_hash):
            print(f"❌ INVALID HASH FORMAT: {relative_path} ({expected_hash})")
            errors += 1
            continue

        file_path = package_root / relative_path
        if not file_path.is_file():
            print(f"❌ MISSING: {relative_path}")
            errors += 1
            continue

        actual_hash = get_sha256(file_path)
        if actual_hash != expected_hash:
            print(f"❌ MISMATCH: {relative_path}")
            print(f"   Expected: {expected_hash}")
            print(f"   Actual:   {actual_hash}")
            errors += 1
        else:
            print(f"✅ OK: {relative_path}")

    if errors > 0:
        print(f"\nManifest verification failed with {errors} error(s).")
        return 1

    print("\nAll public package artifacts verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
