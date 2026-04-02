# Project Structure

```
rag_service/
│
├── app/                              # Main application code
│   ├── api/                          # API endpoints and routes
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app initialization
│   │   │                             # + Startup event for auto DB init
│   │   ├── routes_prod.py            # Production API routes (search, upload)
│   │   └── routes_admin.py           # Admin/debug endpoints
│   │
│   ├── database/                     # Database layer
│   │   ├── __init__.py
│   │   ├── db_models.py              # SQLAlchemy models for PostgreSQL
│   │   ├── main_db.py                # PostgreSQL operations (metadata DB)
│   │   └── vector_db.py              # Pinecone operations (vector DB)
│   │
│   ├── embeddings/                   # Vector embedding generation
│   │   ├── __init__.py
│   │   └── openai_embeddings.py      # Embedding service via OpenRouter
│   │
│   ├── search/                       # Search engine logic
│   │   ├── __init__.py
│   │   └── search_engine.py          # 3-step search pipeline
│   │
│   ├── __init__.py
│   ├── config.py                     # App settings (Pydantic Settings)
│   ├── data_manager.py               # Synchronization manager between DBs
│   └── models.py                     # Pydantic models for API requests/responses
│
├── .env                              # Environment variables for Docker (not in git)
├── .env.example                      # Example env file
├── .dockerignore                     # Docker build exclusions
├── .gitignore                        # Git ignore rules
│
├── docker-compose.yml                # Docker Compose for local development
│                                     # (PostgreSQL + API service)
├── Dockerfile                        # Docker image for deployment
├── project_structure.md              # This file - project structure
├── README.md                         # Setup instructions
└── requirements.txt                  # Python dependencies
```
