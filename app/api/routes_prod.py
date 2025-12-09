"""
API routes for search server
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from datetime import datetime
from typing import Optional
import time
import json

from app.models import (
    SearchRequest,
    SearchResponse,
    HealthResponse,
    EmbedRequest,
    EmbedResponse,
    StatsResponse,
    ChunkResult,
    CreateCallRequest,
    CallResponse,
    CallListResponse
)
from app import __version__
from app.search.search_engine import get_search_engine
from app.database.embeddings import get_embedding_service
from app.database.vector_db import get_vector_db
from app.database.main_db import get_main_db
from app.data_manager import get_data_manager
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.now()
    )


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Main search endpoint

    Search through conference call transcripts with various filters.

    **Parameters:**
    - **filter**: Search filters (metadata, semantic, keyword)
    - **fields**: Fields to return in results
    - **top_k**: Number of results (1-100)
    - **min_score**: Minimum relevance score (0.0-1.0)
    - **sort_by**: Sort by relevance, date, or chunk_index
    - **sort_order**: Sort order (desc or asc)

    **Returns:**
    - List of matching chunks with metadata
    - Total count and average score
    - Execution time
    """
    start_time = time.time()

    try:
        # Get search engine instance
        search_engine = get_search_engine()

        # Perform search
        results = search_engine.search(
            filter=request.filter,
            fields=request.fields,
            top_k=request.top_k,
            min_score=request.min_score,
            sort_by=request.sort_by,
            sort_order=request.sort_order
        )

        # Calculate execution time
        execution_time = int((time.time() - start_time) * 1000)

        # Calculate average score (filter out None values)
        scores = [r.score for r in results if r.score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return SearchResponse(
            results=results,
            total_found=len(results),
            avg_score=avg_score,
            execution_time_ms=execution_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")



@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get database statistics

    Returns information about the indexed data.

    **Returns:**
    - Total chunks indexed
    - Total calls
    - Index dimension
    - Index name
    """
    try:
        # Get vector database instance
        vector_db = get_vector_db()

        # Get stats from Pinecone
        vector_stats = vector_db.get_stats()
        total_vectors = vector_stats.get("total_vector_count", 0)

        # Get stats from metadata database
        metadata_db = get_main_db()
        metadata_stats = metadata_db.get_stats()

        return StatsResponse(
            total_chunks=total_vectors,
            total_calls=metadata_stats.get("total_calls", 0),
            index_dimension=settings.embedding_dimension,
            index_name=settings.pinecone_index_name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")



@router.post("/upload_json", status_code=201)
async def upload_json(request: Request, file: Optional[UploadFile] = File(None)):
    """
    Upload calls from JSON file or JSON body

    This endpoint accepts calls in two ways:
    1. As a JSON file (multipart/form-data)
    2. As JSON directly in request body

    The JSON should be an array of call objects with the following structure:
    ```json
    [
      {
        "transcript": "...",
        "summary": "...",
        "date": "YYYY-MM-DD",
        "attendants": ["Person1", "Person2"],
        "links": {...},
        "meta-data": {"duration_minutes": 30, "call_type": "..."}
      }
    ]
    ```

    **Returns:**
    - Summary of uploaded calls with success/failure counts
    """
    try:
        # Parse JSON from file or body
        if file is not None:
            raw = await file.read()
            text = raw.decode('utf-8').strip()
        else:
            body = await request.body()
            if not body:
                raise HTTPException(status_code=400, detail="No data provided")
            text = body.decode('utf-8').strip()

        # Parse JSON
        try:
            calls_data = json.loads(text)
            if not isinstance(calls_data, list):
                raise HTTPException(status_code=400, detail="JSON must be an array of call objects")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        data_manager = get_data_manager()

        results = {
            "total": len(calls_data),
            "successful": 0,
            "failed": 0,
            "errors": []
        }

        for i, call_data in enumerate(calls_data, 1):
            try:
                # Generate call_id if not provided
                call_id = call_data.get("call_id", f"call-{str(i).zfill(3)}")

                # Transform data to match our schema
                date_str = call_data.get("date", "")
                if date_str and "T" not in date_str:
                    date_str = date_str + "T14:00:00Z"

                # Add the call
                data_manager.add_call(
                    call_id=call_id,
                    full_transcript=call_data.get("transcript", ""),
                    summary=call_data.get("summary", ""),
                    date=datetime.fromisoformat(date_str.replace("Z", "+00:00")),
                    attendants=call_data.get("attendants", []),
                    topic=call_data.get("meta-data", {}).get("call_type", ""),
                    meeting_type=call_data.get("meta-data", {}).get("call_type", ""),
                    duration_minutes=call_data.get("meta-data", {}).get("duration_minutes", 0),
                    meta={
                        "links": call_data.get("links", {}),
                        "metadata": call_data.get("meta-data", {})
                    }
                )

                results["successful"] += 1
                print(f"[{i}/{len(calls_data)}] ✓ Created call: {call_id}")

            except Exception as e:
                results["failed"] += 1
                error_msg = str(e)
                results["errors"].append({
                    "index": i,
                    "call_id": call_data.get("call_id", f"call-{i}"),
                    "error": error_msg
                })
                print(f"[{i}/{len(calls_data)}] ✗ Failed: {error_msg}")

        return {
            "message": f"Bulk upload completed: {results['successful']} successful, {results['failed']} failed",
            **results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/calls/{call_id}", status_code=200)
async def delete_call(call_id: str):
    """
    Delete a call by ID

    Removes the call from both PostgreSQL and Pinecone.

    **Parameters:**
    - **call_id**: Unique call identifier

    **Returns:**
    - Success message
    """
    try:
        data_manager = get_data_manager()
        result = data_manager.delete_call(call_id)

        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Call {call_id} not found")

        return {
            "message": f"Call {call_id} deleted successfully",
            "call_id": call_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete call: {str(e)}")


@router.post("/admin/init-db", status_code=200)
async def initialize_database():
    """
    Initialize database tables

    Creates all necessary tables in PostgreSQL if they don't exist.
    Safe to run multiple times - will not affect existing data.

    **Returns:**
    - Success message with created tables
    """
    try:
        main_db = get_main_db()

        # Initialize database (creates tables if they don't exist)
        main_db.init_db()

        # Get stats to verify
        stats = main_db.get_stats()

        return {
            "message": "Database initialized successfully",
            "tables_created": ["calls"],
            "total_calls": stats.get("total_calls", 0),
            "status": "ready"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {str(e)}")


@router.delete("/admin/clear-all", status_code=200)
async def clear_all_databases():
    """
    Clear all databases (PostgreSQL and Pinecone)

    ⚠️ DANGER: This will delete ALL data from both databases!
    Use only for testing and development.

    **Returns:**
    - Success message with counts of deleted items
    """
    try:
        main_db = get_main_db()
        vector_db = get_vector_db()

        # Get stats before deletion
        stats = main_db.get_stats()
        total_calls_before = stats.get("total_calls", 0)

        vector_stats_chunks = vector_db.get_stats("chunks")
        vector_stats_summaries = vector_db.get_stats("summaries")
        total_chunks_before = vector_stats_chunks.get("total_vector_count", 0)
        total_summaries_before = vector_stats_summaries.get("total_vector_count", 0)

        # Get all calls
        calls = main_db.get_calls(limit=1000)  # Adjust limit if needed

        deleted_count = 0
        errors = []

        # Delete each call
        for call in calls:
            try:
                # Delete from vector DB (both indices)
                vector_db.delete_by_call_id(call.call_id, index_type="chunks")
                vector_db.delete_by_call_id(call.call_id, index_type="summaries")


                # Delete from PostgreSQL
                main_db.delete_call(call.call_id)
                deleted_count += 1
            except Exception as e:
                errors.append(f"Failed to delete {call.call_id}: {str(e)}")
        vector_db.delete_all(index_type="chunks")
        vector_db.delete_all(index_type="summaries")

        # Verify deletion
        stats_after = main_db.get_stats()
        total_calls_after = stats_after.get("total_calls", 0)

        return {
            "message": "Database cleared successfully",
            "deleted_calls": deleted_count,
            "calls_before": total_calls_before,
            "calls_after": total_calls_after,
            "chunks_before": total_chunks_before,
            "summaries_before": total_summaries_before,
            "errors": errors if errors else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear databases: {str(e)}")


