"""
Shared FastAPI dependencies. Routes depend on these, never construct a DB
session or provider themselves — this is the one place `get_llm_provider()`
and `get_embedding_provider()` get wired into a request, so tests can
override them with fakes (see tests/test_api_analyze.py) without touching
route code.
"""
from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.session import SessionLocal
from app.intelligence.embeddings import EmbeddingProvider, get_embedding_provider
from app.intelligence.llm_provider import LLMProvider, get_llm_provider


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_llm() -> LLMProvider:
    return get_llm_provider()


def get_embeddings() -> EmbeddingProvider:
    return get_embedding_provider()


def get_app_settings() -> Settings:
    return get_settings()


DbDep = Depends(get_db)
LlmDep = Depends(get_llm)
EmbeddingsDep = Depends(get_embeddings)
SettingsDep = Depends(get_app_settings)
