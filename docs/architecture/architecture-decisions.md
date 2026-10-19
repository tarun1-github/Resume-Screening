# 📐 Architecture Decision Records (ADR) — FITMENT.AI

> **Audience**: Solution Architects, Technical Leads, and System Maintainers.  
> **Last Reviewed**: 2026-10-19  
> **Related Documents**: [`ARCHITECTURE.md`](file:///e:/Projects/resume-screening-agent/ARCHITECTURE.md), [`docs/architecture/system-context.md`](file:///e:/Projects/resume-screening-agent/docs/architecture/system-context.md).

---

## Index of Architectural Decisions

- [**ADR-001**](#adr-001-authoritative-deterministic-scoring-vs-probabilistic-genai) — Authoritative Deterministic Scoring vs. Probabilistic GenAI
- [**ADR-002**](#adr-002-sqlite-embedded-relational-storage) — SQLite Embedded Relational Storage
- [**ADR-003**](#adr-003-local-content-addressable-file-storage-data) — Local Content-Addressable File Storage (`data/`)
- [**ADR-004**](#adr-004-indian-standard-time-ist-utc0530-for-recruitment-analytics) — Indian Standard Time (IST) for Daily Recruitment Analytics
- [**ADR-005**](#adr-005-deferred-pending-navigation-pattern-in-streamlit) — Deferred Pending-Navigation Pattern in Streamlit
- [**ADR-006**](#adr-006-isolated-stfragment-for-live-clock-rendering) — Isolated `@st.fragment` for Live Clock Rendering
- [**ADR-007**](#adr-007-multi-provider-llm-gateway-with-35-second-timeout-and-offline-fallback) — Multi-Provider LLM Gateway with 35s Timeout & Offline Fallback
- [**ADR-008**](#adr-008-dual-mode-conversational-assistant-architecture) — Dual-Mode Conversational Assistant Architecture

---

### ADR-001: Authoritative Deterministic Scoring vs. Probabilistic GenAI
- **Status**: Accepted & Implemented
- **Context**: In recruitment screening, candidate evaluation directly influences hiring outcomes, compliance audits, and candidate shortlisting. Probabilistic LLMs suffer from non-deterministic temperature drift, token hallucinations (e.g. inventing certifications), and black-box unexplainability.
- **Decision**: All numerical scores (0–100), skill matching, seniority calculations, and accreditation validations must be computed authoritatively using deterministic Python algorithms in [`deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/deterministic_engine.py). LLMs are restricted strictly to qualitative narrative generation and conversational synthesis.
- **Consequences**:
  - *Positive*: 100% reproducible results; zero token cost for core screening; full compliance explainability; operates offline.
  - *Negative*: Complex regex and keyword dictionaries must be maintained to cover emerging industry skill variations.
- **Alternatives Considered**: Pure LLM evaluation with JSON output (rejected due to hallucination and temperature drift).

---

### ADR-002: SQLite Embedded Relational Storage
- **Status**: Accepted & Implemented
- **Context**: The application required relational data modeling (candidates, jobs, screenings, status histories, follow-ups) without imposing complex external database server dependencies (PostgreSQL/MySQL) on local installations.
- **Decision**: Adopt SQLite 3 with WAL mode and `PRAGMA foreign_keys = ON;` located at `data/fitment.db`. All transactions use parameterized SQL queries.
- **Consequences**:
  - *Positive*: Zero server configuration; portable single-file database; hot backups via file copy; robust relational integrity.
  - *Negative*: Concurrency write bottlenecks under high-volume multi-user enterprise loads.
- **Alternatives Considered**: JSON flat files (rejected due to lack of indexing, foreign keys, and query flexibility); PostgreSQL (deferred to enterprise cloud roadmap).

---

### ADR-003: Local Content-Addressable File Storage (`data/`)
- **Status**: Accepted & Implemented
- **Context**: Uploaded PDF and DOCX files must be retained so recruiters can re-screen candidates against new job descriptions without re-uploading documents.
- **Decision**: Store original pristine bytes in partitioned directories (`data/job_descriptions/` and `data/resumes/`) indexed by SHA-256 digests in a `stored_files` table, connected to screenings via a `screening_files` junction table.
- **Consequences**:
  - *Positive*: Automatic deduplication; prevents storage bloat; preserves original document formatting; allows one JD to link to hundreds of candidate screenings.
  - *Negative*: Host disk space must be monitored and pruned over time.
- **Alternatives Considered**: Cloud S3 object storage (rejected to preserve offline capability).

---

### ADR-004: Indian Standard Time (IST, UTC+05:30) for Recruitment Analytics
- **Status**: Accepted & Implemented
- **Context**: Recruiters operating in the primary target geography observed daily activity metrics (Screened, Shortlisted, Interview, Joined) carrying over across UTC midnight boundaries or failing to match their local working day.
- **Decision**: Enforce `Asia/Kolkata` (IST) as the standard timezone for all calendar-day boundary queries using Python's `zoneinfo.ZoneInfo("Asia/Kolkata")`. Daily metrics evaluate `[ist_start, ist_end)` using dual-parameter SQL queries that handle both naive local strings and UTC `Z` strings.
- **Consequences**:
  - *Positive*: Accurate daily activity reporting matching recruiters' physical calendar day; no historical records are deleted.
  - *Negative*: International teams in other timezones see metrics relative to IST unless user-specific timezone preferences are added in the future.

---

### ADR-005: Deferred Pending-Navigation Pattern in Streamlit
- **Status**: Accepted & Implemented
- **Context**: Navigating to Candidate Tracker from Recently Viewed Candidates via `"View All ➔"` attempted to write `st.session_state.sidebar_nav_radio = "📋 Candidate Tracker"` after widget instantiation, throwing `StreamlitWidgetAlreadyInstantiatedError`.
- **Decision**: Introduce a deferred pending navigation queue (`st.session_state.pending_nav`). The button sets `pending_nav` and calls `st.rerun()`. At the top of the next script run, `pending_nav` is popped and applied to `selected_nav` *before* the radio widget is instantiated.
- **Consequences**:
  - *Positive*: Completely eliminates widget instantiation errors across all navigation buttons.
  - *Negative*: Requires adhering to the pending pattern for any future navigation trigger buttons.

---

### ADR-006: Isolated `@st.fragment` for Live Clock Rendering
- **Status**: Accepted & Implemented
- **Context**: Displaying a live real-time clock in Streamlit traditionally required periodic `st.rerun()` calls, causing the entire dashboard to re-evaluate every few seconds, disrupting recruiter typing in text areas.
- **Decision**: Encapsulate the clock pill in an isolated function annotated with `@st.fragment(run_every="5s")`.
- **Consequences**:
  - *Positive*: Real-time IST clock updates smoothly without triggering full-page re-renders.
  - *Negative*: Requires Streamlit version 1.37.0 or newer.

---

### ADR-007: Multi-Provider LLM Gateway with 35-Second Timeout & Offline Fallback
- **Status**: Accepted & Implemented
- **Context**: Relying exclusively on a single proprietary AI API creates vendor lock-in and vulnerability to service outages, rate limits (HTTP 429), or network timeouts.
- **Decision**: Centralize provider calls in [`llm_manager.py`](file:///e:/Projects/resume-screening-agent/llm_manager.py) supporting Google Gemini, OpenRouter Free Tier, NVIDIA NIM, and Groq Cloud. Enforce a strict 35-second socket timeout with automatic failover to offline rule narratives.
- **Consequences**:
  - *Positive*: Uninterrupted user experience during cloud outages; zero unhandled API exceptions.
  - *Negative*: Qualitative explanations during fallbacks are less nuanced than online models.

---

### ADR-008: Dual-Mode Conversational Assistant Architecture
- **Status**: Accepted & Implemented
- **Context**: Recruiters use the chat companion both to inspect specific candidate screening records and to ask general technical questions (e.g., explaining networking protocols).
- **Decision**: The Fitment Assistant implements dual operating modes:
  - **Mode A (Grounded)**: Questions referencing candidate names, scores, or statuses query SQLite via parameterized SQL and return verified facts.
  - **Mode B (Technical Copilot)**: General technical queries without candidate references route to the configured LLM.
- **Consequences**:
  - *Positive*: Prevents hallucinations on candidate facts while still providing general technical assistance.
  - *Negative*: Requires intelligent intent classification to disambiguate edge-case queries.
