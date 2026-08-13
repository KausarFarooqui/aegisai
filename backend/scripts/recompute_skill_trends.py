"""
Recomputes Skill.trend_classification and trend_rationale for every skill
already in the database, using the current app.scoring.skill_trend logic.

Why this script exists: trend_classification is written once, at the
moment a skill's linked AI opportunities change (see
app/workers/analysis_pipeline.py's _update_skill_trends). If the
classification RULES themselves change — as they did after the real
10-process seed run revealed the original design couldn't reach two of
its own six categories, see docs/architecture/decision-log.md — every
skill seeded before that fix keeps its stale classification until
something re-triggers the calculation. Re-running the full (expensive,
real-Groq-calls) seed script is one way to do that; this script is the
cheap way — it's a pure recomputation over data already in the database,
no LLM or embedding calls at all.

Usage:
    cd backend
    python scripts/recompute_skill_trends.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models import Skill  # noqa: E402
from app.repositories.entity_repository import SkillRepository  # noqa: E402
from app.scoring.skill_trend import classify_skill_trend  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        skill_repo = SkillRepository(db)
        skills = db.query(Skill).all()

        if not skills:
            print("No skills in the database yet — nothing to recompute.")
            return

        print(f"Recomputing trend classification for {len(skills)} skills...\n")
        changed = 0

        for skill in skills:
            signals = skill_repo.get_linked_opportunity_signals(skill.id)
            old_trend = skill.trend_classification
            new_trend, new_rationale = classify_skill_trend(signals, skill_is_newly_dynamic=False)

            if new_trend != old_trend:
                print(f"  CHANGED  {skill.name}: {old_trend.value} -> {new_trend.value}")
                changed += 1
            skill.trend_classification = new_trend
            skill.trend_rationale = new_rationale

        db.commit()

        print(f"\nDone. {changed}/{len(skills)} skills changed classification.")
        if changed == 0:
            print("(No changes — either the classifier rules haven't changed since "
                  "these skills were last computed, or the data doesn't produce a "
                  "different result under the current rules.)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
