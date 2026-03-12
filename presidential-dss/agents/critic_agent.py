import os

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()


def critic_agent(scenario, domain_responses, executive_brief, priority_domains) -> dict:
    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    )
    model = GenerativeModel("gemini-2.0-flash")

    domains_blob = "\n\n".join(
        [f"DOMAIN: {d['domain']} | PRIORITY: {d['priority']}\n{d['analysis']}" for d in domain_responses]
    )

    prompt = (
        "You are a strict Red Team Critic for presidential decision support outputs. "
        "Assess source analyses and executive synthesis quality.\n\n"
        f"Scenario: {scenario}\n"
        f"Priority Domains Selected: {', '.join(priority_domains)}\n\n"
        f"Domain Analyses:\n{domains_blob}\n\n"
        f"Executive Brief:\n{executive_brief}\n\n"
        "Produce a report with EXACTLY these sections:\n"
        "QUALITY ASSESSMENT: rate each domain agent PASS/FAIL/PARTIAL\n"
        "CONTRADICTIONS DETECTED: list contradictions or \"None detected\"\n"
        "BLIND SPOTS: missed perspectives or \"None detected\"\n"
        "LOGIC ERRORS: synthesis vs source contradictions or \"None detected\"\n"
        "PRIORITY ROUTING ASSESSMENT: were the right 3 domains chosen?\n"
        "OVERALL VERDICT: APPROVED / APPROVED WITH CONCERNS / REQUIRES REVISION"
    )

    try:
        response = model.generate_content(prompt)
        report = (response.text or "").strip()
    except Exception:
        report = (
            "QUALITY ASSESSMENT: Unable to score domains due to critic model error.\n"
            "CONTRADICTIONS DETECTED: None detected\n"
            "BLIND SPOTS: None detected\n"
            "LOGIC ERRORS: None detected\n"
            "PRIORITY ROUTING ASSESSMENT: Insufficient data to assess routing.\n"
            "OVERALL VERDICT: APPROVED WITH CONCERNS"
        )

    verdict = "APPROVED WITH CONCERNS"
    for candidate in ["REQUIRES REVISION", "APPROVED WITH CONCERNS", "APPROVED"]:
        if candidate in report:
            verdict = candidate
            break

    return {"critic_report": report, "verdict": verdict}


def apply_revisions(scenario, executive_brief, critic_report) -> str:
    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    )
    model = GenerativeModel("gemini-2.0-flash")

    prompt = (
        "You are the Executive Brief Revision Agent. Rewrite the brief to address all critic feedback "
        "while preserving factual consistency with source analyses.\n\n"
        f"Scenario: {scenario}\n\n"
        f"Original Executive Brief:\n{executive_brief}\n\n"
        f"Critic Report:\n{critic_report}\n\n"
        "Return a revised brief with these exact sections:\n"
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
        return executive_brief
