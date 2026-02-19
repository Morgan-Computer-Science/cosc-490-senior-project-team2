# Presidential Decision Support System

A hierarchical multi-agent AI system designed to support complex presidential decision-making by distributing scenario analysis across specialized domain agents and synthesizing findings into a concise executive brief.

---

## Overview

This system uses a **chief-of-staff-style control agent** to coordinate ten domain-specific agents. When a user submits a scenario, the control agent distributes it for parallel analysis, selects the two most relevant domain responses for deeper evaluation, and produces a final executive brief covering options, tradeoffs, risks, and uncertainties.

All agents follow a **shared response format** to ensure consistency and enable straightforward comparison and summarization.

---

## Architecture

```
User Scenario
     │
     ▼
Control Agent (Chief of Staff)
     │
     ├──▶ Economics Agent
     ├──▶ National Security Agent
     ├──▶ Foreign Policy Agent
     ├──▶ Cyber Security Agent
     ├──▶ Public Health Agent
     ├──▶ Immigration & Border Agent
     ├──▶ Energy & Environment Agent
     ├──▶ Disaster Response & Resilience Agent
     ├──▶ Agriculture & Food Security Agent
     └──▶ Housing & Urban Stability Agent
              │
              ▼
     Select Top 2 Most Relevant
              │
              ▼
       Deep Evaluation
              │
              ▼
     Executive Brief Output
```

---

## Domain Agents

| Agent | Responsibility |
|-------|---------------|
| 🏦 **Economics** | Fiscal policy, trade, inflation, employment, and macroeconomic impact |
| 🛡️ **National Security** | Defense posture, intelligence threats, military readiness |
| 🌐 **Foreign Policy** | Diplomatic relations, international agreements, geopolitical strategy |
| 💻 **Cyber Security** | Digital infrastructure threats, data protection, cyber warfare risks |
| 🏥 **Public Health** | Epidemics, healthcare capacity, public health policy |
| 🚧 **Immigration & Border** | Border security, immigration policy, asylum and enforcement |
| ⚡ **Energy & Environment** | Energy supply, climate policy, environmental regulation |
| 🚨 **Disaster Response & Resilience** | Natural disasters, emergency management, infrastructure recovery |
| 🌾 **Agriculture & Food Security** | Food supply chains, agricultural policy, famine and drought risk |
| 🏘️ **Housing & Urban Stability** | Housing affordability, urban infrastructure, community resilience |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python |
| User Interface | Streamlit |
| AI Model | Gemini via Vertex AI |
| Architecture | Multi-agent, hierarchical |

---

## Project Status

> **Phase: Early Development**

The project is currently in the planning and initial setup phase, progressing according to timeline.

- [x] Project scope finalized
- [x] Unified plan and system design agreed upon
- [x] Hierarchical agent structure designed
- [x] Shared response format defined
- [x] Project structure organized
- [ ] Routing and coordination logic
- [ ] First working agents (proof of concept)
- [ ] Full agent suite (10 domain agents)
- [ ] End-to-end evaluation

---

## Getting Started

> ⚠️ This project is under active development. Setup instructions will be updated as the codebase matures.

### Prerequisites

- Python 3.9+
- Google Cloud account with Vertex AI enabled
- Streamlit

### Installation

```bash
git clone https://github.com/your-org/presidential-decision-support.git
cd presidential-decision-support
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

---

## Roadmap

1. **Proof of Concept** — Build and test the first working domain agents
2. **Routing Logic** — Develop the control agent's coordination and selection mechanism
3. **Full Agent Suite** — Expand to all ten domain agents
4. **Evaluation** — Test system effectiveness on complex decision-making scenarios
5. **Refinement** — Iterate based on output quality and user feedback
