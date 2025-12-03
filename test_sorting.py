"""
Test sorting functionality
"""
from app.search.search_engine import get_search_engine
from app.models import SearchFilter, DateRange

def test_sorting():
    engine = get_search_engine()

    # Test 1: Sort by relevance (default - descending)
    print("\n" + "="*70)
    print("TEST 1: Sort by relevance (desc) - default")
    print("="*70)

    results1 = engine.search(
        filter=SearchFilter(summaries="meeting project"),
        top_k=5,
        min_score=0.0,
        fields=["call_id", "summary", "date", "attendants", "score"],
        sort_by="relevance",
        sort_order="desc"
    )

    print(f"Found {len(results1)} results (sorted by score DESC):\n")
    for i, r in enumerate(results1, 1):
        print(f"{i}. {r.call_id} - Score: {r.score:.4f}")
        print(f"   Date: {r.date}")
        print(f"   Text: {r.summary[:]}...\n")

    # Test 2: Sort by relevance ascending
    print("\n" + "="*70)
    print("TEST 2: Sort by relevance (asc)")
    print("="*70)
    filter2 = SearchFilter(summaries="meeting project")
    results2 = engine.search(
        filter=filter2,
        top_k=5,
        min_score=0.0,
        fields=["date", "score"],
        sort_by="relevance",
        sort_order="asc"
    )

    print(f"Found {len(results2)} results (sorted by score ASC):\n")
    for i, r in enumerate(results2, 1):
        print(f"{i}. {r.call_id} - Score: {r.score:.4f}")
        print(f"   Date: {r.date}\n")

    # Test 3: Sort by date descending (newest first)
    print("\n" + "="*70)
    print("TEST 3: Sort by date (desc) - newest first")
    print("="*70)
    filter3 = SearchFilter(
        date_range=DateRange(from_date="2025-09-01", to_date="2025-12-31")
    )
    results3 = engine.search(
        filter=filter3,
        top_k=10,
        fields=["date", "attendants", "meeting_type", "score"],
        sort_by="date",
        sort_order="desc"
    )

    print(f"Found {len(results3)} results (sorted by date DESC):\n")
    for i, r in enumerate(results3, 1):
        print(f"{i}. {r.call_id}")
        print(f"   Date: {r.date}")
        print(f"   Score: {r.score:.4f}")
        print(f"   Type: {r.meeting_type}\n")

    # Test 4: Sort by date ascending (oldest first)
    print("\n" + "="*70)
    print("TEST 4: Sort by date (asc) - oldest first")
    print("="*70)
    filter4 = SearchFilter(
        date_range=DateRange(from_date="2025-09-01", to_date="2025-12-31")
    )
    results4 = engine.search(
        filter=filter4,
        top_k=10,
        fields=["date", "meeting_type"],
        sort_by="date",
        sort_order="asc"
    )

    print(f"Found {len(results4)} results (sorted by date ASC):\n")
    for i, r in enumerate(results4, 1):
        print(f"{i}. {r.call_id}")
        print(f"   Date: {r.date}")
        print(f"   Type: {r.meeting_type}\n")

    # Test 5: Combined semantic search + date sorting
    print("\n" + "="*70)
    print("TEST 5: Semantic search with date sorting (desc)")
    print("="*70)
    filter5 = SearchFilter(summaries="security architecture performance")
    results5 = engine.search(
        filter=filter5,
        top_k=5,
        min_score=0.15,
        fields=["date", "summary", "meeting_type", "score"],
        sort_by="date",
        sort_order="desc"
    )

    print(f"Found {len(results5)} results (semantic + sorted by date DESC):\n")
    for i, r in enumerate(results5, 1):
        print(f"{i}. {r.call_id}")
        print(f"   Score: {r.score:.4f}")
        print(f"   Date: {r.date}")
        print(f"   Type: {r.meeting_type}")
        print(f"   Text: {r.summary[:100]}...\n")

if __name__ == "__main__":
    test_sorting()
