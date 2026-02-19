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
     ├──▶ Domain Agent 1
     ├──▶ Domain Agent 2
     ├──▶ Domain Agent 3
     ├──▶ ...
     └──▶ Domain Agent 10
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

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python |
| User Interface | Streamlit |
| AI Model | Gemini via Vertex AI |
| Architecture | Multi-agent, hierarchical |

---

## Project Status

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
