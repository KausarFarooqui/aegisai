"""
Role and Skill, and the junction tables that connect them into the graph.

Activity <-> Role   (junction: activity_roles)      "who performs this activity"
Role     <-> Skill  (junction: role_skills)          "what skills this role needs"

Design note on Skill.trend_classification: this is NOT set by hand and NOT
set directly by the LLM. It is recomputed by deterministic application logic
(app/scoring) every time an AIOpportunity linked to this skill is created or
updated — see scoring/skill_trend.py. That's what makes "which skills are
declining" a live, explainable query instead of a label someone typed once.
"""
import enum
import uuid

from sqlalchemy import ForeignKey, String, Table, Text, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ProvenanceMixin, TimestampMixin, UUIDPKMixin, pg_enum


class SkillTrend(str, enum.Enum):
    EMERGING = "emerging"
    INCREASING = "increasing"
    AI_AUGMENTED = "ai_augmented"
    CHANGING = "changing"
    DECLINING = "declining"
    ENDURING_HUMAN = "enduring_human_capability"
    UNCLASSIFIED = "unclassified"  # default until an AI opportunity touches it


class Role(Base, UUIDPKMixin, TimestampMixin, ProvenanceMixin):
    __tablename__ = "roles"

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    current_responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)

    activities: Mapped[list["Activity"]] = relationship(  # noqa: F821
        secondary="activity_roles", back_populates="roles"
    )
    skills: Mapped[list["Skill"]] = relationship(
        secondary="role_skills", back_populates="roles"
    )
    future_responsibilities: Mapped[list["FutureResponsibility"]] = relationship(  # noqa: F821
        back_populates="role", cascade="all, delete-orphan"
    )


class Skill(Base, UUIDPKMixin, TimestampMixin, ProvenanceMixin):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    """e.g. 'technical', 'analytical', 'interpersonal', 'regulatory'."""

    trend_classification: Mapped[SkillTrend] = mapped_column(
        pg_enum(SkillTrend, "skill_trend"), default=SkillTrend.UNCLASSIFIED
    )
    trend_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    """One-line, machine-written explanation of *why* the trend is what it is
    (e.g. 'Linked to 3 AI opportunities classed HIGH automation potential') —
    this is what answers 'why does the system believe this' in the UI."""

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_skills", back_populates="skills"
    )


# --- Junction tables ---
# Plain association tables (no extra columns needed yet) rather than mapped
# classes — SQLAlchemy relationship(secondary=...) handles these directly,
# which keeps the many-to-many edges simple while still being real foreign
# keys with referential integrity (not a generic polymorphic blob).

activity_roles = Table(
    "activity_roles",
    Base.metadata,
    Column("activity_id", UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_skills = Table(
    "role_skills",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)
