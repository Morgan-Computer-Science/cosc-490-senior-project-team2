import os

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()


def synthesizer_agent(scenario: str, domain_responses: list) -> str:
    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    )
    model = GenerativeModel("gemini-2.0-flash")

    compiled = "\n\n".join(
        [f"DOMAIN: {item['domain']}\nPRIORITY: {item['priority']}\n{item['analysis']}" for item in domain_responses]
    )

    prompt = (
        "You are the White House Executive Synthesizer. Read all domain analyses and produce a unified "
        "executive brief for the President.\n\n"
        f"Scenario: {scenario}\n\n"
        f"Domain Analyses:\n{compiled}\n\n"
        "Use EXACTLY these section headings:\n"
        "SITUATION SUMMARY\n"
        "KEY POLICY OPTIONS\n"
        "PRINCIPAL RISKS\n"
        "MAJOR TRADEOFFS\n"
        "CRITICAL UNCERTAINTIES\n"
        "RECOMMENDED NEXT STEPS"
    )

    try:
        response = model.generate_content(prompt)
        return (response.text or "").strip()
    except Exception:
        return (
            "SITUATION SUMMARY\nUnable to generate summary due to model error.\n\n"
            "KEY POLICY OPTIONS\nRe-run analyses and validate assumptions.\n\n"
            "PRINCIPAL RISKS\nDecision latency and incomplete situational awareness.\n\n"
            "MAJOR TRADEOFFS\nTimeliness versus analytical depth.\n\n"
            "CRITICAL UNCERTAINTIES\nModel availability and evolving scenario details.\n\n"
            "RECOMMENDED NEXT STEPS\nStabilize information channels and retry synthesis."
        )
