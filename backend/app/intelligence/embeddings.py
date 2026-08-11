"""
EmbeddingProvider — wraps a local sentence-transformers model.

Deliberately the one piece of the AI pipeline with NO external dependency:
no API key, no rate limit, nothing that can go paid or disappear. This is
what backs both the entity-dedup mechanism (app/services/dedup_service.py)
and the evidence semantic search (Phase 4b) — both load-bearing for the
Surprise Record Test, so both need to work with zero chance of an outage
mid-demo.

Verification note (read before trusting this blind): the matching/threshold
logic this feeds into (app/services/dedup_service.py) has been fully unit
tested with synthetic vectors — that logic is proven correct regardless of
what produces the vectors. This specific class — the sentence-transformers
model load and .encode() call — could NOT be executed in the sandbox this
was built in due to a disk-space ceiling on the CPU-only torch wheel
(pytorch.org's trimmed CPU index isn't reachable from that sandbox's
network allowlist, and the default PyPI torch wheel pulls several GB of
CUDA runtime deps that didn't fit). Run `python scripts/verify_embeddings.py`
after `pip install -r requirements.txt` on your machine to confirm this
class works end to end before relying on it — that script is a 10-second
sanity check, not optional homework.
"""
from functools import lru_cache

import numpy as np


class EmbeddingProvider:
    def __init__(self, model_name: str, dimensions: int):
        self.model_name = model_name
        self.dimensions = dimensions
        self._model = None  # lazy-loaded — importing sentence_transformers at
        # module import time would make every file that imports this module
        # pay the (multi-second) model-load cost, including tests that never
        # need it.

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # local import, see above

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, text: str) -> list[float]:
        """Returns a single embedding vector as a plain list[float] — the
        shape pgvector's SQLAlchemy column type expects directly."""
        vector = self._get_model().encode(text, normalize_embeddings=True)
        return vector.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Batched version — used by the seed script so embedding ~50
        evidence summaries doesn't mean 50 separate model calls."""
        vectors = self._get_model().encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    from app.config.settings import get_settings

    settings = get_settings()
    return EmbeddingProvider(settings.embedding_model, settings.embedding_dimensions)
