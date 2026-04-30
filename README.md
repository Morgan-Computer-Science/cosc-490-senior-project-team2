[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=22437444&assignment_repo_type=AssignmentRepo)
# Presidential Decision Support System (PDSS)
### White House Situation Room — Command Interface
**COSC 490 Senior Project | Morgan State University**

---

> **SIMULATED EXERCISE — NOT REAL INTELLIGENCE — FOR DEMONSTRATION PURPOSES ONLY**

---

## Overview

The Presidential Decision Support System (PDSS) is an AI-powered multi-user command interface simulating the White House Situation Room. Built on Google Cloud Platform using Vertex AI and Gemini 2.5 Flash, the system analyzes national security and policy scenarios across 10 domains, generates structured executive briefs, and supports secure communication between the President and the chain of command.

The system features a full role-based login system, persistent brief storage, brief distribution, secure messaging between users, and a complete multi-agent AI pipeline with automated quality review and self-healing revision.

---

## Quick Start

```bash
git clone https://github.com/Morgan-Computer-Science/cosc-490-senior-project-team2
cd cosc-490-senior-project-team2/presidential-dss
bash run.sh
```

`run.sh` handles everything automatically:
- Installs Google Cloud CLI if not present
- Prompts authentication if not logged in
- Sets the GCP project
- Installs Python dependencies
- Clears Python cache
- Launches the Streamlit app on port 8501

Open **Chrome or Firefox** and go to `http://localhost:8501`. Safari has known JavaScript compatibility issues with Streamlit.

---

## Prerequisites

- Python 3.12+
- A Google Cloud Platform account with Vertex AI API enabled on the `presidential-dss` project
- Git

---

## Manual Setup (if run.sh fails)

```bash
# Install gcloud CLI
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
tar -xf google-cloud-cli-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
source ~/.bashrc

# Authenticate
gcloud init
gcloud auth application-default login
gcloud config set project presidential-dss

# Set up environment
cp .env.example .env
# .env should contain:
# GOOGLE_CLOUD_PROJECT=presidential-dss
# GOOGLE_CLOUD_LOCATION=us-central1
# GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py --server.port 8501
```

---

## User Accounts

| Username | Password | Role | Display |
|----------|----------|------|---------|
| `president` | `eagle1600` | President | POTUS |
| `vp` | `vp2025` | Vice President | VPOTUS |
| `secdef` | `pentagon2025` | Secretary of Defense | SECDEF |
| `secstate` | `foggy2025` | Secretary of State | SECSTATE |
| `nsa` | `nsc2025` | National Security Advisor | NSA |
| `cia` | `langley2025` | Director of Central Intelligence | DCI |
| `cjcs` | `joint2025` | Chairman, Joint Chiefs of Staff | CJCS |
| `cos` | `chiefs2025` | White House Chief of Staff | COS |
| `advisor` | `sitroom2025` | Senior Policy Advisor | ADVISOR |
| `admin` | `admin` | System Administrator | ADMIN |

---

## Role-Based Access

### President (POTUS)
- Generate AI-powered executive briefs from any scenario
- Access all 10 analysis tabs
- Adjust domain weights before generating a brief
- Distribute briefs to any member of the chain of command
- View, load, and delete previous briefs
- Send and receive secure messages to and from all users

### Chain of Command (VP, SECDEF, NSA, etc.)
- Receive briefs distributed by the President
- Load and read distributed briefs in full
- View all analysis tabs after loading a brief
- Send and receive secure messages
- Reply to and delete messages
- Cannot generate new briefs

### Admin
- View all briefs from all operators
- Full archive access

---

## AI Pipeline

The system runs a hierarchical multi-agent pipeline powered by Gemini 2.5 Flash on Vertex AI:

