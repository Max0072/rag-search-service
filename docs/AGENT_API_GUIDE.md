# Search API Guide for Iterative RAG Agent

## Overview

This API provides unified search capabilities for conference call transcripts with hybrid search (semantic + metadata filtering). Designed for iterative RAG agents that need to progressively refine queries and gather context.

**Base URL:** `http://localhost:8000/api/v1`

---

## Core Concepts

### Two-Level Search Strategy

1. **Summary-level search** - Fast overview, find relevant calls
2. **Chunk-level search** - Detailed exploration within specific calls

### Available Fields

You control what data is returned by specifying `fields`:

```json
{
  "call_id": "Unique call identifier",
  "date": "Call date (ISO format)",
  "attendants": ["List of participants"],
  "meeting_type": "Type of meeting",
  "summary": "Full summary text (for summary search)",
  "full_transcript": "Complete transcript (for any search)",
  "chunk_text": "Chunk content (for chunk search)",
  "chunk_index": "Position in transcript",
  "score": "Relevance score (0.0-1.0)",
  "speaker": "Speaker name",
  "timestamp": "Timestamp in transcript"
}
```

---

## Iteration 1: Overview Search (Summaries)

**Goal:** Find which calls are relevant to the user's question.

### Request Pattern

```bash
POST /search
Content-Type: application/json

{
  "filter": {
    "summaries": "notification system architecture WebSocket SSE"
  },
  "fields": ["call_id", "summary", "date", "attendants", "meeting_type", "score"],
  "top_k": 5
}
```

### When to Use
- Initial exploration
- Broad questions ("What was discussed about X?")
- Finding relevant meetings
- Understanding context across multiple calls

### Response

```json
{
  "results": [
    {
      "call_id": "call-005",
      "summary": "Architecture Review: Notification System Redesign...",
      "date": "2025-11-12T16:00:00",
      "attendants": ["Robert", "Nina", "Kevin", "Sophia", "Marcus"],
      "meeting_type": "architecture_review",
      "score": 0.68
    }
  ],
  "total_found": 5,
  "avg_score": 0.62,
  "execution_time_ms": 1420
}
```

**Interpretation:**
- High score (0.6+) = Very relevant
- Medium score (0.4-0.6) = Potentially relevant
- Low score (<0.4) = Marginally relevant

---

## Iteration 2: Detailed Search (Chunks)

**Goal:** Find specific details, quotes, or technical information.

### Request Pattern

```bash
POST /search

{
  "filter": {
    "call_id": ["call-005"],  # Narrow to relevant calls from Iteration 1
    "chunks": "SSE WebSocket decision reasoning trade-offs"
  },
  "fields": ["call_id", "chunk_text", "score", "date"],
  "top_k": 10
}
```

### When to Use
- Need specific quotes or details
- Looking for technical specifics
- Want to understand reasoning
- Need context around decisions

### Response

```json
{
  "results": [
    {
      "call_id": "call-005",
      "chunk_text": "Robert: Based on everything we've discussed, here's what I'm thinking: we go with Sophia's SSE approach for now. It gives us real-time notifications with manageable complexity and timeline...",
      "score": 0.72,
      "date": "2025-11-12T16:00:00"
    }
  ],
  "total_found": 10,
  "avg_score": 0.65,
  "execution_time_ms": 850
}
```

---

## Iteration 3: Get Full Context

**Goal:** Retrieve complete transcript or summary for final answer synthesis.

### Option A: Include in Search Results

```bash
POST /search

{
  "filter": {
    "call_id": ["call-005"],
    "summaries": "notification system"
  },
  "fields": ["call_id", "summary", "full_transcript", "date"],
  "top_k": 1
}
```

### Option B: Batch Fetch Multiple Calls

```bash
POST /search

{
  "filter": {
    "call_id": ["call-001", "call-002", "call-005"]
  },
  "fields": ["call_id", "summary", "full_transcript", "date", "attendants"],
  "top_k": 10
}
```

**Note:** When using metadata-only filters (no `chunks` or `summaries`), results have `score: null`.

---

## Common Search Patterns

### Pattern 1: Who said what?

```json
{
  "filter": {
    "attendants": ["Max", "Savva"],
    "chunks": "Max Savva backend API progress"
  },
  "fields": ["call_id", "chunk_text", "attendants", "date"],
  "top_k": 5
}
```

### Pattern 2: Time-based search

```json
{
  "filter": {
    "date_range": {
      "from": "2025-10-01",
      "to": "2025-10-31"
    },
    "chunks": "security vulnerabilities SQL injection"
  },
  "top_k": 10
}
```

### Pattern 3: Technical deep-dive

```json
{
  "filter": {
    "meeting_type": "architecture_review",
    "chunks": "WebSocket SSE comparison pros cons"
  },
  "fields": ["call_id", "chunk_text", "full_transcript", "score"],
  "top_k": 5
}
```

### Pattern 4: Cross-call analysis

```json
{
  "filter": {
    "summaries": "database performance optimization"
  },
  "fields": ["call_id", "summary", "date", "meeting_type", "score"],
  "top_k": 10
}
```

Then analyze patterns across multiple calls.

---

## Filter Reference

### Metadata Filters (Fast, cheap)

```json
{
  "filter": {
    "call_id": "call-001" | ["call-001", "call-002"],
    "date": "2025-11-05",
    "date_range": {"from": "2025-10-01", "to": "2025-10-31"},
    "attendants": ["Max", "Savva"],  // ANY logic
    "meeting_type": "project_status",
    "speaker": "Max"
  }
}
```

### Semantic Filters (Slower, expensive)

```json
{
  "filter": {
    "chunks": "semantic query for detailed search",
    "summaries": "semantic query for overview search"
  }
}
```

