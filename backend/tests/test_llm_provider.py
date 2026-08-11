"""
Tests for app/intelligence/llm_provider.py's control flow — fallback
switching and the retry-then-fail validation loop — using fake providers
that never touch the network. This is deliberately separate from actually
verifying Groq/Ollama respond correctly (see scripts/test_llm_connection.py,
which needs a real API key and can't run in an automated test suite).
"""
import json

import pytest
from pydantic import BaseModel

from app.intelligence.llm_provider import (
    LLMOrchestrator,
    LLMProvider,
    LLMUnavailableError,
    LLMValidationError,
)


class DummySchema(BaseModel):
    value: int


class FakeProvider(LLMProvider):
    """A provider whose behavior is scripted for testing: raises on the
    first N calls, then returns `response`."""

    def __init__(self, name: str, response: str | None = None, fail_times: int = 0):
        self.name = name
        self.response = response
        self.fail_times = fail_times
        self.calls = 0

    def _raw_complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise LLMUnavailableError(f"{self.name} simulated failure #{self.calls}")
        return self.response


def test_complete_json_succeeds_on_valid_first_response():
    provider = FakeProvider("primary", response=json.dumps({"value": 42}))
    result = provider.complete_json("sys", "user", DummySchema)
    assert result.value == 42
    assert provider.calls == 1


def test_complete_json_retries_once_then_succeeds():
    """Simulates the model returning malformed JSON once, then valid JSON —
    the retry-with-feedback path."""
    responses = iter(["not json at all", json.dumps({"value": 7})])

    class FlakyProvider(LLMProvider):
        name = "flaky"

        def _raw_complete(self, system_prompt, user_prompt):
            return next(responses)

    result = FlakyProvider().complete_json("sys", "user", DummySchema, max_retries=1)
    assert result.value == 7


def test_complete_json_raises_llm_validation_error_after_exhausting_retries():
    provider = FakeProvider("always-broken", response="not json")
    with pytest.raises(LLMValidationError):
        provider.complete_json("sys", "user", DummySchema, max_retries=1)
    assert provider.calls == 2  # initial attempt + 1 retry, no more


def test_complete_json_rejects_json_that_doesnt_match_schema():
    provider = FakeProvider("wrong-shape", response=json.dumps({"wrong_field": "x"}))
    with pytest.raises(LLMValidationError):
        provider.complete_json("sys", "user", DummySchema, max_retries=0)


# --- Orchestrator fallback behavior ---

def test_orchestrator_uses_primary_when_it_succeeds():
    primary = FakeProvider("primary", response="ok-primary", fail_times=0)
    fallback = FakeProvider("fallback", response="ok-fallback", fail_times=0)
    orchestrator = LLMOrchestrator(primary=primary, fallback=fallback)

    result = orchestrator._raw_complete("sys", "user")
    assert result == "ok-primary"
    assert primary.calls == 1
    assert fallback.calls == 0


def test_orchestrator_falls_back_when_primary_unavailable():
    """The core resilience test: if Groq (primary) is down/rate-limited,
    the orchestrator must transparently use Ollama (fallback) instead of
    raising — this is what makes 'what if the free-tier service goes
    away' a solved problem rather than a hypothetical."""
    primary = FakeProvider("primary", fail_times=99)  # fails on every call
    fallback = FakeProvider("fallback", response="ok-fallback", fail_times=0)
    orchestrator = LLMOrchestrator(primary=primary, fallback=fallback)

    result = orchestrator._raw_complete("sys", "user")
    assert result == "ok-fallback"
    assert fallback.calls == 1


def test_orchestrator_propagates_error_when_both_providers_unavailable():
    primary = FakeProvider("primary", fail_times=99)
    fallback = FakeProvider("fallback", fail_times=99)
    orchestrator = LLMOrchestrator(primary=primary, fallback=fallback)

    with pytest.raises(LLMUnavailableError):
        orchestrator._raw_complete("sys", "user")
