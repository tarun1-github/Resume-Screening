# 🤝 Contributing to FITMENT.AI Recruitment Intelligence Platform

Thank you for your interest in contributing to **FITMENT.AI**! This guide outlines our engineering principles, repository structure, contribution workflows, and quality standards.

---

## 1. Core Engineering Principles

1. **Authoritative Determinism**: Scoring calculations, seniority detection, and competency matching must remain strictly deterministic in Python (`deterministic_engine.py`). Never delegate numerical scoring or gatekeeping decisions to LLMs.
2. **Zero-PII Version Control**: Real resumes, candidate contact details, and database files must never be committed to Git. All tests must use synthetic, non-PII fixtures.
3. **No Uninstantiated Widget Modifications**: In Streamlit (`app.py`), never assign directly to `st.session_state.<widget_key>` after a widget is instantiated. Use the pending navigation flag pattern (`st.session_state.pending_nav`).
4. **Resilient Offline Fallbacks**: All features must function offline without raising uncaught exceptions if cloud AI APIs are disconnected or unavailable.

---

## 2. Development Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12 (64-bit)
- Git

### Initializing the Local Environment
```powershell
# Clone the repository
git clone https://github.com/tarun1-github/Resume-Screening.git
cd Resume-Screening

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create local environment file
copy .env.example .env
```

---

## 3. How to Make Code Changes

### A. Adding or Extending Deterministic Screening Rules
1. Open [`deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/deterministic_engine.py).
2. For new technical skill categories or keyword mappings, update the keyword dictionaries and regex patterns.
3. For accreditations, update `detect_certifications()`.
4. Ensure all new matching logic includes comprehensive tests in [`tests/test_deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/tests/test_deterministic_engine.py).

### B. Adding a New LLM Provider
1. Open [`llm_manager.py`](file:///e:/Projects/resume-screening-agent/llm_manager.py).
2. Register the provider specification in `PROVIDER_SPECS`.
3. Add health-check validation logic to `validate_provider_health()`.
4. Implement the provider call in `generate_qualitative_assessment()` and `generate_general_assistant_response()`.
5. Enforce strict timeout handling (`timeout_seconds=35.0`) and offline fallback.

### C. Database Schema Migrations
1. Open [`registry.py`](file:///e:/Projects/resume-screening-agent/registry.py).
2. Update table creation statements in `init_db()`.
3. Include idempotent migration logic (`PRAGMA table_info`, `ALTER TABLE ... ADD COLUMN`) to ensure existing databases upgrade seamlessly without data loss.

---

## 4. Testing & Verification Requirements

Before submitting changes or proposing commits, execute the complete test suite:

```powershell
# Run the complete test suite
python -m unittest discover tests

# Syntax and compilation check
python -m py_compile app.py registry.py deterministic_engine.py chatbot.py llm_manager.py storage.py parser.py
```

All tests must pass (155+ tests). If you add new functionality, write corresponding unit tests under `tests/`.

---

## 5. Pre-Commit Quality & Security Checklist

Before committing any files:
- [ ] Run `git status` to ensure `.env`, `fitment.db`, `data/*.pdf`, `data/*.docx`, and logs are untracked.
- [ ] Verify no hardcoded API keys, tokens, or passwords exist in your code.
- [ ] Confirm all unit tests pass (`python -m unittest discover tests`).
- [ ] Verify Streamlit starts cleanly without warnings: `streamlit run app.py`.
- [ ] Follow semantic commit message format (e.g. `feat: add IST clock pill to welcome banner`).

---

## 6. Code Style & Conventions

- Follow **PEP 8** style guidelines.
- Use explicit type annotations for all new function definitions (`typing.List`, `typing.Dict`, `typing.Optional`, `typing.Tuple`).
- Document public functions and classes with descriptive docstrings detailing arguments, returns, and failure conditions.
- Preserve existing comments and docstrings.
