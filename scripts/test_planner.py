import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.orca.planner import plan_query

TEST_CASES = [
    {
        "name": "Sea Conditions with explicit location",
        "question": "Is it safe to take a small boat out near Mangaluru today?",
        "expected_type": "sea_conditions",
        "expected_location": "Mangaluru",
    },
    {
        "name": "Protected Area with explicit location",
        "question": "Can I fish near Goa without entering a protected zone?",
        "expected_type": "protected_area",
        "expected_location": "Goa",
    },
    {
        "name": "Missing Location (Sea conditions query)",
        "question": "Are the waves too rough for sailing right now?",
        "expected_type": "sea_conditions",
        "expected_location": None,
    },
    {
        "name": "Missing Location (Protected area query)",
        "question": "Can I drop an anchor in a marine sanctuary?",
        "expected_type": "protected_area",
        "expected_location": None,
    },
    {
        "name": "Varied phrasing: Choppy waters inquiry",
        "question": "How choppy is the water around Mumbai today?",
        "expected_type": "sea_conditions",
        "expected_location": "Mumbai",
    },
    {
        "name": "Varied phrasing: Marine sanctuary boundary inquiry",
        "question": "Are there any restricted marine conservation boundaries near Karwar?",
        "expected_type": "protected_area",
        "expected_location": "Karwar",
    },
    {
        "name": "Off-topic query with coastal city mentioned",
        "question": "What are the best hotels to stay at in Chennai?",
        "expected_type": "unsupported",
        "expected_location": "Chennai",
    },
    {
        "name": "Completely off-topic query without location",
        "question": "Can you explain how a binary search algorithm works?",
        "expected_type": "unsupported",
        "expected_location": None,
    },
]

def main():
    print("=" * 70)
    print("ORCA PLANNER PROMPT VERIFICATION TEST SUITE (KHA-18)")
    print("=" * 70)

    total = len(TEST_CASES)
    passed = 0

    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"\n[Test {idx}/{total}] {tc['name']}")
        print(f"Question: \"{tc['question']}\"")
        try:
            result = plan_query(tc["question"])
            
            # Location check: either exact match or case-insensitive contains
            loc_match = False
            if tc["expected_location"] is None:
                loc_match = (result.location is None)
            else:
                loc_match = (
                    result.location is not None and 
                    tc["expected_location"].lower() in result.location.lower()
                )

            type_match = (result.questionType == tc["expected_type"])

            if loc_match and type_match:
                print(f"Result: PASS -> location='{result.location}', questionType='{result.questionType}'")
                passed += 1
            else:
                print(f"Result: FAIL")
                print(f"  Expected: location={tc['expected_location']}, questionType='{tc['expected_type']}'")
                print(f"  Actual:   location={result.location}, questionType='{result.questionType}'")
        except Exception as e:
            print(f"Result: ERROR -> {e.__class__.__name__}: {str(e).splitlines()[0]}")

    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print("ALL TESTS PASSED SUCCESSFULLY.")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
