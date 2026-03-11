from __future__ import annotations
from typing import List


def oversight_flags(scenario: str) -> List[str]:
    flags = []
    s = scenario.lower()

    if "election" in s or "campaign" in s or "vote" in s:
        flags.append("Scenario touches elections: require legal counsel + nonpartisan compliance review.")
    if "surveillance" in s or "monitor" in s or "track citizens" in s:
        flags.append("Potential civil liberties impact: require constitutional + privacy review.")
    if "military" in s or "strike" in s or "war" in s:
        flags.append("Use of force considerations: require NSC + legal authorities review.")
    if "emergency" in s or "martial" in s:
        flags.append("Emergency powers: require strict time limits, documentation, and oversight.")

    if not flags:
        flags.append("Human oversight required: confirm legal authority, budget, and implementation feasibility.")

    return flags