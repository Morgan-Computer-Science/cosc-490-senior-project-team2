from __future__ import annotations

import time
from typing import List

from pydantic import ValidationError

from .schemas import AgentResponse
from .guardrails import oversight_flags
from .llm import LLMClient, LLMConfig


# Use flash by default to reduce quota/rate-limit issues
LLM = LLMClient(LLMConfig(mode="vertex", vertex_model="gemini-1.5-flash", temperature=0.2))


def set_llm_runtime(mode: str, model: str, temperature: float):
    LLM.set_runtime(mode=mode, model=model, temperature=temperature)


AGENT_JSON_INSTRUCTIONS = """
Return ONLY valid JSON (no markdown, no backticks).
Follow this schema exactly (field names must match):

{
  "agent_name": "...",
  "domain": "...",
  "relevance_score": 0.0,
  "situation_summary": "...",
  "key_facts_needed": ["..."],
  "assumptions": ["..."],
  "options": [
    {
      "title": "...",
      "summary": "...",
      "pros": ["..."],
      "cons": ["..."],
      "prerequisites": ["..."],
      "estimated_time_to_effect": "...",
      "equity_considerations": ["..."]
    }
  ],
  "recommended_option": "...",
  "rationale": "...",
  "risk_level": "Low|Moderate|High|Severe",
  "risks": [
    {
      "risk": "...",
      "likelihood": "Low|Medium|High",
      "impact": "Low|Medium|High",
      "mitigation": "..."
    }
  ],
  "confidence": "Low|Medium|High",
  "uncertainty_notes": ["..."],
  "metrics_to_monitor": ["..."],
  "human_oversight_flags": ["..."]
}
""".strip()


def _fallback_agent(agent_name: str, domain: str, scenario: str, error_text: str) -> AgentResponse:
    flags = oversight_flags(scenario)
    return AgentResponse(
        agent_name=agent_name,
        domain=domain,
        relevance_score=0.0,
        situation_summary=f"{domain}: (Fallback) Gemini output failed. Using minimal safe response.",
        key_facts_needed=[
            "Confirm legal authorities and approval chain",
            "Pull authoritative datasets and incident reports",
            "Consult SMEs and agency leads for validation",
        ],
        assumptions=["Model output invalid or quota-limited; require human review."],
        options=[],
        recommended_option="",
        rationale=error_text[:700],
        risk_level="Moderate",
        risks=[],
        confidence="Low",
        uncertainty_notes=["Re-run with fewer domains, lower temperature, or wait 1–2 minutes."],
        metrics_to_monitor=[],
        human_oversight_flags=flags,
    )


def build_domain_response(agent_name: str, domain: str, scenario: str) -> AgentResponse:
    flags = oversight_flags(scenario)

    system = f"""
You are {agent_name}, a top-level policy advisor for the domain: {domain}.
You must be non-partisan, lawful, safety-focused, and emphasize human oversight.
Do not propose illegal actions or civil-liberties violations.
Be concise and executive-usable.
{AGENT_JSON_INSTRUCTIONS}
""".strip()

    user = f"""
Scenario:
{scenario}

Requirements:
- Provide at least 2 options with clear tradeoffs.
- Include risks, mitigations, and uncertainty notes.
- Include monitoring metrics.
- Include human oversight flags.
- Avoid partisan or campaign language.

These oversight flags MUST be included (verbatim) if relevant:
{flags}
""".strip()

    try:
        data = LLM.generate_json(system=system, user=user)

        # If llm.py returns an error-json fallback, convert to AgentResponse fallback
        if isinstance(data, dict) and data.get("error") is True:
            return _fallback_agent(agent_name, domain, scenario, str(data.get("details", data)))

        # force oversight flags from our layer
        if "human_oversight_flags" not in data or not isinstance(data["human_oversight_flags"], list):
            data["human_oversight_flags"] = []
        for f in flags:
            if f not in data["human_oversight_flags"]:
                data["human_oversight_flags"].append(f)

        return AgentResponse.model_validate(data)

    except (ValueError, ValidationError) as e:
        return _fallback_agent(agent_name, domain, scenario, str(e))


def all_domain_agents(scenario: str, throttle_seconds: float = 1.2) -> List[AgentResponse]:
    """
    Runs the 10 domain agents sequentially with throttling to reduce 429 rate limits.
    """
    domains = [
        ("Economy Agent", "Economy & Markets"),
        ("National Security Agent", "National Security"),
        ("International Relations Agent", "International Relations"),
        ("Employment Agent", "Employment & Labor"),
        ("Healthcare Agent", "Healthcare & Public Health"),
        ("Climate Agent", "Climate & Environment"),
        ("Energy Agent", "Energy"),
        ("Technology Agent", "Technology & Cyber"),
        ("Public Safety Agent", "Public Safety & Homeland Resilience"),
        ("Inflation Agent", "Inflation & Cost of Living"),
    ]

    responses: List[AgentResponse] = []
    for a, d in domains:
        responses.append(build_domain_response(a, d, scenario))
        time.sleep(throttle_seconds)  # throttle to avoid 429

    return responses