import hashlib
import sys
import datetime
import subprocess
from typing import Dict, Any


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def hash_file(filepath: str) -> str:
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return "file_not_found"


def get_traceability_metadata(data_filepath: str) -> Dict[str, Any]:
    """
    Returns demonstrative metadata for traceability.
    """
    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "git_commit": get_git_commit(),
        "data_hash": hash_file(data_filepath),
    }
