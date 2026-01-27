"""
Test search functionality with loaded data
"""
from app.search.search_engine import get_search_engine
from app.models import SearchFilter, DateRange

def print_results(title, results):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        if hasattr(result, 'call_id') and result.call_id:
            print(f"{i}. Call ID: {result.call_id}")
        if hasattr(result, 'score') and result.score:
            print(f"   Score: {result.score:.4f}")
        if hasattr(result, 'date') and result.date:
            print(f"   Date: {result.date}")
        if hasattr(result, 'attendants') and result.attendants:
            print(f"   Attendants: {', '.join(result.attendants)}")
        if hasattr(result, 'meeting_type') and result.meeting_type:
            print(f"   Type: {result.meeting_type}")
        if result.chunk_text:
            preview = result.chunk_text[:150] + "..." if len(result.chunk_text) > 150 else result.chunk_text
            print(f"   Text: {preview}")
        print()

def test_search():
    engine = get_search_engine()

    # Test 1: Search by summary - security related
    print("\n🔍 TEST 1: Semantic search - 'security vulnerabilities and authentication'")
    filter1 = SearchFilter(
        summaries="security vulnerabilities and authentication"
    )
    results1 = engine.search(
        filter=filter1,
        top_k=3,
        min_score=0.25,
        fields=["date", "attendants", "meeting_type"]
    )
    print_results("Semantic search - security", results1)

    # Test 2: Search by summary - performance related
    print("\n🔍 TEST 2: Semantic search - 'performance optimization and database queries'")
    filter2 = SearchFilter(
        summaries="performance optimization and database queries"
    )
    results2 = engine.search(
        filter=filter2,
        top_k=3,
        min_score=0.25,
        fields=["date", "attendants"]
    )
    print_results("Semantic search - performance", results2)

    # Test 3: Metadata filter - specific attendant
    print("\n🔍 TEST 3: Metadata filter - attendant 'Max'")
    filter3 = SearchFilter(
        attendants=["Max"]
    )
    results3 = engine.search(
        filter=filter3,
        top_k=10,
        fields=["date", "attendants", "meeting_type"]
    )
    print_results("Metadata filter - Max", results3)

    # Test 4: Date range filter
    print("\n🔍 TEST 4: Date range filter - October 2025")
    filter4 = SearchFilter(
        date_range=DateRange(
            from_date="2025-10-01",
            to_date="2025-10-31"
        )
    )
    results4 = engine.search(
        filter=filter4,
        top_k=10,
        fields=["date", "attendants", "meeting_type"]
    )
    print_results("Date range - October 2025", results4)

    # Test 5: Combined filter - semantic + metadata
    print("\n🔍 TEST 5: Combined - semantic search + attendant filter")
    filter5 = SearchFilter(
        summaries="API design and architecture",
        attendants=["Robert"]
    )
    results5 = engine.search(
        filter=filter5,
        top_k=5,
        min_score=0.3,
        fields=["date", "attendants"]
    )
    print_results("Combined - API + Robert", results5)

    # Test 6: Meeting type filter
    print("\n🔍 TEST 6: Metadata filter - meeting type 'planning'")
    filter6 = SearchFilter(
        meeting_type="planning"
    )
    results6 = engine.search(
        filter=filter6,
        top_k=10,
        fields=["date", "attendants", "meeting_type"]
    )
    print_results("Meeting type - planning", results6)

if __name__ == "__main__":
    test_search()