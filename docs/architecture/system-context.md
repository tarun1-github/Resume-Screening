# 🌐 System Context — FITMENT.AI Recruitment Intelligence Platform

> **Audience**: Solution Architects, Enterprise IT Teams, and Engineering Leadership.  
> **Last Reviewed**: 2026-10-19  
> **Related Documents**: [`docs/architecture/application-components.md`](file:///e:/Projects/resume-screening-agent/docs/architecture/application-components.md), [`docs/architecture/deployment-architecture.md`](file:///e:/Projects/resume-screening-agent/docs/architecture/deployment-architecture.md).

---

## 1. System Context & Operational Environment

**FITMENT.AI** is deployed as an on-premise or local workstation recruitment intelligence application. It bridges the gap between unstructured candidate documents (PDF/DOCX/TXT resumes and job descriptions) and structured recruitment pipeline decisions.

The system interacts with human actors (recruiters, hiring managers) and optional cloud inference providers, maintaining clear trust and network boundaries.

```mermaid
flowchart TD
    subgraph Users ["Human Stakeholders"]
        Recruiter["Technical Recruiter / Talent Acquisition Specialist"]
        HiringMgr["Hiring Manager / Technical Lead"]
    end

    subgraph SystemBoundary ["FITMENT.AI System Boundary (Local Host / Internal Network)"]
        subgraph WebLayer ["Presentation Layer"]
            UI["Streamlit Web UI (Port 8501)<br/>• Screening Workspace<br/>• Candidate Tracker<br/>• Fitment Assistant<br/>• Live IST Clock"]
        end

        subgraph CoreProcessing ["Application Processing Layer"]
            Parser["Document Parser (pypdf, python-docx)"]
            Engine["Deterministic Fitment Engine"]
            Assistant["Fitment Assistant Intent Router"]
        end

        subgraph LocalPersistence ["Durable Local Storage (data/)"]
            DB[(SQLite Database: fitment.db)]
            FileStore["Local File Store<br/>• data/job_descriptions/<br/>• data/resumes/"]
            Logs["data/logs/"]
        end
    end

    subgraph ExternalCloud ["Optional External Cloud Services (HTTPS)"]
        GeminiAPI["Google Gemini API (REST / JSON)"]
        OpenRouterAPI["OpenRouter Gateway (REST / JSON)"]
        NvidiaAPI["NVIDIA NIM API (REST / JSON)"]
        GroqAPI["Groq Cloud API (REST / JSON)"]
    end

    Recruiter <-->|Browser HTTP / WebSocket| UI
    HiringMgr <-->|Browser HTTP / WebSocket| UI

    UI --> Parser
    UI --> Engine
    UI <--> Assistant

    Parser --> FileStore
    Engine --> DB
    Assistant <--> DB

    UI -.->|Optional Qualitative Narrative (Outbound HTTPS)| ExternalCloud
    Assistant -.->|Optional Mode B Technical Q&A (Outbound HTTPS)| ExternalCloud

    classDef user fill:#E0E7FF,stroke:#4338CA,color:#1E1B4B,stroke-width:1.5px;
    classDef system fill:#EFF6FF,stroke:#2563EB,color:#172033,stroke-width:2px;
    classDef storage fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:1.5px;
    classDef cloud fill:#F8FAFC,stroke:#94A3B8,color:#475569,stroke-dasharray: 4 4;

    class Recruiter,HiringMgr user;
    class UI,Parser,Engine,Assistant system;
    class DB,FileStore,Logs storage;
    class GeminiAPI,OpenRouterAPI,NvidiaAPI,GroqAPI cloud;
```

---

## 2. Stakeholder Profiles & Use Cases

| Stakeholder | Primary Objectives | Typical System Interaction |
| :--- | :--- | :--- |
| **Technical Recruiter** | Rapid initial candidate vetting, contact discovery, skill verification, and interview question preparation. | Uploads JD and resume files; reviews instantaneous scorecards; updates candidate recruitment status; schedules follow-up tasks. |
| **Hiring Manager** | Reviewing shortlisted candidates, analyzing verified technical competencies, inspecting skill gaps, and reviewing candidate dossiers. | Uses Candidate Tracker to filter and inspect candidate profiles; reviews technical interview probing questions; downloads markdown dossiers. |
| **System Administrator** | Maintaining local installation, configuring API keys, performing database backups, and reviewing audit logs. | Manages `.env` configurations; executes backup scripts; monitors local file disk usage under `data/`. |

---

## 3. Online vs. Offline Capability Boundaries

A critical requirement of enterprise recruitment is continuous operational readiness, regardless of network availability or third-party cloud service outages.

### What Works 100% Offline (Zero External Calls)
- **Document Parsing**: Reading and extracting clean text from PDF, DOCX, DOC, and TXT files using local Python libraries (`pypdf`, `python-docx`).
- **Metadata Extraction**: Parsing candidate names, email addresses, phone numbers, locations, organizations, and designations via regex.
- **Competency & Seniority Analysis**: Matching skills against industry dictionaries, computing total and relevant years of experience, and verifying vendor accreditations.
- **Mathematical Scoring (0–100)**: Computing category scores (skills, experience, education, certifications) using configurable weights.
- **Data Persistence**: Storing original document files under `data/`, deduplicating via SHA-256, and writing candidate profiles, screening records, and audit history to SQLite.
- **Candidate Tracker**: Browsing, filtering, searching, and resetting candidate views.
- **Database-Grounded Chatbot (Mode A)**: Querying candidate scores, contact numbers, follow-ups, and comparison tables.
- **Live IST Clock & Daily Analytics**: Calculating today's recruitment metrics in Indian Standard Time (`Asia/Kolkata`).

### What Requires External Network Access (Outbound HTTPS)
- **Qualitative Narrative Synthesis**: Generating descriptive prose summaries of candidate strengths and nuances using Google Gemini, OpenRouter, NVIDIA NIM, or Groq.
- **General Technical Copilot (Mode B)**: Asking the chatbot open-ended technical questions that do not pertain to candidates registered in the SQLite database (e.g., explaining SIP protocols, drafting interview evaluation templates).
- **External AI Connectivity Verification**: Pinging provider endpoints to confirm API key validity.

> [!NOTE]
> When external network access is unavailable, FITMENT.AI gracefully degrades: the qualitative synthesis automatically displays an authoritative deterministic summary, leaving all core screening metrics completely operational.
