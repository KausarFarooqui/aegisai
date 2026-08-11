"""
Single import point for every ORM model.

Alembic's env.py imports `Base` from here (via app.models.base) AFTER this
module has run, so every table below is registered on Base.metadata before
autogenerate compares it against the live database. If you add a new model
file, import it here — forgetting this step is the #1 cause of "alembic
autogenerate produced an empty migration."
"""
from app.models.base import Base  # noqa: F401

from app.models.organization import Industry, Organization  # noqa: F401
from app.models.value_chain import ValueChain, Process, Activity  # noqa: F401
from app.models.role_skill import (  # noqa: F401
    Role,
    Skill,
    SkillTrend,
    activity_roles,
    role_skills,
)
from app.models.ai_opportunity import (  # noqa: F401
    AIOpportunity,
    AIAssessment,
    FutureResponsibility,
    AutomationPotential,
    HumanAIResponsibility,
    ImpactBand,
    activity_ai_opportunities,
    ai_opportunity_role_impacts,
    ai_opportunity_skill_impacts,
)
from app.models.evidence import (  # noqa: F401
    ResearchSource,
    Evidence,
    SourceType,
    RelatedEntityType,
)
from app.models.analysis_job import (  # noqa: F401
    AnalysisJob,
    AnalysisTargetType,
    AnalysisJobStatus,
)
from app.models.graph_edge import GraphEdge, GraphNodeType  # noqa: F401

__all__ = [
    "Base",
    "Industry",
    "Organization",
    "ValueChain",
    "Process",
    "Activity",
    "Role",
    "Skill",
    "SkillTrend",
    "activity_roles",
    "role_skills",
    "AIOpportunity",
    "AIAssessment",
    "FutureResponsibility",
    "AutomationPotential",
    "HumanAIResponsibility",
    "ImpactBand",
    "activity_ai_opportunities",
    "ai_opportunity_role_impacts",
    "ai_opportunity_skill_impacts",
    "ResearchSource",
    "Evidence",
    "SourceType",
    "RelatedEntityType",
    "AnalysisJob",
    "AnalysisTargetType",
    "AnalysisJobStatus",
    "GraphEdge",
    "GraphNodeType",
]
