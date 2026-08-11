"""
AnalysisJob.

Every call to POST /api/analyze creates one of these BEFORE any LLM call is
made, and updates it as the pipeline progresses. This is what makes the
Surprise Record Test observable and defensible:
  - a judge can watch status flip pending -> processing -> completed live
  - a crash mid-pipeline leaves a visible failed job with an error_message,
    never a silent gap
  - stage_log gives a full timeline for the "explain what happened" ask

This table is intentionally independent of the entity tables — it tracks
*process*, not *data*, which is why it isn't just a status column bolted
onto Process/Role/Skill/AIOpportunity.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin, pg_enum


class AnalysisTargetType(str, enum.Enum):
    PROCESS = "process"
    ROLE = "role"
    SKILL = "skill"
    AI_OPPORTUNITY = "ai_opportunity"


class AnalysisJobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJob(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "analysis_jobs"

    target_type: Mapped[AnalysisTargetType] = mapped_column(
        pg_enum(AnalysisTargetType, "analysis_target_type")
    )
    input_name: Mapped[str] = mapped_column(String(300), nullable=False)
    """The raw text a user/judge typed in, e.g. 'Warehouse Inventory
    Forecasting' — stored verbatim regardless of outcome."""
    input_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[AnalysisJobStatus] = mapped_column(
        pg_enum(AnalysisJobStatus, "analysis_job_status"),
        default=AnalysisJobStatus.PENDING,
    )
    current_stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(80), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)

    stage_log: Mapped[list] = mapped_column(JSON, default=list)
    """[{"stage": "llm_extraction", "started_at": ..., "duration_ms": ...,
         "detail": "..."}]  — one entry appended per pipeline stage."""

    result_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    """The primary entity created by this job (e.g. the new Process.id),
    once known — lets the frontend jump straight to the new graph node."""
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
