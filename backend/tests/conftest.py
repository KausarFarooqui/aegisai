"""
Shared pytest fixtures.

Tests run against a REAL Postgres database, not sqlite/mocks — the whole
point of this schema is Postgres-specific behaviour (pgvector, native ENUM
types, UUID PKs), so a lighter-weight test DB would validate the wrong
thing. Point DATABASE_URL (in .env, or exported directly) at a disposable
local or Supabase test database before running `pytest`.
"""
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.models import Base


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