```
User submits scenario
        ↓
Control Agent → identifies top 3 priority domains
        ↓
10 Domain Agents → all fire simultaneously via ThreadPoolExecutor
  ├── 3 priority agents   → deep 5-section policy analysis
  └── 7 supporting agents → 3-line domain relevance assessment
        ↓
Synthesizer Agent → builds unified 3-part executive brief
        ↓
Critic Agent (LLM-as-Judge) → reviews all analyses and brief
        ↓
   APPROVED ──────────────────────────────→ Memory → Done
        ↓
REQUIRES REVISION
        ↓
Revision Agent → rewrites brief with critic feedback → Memory → Done
```

### Pre-Pipeline AI Calls
Three additional calls run in parallel before the main pipeline:
- **Severity Assessment** — rates the threat as Low / Moderate / High / Severe
- **Intelligence Feeds** — generates simulated news, health, and cyber threat feeds
- **Geographic Hotspots** — identifies 6 real-world locations relevant to the scenario

### Post-Pipeline AI Calls
- **Agency Activation** — identifies 6 federal agencies with priority levels
- **Policy Simulations** — generates 4 policy options with metrics
- **Chain of Command** — generates an approval workflow with roles and timelines

---

## Agents

### Control Agent
Reads the scenario and selects the 3 most critical policy domains from a pool of 10. Falls back to `[Defense, Economy, Foreign Policy]` on error.

### Domain Agents (×10, parallel)
Ten specialized policy advisor agents representing: Defense, Economy, Healthcare, Foreign Policy, Environment, Education, Energy, Homeland Security, Technology, Justice.

- **Priority agents (3):** Full 5-section analysis — `ANALYSIS / OPTIONS / RISKS / TRADEOFFS / UNCERTAINTIES`
- **Supporting agents (7):** Relevance assessment — `IMPACT / KEY CONCERN / RELEVANCE`

All 10 agents run simultaneously using `concurrent.futures.ThreadPoolExecutor`.

### Synthesizer Agent
Combines all 10 domain outputs into a 3-part executive brief: executive summary sections, priority domain deep dives, and supporting domain assessments.

### Critic Agent (LLM-as-Judge)
Reviews all 10 analyses and the executive brief for quality, contradictions, blind spots, and logic errors. Returns `APPROVED`, `APPROVED WITH CONCERNS`, or `REQUIRES REVISION`.

### Revision Agent
Activated only on `REQUIRES REVISION`. Rewrites the brief incorporating the critic's feedback. This is the self-healing layer of the pipeline.

### Memory Module
Saves scenario, brief, priority domains, and verdict to `memory/past_decisions.json` after every run.

---

## Executive Brief Structure

Each brief is formatted as an official Presidential Daily Brief (PDB):

- **Memo Header** — TO: POTUS, FROM: NSC AI ANALYSIS SYSTEM, DATE, CLASSIFICATION, BRIEFING ID, SUBJECT
- **Diagonal Watermark** — operator name, severity, and timestamp repeating behind the text
- **8 Structured Sections** rendered as individual cards:
  1. Situation Summary
  2. Key Policy Options
  3. Principal Risks
  4. Major Tradeoffs
  5. Critical Uncertainties
  6. Recommended Next Steps
  7. Priority Domain Deep Dives
  8. Supporting Domain Assessments
- **Analytical Footnotes** — which domain agents contributed to each section
- **Signature Block** — Prepared By, Reviewed By, Critic Verdict, Distribution, Briefing ID

---

## Analysis Tabs

| Tab | Contents |
|-----|----------|
| **PDB** | Executive brief with memo header, watermark, footnotes, signature block, and brief distribution |
| **SIGINT / HUMINT** | AI-generated global news, public health alerts, and cyber threat feeds |
| **GEOINT** | Interactive map with 6 geographic hotspots |
| **COA Analysis** | 4 policy options with metrics and success probability chart |
| **Chain of Command** | Agency activation order and approval workflow table |
| **Analyst Reports** | Full domain agent reports — priority expanded, supporting collapsed |
| **NSC Advisor** | AI chat interface with full brief context |
| **Inbox** | Briefs distributed to you with Load and Delete buttons |
| **Messages** | Secure message center with Inbox, Sent, and Compose tabs |
| **Archive** | Full run history table with JSON export |

