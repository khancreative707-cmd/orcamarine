import re
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.orca.synthesis import synthesize_explanation

TEST_SCENARIOS = [
    {
        "name": "Scenario 1: SAFE sea_conditions (Mangaluru)",
        "location_name": "Mangaluru",
        "question_type": "sea_conditions",
        "verdict": "SAFE",
        "risk_score": 18,
        "reasons": [
            "Wind speed is calm at 14.2 km/h.",
            "Wave height is low at 0.8 m.",
            "Distance to nearest Marine Protected Area is 18.5 km.",
        ],
        "data": {
            "windSpeedKmh": 14.2,
            "waveHeightM": 0.8,
            "mpaDistanceKm": 18.5,
        },
    },
    {
        "name": "Scenario 2: CAUTION protected_area (Goa)",
        "location_name": "Goa",
        "question_type": "protected_area",
        "verdict": "CAUTION",
        "risk_score": 55,
        "reasons": [
            "Within 2.1 km of Netravali Marine Sanctuary boundary.",
            "Wind speed is moderate at 22.0 km/h.",
            "Wave height is moderate at 1.4 m.",
        ],
        "data": {
            "windSpeedKmh": 22.0,
            "waveHeightM": 1.4,
            "mpaDistanceKm": 2.1,
        },
    },
    {
        "name": "Scenario 3: UNSAFE storm/high waves (Mumbai)",
        "location_name": "Mumbai",
        "question_type": "sea_conditions",
        "verdict": "UNSAFE",
        "risk_score": 88,
        "reasons": [
            "Wave height exceeds safe threshold at 3.6 m.",
            "Wind speed is dangerous at 48.5 km/h.",
            "Distance to nearest Marine Protected Area is 12.0 km.",
        ],
        "data": {
            "windSpeedKmh": 48.5,
            "waveHeightM": 3.6,
            "mpaDistanceKm": 12.0,
        },
    },
]

def count_sentences(text: str) -> int:
    # Split on period/exclamation/question mark followed by whitespace or end of line (ignoring decimals like 0.8)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    return len(sentences)

def extract_allowed_numbers(scenario: dict) -> set:
    allowed = set()
    for v in scenario["data"].values():
        if v is not None:
            allowed.add(f"{v:g}")
            allowed.add(str(v))
            if isinstance(v, float) and v.is_integer():
                allowed.add(str(int(v)))
    if scenario.get("risk_score") is not None:
        allowed.add(str(scenario["risk_score"]))
    
    # Also extract any numbers present in the input reasons strings
    for r in scenario["reasons"]:
        for n in re.findall(r'\b\d+(?:\.\d+)?\b', r):
            allowed.add(n)
            try:
                val = float(n)
                allowed.add(f"{val:g}")
                if val.is_integer():
                    allowed.add(str(int(val)))
            except ValueError:
                pass
    return allowed

def main():
    print("=" * 70)
    print("ORCA SYNTHESIS PROMPT VERIFICATION TEST SUITE (KHA-19)")
    print("=" * 70)

    total = len(TEST_SCENARIOS)
    passed = 0

    for idx, sc in enumerate(TEST_SCENARIOS, 1):
        print(f"\n[Test {idx}/{total}] {sc['name']}")
        allowed_numbers = extract_allowed_numbers(sc)
        print(f"Allowed traceable numbers: {sorted(allowed_numbers)}")
        
        try:
            explanation = synthesize_explanation(
                location_name=sc["location_name"],
                question_type=sc["question_type"],
                verdict=sc["verdict"],
                reasons=sc["reasons"],
                data=sc["data"],
                risk_score=sc["risk_score"],
            )
            print(f"\nGenerated Explanation:\n\"{explanation}\"")

            # 1. Sentence count check
            num_sentences = count_sentences(explanation)
            sentence_ok = 2 <= num_sentences <= 3
            print(f"- Sentence count: {num_sentences} ({'PASS' if sentence_ok else 'FAIL: Expected 2-3'})")

            # 2. Number traceability check
            found_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', explanation)
            untraceable = []
            for n in found_numbers:
                # Normalize float representation if possible
                try:
                    norm = f"{float(n):g}"
                except ValueError:
                    norm = n
                if n not in allowed_numbers and norm not in allowed_numbers:
                    untraceable.append(n)

            traceability_ok = (len(untraceable) == 0)
            if traceability_ok:
                print(f"- Number Traceability: PASS (Numbers used: {found_numbers})")
            else:
                print(f"- Number Traceability: FAIL (Untraceable / hallucinated numbers: {untraceable})")

            # 3. Verdict alignment check
            verdict_ok = sc["verdict"].lower() in explanation.lower() or (
                sc["verdict"] == "SAFE" and "safe" in explanation.lower()
            ) or (
                sc["verdict"] == "CAUTION" and ("caution" in explanation.lower() or "advis" in explanation.lower())
            ) or (
                sc["verdict"] == "UNSAFE" and ("unsafe" in explanation.lower() or "danger" in explanation.lower() or "avoid" in explanation.lower() or "hazard" in explanation.lower())
            )
            print(f"- Verdict Alignment: {'PASS' if verdict_ok else 'WARNING: Verdict wording missing'}")

            if sentence_ok and traceability_ok and verdict_ok:
                print(f"Result: PASS")
                passed += 1
            else:
                print(f"Result: FAIL")
        except Exception as e:
            print(f"Result: ERROR -> {e.__class__.__name__}: {str(e).splitlines()[0]}")

    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print("ALL SYNTHESIS TESTS PASSED (ZERO HALLUCINATED NUMBERS).")
        sys.exit(0)
    else:
        print("SOME SYNTHESIS TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
