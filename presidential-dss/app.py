import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from agents import run_decision_support

load_dotenv()

st.set_page_config(page_title="Presidential Decision Support System", page_icon="🏛️")
st.title("Presidential Decision Support System")

with st.sidebar:
    st.header("Architecture Overview")
    st.markdown(
        "1. **Control Agent** selects top 3 priority domains\n"
        "2. **10 Domain Agents** analyze the scenario in parallel\n"
        "3. **Synthesizer Agent** builds executive brief\n"
        "4. **Critic Agent** audits quality and may trigger revisions\n"
        "5. **Memory Module** stores decisions"
    )

    st.subheader("Example Scenarios")
    examples = {
        "Cyberattack on power grid": "A coordinated cyberattack disables multiple regional power grids across the United States, disrupting hospitals, transportation, and communications.",
        "Economic recession": "Leading indicators show a deep recession is underway with rising unemployment, banking stress, and consumer confidence collapse.",
        "Pandemic outbreak": "A novel respiratory virus with high transmissibility is spreading rapidly across several states with uncertain fatality rates.",
        "Nuclear threat": "An adversarial nation has elevated nuclear readiness and issued ambiguous strategic warnings amid a regional military crisis.",
        "Climate disaster": "A series of climate-driven extreme weather events has caused nationwide infrastructure damage, displacement, and agricultural disruption.",
    }

    for label, text in examples.items():
        if st.button(label):
            st.session_state["scenario_input"] = text

scenario = st.text_area(
    "Enter national security or policy scenario:",
    value=st.session_state.get("scenario_input", ""),
    height=200,
)

if st.button("Generate Executive Brief"):
    if not scenario.strip():
        st.warning("Please enter a scenario before generating a brief.")
    else:
        progress_placeholder = st.empty()
        progress_logs = []

        def progress_callback(message: str):
            progress_logs.append(f"- {message}")
            progress_placeholder.markdown("\n".join(progress_logs))

        result = run_decision_support(scenario, progress_callback=progress_callback)

        st.subheader("Priority Domains")
        cols = st.columns(3)
        for i, domain in enumerate(result["priority_domains"]):
            cols[i].info(domain)

        verdict = result["verdict"]
        if verdict == "APPROVED":
            st.success(f"Verdict: {verdict}")
        elif verdict == "APPROVED WITH CONCERNS":
            st.warning(f"Verdict: {verdict}")
        else:
            st.error(f"Verdict: {verdict}")

        st.subheader("Executive Brief")
        st.markdown(result["executive_brief"])

        with st.expander("Critic Report"):
            st.markdown(result["critic_report"])

        with st.expander("All Domain Analyses"):
            for entry in result["domain_analyses"]:
                star = " ⭐" if entry["priority"] else ""
                st.markdown(f"### {entry['domain']}{star}")
                st.markdown(entry["analysis"])

        report_text = (
            "Presidential Decision Support System Report\n"
            f"Generated: {datetime.utcnow().isoformat()} UTC\n\n"
            f"Scenario:\n{result['scenario']}\n\n"
            f"Priority Domains: {', '.join(result['priority_domains'])}\n\n"
            f"Verdict: {result['verdict']}\n\n"
            "Executive Brief:\n"
            f"{result['executive_brief']}\n\n"
            "Critic Report:\n"
            f"{result['critic_report']}\n\n"
            "Domain Analyses:\n"
        )

        for entry in result["domain_analyses"]:
            report_text += (
                f"\n=== {entry['domain']} {'⭐' if entry['priority'] else ''} ===\n"
                f"{entry['analysis']}\n"
            )

        st.download_button(
            "Download Full Report (.txt)",
            data=report_text,
            file_name="presidential_dss_report.txt",
            mime="text/plain",
        )
