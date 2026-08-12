"""
Prompt construction for entity extraction.

Kept separate from app/workers/analysis_pipeline.py so the prompt text can
be iterated on (a lot, probably, once you're looking at real Groq output
against real seed data) without touching orchestration/error-handling code.
"""


SYSTEM_PROMPT = """You are an enterprise business process analyst for AEGISAI, \
an AI workforce impact intelligence platform for a fictional retail bank \
("Northstar Bank"). You analyze a named business process and identify its \
activities, the roles that perform them, the skills those roles require, \
and realistic AI opportunities that could affect the process.

You must respond with ONLY valid JSON matching the exact schema you are \
given. No prose, no markdown code fences, no explanation before or after \
the JSON.

For each AI opportunity, propose five factor scores from 0-100 with a \
one-line reason each:
- repetitiveness: how repetitive/routine the underlying activity is
- data_availability: how available structured/digital data is for this task
- predictability: how predictable outcomes/decisions are
- digitalization: how digitized the current process already is
- ai_capability_fit: how well current AI capabilities match this task

Do NOT compute or state a final combined score or impact rating yourself — \
only provide the five individual factor values and reasons. A separate \
deterministic system computes the final score from your inputs.

Be realistic and specific to banking operations. Do not invent business \
benefits or risks that don't plausibly apply. If you believe a role or \
skill is very likely to already exist at a bank in a similar form to one \
listed in "Existing roles/skills you may reuse" below, set is_new=false \
and use a title/name closely matching the existing one — this is only a \
hint for downstream matching, not a final decision."""


def build_process_extraction_prompt(
    process_name: str,
    process_context: str | None,
    existing_role_titles: list[str],
    existing_skill_names: list[str],
) -> tuple[str, str]:
    existing_roles_block = (
        ", ".join(existing_role_titles) if existing_role_titles else "(none yet)"
    )
    existing_skills_block = (
        ", ".join(existing_skill_names) if existing_skill_names else "(none yet)"
    )
    context_line = f"\nAdditional context provided: {process_context}" if process_context else ""

    user_prompt = f"""Analyze this business process for Northstar Bank:

Process name: "{process_name}"{context_line}

Existing roles you may reuse if genuinely applicable: {existing_roles_block}
Existing skills you may reuse if genuinely applicable: {existing_skills_block}

Respond with ONLY a JSON object matching this exact structure:
{{
  "business_purpose": "1-3 sentences on why this process exists",
  "current_challenges": "1-2 sentences on typical problems with this process today",
  "activities": [
    {{"name": "...", "description": "...", "performed_by_role_titles": ["must match a title in roles below"]}}
  ],
  "roles": [
    {{"title": "...", "is_new": true or false, "requires_skill_names": ["must match a name in skills below"]}}
  ],
  "skills": [
    {{"name": "...", "category": "technical|analytical|interpersonal|regulatory", "is_new": true or false}}
  ],
  "ai_opportunities": [
    {{
      "name": "...",
      "description": "...",
      "automation_potential": "low" or "medium" or "high",
      "human_ai_responsibility": "ai_automates" or "ai_augments" or "human_led" or "human_approval_required",
      "business_benefit": "...",
      "risks": "...",
      "affected_activity_names": ["must match a name in activities above"],
      "factor_repetitiveness": {{"value": 0-100, "reason": "..."}},
      "factor_data_availability": {{"value": 0-100, "reason": "..."}},
      "factor_predictability": {{"value": 0-100, "reason": "..."}},
      "factor_digitalization": {{"value": 0-100, "reason": "..."}},
      "factor_ai_capability_fit": {{"value": 0-100, "reason": "..."}}
    }}
  ]
}}

Every cross-reference (performed_by_role_titles, requires_skill_names, \
affected_activity_names) MUST exactly match a name/title that appears \
elsewhere in this same response — invalid references will be rejected. \
Provide 2-6 activities, 1-4 roles, 2-8 skills, and 1-3 AI opportunities. \
Every name must be unique within its own list."""

    return SYSTEM_PROMPT, user_prompt
