"""
Response schemas for process/activity/role/skill/opportunity read endpoints.
All use `from_attributes=True` so they construct directly from SQLAlchemy
ORM objects (`ProcessDetailOut.model_validate(process)`), no manual
dict-building in route handlers.
"""
import uuid

from pydantic import BaseModel, ConfigDict


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str | None
    trend_classification: str
    trend_rationale: str | None


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    current_responsibilities: str | None
    skills: list[SkillOut] = []


class AIAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    factor_repetitiveness: float
    factor_data_availability: float
    factor_predictability: float
    factor_digitalization: float
    factor_ai_capability_fit: float
    factor_rationale: dict
    total_score: float
    impact_band: str
    scoring_model_version: str


class AIOpportunityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    automation_potential: str
    human_ai_responsibility: str
    business_benefit: str | None
    risks: str | None
    source: str
    assessment: AIAssessmentOut | None = None
    affected_roles: list[RoleOut] = []
    affected_skills: list[SkillOut] = []


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    roles: list[RoleOut] = []
    ai_opportunities: list[AIOpportunityOut] = []


class ProcessSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    business_purpose: str | None
    source: str
    aggregate_ai_impact_score: float | None


class ProcessDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    business_purpose: str | None
    current_challenges: str | None
    source: str
    activities: list[ActivityOut] = []
