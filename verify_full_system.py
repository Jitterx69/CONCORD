import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"


def check(name, response, expected_status=200):
    if response.status_code == expected_status:
        print(f"✅ {name}: OK ({response.status_code})")
        return True
    else:
        print(f"❌ {name}: FAILED ({response.status_code})")
        print(f"   Response: {response.text}")
        return False


def verify_system():
    print("⏳ Waiting for backend to start...")
    time.sleep(5)  # Give uvicorn a moment

    # 1. Root System Map
    try:
        print("\n--- Verifying Root API Index ---")
        res = requests.get(f"{BASE_URL}/")
        if check("System Map", res):
            data = res.json()
            print(json.dumps(data, indent=2))
            if "services" not in data:
                print("❌ 'services' key missing in Root response")
                return
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        return

    # 2. Simulation (Holodeck)
    print("\n--- Verifying Simulation Engine ---")
    # Expects Body
    res = requests.post(
        f"{BASE_URL}/api/v1/simulation/session/start", json={"mode": "test"}
    )
    if check("Start Session", res):
        print(f"   Response: {res.json()}")

    # Expects Query Params
    res = requests.post(
        f"{BASE_URL}/api/v1/simulation/action",
        params={"character": "Alice", "action": "run"},
    )
    check("Process Action", res)

    # 3. Causality (Butterfly Effect)
    print("\n--- Verifying Causal Propagator ---")
    # Check trace (GET)
    res = requests.get(
        f"{BASE_URL}/api/v1/causality/trace/00000000-0000-0000-0000-000000000000"
    )
    # 404 is expected for random ID, but 200 means connection worked.
    # Actually let's assume if it returns JSON it's good.
    print(f"   Trace Response Code: {res.status_code}")

    # 4. Agents (BDI)
    print("\n--- Verifying BDI Agents ---")
    # Expects POST with Query Params (UUID and string)
    # Using a dummy UUID
    dummy_uuid = "00000000-0000-0000-0000-000000000000"
    res = requests.post(
        f"{BASE_URL}/api/v1/agents/check-consistency",
        params={"entity_id": dummy_uuid, "action": "run"},
    )
    check("Agent Consistency Check", res, expected_status=200)

    # 5. Quantum (States)
    print("\n--- Verifying Quantum States ---")
    res = requests.get(f"{BASE_URL}/api/v1/quantum/worlds")
    check("List Worlds", res, expected_status=200)


if __name__ == "__main__":
    verify_system()
