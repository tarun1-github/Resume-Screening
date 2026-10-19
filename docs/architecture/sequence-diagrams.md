# ⏱️ Sequence Diagrams — FITMENT.AI Recruitment Intelligence Platform

> **Audience**: Solution Architects, Software Engineers, and QA Automation Engineers.  
> **Last Reviewed**: 2026-10-19  
> **Related Documents**: [`docs/architecture/data-flow.md`](file:///e:/Projects/resume-screening-agent/docs/architecture/data-flow.md), [`APPLICATION_ARCHITECTURE.md`](file:///e:/Projects/resume-screening-agent/APPLICATION_ARCHITECTURE.md).

This document details the exact execution order, synchronous calls, persistence actions, optional cloud steps, and failure paths for the 10 core operational workflows of FITMENT.AI.

---

## 1. Uploading and Parsing a Job Description

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant App as Streamlit UI (app.py)
    participant Store as Storage (storage.py)
    participant Parser as Parser (parser.py)
    participant Reg as Registry (registry.py)

    Recruiter->>App: Drops JD file (PDF / DOCX / TXT)
    App->>Store: save_job_description_file(raw_bytes, filename)
    Store->>Store: Compute SHA-256 Checksum
    alt Duplicate Checksum Exists in DB
        Store-->>App: Return existing file record (reused)
    else New File
        Store->>Store: Write temp file & atomic move to data/job_descriptions/
        Store->>Reg: INSERT INTO stored_files(...)
        Store-->>App: {file_id, stored_relative_path}
    end
    App->>Parser: extract_text_from_file(raw_bytes, filename)
    Parser->>Parser: Extract paragraphs / pages & clean_text()
    alt Content Length < 30 characters
        Parser-->>App: raise EmptyDocumentError
        App-->>Recruiter: Displays warning: "Document is too short or empty"
    else Success
        Parser-->>App: (cleaned_jd_text, total_pages)
        App->>App: Store in st.session_state.jd_text_val
        App-->>Recruiter: Displays "✅ JD loaded successfully!" & character count
    end
```

---

## 2. Uploading and Parsing a Candidate Resume

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant App as Streamlit UI (app.py)
    participant Store as Storage (storage.py)
    participant Parser as Parser (parser.py)
    participant Det as Deterministic Engine

    Recruiter->>App: Drops Resume file (PDF / DOCX)
    App->>Store: save_resume_file(raw_bytes, filename)
    Store->>Store: Compute SHA-256 & Generate collision-safe filename
    Store->>Store: Write atomic file to data/resumes/
    Store-->>App: {file_id, stored_relative_path}
    App->>Parser: extract_text_from_file(raw_bytes, filename)
    Parser-->>App: (cleaned_cv_text, total_pages)
    App->>App: Store in st.session_state.cv_text_val
    App->>Det: extract_candidate_metadata(cleaned_cv_text)
    Det-->>App: {name, mobile, email, location, current_org, current_desig}
    App->>Det: compute_candidate_experience(cleaned_cv_text)
    Det-->>App: (years, total_exp_str, rel_exp_str)
    App-->>Recruiter: Renders Candidate Summary Strip with metadata
```

---

## 3. Running AI-Assisted Screening (Online Mode)

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant App as Streamlit UI (app.py)
    participant Det as Deterministic Engine
    participant Reg as Registry (registry.py)
    participant LLM as LLM Manager (llm_manager.py)
    participant Cloud as External AI Provider (Gemini / OpenRouter / NVIDIA / Groq)

    Recruiter->>App: Clicks "🚀 Run InstantFit AI Screening"
    App->>Det: evaluate_candidate_deterministically(jd_text, cv_text, weights)
    Det-->>App: det_result (Score, Matched, Missing, Probes)
    App->>LLM: generate_qualitative_assessment(jd_text, cv_text, det_result)
    LLM->>Cloud: POST /chat/completions (35s timeout)
    alt Response Received in < 35s
        Cloud-->>LLM: HTTP 200 OK (Qualitative Summary)
        LLM-->>App: {status: "success", text: narrative, provider: "Gemini"}
    else Provider Times Out or Fails
        LLM-->>App: {status: "offline_fallback", text: rule_narrative}
    end
    App->>Reg: upsert_candidate(...)
    App->>Reg: upsert_job(...)
    App->>Reg: save_screening(..., deterministic_score, llm_analysis)
    App->>Reg: associate_screening_files(screening_id, jd_id, cv_id)
    App-->>Recruiter: Renders Interactive Scorecard with Donut Chart & Qualitative Narrative
```

---

## 4. Running Deterministic Offline Screening

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant App as Streamlit UI (app.py)
    participant Det as Deterministic Engine
    participant Reg as Registry (registry.py)

    Recruiter->>App: Clicks "⚡ Run InstantFit Offline Screening"
    Note over App,Det: No external HTTP calls are dispatched
    App->>Det: evaluate_candidate_deterministically(jd_text, cv_text, weights)
    Det->>Det: Match skill token dictionaries
    Det->>Det: Evaluate experience seniority regex
    Det->>Det: Detect industry certifications
    Det->>Det: Calculate weighted formula: (0.30*skills + 0.40*exp + 0.15*edu + 0.15*certs)
    Det->>Det: Generate targeted interview probing questions
    Det-->>App: det_result
    App->>Reg: upsert_candidate(...)
    App->>Reg: save_screening(..., llm_provider="Offline / Deterministic")
    App->>Reg: associate_screening_files(...)
    App-->>Recruiter: Renders Scorecard with verified badges & Probing Questions
```

---

## 5. Persisting Candidate and Screening Results

```mermaid
sequenceDiagram
    autonumber
    participant App as Streamlit UI
    participant Reg as Registry (registry.py)
    participant DB as SQLite (data/fitment.db)

    App->>Reg: upsert_candidate(candidate_id, name, mobile, email, ...)
    Reg->>DB: SELECT candidate_id FROM candidates WHERE mobile = ? OR email = ?
    alt Candidate Exists
        Reg->>DB: UPDATE candidates SET updated_at = ?, ... WHERE candidate_id = ?
    else New Candidate
        Reg->>DB: INSERT INTO candidates (...) VALUES (...)
    end
    App->>Reg: upsert_job(job_title, job_description, ...)
    Reg->>DB: INSERT OR REPLACE INTO jobs (...)
    App->>Reg: save_screening(screening_id, candidate_id, job_id, scores, skills, ...)
    Reg->>DB: INSERT INTO screenings (...)
    App->>Reg: associate_screening_files(screening_id, jd_file_id, cv_file_id)
    Reg->>DB: INSERT INTO screening_files (screening_id, file_id, file_role, created_at)
    Reg-->>App: Complete Transaction Committed
```

---

## 6. Loading a Saved JD or Resume

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant App as Streamlit UI
    participant Store as Storage (storage.py)
    participant Reg as Registry (registry.py)
    participant Parser as Parser (parser.py)

    Recruiter->>App: Selects previous document from dropdown picker
    App->>Store: read_stored_file_bytes(selected_file_id)
    Store->>Store: resolve_stored_path(relative_path) -> Path traversal check
    Store->>Store: Read binary file from disk
    Store-->>App: file_bytes
    App->>Parser: extract_text_from_file(file_bytes, filename)
    Parser-->>App: cleaned_text
    App->>App: Populate text area session state
    App-->>Recruiter: Displays loaded document with verification badge
```

---

## 7. Updating Recruitment Status & Transition History

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant App as Streamlit UI / Chatbot
    participant Reg as Registry (registry.py)
    participant DB as SQLite (data/fitment.db)

    Recruiter->>App: Changes status dropdown to "Shortlisted" (or sends chat instruction)
    App->>Reg: update_candidate_status(candidate_id, new_status="Shortlisted", notes="Approved")
    Reg->>DB: SELECT current_status FROM candidates WHERE candidate_id = ?
    DB-->>Reg: previous_status = "Screened"
    Reg->>DB: UPDATE candidates SET current_status = 'Shortlisted', updated_at = ? WHERE candidate_id = ?
    Reg->>DB: INSERT INTO candidate_status_history (candidate_id, previous_status, new_status, changed_at, notes, changed_by) VALUES (?, ?, ?, ?, ?, ?)
    Reg-->>App: True (Status Updated)
    App-->>Recruiter: Displays confirmation notification & updates Candidate Tracker
```

---

## 8. Asking a Candidate-Specific Chatbot Question (Mode A)

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant ChatUI as Fitment Assistant UI
    participant Bot as Chatbot Router (chatbot.py)
    participant Reg as Registry (registry.py)
    participant DB as SQLite (data/fitment.db)

    Recruiter->>ChatUI: Submits: "What is Tarun's fitment score and contact number?"
    ChatUI->>Bot: ask(user_query, selected_candidate_id)
    Bot->>Bot: Security Check: Check for secrets / passwords request -> Passed
    Bot->>Bot: Entity Resolution: resolve_candidate_for_query("Tarun")
    Bot->>Reg: find_candidate_by_name("Tarun")
    Reg->>DB: SELECT * FROM candidates WHERE name LIKE '%Tarun%'
    DB-->>Reg: candidate_record (Tarun)
    Reg-->>Bot: candidate_record
    Bot->>Reg: get_candidate_screenings(candidate_id)
    Reg->>DB: SELECT * FROM screenings WHERE candidate_id = ? ORDER BY screening_timestamp DESC
    DB-->>Reg: latest_screening
    Reg-->>Bot: [latest_screening]
    Bot->>Bot: Format grounded response with score (85/100) & mobile
    Bot-->>ChatUI: {answer: formatted_markdown, candidate_id: "cid-123"}
    ChatUI-->>Recruiter: Renders answer with "📋 Copy Response" action
```

---

## 9. Asking a Generic Technical Question through LLM (Mode B)

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant ChatUI as Fitment Assistant UI
    participant Bot as Chatbot Router (chatbot.py)
    participant LLM as LLM Manager (llm_manager.py)
    participant Cloud as Cloud Provider (Gemini / OpenRouter / NVIDIA)

    Recruiter->>ChatUI: Submits: "Explain the SIP three-way handshake for voice networks."
    ChatUI->>Bot: ask(user_query)
    Bot->>Bot: Entity Resolution: No candidate found & general technical term detected
    Bot->>LLM: generate_general_assistant_response(query, conversation_history)
    LLM->>Cloud: POST /chat/completions (Technical Explanation Prompt)
    Cloud-->>LLM: HTTP 200 OK (Detailed SIP Explanation)
    LLM-->>Bot: {status: "success", text: explanation_text, provider: "Gemini"}
    Bot-->>ChatUI: {answer: explanation_text, provider: "Gemini"}
    ChatUI-->>Recruiter: Renders technical response with copy buttons
```

---

## 10. Handling Provider Failures, Missing Files & DB Errors

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant App as Streamlit UI
    participant Store as Storage (storage.py)
    participant LLM as LLM Manager (llm_manager.py)
    participant DB as SQLite Registry

    Note over App,Store: Scenario A: Missing Stored File
    Recruiter->>App: Requests deleted resume
    App->>Store: read_stored_file_bytes("missing_file_id")
    Store-->>App: raise FileNotFoundError("Stored file does not exist")
    App-->>Recruiter: Displays friendly error: "Document file not found on disk"

    Note over App,LLM: Scenario B: Cloud Provider Timeout / Rate Limit
    Recruiter->>App: Runs screening with expired API key or network down
    App->>LLM: generate_qualitative_assessment(...)
    LLM->>LLM: Dispatches HTTP request with 35s timeout
    LLM-->>LLM: Socket Timeout / HTTP 429 Rate Limit
    LLM-->>App: {status: "offline_fallback", text: "Offline assessment used"}
    App-->>Recruiter: Renders complete deterministic scorecard without crashing

    Note over App,DB: Scenario C: Database Concurrency / Lock
    App->>DB: execute UPDATE candidates ...
    DB-->>App: sqlite3.OperationalError: database is locked
    App->>App: Context manager retries with exponential backoff
    App-->>Recruiter: Recovers transparently
```
