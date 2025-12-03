"""
Simple test to debug search
"""
from app.search.search_engine import get_search_engine
from app.models import SearchFilter

def test_simple():
    engine = get_search_engine()

    # Test 1: Get all calls (no filter)
    print("\n🔍 TEST 1: Get all calls (no filter)")
    filter1 = SearchFilter()
    results1 = engine.search(filter=filter1, top_k=20, fields=["call_id", "date", "attendants", "summary"])

    print(f"Found {len(results1)} calls:")
    for r in results1:
        print(f"  - {r.call_id}: {r.summary[:80] if r.summary else 'No text'}...")

    # Test 2: Semantic search with lower min_score
    print("\n🔍 TEST 2: Semantic search - 'security' (min_score=0.0)")
    filter2 = SearchFilter(summaries="security")
    results2 = engine.search(filter=filter2, top_k=5, min_score=0.0, fields=["date", "call_id", "score", "summary"])

    print(f"Found {len(results2)} results:")
    for r in results2:
        print(f"  - {r.call_id} (score: {r.score:.4f})")
        print(f"    {r.summary[:100] if r.summary else 'No text'}...")

    # Test 3: Semantic search - 'customer analytics'
    print("\n🔍 TEST 3: Semantic search - 'customer analytics' (min_score=0.0)")
    filter3 = SearchFilter(summaries="customer analytics dashboard")
    results3 = engine.search(filter=filter3, top_k=3, min_score=0.0, fields=["date", "summary", "call_id", "score"])

    print(f"Found {len(results3)} results:")
    for r in results3:
        print(f"  - {r.call_id} (score: {r.score:.4f})")
        print(f"    {r.summary[:100] if r.summary else 'No text'}...")

if __name__ == "__main__":
    test_simple()