**⚠️ Important:** Cannot use both `chunks` and `summaries` in the same query.

### Keyword Filters

```json
{
  "filter": {
    "contains": "WebSocket" | ["WebSocket", "SSE"],
    "not_contains": ["deprecated", "obsolete"]
  }
}
```

---

## Sorting & Filtering

### Sort Options

```json
{
  "sort_by": null | "relevance" | "date" | "chunk_index",
  "sort_order": "desc" | "asc"
}
```

**Default:** `sort_by: null` (no sorting, original order)

**When to use:**
- `"relevance"` - When using semantic search (chunks/summaries)
- `"date"` - Chronological analysis
- `"chunk_index"` - Reading transcript in order
- `null` - Metadata-only queries or when order doesn't matter

### Score Filtering

```json
{
  "min_score": 0.5,  // Filter out low-relevance results
  "top_k": 10        // Limit results
}
```

---

## Decision Tree for Agent

```
User Question
    │
    ├─ Broad/Overview → Use SUMMARIES
    │   ├─ High scores (0.6+)? → Answer from summaries
    │   └─ Need more detail? → Go to chunks in top calls
    │
    ├─ Specific Detail → Use CHUNKS
    │   ├─ Know which calls? → Filter by call_id
    │   └─ Don't know? → Search all, then filter top calls
    │
    └─ Metadata Query → Use metadata filters only
        └─ Need text? → Add fields: ["summary", "full_transcript"]
```

---

## Example: Multi-Iteration Flow

### User asks: "Why was SSE chosen over WebSockets?"

**Iteration 1: Find relevant call**
```json
POST /search
{
  "filter": {"summaries": "SSE WebSocket notification system decision"},
  "fields": ["call_id", "summary", "date", "score"],
  "top_k": 3
}
```

**Result:** Found `call-005` with score 0.68

**Iteration 2: Get decision reasoning**
```json
POST /search
{
  "filter": {
    "call_id": ["call-005"],
    "chunks": "SSE WebSocket decision reasoning Robert"
  },
  "fields": ["chunk_text", "score"],
  "top_k": 5
}
```

**Result:** Found 5 chunks with decision reasoning

**Iteration 3: Get full context if needed**
```json
POST /search
{
  "filter": {"call_id": ["call-005"]},
  "fields": ["summary", "full_transcript"],
  "top_k": 1
}
```

**Result:** Complete summary showing all 3 proposals and final decision

---

## Best Practices

### ✅ DO

1. **Start broad, then narrow**
   - Use summaries first
   - Then search chunks in relevant calls

2. **Use call_id filtering**
   - After finding relevant calls, filter by their IDs
   - Reduces search space and improves relevance

3. **Request only needed fields**
   - Smaller responses = faster processing
   - `full_transcript` is large, only request when needed

4. **Adjust top_k based on iteration**
   - Iteration 1 (summaries): `top_k: 3-5`
   - Iteration 2 (chunks): `top_k: 5-10`
   - Final retrieval: `top_k: 1-3`

5. **Use appropriate min_score**
   - High stakes: `min_score: 0.6`
   - Exploratory: `min_score: 0.3`
   - Cast wide net: `min_score: 0.0`

### ❌ DON'T

1. **Don't use both chunks and summaries**
   - Pick one based on your goal
   - Use summaries for overview, chunks for details

2. **Don't ignore scores**
   - Scores < 0.3 are usually not relevant
   - Prioritize high-scoring results

3. **Don't request full_transcript unnecessarily**
   - Transcripts are 5-20KB each
   - Use chunks for specific info

4. **Don't forget to filter by call_id**
   - Searching all calls every iteration is inefficient
   - Use iteration 1 results to narrow iteration 2

---

## Performance Tips

### Fast Queries
- Metadata-only filters: ~10-50ms
- Summary search (3-5 calls): ~1-2 seconds
- Chunk search (filtered calls): ~500-1000ms

### Slow Queries
- Chunk search across all calls: 2-5 seconds
- Large top_k (50+): Slower processing
- Complex semantic queries: More embedding time

### Optimization
```json
{
  "filter": {
    "date_range": {"from": "2025-10-01", "to": "2025-10-31"},  // ← Fast filter first
    "attendants": ["Max"],                                      // ← More filtering
    "chunks": "specific technical detail"                       // ← Then semantic search
  },
  "top_k": 5  // ← Smaller = faster
}
```

---

## Error Handling

### Common Errors

**422 Validation Error**
```json
{"detail": [{"loc": ["body", "filter", "call_id"], "msg": "Field required"}]}
```
→ Check request format against schema

**500 Internal Server Error**
```json
{"detail": "Search failed: ..."}
```
→ Check logs for detailed error

### Recovery Strategies

1. **If no results:**
   - Broaden query (remove filters)
   - Try synonyms in semantic search
   - Check date ranges

2. **If too many results:**
   - Increase `min_score`
   - Add more metadata filters
   - Reduce `top_k`

3. **If irrelevant results:**
   - Refine semantic query
   - Add `not_contains` filters
   - Use more specific keywords

---

## API Endpoints

### Health Check
```bash
GET /health
```

### Statistics
```bash
GET /stats
```

Response:
```json
{
  "total_chunks": 277,
  "total_calls": 5,
  "index_dimension": 1536,
  "index_name": "conference-calls"
}
```

### List All Calls
```bash
GET /calls?limit=10&offset=0
```

### Get Specific Call
```bash
GET /calls/{call_id}
```

---

## Conclusion

This API is designed for iterative refinement:
1. **Explore** with summaries
2. **Dig deeper** with chunks
3. **Synthesize** with full context

Use metadata filters to narrow scope before expensive semantic search. Always check scores to gauge relevance. Request only the fields you need.

**Happy searching! 🚀**