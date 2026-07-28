import hashlib
import hmac
import json
import sys
import re
from pathlib import Path


def fail(msg):
    print(f"Error: {msg}")
    sys.exit(1)


def is_hex_string(s, length):
    return (
        isinstance(s, str) and len(s) == length and bool(re.match(r"^[0-9a-fA-F]+$", s))
    )


def main():
    print("=== Cryptographic Revelation and Verification ===")

    SCRIPT_DIR = Path(__file__).resolve().parent
    REPO_ROOT = SCRIPT_DIR.parents[1]

    PUBLIC_COMMITMENT_PATH = REPO_ROOT / "commitments" / "world-cup-2026-pre-final.json"

    # 1. Load Public Commitment
    if not PUBLIC_COMMITMENT_PATH.exists():
        fail(f"{PUBLIC_COMMITMENT_PATH} not found.")

    try:
        pub_data = json.loads(PUBLIC_COMMITMENT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fail("Public commitment is not valid JSON.")

    # Validate schema_version, experiment and algorithm in public commitment
    if pub_data.get("schema_version") != 1:
        fail("Invalid schema_version in public commitment.")
    if pub_data.get("experiment") != "world-cup-2026-pre-final":
        fail("Invalid experiment in public commitment.")
    if pub_data.get("algorithm") != "HMAC-SHA256":
        fail("Invalid algorithm in public commitment.")

    expected_hmac = pub_data.get("commitment")
    if not is_hex_string(expected_hmac, 64):
        fail("Public commitment HMAC is invalid.")

    print(f"[1] Public Commitment Loaded (HMAC): {expected_hmac}")

    # 2. Load Private Manifest and Key from local branch
    key_path = SCRIPT_DIR / "precommit_key.hex"
    manifest_path = SCRIPT_DIR / "precommit_manifest.json"

    if not key_path.exists() or not manifest_path.exists():
        fail("Private key or manifest missing.")

    try:
        key_text = key_path.read_text(encoding="utf-8").strip()
        secret_key = bytes.fromhex(key_text)
    except ValueError:
        fail("Private key is not valid hexadecimal.")

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fail("Private manifest is not valid JSON.")

    if len(secret_key) != 32:
        fail("Private key must be 32 bytes.")

    print(f"[2] HMAC key loaded: OK ({len(secret_key)} bytes)")

    # Validate private manifest metadata
    if manifest_data.get("schema_version") != 1:
        fail("Invalid manifest schema_version.")
    if manifest_data.get("experiment") != "world-cup-2026-pre-final":
        fail("Invalid manifest experiment.")

    # 3. Canonicalize Manifest exactly as in commitment generation
    canonical_manifest = json.dumps(
        manifest_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    # 4. Compute HMAC-SHA256
    computed_hmac = hmac.new(
        secret_key,
        canonical_manifest,
        hashlib.sha256,
    ).hexdigest()

    print(f"[3] Computed HMAC-SHA256: {computed_hmac}")

    if hmac.compare_digest(computed_hmac, expected_hmac):
        print("    -> SUCCESS: HMAC MATCHES PUBLIC COMMITMENT!")
    else:
        fail("HMAC MISMATCH!")

    # 5. Verify Artifacts
    print("\n=== Verifying Attached Artifacts ===")

    artifacts = manifest_data.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 2:
        fail("Manifest must declare exactly two artifacts.")

    EXPECTED_ARTIFACTS = {
        "palpites_final.md",
        "montecarlo_final_10M.md",
    }

    names = [item.get("filename") for item in artifacts]

    if set(names) != EXPECTED_ARTIFACTS or len(set(names)) != len(names):
        fail("Unexpected or duplicate artifact filenames.")

    for artifact_meta in artifacts:
        name = artifact_meta.get("filename")
        if not isinstance(name, str) or Path(name).name != name:
            fail("Artifact filenames must not contain paths.")

        expected_sha = artifact_meta.get("sha256")
        if not is_hex_string(expected_sha, 64):
            fail(f"Invalid sha256 for artifact {name}.")

        expected_size = artifact_meta.get("size_bytes")
        if not isinstance(expected_size, int) or expected_size < 0:
            fail(f"Invalid size_bytes for artifact {name}.")

        art_path = SCRIPT_DIR / name
        if not art_path.exists():
            fail(f"Missing file: {name}")

        content = art_path.read_bytes()
        actual_size = len(content)
        actual_sha = hashlib.sha256(content).hexdigest()

        if actual_size != expected_size:
            fail(
                f"Size mismatch for {name}. Expected: {expected_size}, Actual: {actual_size}"
            )

        match = "OK" if hmac.compare_digest(actual_sha, expected_sha) else "FAIL"
        print(f"    - {name}: {match}")
        print(f"      Expected: {expected_sha}")
        print(f"      Actual:   {actual_sha}")

        if not hmac.compare_digest(actual_sha, expected_sha):
            fail(f"SHA-256 mismatch for {name}.")

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
