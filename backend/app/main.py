# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deps import init_data
from .routers import courses, ranking, runs, talent

app = FastAPI(
    title="Polimi Course Advisor Backend",
    version="0.3.0",
)

# CORS: allow local frontend dev
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """
    Initialize in-memory data (courses + graph).
    """
    init_data()
    print("[startup] Data initialized (courses.json + graph built)", flush=True)


@app.get("/health")
async def health_root():
    """
    Basic health endpoint (legacy Phase 0 compatible).
    """
    return {
        "status": "ok",
        "service": "backend",
        "phase": 3,
        "path": "/health",
    }


@app.get("/api/health")
async def health_api():
    """
    API-prefixed health endpoint for the frontend.
    Validates Supabase connection if env vars are present.
    """
    import os
    from ..core.supabase_client import get_supabase
    
    db_status = "not_configured"
    error_detail = None
    
    url = os.getenv("SUPABASE_URL")
    admin_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if url and admin_key:
        try:
            supabase = get_supabase()
            # Lightweight query to validate connection
            # We use admin client to check student_profiles
            res = supabase.table("student_profiles").select("user_id").limit(1).execute()
            
            if anon_key:
                db_status = "ok"
            else:
                db_status = "partial_config (missing anon key)"
        except Exception as e:
            db_status = "error"
            error_detail = str(e)
            
    return {
        "status": "ok" if db_status in ["ok", "not_configured"] else "error",
        "service": "backend",
        "database": db_status,
        "database_error": error_detail,
        "phase": 3,
        "path": "/api/health",
    }


# Attach API routers
app.include_router(courses.router, prefix="/api")
app.include_router(ranking.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(talent.router, prefix="/api")