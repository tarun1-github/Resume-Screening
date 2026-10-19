# 🧠 Progressive Mental Models — FITMENT.AI Recruitment Intelligence Platform

> **Audience**: All Engineers, Architects, Recruiters, and Technical Leaders.  
> **Last Reviewed**: 2026-10-19  
> **Core Companion Docs**: [`docs/learning/KNOWLEDGE_MAP.md`](file:///e:/Projects/resume-screening-agent/docs/learning/KNOWLEDGE_MAP.md), [`APPLICATION_ARCHITECTURE.md`](file:///e:/Projects/resume-screening-agent/APPLICATION_ARCHITECTURE.md).

---

## 1. The 30-Second Mental Model (Elevator Pitch)

> **Analogy**: *Think of FITMENT.AI as an expert technical interviewer sitting right beside you. Instead of guessing or hallucinating candidate scores, it uses a precise mathematical ruler to measure exact skill overlap and experience depth, stores the results in an audit-ready ledger, and lets you query candidate details through a smart conversational companion.*

### The Core Essence
FITMENT.AI takes a Job Description and a Candidate Resume, extracts verified facts (skills, experience, certifications), calculates a mathematically reproducible fitment score (0–100), saves the evaluation in a local SQLite database, and optionally enriches the report with qualitative AI executive summaries—all while operating 100% reliably offline.

---

## 2. The Beginner Mental Model: The Assembly Line

> **Analogy**: *An automated factory assembly line where raw materials enter at one end, pass through inspection stations, get stamped with a quality score, and are packaged into an executive report.*

```mermaid
flowchart LR
    subgraph Station1 ["Station 1: Unpack"]
        RawDocs["PDF / DOCX Uploads"] --> Parser["Text Extractor"]
    end

    subgraph Station2 ["Station 2: Inspect & Measure"]
        Parser --> Scanner["Rule Inspector<br/>• Matches Skills<br/>• Checks Years<br/>• Verifies Certs"]
    end

    subgraph Station3 ["Station 3: Quality Stamp"]
        Scanner --> Scorer["Score Calculator<br/>(Weighted 0-100 Math)"]
    end

    subgraph Station4 ["Station 4: Warehouse & Display"]
        Scorer --> DB[("SQLite Warehouse")]
        Scorer --> UI["Recruiter Dashboard"]
    end
```

### Key Beginner Concepts
- **Inputs**: Two text or document files (Job Description + Resume).
- **Processing**: The system searches for exact keywords, calculates years of experience, and validates certifications.
- **Outputs**:
  - A numerical score from 0 to 100.
  - A color-coded verdict: **Strong Fit** (Green $\ge 75$), **Moderate Fit** (Amber $55–74$), **Weak Fit** (Red $< 55$).
  - A checklist of matched skills and missing competency gaps.
  - 3 targeted technical interview questions.

> [!TIP]
> **Remember This**: FITMENT.AI never guesses your candidate's score. The score is calculated using pure math, meaning the same resume always gets the exact same score.

---

## 3. The Developer Mental Model: Functions, State & Schema

For developers writing code in Python, Streamlit, and SQLite:

```mermaid
flowchart TD
    subgraph StreamlitApp ["app.py (Streamlit Web Tier)"]
        UI_Event["User Interaction / Upload"] --> ScriptRun["Top-to-Bottom Script Run"]
        ScriptRun --> PendingNav{"Check pending_nav"}
        PendingNav --> RadioNav["Render sidebar_nav_radio"]
        RadioNav --> ViewDispatcher{"chosen_nav Dispatcher"}
    end

    subgraph BusinessLogic ["Core Processing Services"]
        ViewDispatcher -->|Parse| P["parser.py: extract_text_from_file()"]
        ViewDispatcher -->|Store| S["storage.py: save_resume_file()"]
        ViewDispatcher -->|Score| D["deterministic_engine.py: evaluate_candidate_deterministically()"]
        ViewDispatcher -->|Chat| C["chatbot.py: FitmentAssistant.ask()"]
    end

    subgraph Persistence ["Data Store (data/)"]
        S --> DB[(SQLite: fitment.db)]
        D --> DB
        C <--> DB
    end

    subgraph OptionalCloud ["Cloud Egress"]
        D -.->|Qualitative Narrative| L["llm_manager.py: generate_qualitative_assessment()"]
        C -.->|Mode B Technical Q&A| L
    end
```

### Developer Invariants
1. **Streamlit Script Lifecycle**: Every button click re-executes the file from line 1. State must be preserved in `st.session_state`.
2. **Widget Key Protection**: Never assign to a widget's session state key after instantiation. Always set `st.session_state.pending_nav` and call `st.rerun()`.
3. **Database Parameterization**: Never use string interpolation in SQL. Every query uses `?` placeholders.
4. **Isolated Refresh**: Real-time clocks run inside `@st.fragment(run_every="5s")` to prevent full-page script re-runs.

---

## 4. The Solution Architect Mental Model: Boundaries, Ownership & Invariants

```mermaid
flowchart TD
    subgraph TrustBoundary ["Local Trust Perimeter (Workstation / On-Premise Host)"]
        subgraph WebProcess ["Process 1: Web Application"]
            Streamlit["Streamlit UI Server (:8501)"]
            Engine["Deterministic Engine Core"]
            AssistantRouter["Intent Router & Dispatcher"]
        end

        subgraph LocalDisk ["Durable Local Storage (data/)"]
            SQLiteDB[("SQLite 3 Database (fitment.db)<br/>Data Ownership: Complete Relational Truth")]
            Filesystem["Local Content-Addressable Storage<br/>• data/job_descriptions/<br/>• data/resumes/"]
        end
    end

    subgraph ExternalPerimeter ["External Egress Perimeter (Outbound HTTPS :443)"]
        AIProviders["Cloud LLM Endpoints<br/>(Gemini, OpenRouter, NVIDIA NIM, Groq)<br/>Data Ownership: Ephemeral, Stateless Inference"]
    end

    Streamlit <--> SQLiteDB
    Streamlit <--> Filesystem
    Engine --> SQLiteDB
    AssistantRouter <--> SQLiteDB
    Streamlit -.->|Only Minimized Evidence (No Raw PDFs)| AIProviders
```

### Architectural Invariants & Tradeoffs
- **Relational Integrity**: Foreign keys (`PRAGMA foreign_keys = ON;`) ensure zero orphan screenings or dangling junction records.
- **Timezone Governance**: Standardized on Indian Standard Time (`Asia/Kolkata`) across all daily boundary calculations.
- **Graceful Degradation**: If external AI APIs drop or time out (exceeding 35s), the system degrades to deterministic narratives with zero crash.

---

## 5. The AI Mental Model: The Dual Brain

> **Analogy**: *Think of the AI architecture as a courthouse. The **Judge** (Deterministic Engine) applies strict written laws and calculations to decide the verdict. The **Court Reporter** (Generative AI) writes an eloquent, nuanced narrative summary of the trial.*

```mermaid
flowchart TD
    subgraph Brain1 ["Left Brain: The Analytical Judge (Deterministic)"]
        J1["Regex Tokenizer"]
        J2["Experience Tenure Math"]
        J3["Accreditation Validator"]
        J4["Scoring Formula: 0-100"]
    end

    subgraph TruthGate ["Authoritative Truth Gate"]
        Verdict["Defensible Score & Verdict"]
    end

    subgraph Brain2 ["Right Brain: The Articulate Reporter (Generative AI)"]
        R1["Qualitative Executive Summary"]
        R2["Nuanced Strengths & Gap Observations"]
        R3["Advisory Interview Strategy"]
    end

    Brain1 --> TruthGate
    TruthGate --> Brain2
    Brain2 -.->|Advisory Commentary| FinalReport["Unified Recruiter Scorecard"]
    TruthGate --> FinalReport
```

### Common AI Misconceptions
- ❌ *Misconception*: "The LLM calculates the 85/100 score."  
  ✅ *Reality*: Python calculates the 85/100 score using math. The LLM only writes qualitative text.
- ❌ *Misconception*: "The chatbot uses Vector RAG with cosine embeddings."  
  ✅ *Reality*: The chatbot uses relational SQL queries against SQLite for 100% precision on candidate contact numbers, scores, and status history.

---

## 6. The Operational Model: The Diagnostic Triage Tree

When diagnosing system issues in production, use this systematic mental model:

```mermaid
flowchart TD
    Problem["Issue Observed in Platform"] --> Q1{"Does the Streamlit Web Page Load?"}

    Q1 -->|No| CheckProcess["Check Python Process:
• Is port 8501 in use?
• Run: Get-Process python"]

    Q1 -->|Yes| Q2{"Is the Issue Scoring or Document Related?"}

    Q2 -->|Yes| CheckParser["Check Document Parser:
• Is the PDF scanned/flattened image?
• Is extracted length < 30 chars?
• Check data/logs/"]

    Q2 -->|No| Q3{"Is the Issue with the Live Clock or Daily Counts?"}

    Q3 -->|Yes| CheckTimezone["Check Timezone & SQLite:
• Verify system clock in IST
• Check registry.get_dashboard_analytics_summary()
• Confirm database records exist for today"]

    Q3 -->|No| Q4{"Is the Issue with AI Summaries or Chatbot?"}

    Q4 -->|Yes| CheckAI["Check AI Service Connectivity:
• Is API key present in .env or Settings?
• Check provider health probe in sidebar
• Did external call time out (>35s)?"]
```

---

## 7. The Security Model: Trust Boundaries & Data Exfiltration Defense

```mermaid
flowchart LR
    subgraph PublicZone ["Untrusted External Zone"]
        MaliciousPDF["Uploaded Resume with<br/>Prompt Injection or Path Traversal"]
        AttackerPrompt["Chat Query requesting<br/>API Keys / Passwords"]
    end

    subgraph ArmorPlate ["FITMENT.AI Security Shields"]
        PathShield["os.path.commonpath()<br/>Blocks Directory Traversal"]
        ParserShield["Plaintext Only<br/>Zero Executable Macros"]
        SecretShield["Regex Keyword Filter<br/>Blocks Credential Leakage"]
    end

    subgraph SafeCore ["Protected Internal Core"]
        Storage["data/ Filesystem"]
        DB["SQLite Database"]
        Keys[".env Volatile Memory"]
    end

    MaliciousPDF --> PathShield
    MaliciousPDF --> ParserShield
    AttackerPrompt --> SecretShield

    PathShield -->|Validated| Storage
    ParserShield -->|Sanitized Text| DB
    SecretShield -->|Blocked| SafeCore
```

### Security Takeaways
1. Resumes never execute code.
2. Target paths never escape `./data`.
3. API keys never enter SQL databases or candidate dossiers.
4. Chatbot never displays secrets.
