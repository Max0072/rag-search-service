"""
FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_prod import router
from app import __version__

# Create FastAPI app
app = FastAPI(
    title="Conference Call Search API",
    description="Search API for conference call transcripts with hybrid retrieval",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Startup event - initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        from app.database.main_db import get_main_db
        main_db = get_main_db()
        main_db.init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Database initialization failed: {e}")
        # Don't fail startup, just log the warning

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Conference Call Search API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/v1/health"
    }