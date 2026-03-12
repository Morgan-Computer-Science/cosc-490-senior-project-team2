import os

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()


DOMAINS = [
    "Defense",
    "Economy",
    "Healthcare",
    "Foreign Policy",
    "Environment",
    "Education",
    "Energy",
    "Homeland Security",
    "Technology",
    "Justice",
]


def initialize_vertex() -> None:
    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    )


def control_agent(scenario: str) -> list:
    try:
        initialize_vertex()
        model = GenerativeModel("gemini-2.0-flash")

        prompt = (
            "You are a presidential chief-of-staff routing agent. "
            "Given the scenario, identify the top 3 priority domains from this exact list: "
            "Defense, Economy, Healthcare, Foreign Policy, Environment, Education, Energy, "
            "Homeland Security, Technology, Justice.\n\n"
            "Return ONLY a comma-separated list of exactly 3 domain names from the list.\n\n"
            f"Scenario: {scenario}"
        )

        response = model.generate_content(prompt)
        text = (response.text or "").strip()

        selected = [item.strip() for item in text.replace("\n", ",").split(",") if item.strip()]
        filtered = []
        for domain in selected:
            if domain in DOMAINS and domain not in filtered:
                filtered.append(domain)
            if len(filtered) == 3:
                break

        if len(filtered) == 3:
            return filtered
        return ["Defense", "Economy", "Foreign Policy"]
    except Exception:
        return ["Defense", "Economy", "Foreign Policy"]
