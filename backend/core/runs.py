# backend/core/runs.py

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Constants
RUNS_DIR = Path(__file__).parent.parent / "data" / "runs"

def create_run_snapshot(snapshot: Dict[str, Any]) -> str:
    """
    Persists a run snapshot to disk and returns its run_id.
    """
    # Ensure directory exists
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate UUID v4
    run_id = str(uuid.uuid4())
    
    # Inject ID into the payload itself for consistency
    snapshot["run_id"] = run_id

    # Add metadata
    snapshot_data = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "payload": snapshot
    }

    # Write to file
    file_path = RUNS_DIR / f"{run_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

    return run_id

def get_run_snapshot(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a run snapshot from disk by its run_id.
    """
    file_path = RUNS_DIR / f"{run_id}.json"
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None
