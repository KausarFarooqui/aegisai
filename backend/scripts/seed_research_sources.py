"""
Loads data/seed/research_sources.py's curated corpus into the
ResearchSource table, embedding each summary with the same
EmbeddingProvider the rest of the app uses (so semantic search over
evidence works identically whether the source was seeded or added later).

Idempotent: matches existing rows by URL, so re-running this after adding
new entries to research_sources.py only inserts the new ones.

Usage:
    cd backend
    python scripts/seed_research_sources.py
"""
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parents[0]
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.intelligence.embeddings import get_embedding_provider  # noqa: E402
from app.models import ResearchSource, SourceType  # noqa: E402
from data.seed.research_sources import RESEARCH_SOURCES, RETRIEVED_DATE  # noqa: E402


def main() -> None:
    db = SessionLocal()
    embeddings = get_embedding_provider()

    try:
        existing_urls = {row[0] for row in db.query(ResearchSource.url).all()}
        to_insert = [s for s in RESEARCH_SOURCES if s["url"] not in existing_urls]

        if not to_insert:
            print(f"All {len(RESEARCH_SOURCES)} research sources already loaded — nothing to do.")
            return

        print(f"Loading {len(to_insert)} new research sources "
              f"({len(RESEARCH_SOURCES) - len(to_insert)} already present)...")

        summaries = [s["summary"] for s in to_insert]
        vectors = embeddings.encode_batch(summaries)

        for source_data, vector in zip(to_insert, vectors):
            record = ResearchSource(
                title=source_data["title"],
                url=source_data["url"],
                source_type=SourceType(source_data["source_type"]),
                publication_date=source_data["publication_date"],
                retrieved_date=RETRIEVED_DATE,
                summary=source_data["summary"],
                embedding=vector,
            )
            db.add(record)
            print(f"  + [{source_data['source_type']}] {source_data['title']}")

        db.commit()
        print(f"\nDone. {len(to_insert)} research sources loaded and embedded.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
