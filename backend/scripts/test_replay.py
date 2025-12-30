# backend/scripts/test_replay.py

import sys
import os
import requests
import json
import uuid

# Add backend to path for imports if needed, but we'll use requests to hit the running server
BASE_URL = "http://localhost:8000/api"

def test_run_replay():
    print("Testing Run Replay...")
    
    # 1. Call /api/chat
    chat_payload = {
        "messages": [
            {"role": "user", "content": "I am interested in video games."}
        ],
        "top_k": 3
    }
    
    print(f"Calling {BASE_URL}/chat...")
    try:
        resp = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        resp.raise_for_status()
        chat_data = resp.json()
    except Exception as e:
        print(f"Error calling /api/chat: {e}")
        return

    run_id = chat_data.get("run_id")
    if not run_id:
        print("FAILED: No run_id found in /api/chat response.")
        return
    
    print(f"SUCCESS: Got run_id: {run_id}")

    # 2. Call /api/runs/{run_id}
    print(f"Calling {BASE_URL}/runs/{run_id}...")
    try:
        resp = requests.get(f"{BASE_URL}/runs/{run_id}")
        resp.raise_for_status()
        run_data = resp.json()
    except Exception as e:
        print(f"Error calling /api/runs: {e}")
        return

    persisted_run_id = run_data.get("run_id")
    if persisted_run_id == run_id:
        print("SUCCESS: Replay data matches original run_id.")
    else:
        print(f"FAILED: Replay run_id mismatch. Expected {run_id}, got {persisted_run_id}")
        return

    # 3. Check payload structure
    if "payload" in run_data and "reply" in run_data["payload"]:
        print("SUCCESS: Replay payload contains expected fields.")
    else:
        print("FAILED: Replay payload missing required fields.")
        return

    print("\nALL TESTS PASSED!")

if __name__ == "__main__":
    test_run_replay()
