"""
Shared pytest fixtures.

Tests run against a REAL Postgres database, not sqlite/mocks — the whole
point of this schema is Postgres-specific behaviour (pgvector, native ENUM
types, UUID PKs), so a lighter-weight test DB would validate the wrong
thing. Point DATABASE_URL (in .env, or exported directly) at a disposable
local or Supabase test database before running `pytest`.
"""
import sys
from urllib.parse import urlparse

import pytest
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.session import SessionLocal, engine
from app.models import Base


def _guard_against_non_local_database() -> None:
    """
    Refuses to even start the test session if DATABASE_URL doesn't point
    at localhost. This suite's session-scoped fixture (_create_schema,
    below) drops every table when the session ends — correct and safe for
    a disposable local test database, catastrophic against anything else.

    This used to be enforced only by a comment ("point DATABASE_URL at a
    local/test database before running pytest") — a convention that
    depends on remembering to type the override correctly in every fresh
    terminal, forever. It failed exactly that way once: a bare `pytest`
    run in a new terminal picked up .env's default (the real Supabase
    project) instead of the local override, and wiped every real seeded
    row — 12 processes' worth of real Groq-generated data, gone in one
    command. This function is the structural fix: an enforced check that
    runs before any fixture, not a reminder that's easy to forget.
    """
    settings = get_settings()
    normalized = settings.database_url.replace("postgresql+psycopg", "postgresql", 1)
    host = (urlparse(normalized).hostname or "").lower()

    if host not in ("localhost", "127.0.0.1"):
        sys.exit(
            "\n\n"
            "REFUSING TO RUN: DATABASE_URL does not point at localhost.\n"
            f"  Configured host: {host!r}\n\n"
            "This test suite drops every table in the target database when the\n"
            "session ends (tests/conftest.py::_create_schema) -- safe for a\n"
            "disposable local test database, destructive against anything else,\n"
            "including a real Supabase project.\n\n"
            "Run tests against a local database instead, for example:\n"
            '  DATABASE_URL="postgresql+psycopg://postgres:testpass@localhost:5433/aegisai_test" pytest tests/ -v\n\n'
            "If you genuinely need to run this suite against a non-local\n"
            "database, edit this guard in tests/conftest.py deliberately --\n"
            "do not bypass it by accident.\n"
        )


_guard_against_non_local_database()


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Creates every table once for the test session, drops them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
