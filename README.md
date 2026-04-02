# RAG Search Service

A Retrieval-Augmented Generation (RAG) backend for searching and indexing conference call transcripts with semantic and metadata-based filtering.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI    │────▶│  PostgreSQL  │     │  Pinecone   │
│   (API)      │     │  (metadata)  │     │  (vectors)  │
└──────┬───────┘     └──────────────┘     └─────────────┘
       │                                        ▲
       │         ┌──────────────┐               │
       └────────▶│ OpenRouter   │───────────────┘
                 │ (embeddings) │
                 └──────────────┘
```

**How it works:**

1. Conference call transcripts are chunked and embedded via OpenRouter (OpenAI-compatible API)
2. Chunks and summaries are stored in Pinecone for vector similarity search
3. Full transcripts and metadata are stored in PostgreSQL
4. Search combines metadata filters (date, attendants) with semantic similarity

## Tech Stack

| Component        | Technology                            |
|------------------|---------------------------------------|
| Framework        | FastAPI + Uvicorn                     |
| Metadata DB      | PostgreSQL 15                         |
| Vector DB        | Pinecone (Serverless)                 |
| Embeddings       | OpenRouter (`text-embedding-3-large`) |
| ORM              | SQLAlchemy                            |
| Validation       | Pydantic                              |
| Containerization | Docker & Docker Compose               |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [OpenRouter](https://openrouter.ai/) API key (for embeddings)
- [Pinecone](https://www.pinecone.io/) account and API key

## Quick Start

1. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your API keys:

   ```
   OPENROUTER_API_KEY=your-openrouter-key
   PINECONE_API_KEY=your-pinecone-key
   ```

2. **Start the service**

   ```bash
   docker-compose up --build -d
   ```

3. **Verify it's running**

   ```bash
   curl http://localhost:8000/health
   ```

4. **Open API docs** at [http://localhost:8000/docs](http://localhost:8000/docs)

## Stopping the Service

```bash
# Stop while preserving data
docker-compose down

# Stop and remove all data (including PostgreSQL volumes)
docker-compose down -v
```

## API Endpoints

### Public

| Method | Endpoint           | Description                     |
|--------|--------------------|---------------------------------|
| GET    | `/health`          | Health check                    |
| GET    | `/stats`           | Database statistics             |
| POST   | `/search`          | Search transcripts with filters |
| POST   | `/upload_json`     | Bulk upload calls from JSON     |
| DELETE | `/calls/{call_id}` | Delete a call                   |

### Admin

| Method | Endpoint                 | Description                |
|--------|--------------------------|----------------------------|
| POST   | `/admin/init-db`         | Initialize database tables |
| GET    | `/admin/calls`           | List all calls (paginated) |
| POST   | `/admin/calls`           | Create a single call       |
| GET    | `/admin/calls/{call_id}` | Get call details           |
| DELETE | `/admin/clear-all`       | Delete all data            |

### Search Example

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "chunks": "API timeout issues",
      "attendants": ["Alice"]
    },
    "top_k": 5,
    "min_score": 0.7
  }'
```

## Environment Variables

| Variable                        | Default                          | Description                   |
|---------------------------------|----------------------------------|-------------------------------|
| `OPENROUTER_API_KEY`            | —                                | OpenRouter API key (required) |
| `PINECONE_API_KEY`              | —                                | Pinecone API key (required)   |
| `PINECONE_CLOUD`                | `aws`                            | Pinecone cloud provider       |
| `PINECONE_ENVIRONMENT`          | `us-east-1`                      | Pinecone region               |
| `PINECONE_INDEX_NAME`           | `conference-calls`               | Chunks index name             |
| `PINECONE_SUMMARIES_INDEX_NAME` | `conference-summaries`           | Summaries index name          |
| `EMBEDDING_MODEL`               | `openai/text-embedding-3-large`  | Embedding model               |
| `EMBEDDING_DIMENSION`           | `1536`                           | Embedding vector dimension    |
| `DATABASE_URL`                  | (set in docker-compose)          | PostgreSQL connection string  |
| `DEFAULT_TOP_K`                 | `10`                             | Default results per query     |
| `MIN_RELEVANCE_SCORE`           | `0.7`                            | Minimum relevance threshold   |

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
