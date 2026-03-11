from __future__ import annotations

from typing import List, Dict
from .schemas import AgentResponse, ExecutiveBrief
from .scoring import relevance_score
from .guardrails import oversight_flags


def score_agents(responses: List[AgentResponse], scenario: str) -> List[AgentResponse]:
    for r in responses:
        r.relevance_score = relevance_score(r.domain, scenario)
    return sorted(responses, key=lambda x: x.relevance_score, reverse=True)


def deep_dive(agent: AgentResponse) -> AgentResponse:
    agent.assumptions.append("Deep-dive: verify assumptions via data pulls and SME review within 24–72 hours.")
    agent.uncertainty_notes.append("Deep-dive: sensitivity analysis may change recommendation ordering.")
    agent.metrics_to_monitor.extend(["Early warning indicators", "Adverse outcome triggers (stop/adjust thresholds)"])
    return agent


def build_executive_brief(scenario: str, ranked: List[AgentResponse], top_k: int = 2) -> ExecutiveBrief:
    top = ranked[:top_k]
    top_domains = [t.domain for t in top]

    appendix: Dict[str, AgentResponse] = {}
    for t in top:
        appendix[t.domain] = deep_dive(t)

    top_risks = []
    uncertainties = []
    metrics = []
    oversight = oversight_flags(scenario)

    for t in top:
        top_risks.extend([ri.risk for ri in t.risks][:2])
        uncertainties.extend(t.uncertainty_notes[:2])
        metrics.extend(t.metrics_to_monitor[:3])

    recommended_path = (
        f"Prioritize a phased, measurable response led by {top_domains[0]} "
        f"with coordination support from {top_domains[1] if len(top_domains) > 1 else top_domains[0]}."
    )

    return ExecutiveBrief(
        scenario=scenario,
        top_domains=top_domains,
        recommended_path=recommended_path,
        key_tradeoffs=[
            "Speed vs. certainty (rapid action increases risk under uncertainty)",
            "Central coordination vs. agency autonomy (coherence vs. execution speed)",
            "Short-term stabilization vs. long-term structural impact",
        ],
        top_risks=list(dict.fromkeys(top_risks))[:5],
        uncertainties=list(dict.fromkeys(uncertainties))[:6],
        immediate_actions_72h=[
            "Confirm legal authorities and decision rights (who can approve what).",
            "Pull the minimum critical data needed to validate top assumptions.",
            "Assign owners + deadlines for implementation milestones.",
            "Define success metrics and stop/adjust thresholds.",
        ],
        actions_30d=[
            "Run scenario simulations and stress tests for best/base/worst cases.",
            "Engage key stakeholders for feasibility and alignment checks.",
            "Deploy monitoring dashboard for metrics and early warning indicators.",
        ],
        actions_180d=[
            "Evaluate outcomes vs. baseline; document lessons learned.",
            "Institutionalize governance: audits, model updates, oversight reviews.",
        ],
        metrics_to_monitor=list(dict.fromkeys(metrics))[:10],
        ethics_and_oversight=[
            "Human-in-the-loop: final decisions remain with leadership.",
            "Document assumptions, uncertainties, and dissenting views.",
            "Civil liberties and privacy reviews for sensitive actions.",
            *oversight,
        ],
        appendix=appendix,
    )