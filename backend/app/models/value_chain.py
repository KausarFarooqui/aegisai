"""
ValueChain -> Process -> Activity.

Industry -> contains -> ValueChain -> contains -> Process -> contains -> Activity

Process and Activity both carry `source` (seed vs dynamic) via ProvenanceMixin
because these are the two entity types the Surprise Record Test creates live.
"""
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ProvenanceMixin, TimestampMixin, UUIDPKMixin
from app.models.role_skill import EMBEDDING_DIM


class ValueChain(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "value_chains"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    """Display order along the value chain, e.g. Origination=1, Servicing=2..."""

    industry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("industries.id", ondelete="CASCADE")
    )
    industry: Mapped["Industry"] = relationship(back_populates="value_chains")  # noqa: F821

    processes: Mapped[list["Process"]] = relationship(
        back_populates="value_chain", cascade="all, delete-orphan"
    )


class Process(Base, UUIDPKMixin, TimestampMixin, ProvenanceMixin):
    __tablename__ = "processes"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_challenges: Mapped[str | None] = mapped_column(Text, nullable=True)

    value_chain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("value_chains.id", ondelete="CASCADE")
    )
    value_chain: Mapped["ValueChain"] = relationship(back_populates="processes")

    activities: Mapped[list["Activity"]] = relationship(
        back_populates="process", cascade="all, delete-orphan"
    )

    # Populated once the dynamic pipeline (or seed script) has computed a
    # rolled-up AI impact for this process, so dashboard queries don't need
    # to re-aggregate every request. Recomputed whenever a child Activity's
    # AI opportunities change.
    aggregate_ai_impact_score: Mapped[float | None] = mapped_column(nullable=True)


class Activity(Base, UUIDPKMixin, TimestampMixin, ProvenanceMixin):
    __tablename__ = "activities"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    """Embedding of `name` — same dedup purpose as Role.embedding/Skill.embedding."""

    process_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE")
    )
    process: Mapped["Process"] = relationship(back_populates="activities")

    roles: Mapped[list["Role"]] = relationship(  # noqa: F821
        secondary="activity_roles", back_populates="activities"
    )
    ai_opportunities: Mapped[list["AIOpportunity"]] = relationship(  # noqa: F821
        secondary="activity_ai_opportunities", back_populates="activities"
    )
