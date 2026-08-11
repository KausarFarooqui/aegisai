"""
Verifies app/intelligence/embeddings.py against the REAL sentence-transformers
model. Run this once after `pip install -r requirements.txt`, before trusting
the dedup pipeline — this could not be run in the environment this codebase
was developed in due to a disk-space ceiling on the torch install (see the
docstring in app/intelligence/embeddings.py for exactly why).

Usage:
    cd backend
    python scripts/verify_embeddings.py

Expected output: three similarity scores, with the near-duplicate pair
scoring meaningfully higher than the unrelated pair. If the near-duplicate
score is NOT higher, something is wrong before this touches real data —
stop and investigate rather than proceeding to seed the database.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.intelligence.embeddings import get_embedding_provider  # noqa: E402
from app.services.dedup_service import cosine_similarity  # noqa: E402


def main() -> None:
    print(f"Loading model... (this downloads the model on first run)")
    provider = get_embedding_provider()
    print(f"Model: {provider.model_name} (expected dim: {provider.dimensions})")

    pairs = [
        ("Data Analyst", "Data Analyst II", "near-duplicate (should score HIGH)"),
        ("Data Analyst", "Compliance Officer", "unrelated role (should score LOW)"),
        ("Credit Risk Assessment", "Credit Risk Analysis", "near-duplicate (should score HIGH)"),
    ]

    print("\n--- Similarity checks ---")
    results = []
    for text_a, text_b, expectation in pairs:
        vec_a = provider.encode(text_a)
        vec_b = provider.encode(text_b)

        assert len(vec_a) == provider.dimensions, (
            f"Embedding dimension mismatch: got {len(vec_a)}, "
            f"expected {provider.dimensions}. Check EMBEDDING_DIMENSIONS in "
            f".env matches the actual model's output size."
        )

        sim = cosine_similarity(vec_a, vec_b)
        results.append((text_a, text_b, sim, expectation))
        print(f'  "{text_a}" vs "{text_b}": {sim:.4f}  [{expectation}]')

    near_dup_scores = [r[2] for r in results if "HIGH" in r[3]]
    unrelated_scores = [r[2] for r in results if "LOW" in r[3]]

    print("\n--- Sanity check ---")
    if min(near_dup_scores) > max(unrelated_scores):
        print("PASS: near-duplicate pairs score higher than the unrelated pair.")
        print(f"      near-duplicate range: {min(near_dup_scores):.4f}-{max(near_dup_scores):.4f}")
        print(f"      unrelated score:      {max(unrelated_scores):.4f}")
        print(
            f"\nSuggested ENTITY_SIMILARITY_THRESHOLD starting point: "
            f"{(min(near_dup_scores) + max(unrelated_scores)) / 2:.2f} "
            f"(midpoint — tune against your real seed data on Day 1)."
        )
    else:
        print("FAIL: near-duplicate scores did not separate cleanly from the "
              "unrelated pair. Do not proceed to seeding until this is resolved.")
        sys.exit(1)


if __name__ == "__main__":
    main()
