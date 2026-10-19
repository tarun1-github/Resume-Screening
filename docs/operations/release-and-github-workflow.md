# 🚀 Release Engineering & GitHub Workflow — FITMENT.AI

> **Audience**: Release Managers, Core Maintainers, and Contributing Engineers.  
> **Last Reviewed**: 2026-10-19  

---

## 1. Branching & Governance Model

FITMENT.AI maintains a clean, linear Git history:
- **`main`**: Production-ready branch. Every commit on `main` must compile cleanly and pass all automated tests.
- **Feature Branches**: Named descriptively: `feat/<feature-name>`, `fix/<issue-name>`, `docs/<topic-name>`.

---

## 2. Pre-Commit Quality & Security Gate

Before staging or proposing any commit, developers must execute this strict 5-step checklist:

### Step 1: Privacy & Secret Scan
Run `git status` and verify that no untracked secrets or candidate data are staged:
```powershell
git status --short --branch
```
- **Must NOT appear in Git status**:
  - ❌ `.env`
  - ❌ `*.db` / `data/fitment.db`
  - ❌ `data/*.pdf` / `data/*.docx` / `data/resumes/*`
  - ❌ `data/logs/*`
  - ❌ `__pycache__/` / `.venv/`

### Step 2: Code Compilation Check
Ensure all modified Python modules compile without syntax errors:
```powershell
python -m py_compile app.py registry.py deterministic_engine.py chatbot.py llm_manager.py storage.py parser.py api.py
```

### Step 3: Run Full Regression Test Suite
Ensure all 155 unit tests pass:
```powershell
python -m unittest discover tests
```

### Step 4: Review Staged Changes
Inspect the exact diff before committing:
```powershell
git diff
```

---

## 3. Conventional Commit Standards

Commits must follow the Conventional Commits specification:
- `feat: add live IST clock pill and fragment refresh`
- `fix: resolve StreamlitWidgetAlreadyInstantiatedError in View All navigation`
- `docs: refresh complete architecture knowledge base and learning vault`
- `test: add unit tests for IST daily analytics boundaries`
- `refactor: optimize candidate lookup queries in registry`

---

## 4. Release Tagging & Publication Protocol

When cutting a new production release:

1. Update version number and release date in [`CHANGELOG.md`](file:///e:/Projects/resume-screening-agent/CHANGELOG.md).
2. Commit verified changes:
   ```powershell
   git add <verified_files>
   git commit -m "chore(release): v2.2.0 - IST Clock, View All Navigation, and Daily Analytics"
   ```
3. Tag the release:
   ```powershell
   git tag -a v2.2.0 -m "Release v2.2.0: IST Clock, View All Navigation, and Daily Analytics"
   ```
4. Push to remote origin without force-pushing:
   ```powershell
   git push origin main
   git push origin --tags
   ```
