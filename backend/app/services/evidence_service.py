"""
EvidenceService — best-effort semantic search linking an AIOpportunity to
supporting research, via the curated ResearchSource corpus
(data/seed/research_sources.py).

Deliberately reuses app.services.dedup_service.find_best_match — the
underlying operation ("given a query embedding, find the closest existing
row above a similarity threshold, or admit nothing qualifies") is
identical to entity dedup; only what's being searched differs (research
sources here, roles/skills there). No reason to maintain two copies of
that logic.

This is explicitly best-effort: if no research source clears the
similarity threshold, no Evidence record is created and the pipeline
continues normally — the MODUS brief requires distinguishing "no research
available" from a fabricated citation, not requiring evidence to exist for
every opportunity.
"""
from app.models import AIOpportunity, Evidence, RelatedEntityType
from app.repositories.entity_repository import ResearchSourceRepository
from app.services.dedup_service import EntityCandidate, find_best_match


class EvidenceService:
    def __init__(self, db, embedding_provider, relevance_threshold: float):
        self.db = db
        self.embeddings = embedding_provider
        self.threshold = relevance_threshold
        self.research_sources = ResearchSourceRepository(db)

    def find_evidence_for_opportunity(self, opportunity: AIOpportunity) -> Evidence | None:
        """
        Returns a new, unsaved Evidence instance if a sufficiently relevant
        research source exists, else None. Caller is responsible for
        adding it to the session — kept as a pure lookup here so it's
        trivially testable without a live DB write.
        """
        query_text = f"{opportunity.name}. {opportunity.description or ''}".strip()
        query_embedding = self.embeddings.encode(query_text)

        candidates = self.research_sources.find_similar(query_embedding, limit=3)
        entity_candidates = [
            EntityCandidate(entity_id=str(c.id), name=c.title, embedding=c.embedding)
            for c in candidates
        ]
        match = find_best_match(query_embedding, entity_candidates, self.threshold)
        if not match.matched:
            return None

        source = next(c for c in candidates if str(c.id) == match.candidate.entity_id)
        return Evidence(
            research_source=source,
            related_entity_type=RelatedEntityType.AI_OPPORTUNITY,
            related_entity_id=opportunity.id,
            extracted_finding=source.summary,
            relevance_score=match.similarity,
            confidence=match.similarity,
            # NOTE: confidence is set equal to the raw similarity score as a
            # deliberate simplification for this phase — the schema (see
            # app/models/evidence.py) anticipates confidence coming from a
            # separate LLM judgment of whether the source actually supports
            # the finding, distinct from embedding similarity. Adding that
            # would mean one more LLM call per AI opportunity, meaningfully
            # increasing pipeline latency for a refinement that doesn't
            # change what's demonstrable right now. Documented here and in
            # the decision log as a known, intentional scope boundary.
        )
