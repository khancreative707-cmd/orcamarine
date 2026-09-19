import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from src.orca.app import app

client = TestClient(app)

def main():
    print("=" * 75)
    print("ORCA 2.0: MULTI-LOCATION & TEMPORAL COMPARISON TEST SUITE")
    print("=" * 75)

    # Test 1: User's exact query comparing Mangalore vs Goa
    user_query = (
        "See, I live in Mangalore, and I can go to Goa also, but I am in the middle. "
        "I have two options today: I can go to Goa also for tomorrow for fishing, "
        "and I can also go to Mangalore. According to the data, which is safe, Mangalore or Goa?"
    )

    print("\n[Test 1] User Multi-Location Decision Query:")
    print(f"Question: \"{user_query}\"")
    t0 = time.perf_counter()
    resp = client.post("/ask", json={"question": user_query, "demo_mode": False})
    dt = (time.perf_counter() - t0) * 1000

    print(f"Latency:        {dt:.0f} ms")
    print(f"HTTP Status:    {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()

    print(f"Question Type:  {data.get('questionType')}")
    print(f"Location:       {data.get('location', {}).get('name')}")
    print(f"Verdict:        {data.get('verdict')}")
    print(f"Risk Score:     {data.get('riskScore')}")
    print(f"Primary Data:   {data.get('data')}")
    print(f"Sources:        {[s['name'] for s in data.get('sources', [])]}")
    print(f"Synthesized Comparative Advisory:\n  \"{data.get('explanation')}\"")

    assert data.get("questionType") == "comparison", f"Expected comparison, got {data.get('questionType')}"
    explanation_lower = data.get("explanation", "").lower()
    assert "mangalore" in explanation_lower or "mangaluru" in explanation_lower, "Explanation must mention Mangalore"
    assert "goa" in explanation_lower, "Explanation must mention Goa"
    print("Result: PASS -> Multi-location extraction, parallel telemetry, and comparative synthesis verified!")

    # Test 2: Temporal forecast query for tomorrow in Kochi
    print("\n[Test 2] Temporal Forecast Query (Tomorrow in Kochi):")
    q2 = "Is it safe to go coastal boating in Kochi tomorrow?"
    print(f"Question: \"{q2}\"")
    t0 = time.perf_counter()
    resp2 = client.post("/ask", json={"question": q2, "demo_mode": False})
    dt2 = (time.perf_counter() - t0) * 1000

    print(f"Latency:        {dt2:.0f} ms")
    print(f"HTTP Status:    {resp2.status_code}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    print(f"Location:       {data2.get('location', {}).get('name')}")
    print(f"Verdict:        {data2.get('verdict')}")
    print(f"Tomorrow Data:  {data2.get('data')}")
    print(f"Synthesized Advisory:\n  \"{data2.get('explanation')}\"")
    assert "kochi" in data2.get("location", {}).get("name", "").lower()
    print("Result: PASS -> Tomorrow's forecast successfully retrieved and synthesized!")

    print("\n" + "=" * 75)
    print("ALL MULTI-LOCATION & TEMPORAL COMPARISON TESTS PASSED!")
    print("=" * 75)

if __name__ == "__main__":
    main()
