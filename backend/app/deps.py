# backend/app/deps.py

import json
from pathlib import Path
from typing import Any, List, Dict, Optional

from .models import CourseDetail

# NOTE: Using build_course_graph from core.graph as implemented in Phase 2
from ..core.graph import build_course_graph
# Import Course dataclass for type conversion
from ..core.models import Course
from ..core.pagerank import global_pagerank

# Resolve backend/ directory (one level above app/)
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
COURSES_PATH = DATA_DIR / "courses.json"

_courses_cache: Optional[List[Dict[str, Any]]] = None
_graph_cache: Any = None
_global_pagerank_cache: Optional[Dict[str, float]] = None


def _load_courses_from_disk() -> List[Dict[str, Any]]:
    if not COURSES_PATH.exists():
        raise FileNotFoundError(f"courses.json not found at: {COURSES_PATH}")
    with COURSES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("courses.json is expected to be a list of course objects.")
    return data


def init_data() -> None:
    """
    Initialize in-memory data caches (courses + graph).
    Called once at app startup.
    """
    global _courses_cache, _graph_cache, _global_pagerank_cache
    _courses_cache = _load_courses_from_disk()
    
    # Convert dicts to Course objects for graph building
    course_objects = []
    for item in _courses_cache:
        # Reconstruct Course object from dict
        # Similar logic to load_courses in core/models.py
        ssd_raw = item.get("ssd", []) or []
        ssd_list = [str(s).strip() for s in ssd_raw if s] if isinstance(ssd_raw, list) else [str(ssd_raw).strip()]
        
        c_obj = Course(
            code=str(item.get("code", "")).strip(),
            name=str(item.get("name", "")).strip(),
            cfu=float(item.get("cfu", 0)),
            semester=int(item.get("semester", 0)),
            language=str(item.get("language", "") or "UNKNOWN").strip().upper(),
            group=str(item.get("group", "") or "UNKNOWN").strip(),
            ssd=ssd_list,
            description=str(item.get("description", "") or "").strip(),
            raw=item
        )
        course_objects.append(c_obj)

    _graph_cache = build_course_graph(course_objects)

    # Compute global centrality once
    print("[startup] Computing global PageRank...", flush=True)
    _global_pagerank_cache = global_pagerank(_graph_cache)
    print(f"[startup] Global PageRank entries: {len(_global_pagerank_cache)}", flush=True)


def get_courses_raw() -> List[Dict[str, Any]]:
    """
    Low-level accessor returning raw dicts as loaded from JSON.
    Raises if init_data() was not called.
    """
    if _courses_cache is None:
        raise RuntimeError("Course data not initialized. Call init_data() at startup.")
    return _courses_cache


def get_courses_as_models() -> List[CourseDetail]:
    """
    Convenience helper to get courses as Pydantic models.
    Description and alpha_group_last are mapped if present.
    """
    raw = get_courses_raw()
    return [CourseDetail(**item) for item in raw]


def get_graph() -> Any:
    """
    Return the in-memory course graph built at startup.
    """
    if _graph_cache is None:
        raise RuntimeError("Graph not initialized. Call init_data() at startup.")
    return _graph_cache


def get_global_pagerank() -> Dict[str, float]:
    """
    Return the precomputed global PageRank scores.
    """
    if _global_pagerank_cache is None:
        raise RuntimeError("Global PageRank not initialized. Call init_data() at startup.")
    return _global_pagerank_cache
