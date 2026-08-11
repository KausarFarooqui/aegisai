"""
LLMProvider abstraction.

This is the direct answer to the MODUS "Model Abstraction" requirement and
to "what happens if your free-tier LLM becomes unavailable mid-demo": the
rest of the codebase (app/intelligence/extraction.py, workers, etc.) never
imports GroqProvider or OllamaProvider directly — it calls
`get_llm_provider().complete_json(...)`, and that function owns the
primary-then-fallback decision. Swapping or adding a provider means adding
one class here, not touching any calling code.

Verification note: GroqProvider and OllamaProvider are written against
each SDK's documented, stable public API, but neither has been exercised
against a live endpoint in the environment this was built in — Groq needs
a real API key (not something to paste into this chat), and Ollama needs
a local model pull that wasn't available in that sandbox either. Run
`python scripts/test_llm_connection.py` after setting GROQ_API_KEY in
.env to confirm this actually talks to Groq before relying on it.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger("aegisai.llm")

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMProviderError(Exception):
    """Base class for all LLM-related failures."""


class LLMUnavailableError(LLMProviderError):
    """Raised for connection failures, timeouts, rate limits — anything that
    means 'try the fallback provider,' as opposed to a validation problem
    with what came back."""


class LLMValidationError(LLMProviderError):
    """Raised when the LLM's output, even after a retry with feedback,
    still doesn't validate against the required schema. The caller (the
    analysis pipeline, Phase 4b) is expected to catch this and mark the
    AnalysisJob as failed with this message — never to substitute
    fabricated data."""


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def _raw_complete(self, system_prompt: str, user_prompt: str) -> str:
        """Returns the raw text response. Raises LLMUnavailableError on any
        connection/rate-limit/timeout failure."""

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[SchemaT],
        max_retries: int = 1,
    ) -> SchemaT:
        """
        Calls the model, parses the response as JSON, validates it against
        `schema`. On a parse/validation failure, retries up to
        `max_retries` times with the validation error appended to the
        prompt so the model can self-correct. If it still fails, raises
        LLMValidationError — the caller must not treat this as "close
        enough" and proceed with an unvalidated result.
        """
        attempt_prompt = user_prompt
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            raw = self._raw_complete(system_prompt, attempt_prompt)
            try:
                parsed = json.loads(raw)
                return schema.model_validate(parsed)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "LLM output failed validation on attempt %d/%d (%s): %s",
                    attempt + 1, max_retries + 1, self.name, exc,
                )
                attempt_prompt = (
                    f"{user_prompt}\n\n"
                    f"Your previous response failed validation with this error:\n"
                    f"{exc}\n\n"
                    f"Return ONLY valid JSON matching the required schema exactly. "
                    f"No prose, no markdown code fences, no explanation."
                )

        raise LLMValidationError(
            f"{self.name} failed to produce valid output for schema "
            f"{schema.__name__} after {max_retries + 1} attempts: {last_error}"
        )


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = None
        self._api_key = api_key

    def _get_client(self):
        if self._client is None:
            from groq import Groq

            self._client = Groq(api_key=self._api_key)
        return self._client

    @retry(
        retry=retry_if_exception_type(LLMUnavailableError),
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        reraise=True,
    )
    def _raw_complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,  # low — this is extraction/classification, not creative writing
            )
            return response.choices[0].message.content
        except Exception as exc:  # groq SDK raises its own exception hierarchy;
            # normalized to LLMUnavailableError so callers only handle one type.
            raise LLMUnavailableError(f"Groq request failed: {exc}") from exc


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    @retry(
        retry=retry_if_exception_type(LLMUnavailableError),
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        reraise=True,
    )
    def _raw_complete(self, system_prompt: str, user_prompt: str) -> str:
        import httpx

        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(f"Ollama request failed: {exc}") from exc


class LLMOrchestrator(LLMProvider):
    """
    Tries the primary provider; on LLMUnavailableError, falls back to the
    secondary. LLMValidationError is NOT caught here — a schema mismatch
    means the prompt or schema needs fixing, not a different provider, so
    it propagates straight to the caller.
    """
    name = "orchestrator"

    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback

    def _raw_complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            return self.primary._raw_complete(system_prompt, user_prompt)
        except LLMUnavailableError as exc:
            logger.warning(
                "Primary provider (%s) unavailable, falling back to %s: %s",
                self.primary.name, self.fallback.name, exc,
            )
            return self.fallback._raw_complete(system_prompt, user_prompt)


def get_llm_provider() -> LLMOrchestrator:
    from app.config.settings import get_settings

    settings = get_settings()
    groq = GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)
    ollama = OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

    if settings.llm_primary_provider == "ollama":
        return LLMOrchestrator(primary=ollama, fallback=groq)
    return LLMOrchestrator(primary=groq, fallback=ollama)
