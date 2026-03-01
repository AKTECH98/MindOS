"""
MindOS FastAPI backend entrypoint.

Run from the project root:
    .venv/bin/uvicorn backend.main:app --reload --port 8000
"""
import sys
from pathlib import Path

# Add backend/ to sys.path so that data/, core/, integrations/, config
# are importable as top-level packages (consistent with original codebase).
BACKEND_DIR = Path(__file__).parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import xp, tasks, sessions, calendar, stats

app = FastAPI(
    title="MindOS API",
    description="Backend API for MindOS — personal productivity OS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(xp.router,       prefix="/api")
app.include_router(tasks.router,    prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(stats.router,    prefix="/api")


@app.on_event("startup")
def on_startup():
    try:
        init_db()
        print("✅ MindOS API started — DB initialized.")
    except Exception as e:
        print(f"⚠️  DB init warning: {e}")


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "MindOS API"}
