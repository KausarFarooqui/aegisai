"""
Base repository.

Per the MODUS clean-architecture requirement: API routes never touch
SQLAlchemy directly. They call a service, which calls a repository, which
is the only layer that writes queries. This file is the generic CRUD base;
entity-specific repositories (entity_repository.py) add the pgvector
similarity search and other domain-specific queries.
"""
import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        return self.db.scalar(stmt) or 0

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        return entity
