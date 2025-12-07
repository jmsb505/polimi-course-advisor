# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deps import init_data
from .routers import courses, ranking

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
    """
    return {
        "status": "ok",
        "service": "backend",
        "phase": 3,
        "path": "/api/health",
    }


# Attach API routers
app.include_router(courses.router, prefix="/api")
app.include_router(ranking.router, prefix="/api")