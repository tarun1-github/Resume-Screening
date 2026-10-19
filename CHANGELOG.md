# 📜 Changelog — FITMENT.AI Recruitment Intelligence Platform

All notable changes to the FITMENT.AI platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.2.0] — 2026-10-19

### Added
- **Live IST Clock Pill**: Integrated a real-time clock pill into the Welcome Banner displaying formatted Indian Standard Time (`DD Mon YYYY, HH:MM:SS IST (UTC+05:30)`). Implemented isolated auto-refresh using `@st.fragment(run_every="5s")`.
- **Date-Aware Daily Analytics**: Re-engineered `registry.get_dashboard_analytics_summary()` to compute today's counts (Screened, Shortlisted, Interview, Joined) strictly within the active IST calendar day `[ist_start, ist_end)` using parameterized SQL boundary queries.
- **Candidate Last-Screened Timestamps in IST**: Added `format_last_screened()` and `get_candidate_last_screened_timestamp()`, rendering candidate screening timestamps across Candidate Summary, Full Profile Dialog, Candidate Tracker expanders, and Recently Viewed cards.
- **Automated Filter Reset**: When clicking "View All ➔" from Recently Viewed Candidates, Candidate Tracker opens with all search filters and status dropdowns reset to display the full candidate pool.
- **Comprehensive Test Suite**: Added `tests/test_daily_analytics_navigation_timestamps.py` with 10 unit tests verifying IST boundary transitions, safe navigation, and timestamp formatting.

### Fixed
- **View All Navigation Bug**: Resolved `StreamlitWidgetAlreadyInstantiatedError` by replacing direct assignments to `st.session_state.sidebar_nav_radio` with a deferred pending navigation pattern (`st.session_state.pending_nav`).
- **Module Reload Guards**: Added defensive in-memory module reloading safeguards in `app.py` to prevent `AttributeError: module 'registry' has no attribute 'get_current_ist_str'` during hot development server reloads.

---

## [2.1.0] — 2026-10-18

### Added
- **Space-Efficient Enterprise Light Theme**: Redesigned UI with `#F3F6FC` canvas, `#FFFFFF` panels, `#2563EB` primary accents, and `#172033` slate typography.
- **Compact Header**: Streamlined top navigation header (~85px tall) with verified AI connectivity badge and a top-right `↻ Refresh Page` action.
- **Fitment Assistant Companion**: Right-side conversational copilot (~26% width) featuring instant client-side `📋 Copy Response` buttons and quick-copy action pills (`📄 Copy Details`, `🎯 Copy Summary`, `🎤 Copy Probes`).
- **11-Stage Recruitment Pipeline**: Added lifecycle stages (`New`, `Screened`, `Shortlisted`, `Recruiter Review`, `Interview Scheduled`, `Interview Completed`, `On Hold`, `Rejected`, `Selected`, `Offer Released`, `Joined`) with immutable audit logging in `candidate_status_history`.

---

## [2.0.0] — 2026-10-16

### Added
- **InstantFit Deterministic Screening Engine**: 100% offline, zero-hallucination mathematical scoring (0–100) based on regex token matching and configurable category weights.
- **Durable File Storage Engine (`storage.py`)**: Persistent file storage under `data/job_descriptions/` and `data/resumes/` with SHA-256 deduplication and path traversal validation.
- **Multi-Provider LLM Gateway (`llm_manager.py`)**: Unified gateway supporting Google Gemini, OpenRouter Free Tier, NVIDIA NIM, and Groq Cloud with 35-second timeouts and automatic offline fallback.
- **Relational Candidate Registry (`registry.py`)**: SQLite relational database (`data/fitment.db`) with 7 tables, indexing, and parameterized query execution.

---

## [1.0.0] — 2026-10-15

### Added
- Initial proof-of-concept candidate screening portal with PDF text extraction (`parser.py`) and basic keyword alignment.
