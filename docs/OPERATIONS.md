# 🛠️ Operations & Administration Runbook — Recruitment Intelligence Platform

> **Audience**: Platform Administrators, DevOps Engineers, and System Operators.  
> **Note**: For the modular, expanded operations runbooks, visit [**docs/operations/**](file:///e:/Projects/resume-screening-agent/docs/operations/setup-and-installation.md) and the [**Master Documentation Index**](file:///e:/Projects/resume-screening-agent/docs/README.md).

---


### Minimum System Specifications
- **Operating System**: Windows 10/11, Ubuntu 20.04/22.04 LTS, or macOS 12+
- **Python**: Version 3.10, 3.11, or 3.12 (64-bit)
- **Disk Space**: Minimum 2 GB free (accommodates SQLite database and stored resumes)
- **Memory (RAM)**: Minimum 4 GB (8 GB recommended for concurrent multi-page document parsing)

### Clean Setup Procedure

```powershell
# 1. Clone repository
git clone https://github.com/tarun1-github/Resume-Screening.git
cd Resume-Screening

# 2. Create isolated virtual environment
python -m venv .venv

# 3. Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 4. Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2. Startup, Execution & Shutdown

### Launching the Streamlit Web Portal
```powershell
# Standard local development
streamlit run app.py

# Headless / server mode (port 8501)
streamlit run app.py --server.port 8501 --server.headless true
```
The portal will be accessible at: `http://localhost:8501`.

### Launching the Headless REST API (Optional)
```powershell
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be accessible at: `http://localhost:8000/docs`.

### Stopping the Services
- **Foreground Process**: Press `Ctrl + C` in the active terminal window.
- **Background Daemon Process (PowerShell)**:
  ```powershell
  # Find running Streamlit process
  Get-Process -Name python | Where-Object { $_.CommandLine -like "*streamlit*" }
  # Terminate process
  Stop-Process -Id <ProcessId> -Force
  ```

---

## 3. Configuration Management

Configuration parameters are loaded from environment variables or a local `.env` file via `python-dotenv`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `FITMENT_DATA_DIR` | `./data` | Root directory for file storage, database, and logs. |
| `DATABASE_URL` | `sqlite:///./data/fitment.db` | Connection string for candidate registry. |
| `LLM_PROVIDER` | `gemini` | Preferred AI provider (`gemini`, `openrouter`, `nvidia`, `groq`, `offline`). |
| `LLM_TIMEOUT_SECONDS`| `30` | Network timeout budget for external AI calls. |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key. |
| `OPENROUTER_API_KEY`| *(empty)* | OpenRouter API key. |
| `NVIDIA_API_KEY` | *(empty)* | NVIDIA Build NIM API key. |
| `GROQ_API_KEY` | *(empty)* | Groq Cloud API key. |

To apply configuration changes, update `.env` and restart the Streamlit server or use the in-app **`↻ Refresh Page`** action.

---

## 4. File Storage & Database Administration

### Directory Structure & Layout
All persistent application state is located under `data/`:
```text
data/
├── fitment.db                 # SQLite Relational Registry
├── job_descriptions/          # Uploaded Job Descriptions (.docx, .pdf, .txt)
├── resumes/                   # Uploaded Candidate Resumes (.docx, .pdf, .txt)
└── logs/                      # Application diagnostics and runtime traces
```

### Database Backup
SQLite databases can be backed up safely while running:
```powershell
# Create automated timestamped snapshot
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item data/fitment.db "data/fitment_backup_$timestamp.db"
```

### Database Recovery
```powershell
# Restore from snapshot
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Copy-Item "data/fitment_backup_<timestamp>.db" data/fitment.db
```

### Storage Retention & Pruning Policy
To purge archived files older than 180 days while preserving candidate records:
```powershell
$limit = (Get-Date).AddDays(-180)
Get-ChildItem -Path "data/resumes", "data/job_descriptions" -File | Where-Object { $_.LastWriteTime -lt $limit } | Remove-Item
```

---

## 5. Automated Testing & Verification

Run the complete regression test suite prior to deploying updates:

```powershell
# Run all tests
python -m unittest discover tests

# Run specific test modules
python -m unittest tests/test_file_storage.py
python -m unittest tests/test_screening_files_normalization.py
python -m unittest tests/test_deterministic_engine.py
python -m unittest tests/test_portal_upgrades.py
python -m unittest tests/test_api.py
```

Expected result:
```text
Ran 85 tests in ~13s
OK
```

---

## 6. Troubleshooting Common Issues

### Issue 1: `TypeError: string indices must be integers, not 'str'` in Screening History
- **Root Cause**: An unnormalized screening files structure (a dictionary key passed as a record).
- **Resolution**: Ensured `registry.normalize_screening_files()` parses dictionary, list, and string formats safely. Verify all tests pass with `python -m unittest tests/test_screening_files_normalization.py`.

### Issue 2: External AI Service Timeout / Rate-Limit
- **Symptom**: `⚠️ AI analysis timed out. Falling back to offline assessment.`
- **Behavior**: Normal operational fallback. The deterministic engine calculates scores with zero data loss.
- **Remedy**: Recruiter can switch active provider in the sidebar **⚙️ AI Settings** to Google Gemini, OpenRouter, or Offline mode.

### Issue 3: Streamlit Top Bar Overlaps Header
- **Remedy**: Ensure `padding-top: 2.8rem !important;` is set on `.block-container` in `app.py`, allowing adequate vertical clearance beneath Streamlit's header controls.

---

## 7. Safe Deployment & GitHub Release Guidelines

1. **Verify No Sensitive Data Is Staged**:
   ```powershell
   git status --short
   ```
   Ensure `.env`, `fitment.db`, or loose candidate CV files under `data/` are never listed.
2. **Execute Full Test Suite**:
   ```powershell
   python -m unittest discover tests
   ```
3. **Commit & Push to Remote**:
   ```powershell
   git add app.py parser.py registry.py storage.py chatbot.py llm_manager.py tests/ README.md ARCHITECTURE.md AI_ARCHITECTURE.md SECURITY.md docs/ .env.example .gitignore
   git commit -m "Stabilize recruitment portal and document AI architecture"
   git push origin main
   ```
