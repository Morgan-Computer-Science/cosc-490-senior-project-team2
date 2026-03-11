from __future__ import annotations

from pydantic import ValidationError

from .llm import LLMClient, LLMConfig
from .schemas import ExecutiveBrief, RedTeamReport


LLM = LLMClient(LLMConfig(mode="vertex", vertex_model="gemini-2.0-flash", temperature=0.3))

def set_llm_runtime(mode: str, model: str, temperature: float):
    LLM.set_runtime(mode=mode, model=model, temperature=temperature)


REDTEAM_SYSTEM = """
You are a Red Team analyst for an AI decision-support system.
Your job is to stress-test recommendations and find weaknesses:
- hidden assumptions
- second-order effects
- operational failure modes
- civil liberties / fairness risks
- alternative options not considered
Be non-partisan and safety-focused.

Return ONLY valid JSON matching this schema:
{
  "scenario":"...",
  "critique_summary":"...",
  "failure_modes":["..."],
  "hidden_assumptions":["..."],
  "second_order_effects":["..."],
  "fairness_and_rights_risks":["..."],
  "operational_risks":["..."],
  "alternative_options":["..."],
  "questions_for_humans":["..."],
  "overall_risk_posture":"Low|Moderate|High|Severe"
}
""".strip()


def run_red_team(scenario: str, brief: ExecutiveBrief) -> RedTeamReport:
    user = f"""
Scenario:
{scenario}

Executive brief recommended path:
{brief.recommended_path}

Key tradeoffs:
{brief.key_tradeoffs}

Top risks:
{brief.top_risks}

Uncertainties:
{brief.uncertainties}

Now red-team it thoroughly.
""".strip()

    try:
        data = LLM.generate_json(system=REDTEAM_SYSTEM, user=user)
        return RedTeamReport.model_validate(data)
    except (ValueError, ValidationError) as e:
        return RedTeamReport(
            scenario=scenario,
            critique_summary="(Fallback) Red team failed to parse model output. Re-run with lower temperature.",
            failure_modes=["Model output invalid or not JSON."],
            hidden_assumptions=[],
            second_order_effects=[],
            fairness_and_rights_risks=[],
            operational_risks=[],
            alternative_options=[],
            questions_for_humans=[str(e)[:500]],
            overall_risk_posture="Moderate",
        )