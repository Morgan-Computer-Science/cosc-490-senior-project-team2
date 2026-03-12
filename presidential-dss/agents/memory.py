import json
import os
from datetime import datetime

MEMORY_FILE = "memory/past_decisions.json"


def save_decision(scenario: str, brief: str, domains: list) -> None:
    os.makedirs("memory", exist_ok=True)

    decisions = load_memory()
    decisions.append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "scenario": scenario,
            "brief": brief,
            "domains": domains,
        }
    )

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(decisions, file, indent=2)


def load_memory() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []

    with open(MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_relevant_memory(scenario: str) -> str:
    _ = scenario
    decisions = load_memory()
    if not decisions:
        return "No prior decisions on record."

    recent = decisions[-3:]
    formatted = []
    for idx, item in enumerate(recent, 1):
        formatted.append(
            f"Decision {idx}:\n"
            f"Timestamp: {item.get('timestamp', 'Unknown')}\n"
            f"Scenario: {item.get('scenario', '')}\n"
            f"Priority Domains: {', '.join(item.get('domains', []))}\n"
            f"Brief: {item.get('brief', '')}\n"
        )

    return "\n".join(formatted)
