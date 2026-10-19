# 🏛️ Solution Architecture — Recruitment Intelligence Platform

## 1. Executive Summary & Architectural Scope

The **Recruitment Intelligence Platform** is an enterprise talent acquisition decision-support system. It delivers deterministic, zero-hallucination screening calculations for candidate CVs against target Job Descriptions, combined with qualitative generative AI summaries and a conversational recruitment intelligence assistant.

The core architecture is anchored around three foundational principles:
1. **Authoritative Determinism**: Scoring calculations, skill alignments, and seniority detections are calculated via verifiable regex, token matching, and set-theory algorithms in Python rather than non-deterministic LLM tokens.
2. **Local Registry Grounding**: The SQLite candidate registry is the source of truth for candidate identities, contact numbers, screening histories, and follow-up timelines.
3. **Resilient Offline Continuity**: Complete screening and retrieval workflows operate seamlessly without cloud connectivity or active LLM endpoints.

---

## 2. End-to-End System Context & Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientTier ["Client / Recruiter Presentation Tier"]
        Browser["Recruiter Desktop (Browser)"]
    end

    subgraph PortalTier ["Streamlit Web Application (app.py)"]
        UI_Head["Compact Header & Controls<br/>(↻ Refresh, AI Badge, ⚙️ Settings)"]
        UI_Screen["Screening Workspace (~74% Width)<br/>(01-JD & 02-Resume Side-by-Side)"]
        UI_Tracker["Candidate Tracker & Pipeline<br/>(11 Lifecycle Stages & Search)"]
        UI_Chat["Fitment Assistant Companion (~26% Width)<br/>(Clipboard Copy & Contextual Actions)"]
        UI_Settings["AI Service Configuration & Health Probes"]
    end

    subgraph ServiceTier ["Core Application Services"]
        Storage["storage.py<br/>Durable File Storage Engine"]
        Parser["parser.py<br/>Multi-Format Ingestion (PDF, DOCX, TXT)"]
        DetEngine["deterministic_engine.py<br/>authoritative Pattern-Match Engine"]
        Assistant["chatbot.py<br/>Fitment Assistant Router & Grounding"]
        LLMMgr["llm_manager.py<br/>Multi-Provider LLM Gateway"]
        FastAPI["api.py<br/>[Optional] Headless REST Endpoints"]
    end

    subgraph PersistenceTier ["Persistence Layer (data/)"]
        DB[(SQLite: fitment.db)]
        JD_Dir["data/job_descriptions/<br/>(Original Bytes, SHA-256)"]
        CV_Dir["data/resumes/<br/>(Original Bytes, Collision-Safe)"]
        Logs["data/logs/<br/>(Application Diagnostics)"]
    end

    subgraph ExternalAITier ["Optional External Inference Providers"]
        Gemini["Google Gemini<br/>(gemini-3.5-flash-lite)"]
        OpenRouter["OpenRouter Free Models<br/>(Gemma, Nemotron)"]
        Nvidia["NVIDIA NIM<br/>(StepFun, GLM-5.3)"]
        Groq["Groq Cloud<br/>(Llama-3.3-70b)"]
    end

    Browser <-->|HTTP / WebSocket| UI_Head
    Browser <-->|Uploads & Actions| UI_Screen
    Browser <-->|Pipeline Review| UI_Tracker
    Browser <-->|Chat & Copy Actions| UI_Chat

    UI_Screen -->|Durable Persistence| Storage
    Storage -->|Write File| JD_Dir
    Storage -->|Write File| CV_Dir
    Storage -->|Record File Metadata| DB

    UI_Screen -->|Extract Text| Parser
    Storage -->|Read Bytes| Parser
    Parser -->|Clean Document Text| DetEngine

    DetEngine -->|Calculate Scores & Evidence| UI_Screen
    DetEngine -->|Auto-Upsert Candidate & Screening| DB

    UI_Screen -.->|Qualitative Synthesis Request| LLMMgr
    LLMMgr -.->|Verified Cloud Call| Gemini
    LLMMgr -.->|Fallback Routing| OpenRouter
    LLMMgr -.->|Catalog Routing| Nvidia
    LLMMgr -.->|Fast Inference| Groq

    UI_Chat <-->|Inquiries & Status Inquiries| Assistant
    Assistant <-->|Parameterized SQL Queries| DB
    Assistant -.->|Narrative Synthesis| LLMMgr

    FastAPI -.->|Headless Screening| DetEngine
    FastAPI -.->|Query Candidates| DB

    classDef primary fill:#2563EB,stroke:#1D4ED8,color:#FFFFFF,stroke-width:2px;
    classDef secondary fill:#0891B2,stroke:#0E7490,color:#FFFFFF,stroke-width:2px;
    classDef storage fill:#EFF6FF,stroke:#BFDBFE,color:#172033,stroke-width:1px;
    classDef external fill:#F8FAFC,stroke:#CBD5E1,color:#475569,stroke-dasharray: 4 4;

    class UI_Screen,DetEngine,DB primary;
    class Storage,Assistant,LLMMgr secondary;
    class JD_Dir,CV_Dir,Logs storage;
    class Gemini,OpenRouter,Nvidia,Groq external;
