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
from pydantic import BaseModel, Field, field_validator, model_validator


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
    affected_activity_names: list[str] = Field(..., min_length=1, max_length=6)
    """Must reference names from the top-level `activities` list — builds
    the Activity->AIOpportunity graph edges. An opportunity that doesn't
    plausibly attach to a specific activity in this process shouldn't be
    proposed at all."""
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
    requires_skill_names: list[str] = Field(..., min_length=1, max_length=8)
    """Must reference names from the sibling `skills` list by exact string
    match (case-insensitive) — this is what lets the pipeline build the
    Role->Skill graph edges instead of guessing."""


class ProposedSkill(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    category: str = Field(..., max_length=80)
    is_new: bool


class ProposedActivity(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., max_length=500)
    performed_by_role_titles: list[str] = Field(..., min_length=1, max_length=5)
    """Must reference titles from the sibling `roles` list by exact string
    match (case-insensitive) — builds the Activity->Role graph edges."""


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

    @model_validator(mode="after")
    def _cross_references_resolve(self) -> "EntityExtractionResult":
        """
        Every cross-reference must point at a name that actually exists in
        its sibling list. This is what turns "the LLM hallucinated a role
        name that doesn't exist anywhere else in its own response" from a
        silently broken graph edge into a loud validation failure the
        pipeline can retry or fail cleanly on.
        """
        activity_names = {a.name.strip().lower() for a in self.activities}
        role_titles = {r.title.strip().lower() for r in self.roles}
        skill_names = {s.name.strip().lower() for s in self.skills}

        for activity in self.activities:
            for role_title in activity.performed_by_role_titles:
                if role_title.strip().lower() not in role_titles:
                    raise ValueError(
                        f"Activity '{activity.name}' references role "
                        f"'{role_title}' which is not in the roles list."
                    )

        for role in self.roles:
            for skill_name in role.requires_skill_names:
                if skill_name.strip().lower() not in skill_names:
                    raise ValueError(
                        f"Role '{role.title}' references skill '{skill_name}' "
                        f"which is not in the skills list."
                    )

        for opportunity in self.ai_opportunities:
            for activity_name in opportunity.affected_activity_names:
                if activity_name.strip().lower() not in activity_names:
                    raise ValueError(
                        f"AI opportunity '{opportunity.name}' references activity "
                        f"'{activity_name}' which is not in the activities list."
                    )

        return self
