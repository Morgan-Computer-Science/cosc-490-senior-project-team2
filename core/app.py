import json
from datetime import datetime

import streamlit as st

from core.agents import all_domain_agents, set_llm_runtime
from core.orchestrator import score_agents, build_executive_brief


st.set_page_config(page_title="AI Agents for Presidential Decision Making", layout="wide")

st.title("AI Agents for Presidential Decision Making")
st.caption("Chief-of-Staff Orchestrator • 10 Domain Agents • Top-K Deep Dive • Executive Brief")

if "history" not in st.session_state:
    st.session_state.history = []  # last 5 runs


with st.sidebar:
    st.header("Run Settings")

    mode = st.selectbox("LLM Mode", ["vertex", "mock"], index=0)
    model = st.selectbox("Gemini Model", ["gemini-2.0-flash", "gemini-1.5-pro"], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)

    top_k = st.slider("How many top domains to deep-dive", 1, 3, 2)

    st.markdown("---")
    show_arch_diagram = st.toggle("Show architecture diagram", value=False)

    st.markdown("---")
    st.caption("Vertex mode requires GOOGLE_CLOUD_PROJECT and auth (ADC or service account).")


# apply runtime config
set_llm_runtime(mode=mode, model=model, temperature=temperature)

scenario = st.text_area(
    "Enter a national-level decision scenario",
    height=180,
    placeholder="Example: A major cyberattack disrupts critical infrastructure across multiple states..."
)

colA, colB = st.columns([1, 1])
run = colA.button("Run Agents", type="primary", use_container_width=True)
clear = colB.button("Clear", use_container_width=True)

if clear:
    st.session_state.history = []
    st.rerun()


def _export_run_json(brief, ranked):
    payload = {
        "timestamp": datetime.now().isoformat(),
        "scenario": brief.scenario,
        "top_domains": brief.top_domains,
        "recommended_path": brief.recommended_path,
        "key_tradeoffs": brief.key_tradeoffs,
        "top_risks": brief.top_risks,
        "uncertainties": brief.uncertainties,
        "immediate_actions_72h": brief.immediate_actions_72h,
        "actions_30d": brief.actions_30d,
        "actions_180d": brief.actions_180d,
        "metrics_to_monitor": brief.metrics_to_monitor,
        "ethics_and_oversight": brief.ethics_and_oversight,
        "ranked_agents": [r.model_dump() for r in ranked],
    }
    return json.dumps(payload, indent=2)


if show_arch_diagram:
    st.subheader("Architecture Diagram (Mermaid)")
    st.code(
        """flowchart TB
  U[User / Scenario Input] --> COS[Chief-of-Staff Orchestrator]

  subgraph L1[Top-Level Domain Agents]
    E[Economy & Markets]
    NS[National Security]
    IR[International Relations]
    EMP[Employment & Labor]
    H[Healthcare & Public Health]
    C[Climate & Environment]
    EN[Energy]
    T[Technology & Cyber]
    PS[Public Safety & Resilience]
    INF[Inflation & Cost of Living]
  end

  COS --> E
  COS --> NS
  COS --> IR
  COS --> EMP
  COS --> H
  COS --> C
  COS --> EN
  COS --> T
  COS --> PS
  COS --> INF

  E & NS & IR & EMP & H & C & EN & T & PS & INF --> SCORE[Relevance Scoring + Ranking]
  SCORE --> TOPK[Select Top-K Domains]
  TOPK --> DD[Deep Dive Analysis]
  DD --> BRIEF[Executive Brief Generator]
  BRIEF --> GOV[Ethics + Human Oversight Layer]
  GOV --> OUT[Final Executive Brief Output]""",
        language="text",
    )
    st.caption("Paste into mermaid.live, then export PNG for slides.")


if run:
    if not scenario.strip():
        st.warning("Please enter a scenario first.")
        st.stop()

    with st.spinner("Running 10 domain agents..."):
        responses = all_domain_agents(scenario, throttle_seconds=1.5)
        ranked = score_agents(responses, scenario)
        brief = build_executive_brief(scenario, ranked, top_k=top_k)

    st.subheader("Executive Brief")
    st.write("**Top domains selected:** " + ", ".join(brief.top_domains))
    st.write("**Recommended path:** " + brief.recommended_path)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### Key tradeoffs")
        for t in brief.key_tradeoffs:
            st.write("- " + t)
    with c2:
        st.markdown("### Top risks")
        for r in brief.top_risks:
            st.write("- " + r)
    with c3:
        st.markdown("### Uncertainties")
        for u in brief.uncertainties:
            st.write("- " + u)

    st.markdown("### Action plan")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("**Next 72 hours**")
        for x in brief.immediate_actions_72h:
            st.write("- " + x)
    with a2:
        st.markdown("**Next 30 days**")
        for x in brief.actions_30d:
            st.write("- " + x)
    with a3:
        st.markdown("**Next 180 days**")
        for x in brief.actions_180d:
            st.write("- " + x)

    st.markdown("### Metrics to monitor")
    st.write(", ".join(brief.metrics_to_monitor))

    st.markdown("### Ethics & oversight")
    for e in brief.ethics_and_oversight:
        st.write("- " + e)

    st.markdown("---")
    st.subheader("Export this run")
    export_json = _export_run_json(brief, ranked)
    st.download_button(
        label="Download Run JSON",
        data=export_json,
        file_name=f"presidential_agents_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("Ranked domain agent outputs")
    for r in ranked:
        with st.expander(f"{r.domain} — Relevance: {r.relevance_score:.2f}"):
            st.write(f"**Agent:** {r.agent_name}")
            st.write(f"**Situation summary:** {r.situation_summary}")

            st.write("**Facts needed:**")
            for f in r.key_facts_needed:
                st.write("- " + f)

            st.write("**Assumptions:**")
            for a in r.assumptions:
                st.write("- " + a)

            st.write("**Options:**")
            for opt in r.options:
                st.write(f"**{opt.title}** — {opt.summary}")
                st.write("Pros: " + "; ".join(opt.pros))
                st.write("Cons: " + "; ".join(opt.cons))

            st.write(f"**Recommended:** {r.recommended_option}")
            st.write(f"**Rationale:** {r.rationale}")
            st.write(f"**Risk level:** {r.risk_level} | **Confidence:** {r.confidence}")

            st.write("**Risks:**")
            for ri in r.risks:
                st.write(f"- {ri.risk} (L={ri.likelihood}, I={ri.impact}) → {ri.mitigation}")

            st.write("**Uncertainty notes:**")
            for u in r.uncertainty_notes:
                st.write("- " + u)

            st.write("**Human oversight flags:**")
            for h in r.human_oversight_flags:
                st.write("- " + h)

    st.session_state.history.insert(
        0,
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scenario": scenario,
        },
    )
    st.session_state.history = st.session_state.history[:5]


if st.session_state.history:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Last Runs (Session)")
    for item in st.session_state.history:
        st.sidebar.caption(item["timestamp"])
        st.sidebar.write(item["scenario"][:50] + ("..." if len(item["scenario"]) > 50 else ""))