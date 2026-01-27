"""
Test script to verify search engine works with use cases from project_idea.md

This script tests the following scenarios:
1. "Что Джон говорил на последней конференции?"
2. "Какие проблемы с API обсуждались в марте?"
3. Meeting Intelligence queries
4. Knowledge Base queries
"""

import sys
from datetime import datetime, timedelta
from app.models import SearchFilter, DateRange, SearchRequest
from app.search.search_engine import get_search_engine
from app.database.main_db import get_main_db
from app.database.vector_db import get_vector_db


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_results(results, title: str = "Results"):
    """Pretty print search results"""
    print(f"\n{title}:")
    print(f"{'─'*80}")
    if not results:
        print("  (No results found)")
        return

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Call ID: {result.call_id}")
        if hasattr(result, 'score') and result.score:
            print(f"   Score: {result.score:.4f}")
        if hasattr(result, 'date') and result.date:
            print(f"   Date: {result.date}")
        if hasattr(result, 'attendants') and result.attendants:
            print(f"   Attendants: {', '.join(result.attendants)}")
        if hasattr(result, 'meeting_type') and result.meeting_type:
            print(f"   Type: {result.meeting_type}")
        if hasattr(result, 'chunk_text') and result.chunk_text:
            chunk_preview = result.chunk_text[:150] + "..." if len(result.chunk_text) > 150 else result.chunk_text
            print(f"   Content: {chunk_preview}")
        if hasattr(result, 'chunk_index') and result.chunk_index is not None:
            print(f"   Chunk Index: {result.chunk_index}")
    print(f"{'─'*80}")


def test_use_case_1_iteration_1():
    """
    Use Case 1, Iteration 1: Find last meeting with Max

    Query: "Что Max говорил на последней встрече по статусу проекта?"

    Expected: Find the most recent project status meeting where Max attended
    """
    print_section("USE CASE 1 - ITERATION 1: Find Last Project Status Meeting with Max")

    search_engine = get_search_engine()

    search_filter = SearchFilter(
        attendants=["Max"],
        meeting_type="project_status"
    )

    results = search_engine.search(
        filter=search_filter,
        fields=["call_id", "date", "summary", "attendants", "meeting_type"],
        sort_by="date",
        sort_order="desc",
        top_k=1
    )

    print_results(results, "Latest project status meeting with Max")

    # Extract call_id for iteration 2
    if results:
        return results[0].call_id
    return None


def test_use_case_1_iteration_2(call_id: str):
    """
    Use Case 1, Iteration 2: Get all content about analytics and dashboard

    Query: Get all chunks discussing analytics and dashboard in the identified call

    Expected: All relevant chunks in chronological order
    """

    if not call_id:
        print("\n⚠️  Skipping iteration 2 - no call_id from iteration 1")
        return

    print_section("USE CASE 1 - ITERATION 2: Get Analytics Dashboard Discussion")

    search_engine = get_search_engine()

    search_filter = SearchFilter(
        call_id=[call_id],
        chunks="analytics dashboard customer progress"  # semantic search
    )

    results = search_engine.search(
        filter=search_filter,
        fields=["call_id", "chunk_text", "chunk_index", "score"],
        sort_by="chunk_index",  # chronological order
        top_k=50
    )

    print_results(results, f"Analytics dashboard discussion in call {call_id}")


def test_use_case_2_iteration_1():
    """
    Use Case 2, Iteration 1: Find security and vulnerability discussions in October

    Query: "Какие проблемы безопасности обсуждались в октябре?"

    Expected: Chunks discussing security issues in October
    """
    print_section("USE CASE 2 - ITERATION 1: Security Issues in October")

    search_engine = get_search_engine()

    # Get October date range (using 2025 based on actual data)
    search_filter = SearchFilter(
        date_range=DateRange(**{
            "from": "2025-10-01",
            "to": "2025-10-31"
        }),
        chunks="security vulnerabilities issues problems penetration test",
        contains="security"  # keyword must be present
    )

    results = search_engine.search(
        filter=search_filter,
        fields=["chunk_text", "call_id", "date", "attendants", "score"],
        top_k=20,
        min_score=0.5
    )

    print_results(results, "Security issues in October (chunks)")

    # Extract unique call_ids
    if results:
        call_ids = list(set([r.call_id for r in results]))
        return call_ids
    return []


def test_use_case_2_iteration_2(call_ids: list):
    """
    Use Case 2, Iteration 2: Get summaries for structure

    Query: Get summaries of calls where security issues were discussed

    Expected: Call summaries to provide context for each discussion
    """
    if not call_ids:
        print("\n⚠️  Skipping iteration 2 - no call_ids from iteration 1")
        return

    print_section("USE CASE 2 - ITERATION 2: Get Summaries for Context")

    search_engine = get_search_engine()

    search_filter = SearchFilter(
        call_id=call_ids,
        summaries="security review vulnerabilities"
    )

    results = search_engine.search(
        filter=search_filter,
        fields=["summary", "call_id", "date", "attendants", "topic", "meeting_type"],
        sort_by="date"
    )

    print_results(results, "Call summaries for security discussions")


