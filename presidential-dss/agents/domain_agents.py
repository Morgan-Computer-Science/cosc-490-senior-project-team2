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


def query_domain_agent(domain: str, scenario: str, is_priority: bool) -> dict:
    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    )
    model = GenerativeModel("gemini-2.0-flash")

    if is_priority:
        prompt_style = (
            "You are the senior policy advisor for this domain. Provide a thorough, high-detail analysis "
            "with full context, implications, and actionable policy depth."
        )
    else:
        prompt_style = (
            "You are the policy advisor for this domain. Provide a concise but clear analysis focused on "
            "the most decision-relevant points."
        )

    prompt = (
        f"{prompt_style}\n\n"
        f"Domain: {domain}\n"
        f"Scenario: {scenario}\n\n"
        "Respond in EXACTLY this format:\n"
        "ANALYSIS: [analysis here]\n"
        "OPTIONS: [policy options here]\n"
        "RISKS: [risks here]\n"
        "TRADEOFFS: [tradeoffs here]\n"
        "UNCERTAINTIES: [uncertainties here]"
    )

    try:
        response = model.generate_content(prompt)
        analysis_text = (response.text or "").strip()
    except Exception as error:
        analysis_text = (
            "ANALYSIS: Unable to generate analysis due to an internal error.\n"
            "OPTIONS: Gather additional intelligence and reassess.\n"
            "RISKS: Delayed response and incomplete information.\n"
            "TRADEOFFS: Speed versus confidence in policy direction.\n"
            "UNCERTAINTIES: Model call failed with error details withheld for safety."
        )
        _ = error

    return {"domain": domain, "analysis": analysis_text, "priority": is_priority}
