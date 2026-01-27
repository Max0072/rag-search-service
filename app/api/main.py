"""
FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_prod import router
from app.api.routes_admin import admin_router
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
app.include_router(router, prefix="")
app.include_router(admin_router, prefix="/admin")

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Conference Call Search API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health"
    }


 # - allow_origins=["*"] - разрешает запросы с любых доменов
 #    - ⚠️ Небезопасно для production! Любой сайт сможет делать запросы к вашему API
 #    - Для production нужно указать конкретные домены: ["https://yourapp.com", "https://www.yourapp.com"]
 #  - allow_credentials=True - разрешает отправку cookies и авторизационных заголовков
 #  - allow_methods=["*"] - разрешает все HTTP методы (GET, POST, PUT, DELETE и т.д.)
 #  - allow_headers=["*"] - разрешает все HTTP заголовки