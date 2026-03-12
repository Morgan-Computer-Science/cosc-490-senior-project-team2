import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from .control_agent import control_agent
from .critic_agent import apply_revisions, critic_agent
from .domain_agents import query_domain_agent
from .memory import save_decision
from .synthesizer import synthesizer_agent

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


def run_decision_support(scenario: str, progress_callback=None) -> dict:
    if progress_callback:
        progress_callback("Identifying priority domains...")

    priority_domains = control_agent(scenario)

    domain_results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(query_domain_agent, domain, scenario, domain in priority_domains): domain
            for domain in DOMAINS
        }

        for future in as_completed(futures):
            result = future.result()
            domain_results.append(result)
            if progress_callback:
                progress_callback(f"Completed {result['domain']} analysis.")

    domain_results.sort(key=lambda item: DOMAINS.index(item["domain"]))

    if progress_callback:
        progress_callback("Synthesizing executive brief...")
    original_brief = synthesizer_agent(scenario, domain_results)
    executive_brief = original_brief

    if progress_callback:
        progress_callback("Critic reviewing brief...")
    critic_result = critic_agent(scenario, domain_results, executive_brief, priority_domains)

    if critic_result["verdict"] == "REQUIRES REVISION":
        executive_brief = apply_revisions(scenario, executive_brief, critic_result["critic_report"])

    save_decision(scenario, executive_brief, priority_domains)

    return {
        "scenario": scenario,
        "priority_domains": priority_domains,
        "domain_analyses": domain_results,
        "executive_brief": executive_brief,
        "original_brief": original_brief,
        "critic_report": critic_result["critic_report"],
        "verdict": critic_result["verdict"],
    }
