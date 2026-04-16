import os
from dotenv import load_dotenv
from google import genai

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

_genai_client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)

def query_domain_agent(domain: str, scenario: str, is_priority: bool) -> dict:
    if is_priority:
        prompt_style = (
            "You are the senior policy advisor for this domain. Provide a thorough, high-detail analysis "
            "with full context, implications, and actionable policy depth."
        )
        format_instruction = (
            "Respond in EXACTLY this format:\n"
            "ANALYSIS: [analysis here]\n"
            "OPTIONS: [policy options here]\n"
            "RISKS: [risks here]\n"
            "TRADEOFFS: [tradeoffs here]\n"
            "UNCERTAINTIES: [uncertainties here]"
        )
    else:
        prompt_style = (
            "You are the policy advisor for this domain. "
            "Assess how uniquely relevant this scenario is to your domain. "
            "Be honest — if this domain is not meaningfully affected, say so clearly. "
            "Do not force relevance where none exists."
        )
        format_instruction = (
            "Respond in EXACTLY this format:\n"
            "IMPACT: [High / Moderate / Low / Not Relevant] — [one sentence explanation]\n"
            "KEY CONCERN: [the single most important issue for this domain, "
            "or 'None at this stage' if not relevant]\n"
            "RELEVANCE: [one sentence on this domain's role in the scenario, "
            "or 'This domain is not a factor in the current scenario.']"
        )
    prompt = (
        f"{prompt_style}\n\n"
        f"Domain: {domain}\n"
        f"Scenario: {scenario}\n\n"
        f"{format_instruction}"
    )
    try:
        response = _genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        analysis_text = (response.text or "").strip()
    except Exception as error:
        if is_priority:
            analysis_text = (
                "ANALYSIS: Unable to generate analysis due to an internal error.\n"
                "OPTIONS: Gather additional intelligence and reassess.\n"
                "RISKS: Delayed response and incomplete information.\n"
                "TRADEOFFS: Speed versus confidence in policy direction.\n"
                "UNCERTAINTIES: Model call failed with error details withheld for safety."
            )
        else:
            analysis_text = (
                "IMPACT: Not Relevant — Unable to assess due to an internal error.\n"
                "KEY CONCERN: None at this stage.\n"
                "RELEVANCE: Model call failed. Domain relevance could not be determined."
            )
        _ = error
    return {"domain": domain, "analysis": analysis_text, "priority": is_priority}