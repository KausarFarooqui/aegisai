"""
Entity dedup / matching service.

This is the single mechanism that stops the dynamic analysis pipeline
(Phase 4b/5) from creating "Data Analyst" and "Data Analyst II" as two
separate roles every time someone types a slightly different name into the
Surprise Record Test. When the LLM proposes a role/skill/activity name, this
module is what decides "reuse an existing entity" vs. "this is genuinely
new" — a decision that is NOT made by the LLM, on purpose. That separation
is the actual answer to "how do you prevent duplication/hallucination,"
not a prompting trick.

Deliberately decoupled from HOW the vectors are produced (see
app/intelligence/embeddings.py) — this module only does cosine similarity
and thresholding on plain float vectors. That decoupling is what makes it
fully unit-testable with synthetic vectors, independent of whether the
actual sentence-transformers model is available in a given environment.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EntityCandidate:
    """One existing DB entity being considered as a match — decoupled from
    any particular ORM model so this works identically for Role, Skill,
    Activity, or Process candidates."""
    entity_id: str
    name: str
    embedding: list[float]


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    candidate: EntityCandidate | None
    similarity: float
    """Highest cosine similarity found, whether or not it cleared the
    threshold — always returned so the caller/UI can show 'closest match
    was 0.71, below the 0.86 threshold, so a new entity was created'
    rather than a bare yes/no."""
    all_scores: list[tuple[str, float]]
    """(entity_name, similarity) for every candidate considered, sorted
    descending — full transparency for the 'why was this matched or not'
    explanation panel."""


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a, dtype=np.float64), np.array(b, dtype=np.float64)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def find_best_match(
    query_embedding: list[float],
    candidates: list[EntityCandidate],
    similarity_threshold: float,
) -> MatchResult:
    """
    Returns the best-matching existing entity if its similarity clears
    `similarity_threshold` (from Settings.entity_similarity_threshold,
    default 0.86 — tuned during Day-1 seeding, not hard-coded here).

    If `candidates` is empty, or nothing clears the threshold, `matched`
    is False and the caller should create a new entity — this function
    never invents a match.
    """
    if not candidates:
        return MatchResult(matched=False, candidate=None, similarity=0.0, all_scores=[])

    scored = [
        (c, cosine_similarity(query_embedding, c.embedding)) for c in candidates
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    best_candidate, best_score = scored[0]
    all_scores = [(c.name, round(score, 4)) for c, score in scored]

    if best_score >= similarity_threshold:
        return MatchResult(
            matched=True, candidate=best_candidate, similarity=round(best_score, 4),
            all_scores=all_scores,
        )
    return MatchResult(
        matched=False, candidate=None, similarity=round(best_score, 4),
        all_scores=all_scores,
    )
