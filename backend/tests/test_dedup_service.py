"""
Tests for app/services/dedup_service.py using synthetic vectors.

These deliberately do NOT depend on sentence-transformers/torch being
installed — the matching algorithm (cosine similarity + thresholding) is
correct or incorrect independent of what produces the vectors, so it's
tested in isolation here. See app/intelligence/embeddings.py's docstring
and scripts/verify_embeddings.py for how the real model is verified
separately, on a machine with room for torch.
"""
import numpy as np
import pytest

from app.services.dedup_service import EntityCandidate, cosine_similarity, find_best_match


def test_cosine_similarity_identical_vectors_is_one():
    v = [0.1, 0.5, -0.3, 0.8]
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_opposite_vectors_is_negative_one():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_similarity_handles_zero_vector_without_crashing():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def _perturb(vector: list[float], noise: float, seed: int) -> list[float]:
    """Simulates two embeddings of near-synonymous text: same direction,
    small random perturbation — roughly what 'Data Analyst' vs
    'Data Analyst II' would look like as real embeddings."""
    rng = np.random.default_rng(seed)
    arr = np.array(vector) + rng.normal(0, noise, size=len(vector))
    return arr.tolist()


def test_find_best_match_returns_no_match_when_candidates_empty():
    result = find_best_match([0.1, 0.2], [], similarity_threshold=0.86)
    assert result.matched is False
    assert result.candidate is None
    assert result.all_scores == []


def test_find_best_match_finds_near_duplicate_above_threshold():
    """The core Surprise Record Test scenario: a near-synonymous name
    should match an existing entity rather than create a duplicate."""
    base = [0.5, -0.2, 0.8, 0.1, -0.4, 0.3, 0.6, -0.1] * 4  # 32-dim toy vector
    existing = EntityCandidate(
        entity_id="role-1", name="Data Analyst", embedding=base
    )
    query = _perturb(base, noise=0.01, seed=1)  # tiny perturbation -> near-duplicate

    result = find_best_match(query, [existing], similarity_threshold=0.86)
    assert result.matched is True
    assert result.candidate.name == "Data Analyst"
    assert result.similarity > 0.86


def test_find_best_match_rejects_genuinely_different_entity():
    """A genuinely different role should NOT match, even if it's the only
    candidate — this is what proves the system creates new entities rather
    than forcing everything into existing ones."""
    role_a = [1.0, 0.0, 0.0, 0.0] * 8
    role_b_query = [0.0, 1.0, 0.0, 0.0] * 8  # orthogonal -> unrelated concept

    existing = EntityCandidate(entity_id="role-1", name="Data Analyst", embedding=role_a)
    result = find_best_match(role_b_query, [existing], similarity_threshold=0.86)

    assert result.matched is False
    assert result.candidate is None
    assert result.similarity < 0.86
    # Even on a non-match, the score is surfaced — this is what lets the UI
    # show "closest match was 0.0, below threshold, created new entity"
    assert result.all_scores == [("Data Analyst", pytest.approx(0.0, abs=1e-6))]


def test_find_best_match_picks_the_closest_of_multiple_candidates():
    base = [0.5, 0.5, 0.5, 0.5] * 8
    close = _perturb(base, noise=0.02, seed=2)
    far = [-0.5, 0.1, 0.2, -0.3] * 8

    candidates = [
        EntityCandidate(entity_id="role-1", name="Unrelated Role", embedding=far),
        EntityCandidate(entity_id="role-2", name="Credit Analyst", embedding=close),
    ]
    query = _perturb(base, noise=0.01, seed=3)

    result = find_best_match(query, candidates, similarity_threshold=0.86)
    assert result.matched is True
    assert result.candidate.name == "Credit Analyst"
    # all_scores must be sorted descending by similarity
    assert result.all_scores[0][0] == "Credit Analyst"
    assert result.all_scores[0][1] >= result.all_scores[1][1]


def test_find_best_match_respects_configurable_threshold():
    """Same inputs, different threshold -> different outcome. Proves the
    threshold isn't hard-coded into the matching logic itself."""
    base = [0.3, 0.6, -0.2, 0.4] * 8
    existing = EntityCandidate(entity_id="role-1", name="Compliance Officer", embedding=base)
    query = _perturb(base, noise=0.15, seed=4)  # moderate drift

    loose = find_best_match(query, [existing], similarity_threshold=0.50)
    strict = find_best_match(query, [existing], similarity_threshold=0.999)

    assert loose.matched is True
    assert strict.matched is False
    assert loose.similarity == strict.similarity  # same underlying score either way
