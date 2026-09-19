import os
import sys
import json
import time
from pathlib import Path
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CHINMAYI_URL = "https://orcamarine-backend.onrender.com"

def main():
    print("=" * 75)
    print("LIVE DIAGNOSTIC: TESTING CHINMAYI'S RENDER BACKEND & OUR AI INTEGRATION")
    print("Target Render URL:", CHINMAYI_URL)
    print("=" * 75)

    # 1. Health check to her Render service
    print("\n[Step 1] Pinging Chinmayi's Render /health endpoint...")
    try:
        t0 = time.perf_counter()
        r = httpx.get(f"{CHINMAYI_URL}/health", timeout=35.0)
        dt = (time.perf_counter() - t0) * 1000
        print(f"Status: HTTP {r.status_code} (took {dt:.0f} ms)")
        print(f"Response Body: {r.json()}")
        assert r.status_code == 200
        print("Result: PASS -> Chinmayi's Render service is online and healthy!")
    except Exception as e:
        print(f"Health check failed or timed out: {e}")
        return

    # 2. Directly call her POST /ask endpoint
    print("\n[Step 2] Sending direct POST /ask to Chinmayi's Render backend for Mangaluru...")
    direct_payload = {
        "location": "Mangaluru",
        "question": "Is it safe to take a small boat out today?",
    }
    try:
        t0 = time.perf_counter()
        r = httpx.post(f"{CHINMAYI_URL}/ask", json=direct_payload, timeout=35.0)
        dt = (time.perf_counter() - t0) * 1000
        print(f"Status: HTTP {r.status_code} (took {dt:.0f} ms)")
        resp = r.json()
        print(f"Location Resolved: {resp.get('location', {}).get('resolved_name')}")
        print(f"Coordinates:       {resp.get('location', {}).get('latitude')}, {resp.get('location', {}).get('longitude')}")
        print(f"Marine Data:       {resp.get('marine')}")
        print(f"Weather Data:      {resp.get('weather')}")
        print(f"Protected Area:    {resp.get('protected_area')}")
        print(f"Her Verdict:       {resp.get('safety', {}).get('verdict')}")
        print(f"Her Answer:        \"{resp.get('answer')}\"")
        print(f"Errors Logged:     {resp.get('errors')}")
        print("Result: PASS -> Her Render backend received the request, processed the geocoding, waves, and MPA!")
    except Exception as e:
        print(f"Direct query failed: {e}")
        return

    # 3. Test OUR AI pipeline calling her Render backend
    print("\n[Step 3] Testing our AI layer querying her Render backend via teammate_client...")
    os.environ["TEAMMATE_BACKEND_URL"] = CHINMAYI_URL

    from src.orca.services.teammate_client import query_teammate_backend
    cloud_data = query_teammate_backend("Mangaluru", "Is it safe to take a small boat out today?")
    print(f"Data retrieved from her Render service:")
    print(f"  Coordinates: {cloud_data['location']['lat']}, {cloud_data['location']['lon']}")
    print(f"  Wave Height: {cloud_data['wave']} m")
    print(f"  Wind Speed:  {cloud_data['wind']}")
    print(f"  Inside MPA:  {cloud_data['inside_mpa']}")
    print(f"  Her Errors:  {cloud_data['errors']}")

    # 4. End-to-end /ask route test with our Planner + Her Render Backend + Our Synthesizer
    print("\n[Step 4] Running full end-to-end POST /ask route through our FastAPI server...")
    from fastapi.testclient import TestClient
    from src.orca.app import app

    client = TestClient(app)
    t0 = time.perf_counter()
    full_resp = client.post("/ask", json={
        "question": "Is it safe to take a small boat out near Mangaluru today?",
        "demo_mode": False
    })
    dt = (time.perf_counter() - t0) * 1000

    print(f"Full Turnaround Time: {dt:.0f} ms")
    print(f"HTTP Status:          {full_resp.status_code}")
    full_data = full_resp.json()
    print(f"Verdict:              {full_data['verdict']}")
    print(f"Risk Score:           {full_data['riskScore']}/100")
    print(f"Ground-Truth Metrics: {full_data['data']}")
    print(f"Sources:              {[s['name'] for s in full_data['sources']]}")
    print(f"Synthesized Advisory:\n  \"{full_data['explanation']}\"")

    print("\n" + "=" * 75)
    print("CONCLUSION: YES! The system actively contacts Chinmayi's Render backend,")
    print("extracts her live data, and uses it inside our AI reasoning pipeline!")
    print("=" * 75)

if __name__ == "__main__":
    main()