def test_metadata_first_strategy():
    """
    Strategy: Metadata-first (for known parameters)

    Query: "Найти обсуждение архитектуры с Robert в ноябре"

    Expected: Fast, targeted results
    """
    print_section("STRATEGY TEST: Metadata-First")

    search_engine = get_search_engine()

    search_filter = SearchFilter(
        date_range=DateRange(**{
            "from": "2025-11-01",
            "to": "2025-11-30"
        }),
        attendants=["Robert"],
        meeting_type="architecture_review",
        chunks="architecture design system"
    )

    results = search_engine.search(
        filter=search_filter,
        fields=["call_id", "date", "attendants", "chunk_text", "score"],
        top_k=10
    )

    print_results(results, "Metadata-first strategy results")


def test_content_first_strategy():
    """
    Strategy: Content-first (for open questions)

    Query: "Где упоминались проблемы с уведомлениями?"

    Expected: Semantic search across all data
    """
    print_section("STRATEGY TEST: Content-First")

    search_engine = get_search_engine()

    search_filter = SearchFilter(
        chunks="notification system problems issues polling"
    )

    results = search_engine.search(
        filter=search_filter,
        fields=["chunk_text", "call_id", "date", "attendants", "score"],
        top_k=15,
        min_score=0.4
    )

    print_results(results, "Content-first strategy results")


def test_two_stage_strategy():
    """
    Strategy: Two-stage (combined)

    Query: "Что обсуждалось про quarterly планирование?"

    Stage 1: Summary-level search
    Stage 2: Chunk-level details
    """
    print_section("STRATEGY TEST: Two-Stage (Summary + Chunks)")

    search_engine = get_search_engine()

    # Stage 1: Find relevant calls via summaries
    print("\nStage 1: Summary-level search...")
    search_filter_stage1 = SearchFilter(
        meeting_type="quarterly_planning",
        summaries="quarterly planning accomplishments"
    )

    stage1_results = search_engine.search(
        filter=search_filter_stage1,
        fields=["call_id", "summary", "date", "attendants"],
        top_k=5
    )

    print_results(stage1_results, "Stage 1: Relevant calls (summaries)")

    # Stage 2: Get detailed chunks from found calls
    if stage1_results:
        call_ids = [r.call_id for r in stage1_results]

        print("\nStage 2: Detailed chunk search in found calls...")
        search_filter_stage2 = SearchFilter(
            call_id=call_ids,
            chunks="accomplishments goals objectives timeline"
        )

        stage2_results = search_engine.search(
            filter=search_filter_stage2,
            fields=["chunk_text", "call_id", "chunk_index", "score"],
            sort_by="relevance",
            top_k=10
        )

        print_results(stage2_results, "Stage 2: Detailed chunks")


def check_database_status():
    """Check if databases have data"""
    print_section("DATABASE STATUS CHECK")

    try:
        # Check metadata DB
        main_db = get_main_db()
        stats = main_db.get_stats()

        print("Metadata Database (PostgreSQL):")
        print(f"  Total calls: {stats.get('total_calls', 0)}")
        print(f"  Total chunks: {stats.get('total_chunks', 0)}")
        print(f"  Oldest call: {stats.get('oldest_call', 'N/A')}")
        print(f"  Newest call: {stats.get('newest_call', 'N/A')}")

        # Check vector DB
        vector_db = get_vector_db()
        chunks_stats = vector_db.get_stats("chunks")
        summaries_stats = vector_db.get_stats("summaries")

        print(f"\nVector Database (Pinecone):")
        print(f"  Chunks index vectors: {chunks_stats.get('total_vector_count', 0)}")
        print(f"  Summaries index vectors: {summaries_stats.get('total_vector_count', 0)}")

        # Check if we have data
        has_data = (stats.get('total_calls', 0) > 0 and
                   chunks_stats.get('total_vector_count', 0) > 0)

        if not has_data:
            print("\n⚠️  WARNING: No data found in databases!")
            print("   Please run data ingestion script first.")
            return False

        print("\n✅ Databases contain data, ready for testing")
        return True

    except Exception as e:
        print(f"\n❌ Error checking database status: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all test cases"""
    print("\n" + "="*80)
    print("  SEARCH ENGINE USE CASE TESTING")
    print("  Testing implementation against project_idea.md scenarios")
    print("="*80)

    # Check database status first
    if not check_database_status():
        print("\n❌ Aborting tests - databases are not ready")
        return

    try:
        # Use Case 1: Find Max's latest project status meeting
        call_id = test_use_case_1_iteration_1()
        test_use_case_1_iteration_2(call_id)

        # Use Case 2: Security issues in October
        call_ids = test_use_case_2_iteration_1()
        test_use_case_2_iteration_2(call_ids)

        # Strategy tests
        test_metadata_first_strategy()
        test_content_first_strategy()
        test_two_stage_strategy()

        print_section("TEST SUMMARY")
        print("✅ All use case tests completed!")
        print("\nNote: Results depend on your data.")
        print("If no results were found, ensure your test data matches the queries.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()