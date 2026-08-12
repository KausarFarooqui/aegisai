"""
GET /api/roles, GET /api/roles/{id}, GET /api/skills, GET /api/skills/{id}
— backing the Role Intelligence and Skill Intelligence pages.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Role, Skill
from app.repositories.entity_repository import RoleRepository, SkillRepository
from app.schemas.process import RoleOut, SkillOut

router = APIRouter(tags=["roles-skills"])


@router.get("/api/roles", response_model=list[RoleOut])
def list_roles(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[Role]:
    return RoleRepository(db).list(limit=limit, offset=offset)


@router.get("/api/roles/{role_id}", response_model=RoleOut)
def get_role(role_id: uuid.UUID, db: Session = Depends(get_db)) -> Role:
    role = RoleRepository(db).get_by_id(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail=f"Role {role_id} not found")
    return role


@router.get("/api/skills", response_model=list[SkillOut])
def list_skills(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    trend: str | None = Query(None, description="Filter by trend_classification, e.g. 'declining'"),
    db: Session = Depends(get_db),
) -> list[Skill]:
    repo = SkillRepository(db)
    if trend:
        from app.models import SkillTrend
        from sqlalchemy import select

        try:
            trend_enum = SkillTrend(trend.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trend '{trend}' — expected one of {[e.value for e in SkillTrend]}",
            )
        stmt = select(Skill).where(Skill.trend_classification == trend_enum).offset(offset).limit(limit)
        return list(db.scalars(stmt).all())
    return repo.list(limit=limit, offset=offset)


@router.get("/api/skills/{skill_id}", response_model=SkillOut)
def get_skill(skill_id: uuid.UUID, db: Session = Depends(get_db)) -> Skill:
    skill = SkillRepository(db).get_by_id(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")
    return skill
