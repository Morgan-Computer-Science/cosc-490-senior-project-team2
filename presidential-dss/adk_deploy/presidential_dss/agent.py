import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

load_dotenv()

MODEL = "gemini-2.0-flash"


def domain_instruction(domain_name: str) -> str:
    return (
        f"You are the {domain_name} policy domain agent for a Presidential Decision Support System. "
        "Analyze scenario implications, policy options, risks, tradeoffs, and uncertainties for your domain."
    )


def make_domain_agent(domain_name: str) -> LlmAgent:
    return LlmAgent(
        name=f"{domain_name.lower().replace(' ', '_')}_agent",
        model=MODEL,
        instruction=domain_instruction(domain_name),
    )


defense_agent = make_domain_agent("Defense")
economy_agent = make_domain_agent("Economy")
healthcare_agent = make_domain_agent("Healthcare")
foreign_policy_agent = make_domain_agent("Foreign Policy")
environment_agent = make_domain_agent("Environment")
education_agent = make_domain_agent("Education")
energy_agent = make_domain_agent("Energy")
homeland_security_agent = make_domain_agent("Homeland Security")
technology_agent = make_domain_agent("Technology")
justice_agent = make_domain_agent("Justice")

parallel_analysis = ParallelAgent(
    name="parallel_analysis",
    sub_agents=[
        defense_agent,
        economy_agent,
        healthcare_agent,
        foreign_policy_agent,
        environment_agent,
        education_agent,
        energy_agent,
        homeland_security_agent,
        technology_agent,
        justice_agent,
    ],
)

synthesizer_llm = LlmAgent(
    name="synthesizer_llm",
    model=MODEL,
    instruction=(
        "Synthesize all domain analyses into an executive presidential brief with sections for "
        "situation summary, policy options, risks, tradeoffs, uncertainties, and next steps."
    ),
)

root_agent = SequentialAgent(
    name="presidential_dss_root",
    sub_agents=[parallel_analysis, synthesizer_llm],
)
