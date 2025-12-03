"""
Pydantic models for API requests and responses
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DateRange(BaseModel):
    """Date range filter"""
    from_date: str = Field(..., alias="from", description="Start date (YYYY-MM-DD)")
    to_date: str = Field(..., alias="to", description="End date (YYYY-MM-DD)")

    class Config:
        populate_by_name = True


class SearchFilter(BaseModel):
    """Filters for search query"""
    # Metadata filters
    call_id: Optional[str | List[str]] = Field(None, description="Specific call ID(s)")
    date: Optional[str] = Field(None, description="Exact date (YYYY-MM-DD)")
    date_range: Optional[DateRange] = Field(None, description="Date range")
    attendants: Optional[List[str]] = Field(None, description="Attendants (ANY logic)")
    meeting_type: Optional[str] = Field(None, description="Type of meeting")
    department: Optional[str] = Field(None, description="Department")

    # Semantic filters
    chunks: Optional[str] = Field(None, description="Semantic search in chunks")
    summaries: Optional[str] = Field(None, description="Semantic search in summaries")

    # Keyword filters
    contains: Optional[str | List[str]] = Field(None, description="Must contain keyword(s)")
    not_contains: Optional[List[str]] = Field(None, description="Must not contain keyword(s)")

    # Advanced filters
    speaker: Optional[str] = Field(None, description="Specific speaker")


class SearchRequest(BaseModel):
    """Main search request"""
    filter: SearchFilter = Field(default_factory=SearchFilter, description="Search filters")
    fields: List[str] = Field(
        default=["chunk_text", "call_id", "date", "score"],
        description="Fields to return in results"
    )
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score")
    sort_by: Optional[str] = Field(default=None, description="Sort by: relevance, date, chunk_index")
    sort_order: str = Field(default="desc", description="Sort order: desc or asc")


class ChunkResult(BaseModel):
    """Single chunk result"""
    call_id: Optional[str] = None
    chunk_text: Optional[str] = None
    score: Optional[float] = None
    chunk_index: Optional[int] = None
    date: Optional[str] = None
    attendants: Optional[List[str]] = None
    meeting_type: Optional[str] = None
    timestamp: Optional[str] = None
    speaker: Optional[str] = None

    # Allow extra fields
    class Config:
        extra = "allow"


class SearchResponse(BaseModel):
    """Search response with results and metadata"""
    results: List[ChunkResult]
    total_found: int = Field(description="Total results found (before top_k limit)")
    avg_score: float = Field(description="Average relevance score")
    execution_time_ms: int = Field(description="Query execution time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime


class EmbedRequest(BaseModel):
    """Request to generate embedding"""
    text: str = Field(..., description="Text to embed")


class EmbedResponse(BaseModel):
    """Embedding response"""
    embedding: List[float]
    dimension: int
    model: str


class StatsResponse(BaseModel):
    """Database statistics"""
    total_chunks: int
    total_calls: int
    index_dimension: int
    index_name: str


# ========== Call Management Models ==========

class CreateCallRequest(BaseModel):
    """Request to create a new call record"""
    call_id: str = Field(..., description="Unique call identifier")
    full_transcript: str = Field(..., description="Complete transcript text")
    summary: str = Field(..., description="Brief summary of the call")
    date: datetime = Field(..., description="Date and time of the call")
    attendants: List[str] = Field(..., description="List of participant names")
    topic: Optional[str] = Field(None, description="Call topic/title")
    meeting_type: Optional[str] = Field(None, description="Type of meeting")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    chunks_count: int = Field(default=0, description="Number of chunks")


class CallResponse(BaseModel):
    """Response with call details"""
    call_id: Optional[str] = None
    full_transcript: Optional[str] = None
    summary: Optional[str] = None
    date: Optional[str] = None
    attendants: Optional[List[str]] = None
    topic: Optional[str] = None
    meeting_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None
    chunks_count: Optional[int] = None
    created_at: Optional[str] = None
    processed_at: Optional[str] = None
    updated_at: Optional[str] = None


class CallListResponse(BaseModel):
    """Response with list of calls"""
    calls: List[CallResponse]
    total: int
    limit: int
    offset: int