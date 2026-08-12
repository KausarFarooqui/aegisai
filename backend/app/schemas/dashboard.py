from pydantic import BaseModel


class RoleImpactSummary(BaseModel):
    role_id: str
    title: str
    ai_opportunity_count: int


class DashboardOut(BaseModel):
    total_processes: int
    total_activities: int
    total_roles: int
    total_skills: int
    total_ai_opportunities: int
    high_impact_process_count: int
    """Processes with at least one activity linked to a HIGH or VERY_HIGH
    impact-band AI opportunity."""
    most_affected_roles: list[RoleImpactSummary]
    emerging_skills: list[str]
    declining_skills: list[str]