```

---

## 3. Component Responsibilities & Module Catalog

| Module | Architectural Role | Key Responsibilities | Dependencies |
| :--- | :--- | :--- | :--- |
| **`app.py`** | Presentation Orchestrator | Streamlit UI layout, responsive grid cards, header controls, top-right refresh action, candidate summary strip, scorecard display, right companion panel, and dossier export. | `streamlit`, `storage`, `registry`, `deterministic_engine`, `llm_manager`, `chatbot` |
| **`storage.py`** | Storage Abstraction | Enforces file persistence under `data/job_descriptions/` and `data/resumes/`. Manages collision-safe unique filenames, SHA-256 deduplication, path-traversal prevention, and byte reading. | `hashlib`, `os`, `re`, `shutil`, `registry` |
| **`parser.py`** | Document Ingestion | Safely reads PDF, DOCX, DOC, and TXT files. Sanitizes control characters, strips formatting noise, and extracts raw textual tokens. | `pypdf`, `docx` (`python-docx`) |
| **`deterministic_engine.py`** | Authoritative Evaluation | Extracts candidate metadata (name, mobile, email, organization, designation, experience). Computes exact skill overlap, gap analysis, experience scoring, certification verification, and weighted score synthesis. | `re`, `math` |
| **`registry.py`** | Data Persistence & Schema | Manages SQLite connection lifecycle, parameterized queries, candidate upserts, screening associations, `stored_files` and `screening_files` junction rows, recruitment status audit trail, and follow-up scheduling. | `sqlite3`, `contextlib` |
| **`chatbot.py`** | Intent Routing & Grounding | Parses natural-language recruiter questions, classifies intent (candidate lookup, follow-up check, comparison, status update, interview questions), queries registry, and formats verified markdown responses. | `registry`, `llm_manager` |
| **`llm_manager.py`** | AI Provider Gateway | Manages external AI providers (Gemini, OpenRouter, NVIDIA NIM, Groq). Handles API key resolution, connection timeout budgets, and offline fallback. | `urllib.request`, `json`, `os` |
| **`api.py`** | Headless API Service | Optional FastAPI application providing REST endpoints (`/screen`, `/candidates`, `/health`) for headless orchestration. | `fastapi`, `pydantic`, `registry`, `deterministic_engine` |

---

## 4. Screening Execution Flow

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter / Browser
    participant App as Streamlit UI (app.py)
    participant Store as Storage (storage.py)
    participant Parser as Ingestion (parser.py)
    participant Det as Deterministic Engine
    participant Reg as Registry (registry.py)
    participant AI as LLM Manager (llm_manager.py)
    participant Provider as Cloud LLM Provider

    Recruiter->>App: Uploads JD & Candidate CV
    App->>Store: save_job_description_file(raw_bytes, jd_name)
    Store-->>App: {file_id: jd_id, stored_path: "data/job_descriptions/..."}
    App->>Store: save_resume_file(raw_bytes, cv_name)
    Store-->>App: {file_id: cv_id, stored_path: "data/resumes/..."}
    App->>Parser: extract_text_from_file(jd_bytes)
    Parser-->>App: extracted_jd_text
    App->>Parser: extract_text_from_file(cv_bytes)
    Parser-->>App: extracted_cv_text
    App-->>Recruiter: Displays "✅ JD loaded successfully!" & "✅ Resume loaded successfully!"
    App-->>Recruiter: Renders Candidate Summary Grid

    Recruiter->>App: Clicks "🚀 Run InstantFit AI Screening"
    App->>Det: evaluate_candidate_deterministically(jd_text, cv_text, weights)
    Det-->>App: det_result (Score, Verdict, Matched, Missing, Questions)

    opt AI Inference Connected
        App->>AI: generate_qualitative_assessment(jd_text, cv_text)
        AI->>Provider: POST /chat/completions (timeout: 35s)
        alt Success
            Provider-->>AI: qualitative_analysis_text
            AI-->>App: {status: "success", text: "..."}
        else Timeout / Error
            AI-->>App: {status: "offline_fallback", message: "..."}
        end
    end

    App->>Reg: upsert_candidate(...) -> candidate_id
    App->>Reg: upsert_job(...) -> job_id
    App->>Reg: save_screening(...) -> screening_id
    App->>Reg: associate_screening_files(screening_id, jd_id, cv_id)
    Reg-->>App: Persisted
    App-->>Recruiter: Renders Interactive Scorecard, Evidence, & Dossier Download
```

