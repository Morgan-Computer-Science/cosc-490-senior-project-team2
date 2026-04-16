import os
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

FALLBACK = (
    "SITUATION SUMMARY\n"
    "Unable to generate summary due to model error.\n\n"
    "KEY POLICY OPTIONS\n"
    "Re-run analyses and validate assumptions.\n\n"
    "PRINCIPAL RISKS\n"
    "Decision latency and incomplete situational awareness.\n\n"
    "MAJOR TRADEOFFS\n"
    "Timeliness versus analytical depth.\n\n"
    "CRITICAL UNCERTAINTIES\n"
    "Model availability and evolving scenario details.\n\n"
    "RECOMMENDED NEXT STEPS\n"
    "1. Stabilize information channels and retry synthesis.\n\n"
    "PRIORITY DOMAIN DEEP DIVES\n"
    "Unavailable.\n\n"
    "SUPPORTING DOMAIN ASSESSMENTS\n"
    "Unavailable."
)

def _client():
    return genai.Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    )

def synthesizer_agent(scenario: str, domain_responses: list) -> str:
    priority_responses   = [r for r in domain_responses if r["priority"]]
    supporting_responses = [r for r in domain_responses if not r["priority"]]

    priority_blob = "\n\n".join([
        f"DOMAIN: {r['domain']}\n{r['analysis']}"
        for r in priority_responses
    ])
    supporting_blob = "\n\n".join([
        f"DOMAIN: {r['domain']}\n{r['analysis']}"
        for r in supporting_responses
    ])

    prompt = f"""You are the White House Executive Synthesizer. Your job is to produce a \
structured presidential brief from the domain analyses provided.

SCENARIO: {scenario}

PRIORITY DOMAIN ANALYSES:
{priority_blob}

SUPPORTING DOMAIN ASSESSMENTS:
{supporting_blob}

CRITICAL FORMATTING RULES — YOU MUST FOLLOW THESE EXACTLY:
1. Do NOT add any preamble, title, or header before the first section.
2. Do NOT write "PRESIDENTIAL BRIEF", "DATE:", "SUBJECT:", "CLASSIFICATION:", \
"TO:", "FROM:", or any document header of any kind. The system handles those.
3. Do NOT use markdown heading syntax (##, ###, etc.).
4. Start your response IMMEDIATELY with the text "SITUATION SUMMARY" on the first line.
5. Each section header must appear on its own line in ALL CAPS exactly as written below.
6. Do NOT add --- separators between sections.
7. Use plain text. Bold key terms with **double asterisks** only. \
Use * at the start of a line for bullet points.

YOUR RESPONSE MUST USE EXACTLY THESE 8 SECTION HEADERS IN THIS ORDER:

SITUATION SUMMARY
[2-3 paragraph unified overview of the scenario]

KEY POLICY OPTIONS
[numbered list of 4-6 specific, actionable policy options with brief descriptions]

PRINCIPAL RISKS
[bullet list of 4-6 principal risks weighted toward priority domain findings]

MAJOR TRADEOFFS
[bullet list of 3-5 key tensions between competing policy recommendations]

CRITICAL UNCERTAINTIES
[bullet list of 3-5 critical unknowns that affect decision-making]

RECOMMENDED NEXT STEPS
[numbered list of 5 immediate, specific actions for the President to authorize]

PRIORITY DOMAIN DEEP DIVES
[For each priority domain reproduce its full analysis under a heading \
marked ⭐DOMAIN: [name]. Keep OPTIONS, RISKS, TRADEOFFS, UNCERTAINTIES intact.]

SUPPORTING DOMAIN ASSESSMENTS
[For each supporting domain write DOMAIN: [name] then IMPACT, KEY CONCERN, \
and RELEVANCE on separate labeled lines. Include all domains even if not relevant.]
"""

    try:
        response = _client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = (response.text or "").strip()
        text = re.sub(r'^#+\s*PRESIDENTIAL BRIEF.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'^(DATE|SUBJECT|CLASSIFICATION|TO|FROM)\s*:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*$', '', text, flags=re.MULTILINE)
        match = re.search(r'^SITUATION SUMMARY', text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            text = text[match.start():]
        return text.strip()
    except Exception:
        return FALLBACK