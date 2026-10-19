# 🧭 Codebase Tour & Directory Map — FITMENT.AI

> **Audience**: New Developers, Code Reviewers, and System Maintainers.  
> **Last Reviewed**: 2026-10-19  
> **Related Documents**: [`docs/learning/END_TO_END_WALKTHROUGH.md`](file:///e:/Projects/resume-screening-agent/docs/learning/END_TO_END_WALKTHROUGH.md), [`APPLICATION_ARCHITECTURE.md`](file:///e:/Projects/resume-screening-agent/APPLICATION_ARCHITECTURE.md).

---

## 1. Directory Tree & Architectural Map

```text
E:\Projects\resume-screening-agent/
│
├── app.py                         # Primary Streamlit portal & presentation orchestrator
├── deterministic_engine.py        # Authoritative deterministic evaluation & scoring core
├── registry.py                    # SQLite candidate registry, schema, & IST analytics
├── storage.py                     # Durable file storage engine (data/) with SHA-256 dedup
├── chatbot.py                     # Fitment Assistant intent routing & database grounding
├── llm_manager.py                 # Multi-provider LLM gateway (Gemini, OpenRouter, NVIDIA, Groq)
├── parser.py                      # Multi-format document parser (PDF, DOCX, TXT)
├── api.py                         # Optional FastAPI REST service (/screen, /candidates)
├── agent_engine.py                # Standalone multi-agent pipeline (JD, Matcher, RedFlag, Scorer)
├── mcp_server.py                  # FastMCP tool server exposing screening to external agents
├── multi_agents.py                # Early experimental LangGraph / Chroma prototype
├── requirements.txt               # Pinned production Python dependencies
├── .env.example                   # Sanitized configuration template with placeholder keys
├── .gitignore                     # Git privacy protections for candidate files & secrets
│
├── .streamlit/
│   └── config.toml                # Light theme styling tokens, ports, & upload size limits
│
├── data/                          # Persistent storage root (protected by .gitignore)
│   ├── fitment.db                 # SQLite relational database file
│   ├── job_descriptions/          # Stored job description files (.docx, .pdf, .txt)
│   ├── resumes/                   # Stored candidate resume files (.docx, .pdf, .txt)
│   └── logs/                      # Runtime application diagnostics
│
├── docs/                          # Comprehensive Technical Knowledge Base & Learning Vault
│   ├── README.md                  # Documentation master directory & index
│   ├── architecture/              # System context, components, state, sequence diagrams, ADRs
│   ├── ai/                        # AI ecosystem, deterministic vs GenAI, chatbot, grounding
│   ├── data-and-security/         # Database schema, ER model, data lifecycle, threat model
│   ├── learning/                  # Knowledge map, mental models, tour, glossary, QA, exercises
│   └── operations/                # Setup, config reference, testing guide, troubleshooting
│
└── tests/                         # Automated unit & integration regression test suites
    ├── test_daily_analytics_navigation_timestamps.py  # IST boundaries, navigation, timestamps
    ├── test_deterministic_engine.py                  # Scoring math, regex, certification logic
    ├── test_file_storage.py                          # Path traversal, deduplication, atomic writes
    ├── test_portal_upgrades.py                       # Status transitions, follow-ups, queries
    ├── test_screening_files_normalization.py         # Junction data normalization
    ├── test_api.py                                   # FastAPI REST endpoints
    ├── test_critical_fixes.py                        # Secret shielding & crash prevention
    ├── test_dashboard_analytics.py                   # Analytics aggregations
    └── test_upload_persistence_regression.py         # File persistence regression tests
```

---

## 2. Execution Entry Points

| Entry Point | Command Line | Entry File | Description |
| :--- | :--- | :--- | :--- |
| **Streamlit Web Portal** | `streamlit run app.py` | [`app.py`](file:///e:/Projects/resume-screening-agent/app.py) | Main interactive recruitment portal, candidate tracker, and chat companion. |
| **Headless REST API** | `uvicorn api:app --port 8000` | [`api.py`](file:///e:/Projects/resume-screening-agent/api.py) | REST API exposing `/screen` and `/candidates` endpoints. |
| **Model Context Protocol**| `python mcp_server.py` | [`mcp_server.py`](file:///e:/Projects/resume-screening-agent/mcp_server.py) | FastMCP server exposing `screen_candidate` tool to AI IDEs or Claude Desktop. |
| **Regression Test Runner**| `python -m unittest discover tests`| [`tests/`](file:///e:/Projects/resume-screening-agent/tests) | Executes all 155+ unit and integration tests. |

---

## 3. "Where Do I Find...?" Developer Navigation Guide

| If you want to modify or inspect... | Open this source file | Key Function / Symbol to search |
| :--- | :--- | :--- |
| **Mathematical scoring formulas** | [`deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/deterministic_engine.py) | `evaluate_candidate_deterministically()` |
| **Experience detection & graduation filters** | [`deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/deterministic_engine.py) | `compute_candidate_experience()` |
| **Supported certifications dictionary** | [`deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/deterministic_engine.py) | `detect_certifications()` |
| **Database tables, constraints, & indexes** | [`registry.py`](file:///e:/Projects/resume-screening-agent/registry.py) | `init_db()` |
| **Today's recruitment metrics & IST date filter**| [`registry.py`](file:///e:/Projects/resume-screening-agent/registry.py) | `get_dashboard_analytics_summary()` |
| **Timestamp formatting (`DD Mon YYYY, ... IST`)**| [`registry.py`](file:///e:/Projects/resume-screening-agent/registry.py) | `format_last_screened()` |
| **Live clock UI banner pill** | [`app.py`](file:///e:/Projects/resume-screening-agent/app.py) | `_live_clock_fragment()` |
| **Safe navigation triggers & filter resets** | [`app.py`](file:///e:/Projects/resume-screening-agent/app.py) | `pending_nav` / line 1400–1430 |
| **File deduplication & path traversal check** | [`storage.py`](file:///e:/Projects/resume-screening-agent/storage.py) | `resolve_stored_path()` |
| **Chatbot intent routing & secret shielding** | [`chatbot.py`](file:///e:/Projects/resume-screening-agent/chatbot.py) | `FitmentAssistant.ask()` |
| **Cloud LLM provider configs & timeouts** | [`llm_manager.py`](file:///e:/Projects/resume-screening-agent/llm_manager.py) | `PROVIDER_SPECS`, `DEFAULT_TIMEOUT` |
| **PDF / DOCX text extraction** | [`parser.py`](file:///e:/Projects/resume-screening-agent/parser.py) | `extract_text_from_file()` |
