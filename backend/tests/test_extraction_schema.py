"""
Tests for app/schemas/extraction.py — the contract enforced on every LLM
extraction response, regardless of provider. Pure Pydantic validation,
no LLM call needed.
"""
import pytest
from pydantic import ValidationError

from app.schemas.extraction import EntityExtractionResult


def _valid_payload() -> dict:
    return {
        "business_purpose": "Assess creditworthiness of loan applicants using financial history.",
        "current_challenges": "Manual document review is slow and error-prone.",
        "activities": [
            {
                "name": "Review applicant financial statements",
                "description": "Manual review of submitted documents.",
                "performed_by_role_titles": ["Credit Analyst"],
            }
        ],
        "roles": [
            {"title": "Credit Analyst", "is_new": False, "requires_skill_names": ["Credit Risk Assessment"]}
        ],
        "skills": [{"name": "Credit Risk Assessment", "category": "analytical", "is_new": False}],
        "ai_opportunities": [
            {
                "name": "Automated Document Extraction",
                "description": "Extract structured data from loan documents automatically.",
                "automation_potential": "high",
                "human_ai_responsibility": "ai_automates",
                "business_benefit": "Faster loan processing turnaround.",
                "risks": "Extraction errors on non-standard document formats.",
                "affected_activity_names": ["Review applicant financial statements"],
                "factor_repetitiveness": {"value": 90, "reason": "Same document types processed daily."},
                "factor_data_availability": {"value": 85, "reason": "Digitized documents already available."},
                "factor_predictability": {"value": 80, "reason": "Document structure is fairly consistent."},
                "factor_digitalization": {"value": 75, "reason": "Most documents are already digital."},
                "factor_ai_capability_fit": {"value": 88, "reason": "Document extraction is a mature AI capability."},
            }
        ],
    }


def test_valid_extraction_result_parses_cleanly():
    result = EntityExtractionResult.model_validate(_valid_payload())
    assert result.roles[0].title == "Credit Analyst"
    assert result.ai_opportunities[0].factor_repetitiveness.value == 90


def test_rejects_factor_value_out_of_range():
    payload = _valid_payload()
    payload["ai_opportunities"][0]["factor_repetitiveness"]["value"] = 150
    with pytest.raises(ValidationError):
        EntityExtractionResult.model_validate(payload)


def test_rejects_empty_activities_list():
    payload = _valid_payload()
    payload["activities"] = []
    with pytest.raises(ValidationError):
        EntityExtractionResult.model_validate(payload)


def test_rejects_too_many_ai_opportunities():
    payload = _valid_payload()
    payload["ai_opportunities"] = payload["ai_opportunities"] * 6  # max is 5
    with pytest.raises(ValidationError):
        EntityExtractionResult.model_validate(payload)


def test_rejects_duplicate_role_titles():
    payload = _valid_payload()
    payload["roles"] = [
        {"title": "Credit Analyst", "is_new": False, "requires_skill_names": ["Credit Risk Assessment"]},
        {"title": "credit analyst", "is_new": True, "requires_skill_names": ["Credit Risk Assessment"]},  # same name, different case
    ]
    with pytest.raises(ValidationError, match="Duplicate names"):
        EntityExtractionResult.model_validate(payload)


def test_rejects_too_short_business_purpose():
    payload = _valid_payload()
    payload["business_purpose"] = "Too short"[:5]
    with pytest.raises(ValidationError):
        EntityExtractionResult.model_validate(payload)


def test_rejects_missing_required_field():
    payload = _valid_payload()
    del payload["skills"]
    with pytest.raises(ValidationError):
        EntityExtractionResult.model_validate(payload)


def test_rejects_activity_referencing_nonexistent_role():
    payload = _valid_payload()
    payload["activities"][0]["performed_by_role_titles"] = ["Nonexistent Role"]
    with pytest.raises(ValidationError, match="not in the roles list"):
        EntityExtractionResult.model_validate(payload)


def test_rejects_role_referencing_nonexistent_skill():
    payload = _valid_payload()
    payload["roles"][0]["requires_skill_names"] = ["Nonexistent Skill"]
    with pytest.raises(ValidationError, match="not in the skills list"):
        EntityExtractionResult.model_validate(payload)


def test_rejects_opportunity_referencing_nonexistent_activity():
    payload = _valid_payload()
    payload["ai_opportunities"][0]["affected_activity_names"] = ["Nonexistent Activity"]
    with pytest.raises(ValidationError, match="not in the activities list"):
        EntityExtractionResult.model_validate(payload)


def test_cross_reference_matching_is_case_insensitive():
    """The LLM shouldn't be penalized for trivial casing differences —
    only genuinely dangling references should fail."""
    payload = _valid_payload()
    payload["activities"][0]["performed_by_role_titles"] = ["CREDIT ANALYST"]
    result = EntityExtractionResult.model_validate(payload)
    assert result.activities[0].performed_by_role_titles == ["CREDIT ANALYST"]
