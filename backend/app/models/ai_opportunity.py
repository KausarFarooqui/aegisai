"""
AIOpportunity, AIAssessment, FutureResponsibility.

Activity <-> AIOpportunity  (junction: activity_ai_opportunities)
AIOpportunity <-> Role      (junction: ai_opportunity_role_impacts)  "which roles this touches"
AIOpportunity <-> Skill     (junction: ai_opportunity_skill_impacts) "which skills this changes"
AIOpportunity -> has one -> AIAssessment  (the transparent, deterministic score)
Role -> has many -> FutureResponsibility

Everything under AIAssessment is written ONLY by app/scoring — never
directly by the LLM. The LLM proposes the five 0-100 factor estimates (with
a short reason each, stored in `factor_rationale`); a pure deterministic
function computes `total_score` and `impact_band` from those factors using
the configurable weights in app/scoring/config.py. This split is the answer
to "how do you prevent the AI from just making up a score."
"""
import enum
import uuid

from sqlalchemy import Float, ForeignKey, JSON, String, Table, Text, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ProvenanceMixin, TimestampMixin, UUIDPKMixin, pg_enum


class AutomationPotential(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HumanAIResponsibility(str, enum.Enum):
    """
    The MODUS brief is explicit: high AI potential does NOT mean full
    automation. This enum is what makes that distinction a queryable field
    rather than a sentence buried in prose.
    """
    AI_AUTOMATES = "ai_automates"
    AI_AUGMENTS = "ai_augments"
    HUMAN_LED = "human_led"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"


class ImpactBand(str, enum.Enum):
    LOW = "low"          # 0-30
    MEDIUM = "medium"    # 31-60
    HIGH = "high"        # 61-80
    VERY_HIGH = "very_high"  # 81-100


class AIOpportunity(Base, UUIDPKMixin, TimestampMixin, ProvenanceMixin):
    __tablename__ = "ai_opportunities"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    automation_potential: Mapped[AutomationPotential] = mapped_column(
        pg_enum(AutomationPotential, "automation_potential"),
        default=AutomationPotential.MEDIUM,
    )
    human_ai_responsibility: Mapped[HumanAIResponsibility] = mapped_column(
        pg_enum(HumanAIResponsibility, "human_ai_responsibility"),
        default=HumanAIResponsibility.AI_AUGMENTS,
    )
    business_benefit: Mapped[str | None] = mapped_column(Text, nullable=True)
    risks: Mapped[str | None] = mapped_column(Text, nullable=True)

    activities: Mapped[list["Activity"]] = relationship(  # noqa: F821
        secondary="activity_ai_opportunities", back_populates="ai_opportunities"
    )
    affected_roles: Mapped[list["Role"]] = relationship(  # noqa: F821
        secondary="ai_opportunity_role_impacts"
    )
    affected_skills: Mapped[list["Skill"]] = relationship(  # noqa: F821
        secondary="ai_opportunity_skill_impacts"
    )
    assessment: Mapped["AIAssessment"] = relationship(
        back_populates="ai_opportunity", uselist=False, cascade="all, delete-orphan"
    )


class AIAssessment(Base, UUIDPKMixin, TimestampMixin):
    """
    The transparent scoring record. One row per AIOpportunity.

    Formula (configurable — see app/scoring/config.py):
      total = 0.30*repetitiveness + 0.20*data_availability
            + 0.20*predictability + 0.15*digitalization
            + 0.15*ai_capability_fit

    All five factor_* fields are LLM-proposed estimates (0-100) with a
    one-line rationale each, captured verbatim in factor_rationale so the UI
    can show "why" without re-calling the model. total_score and impact_band
    are ALWAYS computed by deterministic code — never trust an LLM-written
    number into these two columns.
    """
    __tablename__ = "ai_assessments"

    ai_opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_opportunities.id", ondelete="CASCADE"), unique=True
    )
    ai_opportunity: Mapped["AIOpportunity"] = relationship(back_populates="assessment")

    factor_repetitiveness: Mapped[float] = mapped_column(Float)
    factor_data_availability: Mapped[float] = mapped_column(Float)
    factor_predictability: Mapped[float] = mapped_column(Float)
    factor_digitalization: Mapped[float] = mapped_column(Float)
    factor_ai_capability_fit: Mapped[float] = mapped_column(Float)

    factor_rationale: Mapped[dict] = mapped_column(JSON, default=dict)
    """{"repetitiveness": "reason...", "data_availability": "reason...", ...}"""

    total_score: Mapped[float] = mapped_column(Float)
    impact_band: Mapped[ImpactBand] = mapped_column(pg_enum(ImpactBand, "impact_band"))

    scoring_model_version: Mapped[str] = mapped_column(String(20), default="v1")
    """Bumped whenever the weight configuration changes, so historical
    assessments remain interpretable even after the formula is tuned."""


class FutureResponsibility(Base, UUIDPKMixin, TimestampMixin, ProvenanceMixin):
    __tablename__ = "future_responsibilities"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE")
    )
    role: Mapped["Role"] = relationship(back_populates="future_responsibilities")  # noqa: F821

    description: Mapped[str] = mapped_column(Text, nullable=False)
    driven_by_ai_opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_opportunities.id", ondelete="SET NULL"), nullable=True
    )
    """Links back to the specific AIOpportunity that generated this future
    responsibility, so 'why will this role change' is always traceable to a
    concrete cause, not a free-floating LLM sentence."""


# --- Junction tables ---

activity_ai_opportunities = Table(
    "activity_ai_opportunities",
    Base.metadata,
    Column("activity_id", UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("ai_opportunity_id", UUID(as_uuid=True), ForeignKey("ai_opportunities.id", ondelete="CASCADE"), primary_key=True),
)

ai_opportunity_role_impacts = Table(
    "ai_opportunity_role_impacts",
    Base.metadata,
    Column("ai_opportunity_id", UUID(as_uuid=True), ForeignKey("ai_opportunities.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

ai_opportunity_skill_impacts = Table(
    "ai_opportunity_skill_impacts",
    Base.metadata,
    Column("ai_opportunity_id", UUID(as_uuid=True), ForeignKey("ai_opportunities.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)
