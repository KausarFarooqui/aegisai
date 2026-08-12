"""
AEGISAI — Enterprise Workforce Impact Intelligence Platform
FastAPI application entrypoint.

Phase 3 status: app boots, connects to the DB, exposes a health check.
Routers (dashboard/processes/roles/skills/opportunities/analyze/graph/
evidence/analyst) land in Phase 5 — kept out of this file deliberately so
main.py never grows business logic; it only wires things together.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.settings import get_settings
from app.db.session import engine
from app.api.routes import api_router

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("aegisai")

app = FastAPI(
    title="AEGISAI",
    description="Enterprise Workforce Impact Intelligence Platform — "
    "Process x Role x Skill Intelligence Graph (MODUS Assignment 11)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/health", tags=["system"])
def health_check() -> dict:
    """
    Confirms the API is up AND the database is reachable — two separate
    facts. A judge hitting this before the demo should see both are true.
    """
    db_ok = True
    db_error = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — deliberately broad for a health probe
        db_ok = False
        db_error = str(exc)

    return {
        "status": "ok" if db_ok else "degraded",
        "database_connected": db_ok,
        "database_error": db_error,
        "environment": settings.app_env,
    }


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "app": "AEGISAI",
        "docs": "/docs",
        "health": "/api/health",
    }
