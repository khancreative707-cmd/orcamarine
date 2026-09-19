import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from src.orca.app import app

client = TestClient(app)

TEST_CASES = [
    {
        "name": "Case 1: Sea conditions with location (Mangaluru)",
        "payload": {"question": "Is it safe to take a small boat out near Mangaluru today?"},
        "expected_status": "ok",
        "expected_type": "sea_conditions",
        "check_verdict": True,
        "check_explanation": True,
    },
    {
        "name": "Case 2: Protected area with location (Goa)",
        "payload": {"question": "Can I fish near Goa without entering a protected zone?"},
        "expected_status": "ok",
        "expected_type": "protected_area",
        "check_verdict": True,
        "check_explanation": True,
    },
    {
        "name": "Case 3: Missing location",
        "payload": {"question": "Are the waves too rough for sailing right now?"},
        "expected_status": "missing_location",
        "expected_type": "sea_conditions",
        "check_verdict": False,
        "check_explanation": True,
    },
    {
        "name": "Case 4: Unsupported topic",
        "payload": {"question": "What is the capital of France?"},
        "expected_status": "unsupported",
        "expected_type": "unsupported",
        "check_verdict": False,
        "check_explanation": True,
    },
]

def main():
    print("=" * 70)
    print("ORCA POST /ask ROUTE INTEGRATION TEST SUITE (KHA-20)")
    print("=" * 70)

    total = len(TEST_CASES)
    passed = 0

    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"\n[Test {idx}/{total}] {tc['name']}")
        print(f"POST /ask payload: {tc['payload']}")

        response = client.post("/ask", json=tc["payload"])
        if response.status_code != 200:
            print(f"FAIL: HTTP {response.status_code} - {response.text}")
            continue

        data = response.json()
        print(f"HTTP Status: 200 OK")
        print(f"Response Status: {data.get('status')}")
        print(f"Question Type:   {data.get('questionType')}")
        print(f"Verdict:         {data.get('verdict')}")
        print(f"Explanation:     \"{data.get('explanation')}\"")

        # Validation assertions
        status_match = (data.get("status") == tc["expected_status"])
        type_match = (data.get("questionType") == tc["expected_type"])
        has_explanation = bool(data.get("explanation") and len(data["explanation"]) > 15)

        verdict_ok = True
        if tc["check_verdict"]:
            verdict_ok = data.get("verdict") in ["SAFE", "CAUTION", "UNSAFE"]
            data_ok = data.get("data") is not None and "windSpeedKmh" in data["data"]
            loc_ok = data.get("location") is not None and "lat" in data["location"]
        else:
            verdict_ok = (data.get("verdict") is None)
            data_ok = (data.get("data") is None)
            loc_ok = (data.get("location") is None)

        if status_match and type_match and has_explanation and verdict_ok and data_ok and loc_ok:
            print("Result: PASS (Strictly matches CONTRACT.md)")
            passed += 1
        else:
            print("Result: FAIL")
            print(f"  status_match={status_match}, type_match={type_match}, has_explanation={has_explanation}, verdict_ok={verdict_ok}, data_ok={data_ok}, loc_ok={loc_ok}")

    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print("ALL /ask ROUTE INTEGRATION TESTS PASSED.")
        sys.exit(0)
    else:
        print("SOME /ask ROUTE TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
