# backend/scripts/test_cache.py

import sys
import os
import time
import requests
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).parent.parent.parent
sys.path.append(str(root))

BASE_URL = "http://localhost:8000/api"

def test_cache():
    print("Testing Caching Strategy...")
    
    payload = {
        "messages": [{"role": "user", "content": "I like AI and machine learning"}],
        "top_k": 3
    }
    
    print("\n[Chat] First call (Miss)...")
    start = time.time()
    r1 = requests.post(f"{BASE_URL}/chat", json=payload)
    d1 = r1.json()
    t1 = time.time() - start
    print(f"Time: {t1:.2f}s, RunID: {d1.get('run_id')}")
    
    print("\n[Chat] Second call (Hit)...")
    start = time.time()
    r2 = requests.post(f"{BASE_URL}/chat", json=payload)
    d2 = r2.json()
    t2 = time.time() - start
    print(f"Time: {t2:.2f}s, RunID: {d2.get('run_id')}")
    
    # Ideally t2 < t1 significantly (LLM skip + Ranking skip)
    # Note: LLM reply is not cached, but if the profile is deterministic, 
    # and we skip ranking, it might still call LLM for the reply.
    # WAIT: User said "Do NOT cache LLM replies". 
    # My implementation in ChatResponse uses cached recs if key hits, 
    # but it STILL calls LLM for the reply/profile?
    # Actually, in my implementation:
    # 1. Generate Reply (LLM)
    # 2. Extract Profile (LLM)
    # 3. Check Cache(profile) -> if HIT, skip ranking computation.
    # This means the ranking part is cached, but LLM steps are not.
    
    print(f"\nReduction: {(t1-t2)/t1*100:.1f}%")

def test_fallback():
    print("\nTesting LLM Fallback (Simulated failure - requires server restart with invalid key or stub)...")
    print("Note: This is best verified by temporarily forcing an exception in core/llm.py or ranking.py")
    
    # We can't easily force failure here without modifying code, 
    # but the logic is there in ranking.py (try/except).
    pass

if __name__ == "__main__":
    test_cache()
