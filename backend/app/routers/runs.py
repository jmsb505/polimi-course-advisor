# backend/app/routers/runs.py

from fastapi import APIRouter, HTTPException
from ...core.runs import get_run_snapshot

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
)

@router.get("/{run_id}")
async def get_run_endpoint(run_id: str):
    """
    Retrieve a persisted run snapshot by its run_id.
    """
    snapshot = get_run_snapshot(run_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Run snapshot {run_id} not found.")
    
    return snapshot["payload"]
