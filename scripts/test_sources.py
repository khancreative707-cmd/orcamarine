import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from src.orca.app import app

client = TestClient(app)

def main():
    print("=" * 75)
    print("ORCA SOURCE CITATION & FAILURE RESILIENCE TEST SUITE (KHA-21)")
    print("=" * 75)

    all_passed = True

    # -------------------------------------------------------------
    # Test 1: All sources healthy
    # -------------------------------------------------------------
    print("\n[Test 1] All sources healthy (Mangaluru query)")
    res1 = client.post("/ask", json={
        "question": "Is it safe to take a small boat out near Mangaluru today?",
    })
    assert res1.status_code == 200
    data1 = res1.json()
    source_names1 = [s["name"] for s in data1["sources"]]
    print(f"Metrics: {data1['data']}")
    print(f"Sources cited: {source_names1}")

    cond1 = (
        data1["data"]["windSpeedKmh"] is not None and
        data1["data"]["waveHeightM"] is not None and
        data1["data"]["mpaDistanceKm"] is not None and
        "Open-Meteo Marine API" in source_names1 and
        "Protected Planet Marine Dataset" in source_names1
    )
    if cond1:
        print("Result: PASS -> All healthy sources registered and cited.")
    else:
        print("Result: FAIL")
        all_passed = False

    # -------------------------------------------------------------
    # Test 2: Deliberately broken Marine Wave API
    # -------------------------------------------------------------
    print("\n[Test 2] Deliberately broken Marine Wave API")
    res2 = client.post("/ask", json={
        "question": "Is it safe to take a small boat out near Mangaluru today?",
        "simulate_broken_sources": ["wave"],
    })
    assert res2.status_code == 200
    data2 = res2.json()
    source_names2 = [s["name"] for s in data2["sources"]]
    print(f"Metrics: {data2['data']}")
    print(f"Sources cited: {source_names2}")
    print(f"Explanation: \"{data2['explanation']}\"")

    cond2 = (
        data2["data"]["waveHeightM"] is None and
        data2["data"]["windSpeedKmh"] is not None and
        "Open-Meteo Marine API" not in source_names2 and
        "Open-Meteo Weather API" in source_names2 and
        "Protected Planet Marine Dataset" in source_names2
    )
    if cond2:
        print("Result: PASS -> Broken Wave source disappeared from citation list; waveHeightM is null.")
    else:
        print("Result: FAIL")
        all_passed = False

    # -------------------------------------------------------------
    # Test 3: Deliberately broken MPA proximity dataset
    # -------------------------------------------------------------
    print("\n[Test 3] Deliberately broken MPA dataset")
    res3 = client.post("/ask", json={
        "question": "Can I fish near Goa without entering a protected zone?",
        "simulate_broken_sources": ["mpa"],
    })
    assert res3.status_code == 200
    data3 = res3.json()
    source_names3 = [s["name"] for s in data3["sources"]]
    print(f"Metrics: {data3['data']}")
    print(f"Sources cited: {source_names3}")
    print(f"Explanation: \"{data3['explanation']}\"")

    cond3 = (
        data3["data"]["mpaDistanceKm"] is None and
        data3["data"]["windSpeedKmh"] is not None and
        data3["data"]["waveHeightM"] is not None and
        "Protected Planet Marine Dataset" not in source_names3 and
        "Open-Meteo Marine API" in source_names3
    )
    if cond3:
        print("Result: PASS -> Broken MPA source disappeared from citation list; mpaDistanceKm is null.")
    else:
        print("Result: FAIL")
        all_passed = False

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 75)
    if all_passed:
        print("ALL SOURCE CITATION TESTS PASSED (KHA-21 ACCEPTANCE CRITERIA MET).")
        sys.exit(0)
    else:
        print("SOME SOURCE CITATION TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
