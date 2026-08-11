"""
The extraction schema — what the LLM is allowed to produce for a new
Process/Role/Skill/AIOpportunity submitted through the Surprise Record Test.

This is the contract. The LLM's raw output is validated against this schema
before ANYTHING else happens to it. If it doesn't parse, the pipeline
retries once with the validation error appended to the prompt, then fails
the AnalysisJob cleanly (status=failed, real error_message) rather than
falling back to inventing data. See app/intelligence/llm_provider.py for
where this is enforced.

Deliberately: no field here is a final score, a final skill trend, or a
final relationship decision. Everything downstream of this schema (scoring,
dedup, persistence) is deterministic application code — see
app/scoring/impact_score.py and app/services/dedup_service.py.
"""
from pydantic import BaseModel, Field, field_validator


class ProposedFactor(BaseModel):
    value: float = Field(..., ge=0, le=100)
    reason: str = Field(..., min_length=5, max_length=300)


class ProposedAIOpportunity(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    automation_potential: str  # validated against enum values in the service layer
    human_ai_responsibility: str
    business_benefit: str = Field(..., max_length=500)
    risks: str = Field(..., max_length=500)
    factor_repetitiveness: ProposedFactor
    factor_data_availability: ProposedFactor
    factor_predictability: ProposedFactor
    factor_digitalization: ProposedFactor
    factor_ai_capability_fit: ProposedFactor


class ProposedRole(BaseModel):
    title: str = Field(..., min_length=2, max_length=160)
    is_new: bool
    """True if the LLM believes this doesn't match any existing role it was
    shown in context. This is a HINT, not a decision — dedup_service.py
    makes the actual call via embedding similarity regardless of what the
    LLM guessed here."""


class ProposedSkill(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    category: str = Field(..., max_length=80)
    is_new: bool


class ProposedActivity(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., max_length=500)


class EntityExtractionResult(BaseModel):
    """
    Top-level shape the LLM must return for a new Process submitted via
    the Analyze New Element / Surprise Record Test flow. Role/Skill/
    AIOpportunity entry points (Phase 5) use narrower slices of this same
    schema rather than separate ad hoc shapes.
    """
    business_purpose: str = Field(..., min_length=10, max_length=500)
    current_challenges: str = Field(..., max_length=500)
    activities: list[ProposedActivity] = Field(..., min_length=1, max_length=10)
    roles: list[ProposedRole] = Field(..., min_length=1, max_length=8)
    skills: list[ProposedSkill] = Field(..., min_length=1, max_length=12)
    ai_opportunities: list[ProposedAIOpportunity] = Field(..., min_length=1, max_length=5)

    @field_validator("activities", "roles", "skills", "ai_opportunities")
    @classmethod
    def _no_duplicate_names(cls, items: list) -> list:
        name_attr = "title" if hasattr(items[0], "title") else "name" if items else None
        if name_attr:
            names = [getattr(i, name_attr).strip().lower() for i in items]
            if len(names) != len(set(names)):
                raise ValueError(f"Duplicate names within a single extraction response: {names}")
        return items
