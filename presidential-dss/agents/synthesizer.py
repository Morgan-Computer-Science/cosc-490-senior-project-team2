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

    priority_responses = [r for r in domain_responses if r["priority"]]
    supporting_responses = [r for r in domain_responses if not r["priority"]]

    priority_blob = "\n\n".join([
        f"DOMAIN: {r['domain']}\n{r['analysis']}"
        for r in priority_responses
    ])
    supporting_blob = "\n\n".join([
        f"DOMAIN: {r['domain']}\n{r['analysis']}"
        for r in supporting_responses
    ])

    prompt = (
        "You are the White House Executive Synthesizer. Read all domain analyses and produce "
        "a structured presidential brief for the President.\n\n"
        f"Scenario: {scenario}\n\n"
        f"PRIORITY DOMAIN ANALYSES (in-depth):\n{priority_blob}\n\n"
        f"SUPPORTING DOMAIN ASSESSMENTS (relevance checks):\n{supporting_blob}\n\n"
        "Produce the brief using EXACTLY these sections in this order:\n\n"
        "SITUATION SUMMARY\n"
        "[unified overview of the scenario drawn from all inputs]\n\n"
        "KEY POLICY OPTIONS\n"
        "[options drawn primarily from the priority domain analyses]\n\n"
        "PRINCIPAL RISKS\n"
        "[risks weighted toward priority domain findings — note any urgent "
        "secondary risks flagged by supporting domains]\n\n"
        "MAJOR TRADEOFFS\n"
        "[key tensions between priority domain recommendations]\n\n"
        "CRITICAL UNCERTAINTIES\n"
        "[what remains unknown across all domains]\n\n"
        "RECOMMENDED NEXT STEPS\n"
        "[numbered actionable items for immediate presidential action]\n\n"
        "---\n\n"
        "PRIORITY DOMAIN DEEP DIVES\n"
        "[For each priority domain, reproduce its full analysis under its own "
        "heading marked with ⭐. Keep all 5 sections intact.]\n\n"
        "---\n\n"
        "SUPPORTING DOMAIN ASSESSMENTS\n"
        "[For each supporting domain, reproduce its IMPACT, KEY CONCERN, and "
        "RELEVANCE under its own heading. If a domain marked itself as not "
        "relevant, include it anyway so the President sees full coverage.]"
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
            "RECOMMENDED NEXT STEPS\nStabilize information channels and retry synthesis.\n\n"
            "---\n\nPRIORITY DOMAIN DEEP DIVES\nUnavailable.\n\n"
            "---\n\nSUPPORTING DOMAIN ASSESSMENTS\nUnavailable."
        )
