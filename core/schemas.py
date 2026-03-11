from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Literal, Dict

RiskLevel = Literal["Low", "Moderate", "High", "Severe"]
Confidence = Literal["Low", "Medium", "High"]


class RiskItem(BaseModel):
    risk: str
    likelihood: Literal["Low", "Medium", "High"]
    impact: Literal["Low", "Medium", "High"]
    mitigation: str


class Option(BaseModel):
    title: str
    summary: str
    pros: List[str]
    cons: List[str]
    prerequisites: List[str] = Field(default_factory=list)
    estimated_time_to_effect: str = "Unknown"
    equity_considerations: List[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    agent_name: str
    domain: str
    relevance_score: float = 0.0
    situation_summary: str
    key_facts_needed: List[str]
    assumptions: List[str]
    options: List[Option]
    recommended_option: str
    rationale: str
    risk_level: RiskLevel
    risks: List[RiskItem]
    confidence: Confidence
    uncertainty_notes: List[str]
    metrics_to_monitor: List[str]
    human_oversight_flags: List[str]


class ExecutiveBrief(BaseModel):
    scenario: str
    top_domains: List[str]
    recommended_path: str
    key_tradeoffs: List[str]
    top_risks: List[str]
    uncertainties: List[str]
    immediate_actions_72h: List[str]
    actions_30d: List[str]
    actions_180d: List[str]
    metrics_to_monitor: List[str]
    ethics_and_oversight: List[str]
    appendix: Dict[str, AgentResponse]
    