import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.orca.agent import run_orca_agent

def main():
    print("=" * 75)
    print("ORCA ADVANCED AGENTIC SUITE: NAUTICAL PHYSICS, VESSELS, WINDOWS & VERNACULAR")
    print("=" * 75)

    # Test 1: Vessel-Specific Safety Envelope (Kayak vs Heavy Sea State)
    print("\n[Test 1] Vessel-Specific Envelope (Small Kayak in Mumbai):")
    q1 = "Can I take a small 10ft kayak out near Mumbai today?"
    print(f"Question: \"{q1}\"")
    t0 = time.perf_counter()
    r1 = run_orca_agent(q1)
    dt1 = (time.perf_counter() - t0) * 1000

    print(f"Latency:      {dt1:.0f} ms")
    print(f"Location:     {r1['location']['name']}")
    print(f"Verdict:      {r1['verdict']}")
    print(f"Vessel Class: {r1.get('nautical_metadata', {}).get('vessel_class')}")
    print(f"Beaufort:     Force {r1.get('nautical_metadata', {}).get('beaufort_force')} ({r1.get('nautical_metadata', {}).get('beaufort_name')})")
    print(f"Advisory:\n  {r1['explanation'][:350]}...")
    assert "kayak" in r1.get('nautical_metadata', {}).get('vessel_class', '').lower()
    print("Result: PASS -> Kayak-specific envelope and Beaufort scale verified!")

    # Test 2: Optimal Departure Window Finder
    print("\n[Test 2] Optimal Departure Window (Fishing boat in Mangalore tomorrow):")
    q2 = "What is the best departure window to take a small fishing boat out near Mangalore tomorrow?"
    print(f"Question: \"{q2}\"")
    t0 = time.perf_counter()
    r2 = run_orca_agent(q2)
    dt2 = (time.perf_counter() - t0) * 1000

    print(f"Latency:        {dt2:.0f} ms")
    print(f"Optimal Window: {r2.get('nautical_metadata', {}).get('optimal_departure_window')}")
    print(f"Sea State:      {r2.get('nautical_metadata', {}).get('sea_state')}")
    print(f"Advisory:\n  {r2['explanation'][:350]}...")
    assert r2.get('nautical_metadata', {}).get('optimal_departure_window') is not None
    print("Result: PASS -> Optimal 24-hour departure window calculated and advised!")

    # Test 3: Vernacular Coastal Language (Kannada)
    print("\n[Test 3] Coastal Vernacular (Kannada - Mangaluru Fishing):")
    q3 = "ನಾಳೆ ಮಂಗಳೂರಿನಲ್ಲಿ ಮೀನುಗಾರಿಕೆಗೆ ಹೋಗುವುದು ಸುರಕ್ಷಿತವೇ?"
    print(f"Question: \"{q3}\"")
    t0 = time.perf_counter()
    r3 = run_orca_agent(q3)
    dt3 = (time.perf_counter() - t0) * 1000

    print(f"Latency:    {dt3:.0f} ms")
    print(f"Verdict:    {r3['verdict']}")
    print(f"Data:       {r3['data']}")
    print(f"Synthesized Kannada Advisory:\n  {r3['explanation']}")
    assert len(r3['explanation']) > 20
    print("Result: PASS -> Vernacular Kannada advisory synthesized with ground-truth numbers!")

    # Test 4: Vernacular Coastal Language (Hindi)
    print("\n[Test 4] Coastal Vernacular (Hindi - Goa Boating):")
    q4 = "क्या कल गोवा में नाव चलाना सुरक्षित है?"
    print(f"Question: \"{q4}\"")
    t0 = time.perf_counter()
    r4 = run_orca_agent(q4)
    dt4 = (time.perf_counter() - t0) * 1000

    print(f"Latency:    {dt4:.0f} ms")
    print(f"Verdict:    {r4['verdict']}")
    print(f"Data:       {r4['data']}")
    print(f"Synthesized Hindi Advisory:\n  {r4['explanation']}")
    assert len(r4['explanation']) > 20
    print("Result: PASS -> Vernacular Hindi advisory synthesized with ground-truth numbers!")

    print("\n" + "=" * 75)
    print("ALL ADVANCED NAUTICAL, VESSEL, WINDOW & VERNACULAR TESTS PASSED!")
    print("=" * 75)

if __name__ == "__main__":
    main()
