"""
Entity repositories.

The one method worth reading closely here is `find_similar` on
RoleRepository/SkillRepository: it's a pgvector-indexed SQL query
(`ORDER BY embedding <=> :query LIMIT k`), not a Python loop over every
row. That's what makes dedup viable at 10,000 processes instead of just at
seed-data scale — the database does the coarse "which 5 are closest" work,
and the already-tested app/services/dedup_service.py does the fine
"is the closest one actually a match" decision on just those 5.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Activity, AIOpportunity, Process, Role, Skill, ValueChain
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session):
        super().__init__(db, Role)

    def find_similar(self, query_embedding: list[float], limit: int = 5) -> list[Role]:
        if self.count() == 0:
            return []
        stmt = (
            select(Role)
            .where(Role.embedding.is_not(None))
            .order_by(Role.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())


class SkillRepository(BaseRepository[Skill]):
    def __init__(self, db: Session):
        super().__init__(db, Skill)

    def find_similar(self, query_embedding: list[float], limit: int = 5) -> list[Skill]:
        if self.count() == 0:
            return []
        stmt = (
            select(Skill)
            .where(Skill.embedding.is_not(None))
            .order_by(Skill.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_linked_opportunity_signals(self, skill_id: uuid.UUID) -> list["SkillOpportunitySignal"]:
        """
        Every AIOpportunity currently linked to this skill, as the minimal
        (human_ai_responsibility, impact_band) pairs that
        app.scoring.skill_trend.classify_skill_trend needs. Deliberately
        includes opportunities linked in PAST analysis runs, not just the
        one just created — trend classification should reflect the full
        picture, not only the most recent link.
        """
        from app.models import ai_opportunity_skill_impacts
        from app.scoring.skill_trend import SkillOpportunitySignal

        stmt = (
            select(AIOpportunity)
            .join(
                ai_opportunity_skill_impacts,
                AIOpportunity.id == ai_opportunity_skill_impacts.c.ai_opportunity_id,
            )
            .where(ai_opportunity_skill_impacts.c.skill_id == skill_id)
        )
        opportunities = self.db.scalars(stmt).all()
        signals = []
        for opp in opportunities:
            if opp.assessment is not None:
                signals.append(
                    SkillOpportunitySignal(
                        human_ai_responsibility=opp.human_ai_responsibility,
                        impact_band=opp.assessment.impact_band,
                    )
                )
        return signals


class ActivityRepository(BaseRepository[Activity]):
    """
    Deliberately no `find_similar` here. Activities belong to exactly one
    Process and aren't deduped across processes the way Role/Skill are —
    "Document Review" in Loan Underwriting and "Document Review" in Trade
    Finance are legitimately two different activity instances, not the same
    entity. Every dynamic analysis run creates fresh Activity rows for its
    Process. The embedding column still exists (for future cross-process
    similarity analytics) but isn't queried by the dedup pipeline.
    """
    def __init__(self, db: Session):
        super().__init__(db, Activity)


class ProcessRepository(BaseRepository[Process]):
    def __init__(self, db: Session):
        super().__init__(db, Process)

    def get_by_name(self, name: str) -> Process | None:
        stmt = select(Process).where(Process.name.ilike(name))
        return self.db.scalars(stmt).first()


class ValueChainRepository(BaseRepository[ValueChain]):
    def __init__(self, db: Session):
        super().__init__(db, ValueChain)


class AIOpportunityRepository(BaseRepository[AIOpportunity]):
    def __init__(self, db: Session):
        super().__init__(db, AIOpportunity)
