"""
DashboardService — aggregation queries backing GET /api/dashboard.

Kept as a service (not inline in the route) per the clean-architecture
separation: routes call services, services own the queries.

Scalability note: at seed-data/demo scale (dozens to low hundreds of
rows), these are simple aggregate queries. At 10,000 processes, the
"most affected roles" and skill-trend queries would move to materialized
views refreshed on a schedule (or on write, via the same trigger pattern
graph_sync_service.py uses) rather than computed live on every dashboard
load — noted here rather than built now, since it's not needed at this
scale and premature caching adds a real maintenance cost this MVP doesn't
need yet.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Activity,
    AIOpportunity,
    ai_opportunity_role_impacts,
    Process,
    Role,
    Skill,
    SkillTrend,
)
from app.schemas.dashboard import DashboardOut, RoleImpactSummary


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self) -> DashboardOut:
        total_processes = self.db.scalar(select(func.count()).select_from(Process)) or 0
        total_activities = self.db.scalar(select(func.count()).select_from(Activity)) or 0
        total_roles = self.db.scalar(select(func.count()).select_from(Role)) or 0
        total_skills = self.db.scalar(select(func.count()).select_from(Skill)) or 0
        total_ai_opportunities = self.db.scalar(select(func.count()).select_from(AIOpportunity)) or 0

        high_impact_process_count = self._count_high_impact_processes()
        most_affected_roles = self._most_affected_roles(limit=5)
        emerging_skills = self._skills_by_trend(SkillTrend.EMERGING, limit=10)
        declining_skills = self._skills_by_trend(SkillTrend.DECLINING, limit=10)

        return DashboardOut(
            total_processes=total_processes,
            total_activities=total_activities,
            total_roles=total_roles,
            total_skills=total_skills,
            total_ai_opportunities=total_ai_opportunities,
            high_impact_process_count=high_impact_process_count,
            most_affected_roles=most_affected_roles,
            emerging_skills=emerging_skills,
            declining_skills=declining_skills,
        )

    def _count_high_impact_processes(self) -> int:
        from app.models import (
            activity_ai_opportunities,
            AIAssessment,
            ImpactBand,
        )

        stmt = (
            select(func.count(func.distinct(Process.id)))
            .select_from(Process)
            .join(Activity, Activity.process_id == Process.id)
            .join(activity_ai_opportunities, activity_ai_opportunities.c.activity_id == Activity.id)
            .join(AIOpportunity, AIOpportunity.id == activity_ai_opportunities.c.ai_opportunity_id)
            .join(AIAssessment, AIAssessment.ai_opportunity_id == AIOpportunity.id)
            .where(AIAssessment.impact_band.in_([ImpactBand.HIGH, ImpactBand.VERY_HIGH]))
        )
        return self.db.scalar(stmt) or 0

    def _most_affected_roles(self, limit: int) -> list[RoleImpactSummary]:
        stmt = (
            select(Role.id, Role.title, func.count(ai_opportunity_role_impacts.c.ai_opportunity_id).label("cnt"))
            .join(ai_opportunity_role_impacts, ai_opportunity_role_impacts.c.role_id == Role.id)
            .group_by(Role.id, Role.title)
            .order_by(func.count(ai_opportunity_role_impacts.c.ai_opportunity_id).desc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        return [
            RoleImpactSummary(role_id=str(r.id), title=r.title, ai_opportunity_count=r.cnt)
            for r in rows
        ]

    def _skills_by_trend(self, trend: SkillTrend, limit: int) -> list[str]:
        stmt = select(Skill.name).where(Skill.trend_classification == trend).limit(limit)
        return list(self.db.scalars(stmt).all())
