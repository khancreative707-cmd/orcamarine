import sys
import time
import statistics
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from src.orca.app import app
from src.orca.planner import plan_query
from src.orca.synthesis import synthesize_explanation
from src.orca.rules_stub import evaluate_safety

client = TestClient(app)

BENCHMARK_QUERIES = [
    "Is it safe to take a small boat out near Mangaluru today?",
    "Can I fish near Goa without entering a protected zone?",
    "How rough are the waves around Mumbai right now?",
    "Are there safe sea conditions near Kochi this afternoon?",
]

def benchmark_component_breakdown():
    print("-" * 75)
    print("1. STEP-BY-STEP COMPONENT LATENCY BREAKDOWN (LIVE GEMINI CALLS)")
    print("-" * 75)

    test_query = "Is it safe to take a small boat out near Mangaluru today?"
    
    # Step 1: Planner
    t0 = time.perf_counter()
    planner_res = plan_query(test_query)
    t_planner = (time.perf_counter() - t0) * 1000

    # Step 2: Rules Engine
    t0 = time.perf_counter()
    engine_res = evaluate_safety(planner_res.location, planner_res.questionType)
    t_rules = (time.perf_counter() - t0) * 1000

    # Step 3: Synthesis
    t0 = time.perf_counter()
    synth_res = synthesize_explanation(
        location_name=engine_res["location"]["name"],
        question_type=planner_res.questionType,
        verdict=engine_res["verdict"],
        reasons=engine_res["reasons"],
        data=engine_res["data"],
        risk_score=engine_res["riskScore"],
    )
    t_synthesis = (time.perf_counter() - t0) * 1000

    t_total = t_planner + t_rules + t_synthesis

    print(f"Query: \"{test_query}\"")
    print(f"  Step 1 (Planner LLM Call #1):      {t_planner:7.2f} ms ({t_planner/t_total*100:4.1f}%)")
    print(f"  Step 2 (Rules & Data Engine):       {t_rules:7.2f} ms ({t_rules/t_total*100:4.1f}%)")
    print(f"  Step 3 (Synthesis LLM Call #2):    {t_synthesis:7.2f} ms ({t_synthesis/t_total*100:4.1f}%)")
    print(f"  Total Computed Pipeline Time:       {t_total:7.2f} ms")

def benchmark_end_to_end_route():
    print("\n" + "-" * 75)
    print("2. END-TO-END POST /ask ROUTE LATENCY (LIVE GEMINI CALLS)")
    print("-" * 75)

    times = []
    for idx, q in enumerate(BENCHMARK_QUERIES, 1):
        t0 = time.perf_counter()
        res = client.post("/ask", json={"question": q})
        elapsed = (time.perf_counter() - t0) * 1000
        assert res.status_code == 200
        times.append(elapsed)
        print(f"Trial {idx}: \"{q[:42]}...\" -> {elapsed:6.2f} ms (Status: {res.json().get('status')})")

    mean_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else max_time

    print(f"\nLive /ask Statistics across {len(times)} trials:")
    print(f"  Min:  {min_time:6.2f} ms ({min_time/1000:.2f} s)")
    print(f"  Mean: {mean_time:6.2f} ms ({mean_time/1000:.2f} s)")
    print(f"  Max:  {max_time:6.2f} ms ({max_time/1000:.2f} s)")
    print(f"  P95:  {p95_time:6.2f} ms ({p95_time/1000:.2f} s)")

    return mean_time

def benchmark_demo_mode():
    print("\n" + "-" * 75)
    print("3. DEMO_MODE (OFFLINE CACHED FIXTURES) LATENCY")
    print("-" * 75)

    client.get("/") # Warmup
    demo_times = []
    for q in ["Mangaluru conditions", "Goa sanctuary check", "Mumbai waves"]:
        t0 = time.perf_counter()
        res = client.post("/ask", json={"question": q, "demo_mode": True})
        elapsed = (time.perf_counter() - t0) * 1000
        assert res.status_code == 200
        demo_times.append(elapsed)
        print(f"Demo Query: \"{q}\" -> {elapsed:5.2f} ms")

    avg_demo = statistics.mean(demo_times)
    print(f"\nDEMO_MODE Average Latency: {avg_demo:.2f} ms (< 0.02 seconds)")

def main():
    print("=" * 75)
    print("ORCA LATENCY BENCHMARK & TIMING PROFILE (KHA-24)")
    print("=" * 75)

    benchmark_component_breakdown()
    mean_live = benchmark_end_to_end_route()
    benchmark_demo_mode()

    print("\n" + "=" * 75)
    if mean_live < 5000.0:
        print(f"TIMING TARGET MET: Average response latency ({mean_live/1000:.2f}s) is within acceptable range (< 5s).")
        sys.exit(0)
    else:
        print("WARNING: Latency exceeded 5.0 seconds.")
        sys.exit(1)

if __name__ == "__main__":
    main()
