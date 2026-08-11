"""
Verifies app/intelligence/llm_provider.py against the REAL Groq API (and
Ollama, if running locally). This needs your actual GROQ_API_KEY in .env —
that's exactly why it couldn't be run in the environment this codebase was
developed in, and why it's a separate script rather than an automated test.

Usage:
    cd backend
    python scripts/test_llm_connection.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel  # noqa: E402

from app.config.settings import get_settings  # noqa: E402
from app.intelligence.llm_provider import (  # noqa: E402
    GroqProvider,
    LLMUnavailableError,
    LLMValidationError,
    OllamaProvider,
    get_llm_provider,
)


class SanityCheckSchema(BaseModel):
    capital_city: str
    country: str


def main() -> None:
    settings = get_settings()

    print(f"Configured primary provider: {settings.llm_primary_provider}")
    print(f"Groq model: {settings.groq_model}")
    print(f"Ollama: {settings.ollama_base_url} ({settings.ollama_model})\n")

    print("--- Testing Groq directly ---")
    if not settings.groq_api_key or settings.groq_api_key.startswith("your_"):
        print("SKIPPED: GROQ_API_KEY not set in .env. Get one free at "
              "https://console.groq.com/keys and set it before running this.")
    else:
        try:
            groq = GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)
            result = groq.complete_json(
                system_prompt="Respond only with JSON matching the schema. No prose.",
                user_prompt='What is the capital of France? Respond as '
                            '{"capital_city": "...", "country": "..."}',
                schema=SanityCheckSchema,
            )
            print(f"PASS: Groq responded and validated: {result.model_dump()}")
        except (LLMUnavailableError, LLMValidationError) as exc:
            print(f"FAIL: {exc}")

    print("\n--- Testing Ollama directly (skips cleanly if not running) ---")
    try:
        ollama = OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)
        result = ollama.complete_json(
            system_prompt="Respond only with JSON matching the schema. No prose.",
            user_prompt='What is the capital of France? Respond as '
                        '{"capital_city": "...", "country": "..."}',
            schema=SanityCheckSchema,
        )
        print(f"PASS: Ollama responded and validated: {result.model_dump()}")
    except LLMUnavailableError as exc:
        print(f"SKIPPED (expected if Ollama isn't running locally): {exc}")
    except LLMValidationError as exc:
        print(f"FAIL: Ollama responded but output didn't validate: {exc}")

    print("\n--- Testing the orchestrator (primary -> fallback wiring) ---")
    orchestrator = get_llm_provider()
    try:
        result = orchestrator.complete_json(
            system_prompt="Respond only with JSON matching the schema. No prose.",
            user_prompt='What is the capital of Japan? Respond as '
                        '{"capital_city": "...", "country": "..."}',
            schema=SanityCheckSchema,
        )
        print(f"PASS: Orchestrator responded (via {settings.llm_primary_provider} or its "
              f"fallback): {result.model_dump()}")
    except (LLMUnavailableError, LLMValidationError) as exc:
        print(f"FAIL: both providers unavailable or invalid — {exc}")


if __name__ == "__main__":
    main()