---

## 5. Candidate Data & Screening History Model

The SQLite database (`data/fitment.db`) enforces relational integrity through parameterized queries:

### Primary Tables
1. **`candidates`**:
   - `candidate_id` (TEXT, PK): 8-character UUID.
   - `name`, `email`, `mobile`, `location`: Candidate identifiers.
   - `current_organization`, `current_designation`, `total_experience`, `relevant_experience`.
   - `certifications` (TEXT): JSON array of detected certifications.
   - `current_status` (TEXT): Default `'Screened'`.
   - `created_at`, `updated_at`: ISO-8601 timestamps.

2. **`jobs`**:
   - `job_id` (TEXT, PK), `job_title`, `job_description`, `required_skills` (JSON).

3. **`screenings`**:
   - `screening_id` (TEXT, PK): UUID.
   - `candidate_id` (FK -> `candidates`), `job_id` (FK -> `jobs`).
   - `deterministic_score` (INT 0-100), `verdict` (TEXT), `recommendation` (TEXT).
   - `skills_score`, `exp_score`, `cert_score`.
   - `matched_skills` (JSON), `missing_skills` (JSON), `supporting_evidence` (JSON).
   - `interview_questions` (JSON).
   - `llm_analysis` (TEXT), `llm_provider` (TEXT), `llm_model` (TEXT).
   - `screening_timestamp` (TEXT).

4. **`stored_files`**:
   - `file_id` (TEXT, PK), `file_type` (`'job_description'` | `'resume'`).
   - `original_filename`, `stored_relative_path`, `file_size`, `sha256_hash`, `upload_timestamp`.
   - `candidate_id` (FK), `job_id` (FK), `screening_id` (TEXT).

5. **`screening_files` (Junction Table)**:
   - `id` (INTEGER PK AUTOINCREMENT), `screening_id` (FK), `file_id` (FK), `file_role` (`'jd'` | `'resume'`), `created_at`.
   - *Design Note*: Enables many-to-many relationships (e.g. one JD reused across multiple candidate screenings).

6. **`candidate_status_history`**:
   - `id` (PK), `candidate_id` (FK), `screening_id`, `previous_status`, `new_status`, `changed_at`, `notes`, `changed_by`.

7. **`follow_ups`**:
   - `id` (PK), `candidate_id` (FK), `follow_up_date`, `status` (`'pending'` | `'completed'`), `notes`.

---