---

## Brief Distribution System

1. President generates a brief
2. In the PDB tab, selects recipients from the chain of command
3. Adds an optional note and clicks **DISTRIBUTE BRIEF**
4. Each recipient automatically receives a message notification
5. Recipients see the brief in their **Inbox** tab with an UNREAD badge
6. Distribution record shows read/unread status per recipient

---

## Secure Messaging

- Any user can send a message to any other user
- Messages support subject lines, body text, and optional brief reference
- Inbox shows unread messages with a blue dot indicator
- Unread count badge appears on the Messages tab
- Reply directly from within a message
- Delete individual messages from inbox or sent

---

## Domain Weights

Sidebar sliders (1–5) allow the President to elevate or deprioritize specific domains before generating a brief. Elevated domains receive deeper analysis. Deprioritized domains receive relevance checks only.

---

## Persistent Storage

All data is stored in a local SQLite database (`pdss.db`) with 3 tables:

| Table | Contents |
|-------|----------|
| `briefs` | Full brief JSON, metadata, operator, timestamp |
| `distributions` | Which briefs were sent to which users and read receipts |
| `messages` | All secure messages with read receipts |

The database is created automatically on first run and persists across server restarts.

---

## Session Persistence

Login sessions survive page refreshes via a file-based token system. On login a secure random token is generated, saved to the OS temp directory, and appended to the URL. On refresh the token is read from the URL and the session is restored automatically.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| AI Model | Gemini 2.5 Flash via Vertex AI |
| Cloud Platform | Google Cloud Platform (GCP) |
| Agent Framework | Google Gen AI SDK (`google-genai`) |
| Parallel Execution | `concurrent.futures.ThreadPoolExecutor` |
| Frontend | Streamlit |
| Database | SQLite via `db.py` |
| Auth | File-based session tokens |
| Deployment | Local / Google Cloud Run |

---

## Project Structure

```
presidential-dss/
├── agents/
│   ├── __init__.py          # Pipeline orchestrator
│   ├── control_agent.py     # Priority domain routing
│   ├── domain_agents.py     # 10 parallel domain analysts
│   ├── synthesizer.py       # Executive brief generation + revision
│   ├── critic_agent.py      # LLM-as-Judge quality review
│   └── memory.py            # Persistent decision history
├── adk_deploy/
│   └── presidential_dss/
│       └── agent.py         # Vertex AI Agent Engine deployment version
├── memory/
│   └── past_decisions.json  # Auto-generated decision history
├── app.py                   # Streamlit UI
├── db.py                    # SQLite database layer
├── run.sh                   # Auto-setup and launch script
├── requirements.txt
├── .env.example             # Environment variable template
├── .gitignore
└── README.md
```

---

## Security Notes

- `.env` and `credentials.json` are in `.gitignore` and must never be committed
- Authentication uses `gcloud auth application-default login` — no credentials file needed
- `pdss.db` contains session data and should stay local — do not commit it
- Each developer needs their own GCP authentication via `gcloud auth application-default login`

---

## Scenario Examples

Six pre-built scenario templates are available for quick testing:

| Scenario | Description |
|----------|-------------|
| Cyberattack on Power Grid | Coordinated attack disables regional power grids |
| Economic Recession | Deep recession with banking stress and unemployment surge |
| Pandemic Outbreak | Novel respiratory virus spreading rapidly across states |
| Nuclear Threat | Adversarial nation elevates nuclear readiness |
| Climate Disaster | Extreme weather causes nationwide infrastructure damage |
| Border Emergency | Humanitarian surge strains border processing capacity |

---

## Cost Estimate

Each full pipeline run costs approximately **$0.002–$0.004** using Gemini 2.5 Flash on Vertex AI. The GCP free trial provides $300 in credits.

---

## Team

Built as a senior capstone project for COSC 490 at Morgan State University.

| Name | 
|------|
| Justice Thomson | 
| Davon David | 
| Querida Emmanuel | 
| Kimora Taylor | 