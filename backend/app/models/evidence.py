"""
ResearchSource and Evidence — the traceability layer.

Evidence -> references -> ResearchSource

Design note: Evidence is the ONE place in this schema that uses a light
polymorphic association (related_entity_type + related_entity_id) instead of
a typed foreign key. Everywhere else in this schema (Process/Role/Skill/
AIOpportunity) uses real typed junction tables deliberately, because those
relationships are the graph itself and need strict referential integrity.
Evidence is different: it's a cross-cutting annotation that can attach to
almost any entity type (a Process, an AIOpportunity, an AIAssessment, a
Skill's trend classification...). Enumerating a separate junction table per
target type here would multiply tables without adding real integrity value,
since Evidence is additive metadata, not a structural graph edge. This is a
deliberate, explainable exception, not an oversight.
"""
import enum
import uuid
from datetime import date

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin, UUIDPKMixin, pg_enum


class SourceType(str, enum.Enum):
    LAW_REGULATION = "law_regulation"
    REGULATORY_GUIDANCE = "regulatory_guidance"
    INDUSTRY_STANDARD = "industry_standard"
    RESEARCH = "research"
    VENDOR_INFORMATION = "vendor_information"
    GENERAL_WEB_CONTENT = "general_web_content"


class RelatedEntityType(str, enum.Enum):
    PROCESS = "process"
    ACTIVITY = "activity"
    ROLE = "role"
    SKILL = "skill"
    AI_OPPORTUNITY = "ai_opportunity"
    AI_ASSESSMENT = "ai_assessment"


class ResearchSource(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "research_sources"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[SourceType] = mapped_column(pg_enum(SourceType, "source_type"))
    publication_date: Mapped[date | None] = mapped_column(nullable=True)
    retrieved_date: Mapped[date] = mapped_column(nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    """The curated, citable summary text this source contributes — this is
    what gets embedded for semantic search, and what a citation panel shows.
    Never the full original article text (copyright + focus)."""

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384), nullable=True  # matches EMBEDDING_DIMENSIONS in settings
    )

    evidence_entries: Mapped[list["Evidence"]] = relationship(back_populates="research_source")


class Evidence(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "evidence"

    research_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_sources.id", ondelete="CASCADE")
    )
    research_source: Mapped["ResearchSource"] = relationship(back_populates="evidence_entries")

    related_entity_type: Mapped[RelatedEntityType] = mapped_column(
        pg_enum(RelatedEntityType, "related_entity_type")
    )
    related_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    extracted_finding: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float)
    """Cosine similarity between the query embedding and the source
    embedding at retrieval time — stored so a low-confidence match is
    visibly low-confidence in the UI, not hidden."""
    confidence: Mapped[float] = mapped_column(Float)
    """LLM's self-reported confidence that this source actually supports
    the finding, separate from raw similarity — two different signals,
    both shown, so nothing is silently overstated."""