## 6. Recruitment Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> New: Uploaded / Candidate Identified
    New --> Screened: InstantFit Evaluation Run
    Screened --> Recruiter_Review: Recruiter Inspection
    Screened --> Shortlisted: Score Meets Benchmark
    Screened --> Rejected: Major Competency Gaps

    Recruiter_Review --> Shortlisted: Candidate Approved
    Recruiter_Review --> On_Hold: Pending Headcount/Role Shift
    Recruiter_Review --> Rejected: Disqualified

    Shortlisted --> Interview_Scheduled: Rounds Scheduled
    Interview_Scheduled --> Interview_Completed: Evaluation Complete
    Interview_Completed --> Selected: Hiring Manager Decision
    Interview_Completed --> Rejected: Technical Deficit
    Interview_Completed --> On_Hold: Pool Backup

    Selected --> Offer_Released: HR Approval
    Offer_Released --> Joined: Candidate Onboarded
    Offer_Released --> Rejected: Offer Declined

    On_Hold --> Shortlisted: Pipeline Reactivated
    On_Hold --> Rejected: Requisition Closed
```

Every transition writes an immutable audit record in `candidate_status_history`.

---

## 7. Fitment Assistant Conversational Execution

The Fitment Assistant (`chatbot.py`) functions as a domain-specialized conversational agent:

1. **Context Resolution**: Checks whether an active candidate is selected (`active_candidate_id`) or if the user's message mentions a registered candidate's name.
2. **Intent Classification**:
   - **Candidate Lookup**: Factual queries about designation, experience, contact details, or fitment score.
   - **Follow-up Inquiries**: Queries about upcoming, overdue, or due-today candidate milestones.
   - **Screening Comparisons**: Chronological evaluation events across multiple screenings.
   - **Interview Probe Requests**: Role-specific technical probing questions.
   - **Status Transitions**: Modifying candidate hiring status.
3. **Database Grounding**: Executes parameterized SQL queries against `registry.py` to fetch verified ground truth.
4. **Response Formatting**: Formats plain-text markdown summaries with highlights, bullets, and scorecards.
5. **Client-Side Copy Actions**: Emits plain-text payload for the `📋 Copy Response` client-side clipboard button.

---

## 8. Security Boundaries & Design Safeguards

- **No Remote Code Execution**: Document parsers exclusively extract text strings; no active scripts, macros, or executables are evaluated.
- **Path Traversal Defense**: `storage.py` resolves canonical paths and verifies `os.path.commonpath([base_dir, resolved]) == base_dir` before writing or reading.
- **Data Protection**: Uploaded candidate files, SQLite database, and logs are segregated into `data/` and excluded from Git commits via `.gitignore`.
- **Zero API Key Leakage**: API credentials reside in local `.env` or password-masked Streamlit widgets; keys are never stored in database tables or logs.
- **SQL Parameterization**: All database transactions use SQLite `?` placeholders, eliminating SQL injection risks.

---

## 9. Comprehensive Architecture Vault & Specialized Guides

For specialized architectural topics, refer to the following companion guides:

- [**Application Architecture (`APPLICATION_ARCHITECTURE.md`)**](file:///e:/Projects/resume-screening-agent/APPLICATION_ARCHITECTURE.md) — Detailed tier breakdown, data contracts, and component interfaces.
- [**Data Architecture (`DATA_ARCHITECTURE.md`)**](file:///e:/Projects/resume-screening-agent/DATA_ARCHITECTURE.md) — SQLite schema, ER model, storage engine, and IST timezone boundary queries.
- [**AI Architecture (`AI_ARCHITECTURE.md`)**](file:///e:/Projects/resume-screening-agent/AI_ARCHITECTURE.md) — AI taxonomy, deterministic scoring formulas, and provider integrations.
- [**Security Policy (`SECURITY.md`)**](file:///e:/Projects/resume-screening-agent/SECURITY.md) — STRIDE threat model, secrets governance, and PII protection.
- [**Documentation Vault (`docs/README.md`)**](file:///e:/Projects/resume-screening-agent/docs/README.md) — Master index of all 33+ specialized technical guides across Architecture, AI, Data & Security, Learning, and Operations.

