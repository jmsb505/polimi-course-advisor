# backend/core/cache.py

import json
import hashlib
from typing import Any, Dict, List, Optional
from collections import deque

def normalize_student_profile(profile: dict) -> dict:
    """
    Returns a canonical version of the student profile for stable hashing.
    - Sorts lists
    - Lowercases strings in lists
    - Removes empty fields
    """
    if not profile:
        return {}

    normalized = {}
    for key, value in profile.items():
        if value is None or value == "" or value == []:
            continue
        
        if isinstance(value, list):
            # Dedupe and sort
            processed = sorted(list(set(str(v).strip().lower() for v in value if v)))
            if processed:
                normalized[key] = processed
        elif isinstance(value, str):
            normalized[key] = value.strip().lower()
        else:
            normalized[key] = value
            
    return normalized

def profile_cache_key(profile: dict, params: dict) -> str:
    """
    Generates a unique SHA256 key for a profile and optional ranking parameters.
    """
    norm_profile = normalize_student_profile(profile)
    # Combine profile and params into a single stable string
    data = {
        "profile": norm_profile,
        "params": {k: v for k, v in sorted(params.items())}
    }
    payload = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class RankingCache:
    """
    Simple FIFO bounded cache for ranking results.
    """
    def __init__(self, max_size: int = 128):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._order = deque()

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            # Update existing (don't move in FIFO)
            self._cache[key] = value
            return

        if len(self._cache) >= self.max_size:
            # Evict oldest
            oldest = self._order.popleft()
            del self._cache[oldest]

        self._cache[key] = value
        self._order.append(key)

# Global singleton
ranking_cache = RankingCache(max_size=128)
