import os
import sys
import time
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from src.orca.app import app

client = TestClient(app)

DEMO_TESTS = [
    {
        "name": "Rehearsed City 1: Mangaluru (Clearly SAFE)",
        "question": "Is it safe to take a small boat out near Mangaluru today?",
        "expected_verdict": "SAFE",
        "expected_risk": 18,
        "expected_location": "Mangaluru",
        "key_phrase": "calm and favorable",
    },
    {
        "name": "Rehearsed City 2: Goa (MPA-boundary CAUTION)",
        "question": "Can I fish near Goa without entering a protected zone?",
        "expected_verdict": "CAUTION",
        "expected_risk": 55,
        "expected_location": "Goa",
        "key_phrase": "Netravali Marine Sanctuary",
    },
    {
        "name": "Rehearsed City 3: Mumbai (High-wave UNSAFE)",
        "question": "Is it safe to go out in Mumbai during the storm?",
        "expected_verdict": "UNSAFE",
        "expected_risk": 88,
        "expected_location": "Mumbai",
        "key_phrase": "gale-force winds",
    },
]

def main():
    print("=" * 75)
    print("ORCA DEMO_MODE FIXTURES VERIFICATION TEST SUITE (KHA-23)")
    print("=" * 75)

    all_passed = True

    # Warm up client on healthcheck
    client.get("/")

    # 1. Test using demo_mode flag in request
    for idx, tc in enumerate(DEMO_TESTS, 1):
        print(f"\n[Test {idx}/3] {tc['name']}")
        start_time = time.perf_counter()

        response = client.post("/ask", json={
            "question": tc["question"],
            "demo_mode": True,
        })
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert response.status_code == 200
        data = response.json()

        print(f"Latency:         {elapsed_ms:.2f} ms")
        print(f"Location:        {data['location']['name']}")
        print(f"Verdict:         {data['verdict']}")
        print(f"Risk Score:      {data['riskScore']}")
        print(f"Spoken Text:\n  \"{data['explanation']}\"")

        verdict_match = (data["verdict"] == tc["expected_verdict"])
        risk_match = (data["riskScore"] == tc["expected_risk"])
        loc_match = (data["location"]["name"] == tc["expected_location"])
        phrase_match = (tc["key_phrase"].lower() in data["explanation"].lower())
        fast_latency = (elapsed_ms < 100.0)

        if verdict_match and risk_match and loc_match and phrase_match and fast_latency:
            print("Result: PASS (Instant response, exact fixture matched)")
        else:
            print("Result: FAIL")
            print(f"  verdict_match={verdict_match}, risk_match={risk_match}, loc_match={loc_match}, phrase_match={phrase_match}, fast={fast_latency}")
            all_passed = False

    # 2. Test using DEMO_MODE environment variable
    print("\n[Test 4] Verifying DEMO_MODE via Environment Variable")
    os.environ["DEMO_MODE"] = "true"
    res_env = client.post("/ask", json={
        "question": "Are conditions safe in Mangaluru?",
    })
    os.environ.pop("DEMO_MODE", None)

    data_env = res_env.json()
    if data_env.get("verdict") == "SAFE" and data_env.get("location", {}).get("name") == "Mangaluru":
        print("Result: PASS -> DEMO_MODE environment variable activated offline fixtures globally.")
    else:
        print("Result: FAIL -> DEMO_MODE environment variable not honored.")
        all_passed = False

    print("\n" + "=" * 75)
    if all_passed:
        print("ALL DEMO_MODE FIXTURE TESTS PASSED (KHA-23 ACCEPTANCE CRITERIA MET).")
        sys.exit(0)
    else:
        print("SOME DEMO_MODE TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
