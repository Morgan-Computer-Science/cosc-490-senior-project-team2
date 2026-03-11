from __future__ import annotations
from typing import Dict
import re

DOMAIN_KEYWORDS: Dict[str, list[str]] = {
    "Economy & Markets": ["gdp", "recession", "markets", "growth", "stocks", "trade", "tax", "budget"],
    "National Security": ["terror", "attack", "defense", "military", "intel", "border", "threat"],
    "International Relations": ["allies", "treaty", "sanctions", "diplomacy", "nato", "un", "china", "russia"],
    "Employment & Labor": ["jobs", "unemployment", "wages", "labor", "workforce", "union"],
    "Healthcare & Public Health": ["hospital", "pandemic", "disease", "medicine", "medicaid", "public health"],
    "Climate & Environment": ["climate", "flood", "wildfire", "emissions", "environment", "epa"],
    "Energy": ["oil", "gas", "grid", "electricity", "renewables", "pipeline", "opec"],
    "Technology & Cyber": ["cyber", "ai", "tech", "breach", "infrastructure", "semiconductor", "data"],
    "Public Safety & Homeland Resilience": ["crime", "fema", "disaster", "police", "homeland", "resilience"],
    "Inflation & Cost of Living": ["inflation", "prices", "rent", "groceries", "cost of living", "cpi"],
}

def relevance_score(domain: str, scenario: str) -> float:
    words = re.findall(r"[a-zA-Z']+", scenario.lower())
    text = " ".join(words)
    keys = DOMAIN_KEYWORDS.get(domain, [])
    hits = sum(1 for k in keys if k in text)
    return min(1.0, hits / max(3, int(len(keys) * 0.25)))