# 🔧 Troubleshooting Runbook & Diagnostics — FITMENT.AI

> **Audience**: Platform Operators, System Administrators, and Support Engineers.  
> **Last Reviewed**: 2026-10-19  

---

## 1. Quick Diagnostic Triage Table

| Symptom / Error Message | Suspected Subsystem | Quick Remediation |
| :--- | :--- | :--- |
| `StreamlitWidgetAlreadyInstantiatedError` | Streamlit Navigation (`app.py`) | Use `st.session_state.pending_nav` and call `st.rerun()`. Never assign directly to `sidebar_nav_radio`. |
| `AttributeError: module 'registry' has no attribute 'get_current_ist_str'` | In-Memory Module Cache | Hot reload cached module via `importlib.reload(registry)` or restart Streamlit server. |
| Daily Activity counts carrying over from yesterday | Daily Analytics Query (`registry.py`) | Verify system clock timezone is set to IST; confirm `registry.get_dashboard_analytics_summary()` uses active IST boundaries. |
| `TypeError: string indices must be integers, not 'str'` | Screening Files Normalization | Ensure `registry.normalize_screening_files()` processes the record before rendering. |
| `Address already in use (port 8501)` | OS Network Binding | Terminate orphaned Python process or launch on alternative port: `--server.port 8502`. |
| `⚠️ AI analysis timed out. Falling back to offline assessment.` | Cloud LLM Gateway (`llm_manager.py`) | Expected behavior when cloud providers exceed 35s. Deterministic scorecard remains 100% accurate. |
| `EmptyDocumentError: Extracted content is too short` | Document Parser (`parser.py`) | Document contains flattened scanned image. Upload a PDF with selectable text or DOCX format. |

---

## 2. In-Depth Diagnostic Runbooks

### Runbook 1: Streamlit Widget Already Instantiated Error
- **Symptom**: Red error screen in browser:
  ```text
  streamlit.errors.StreamlitWidgetAlreadyInstantiatedError:
  st.session_state.sidebar_nav_radio cannot be modified after the widget with key sidebar_nav_radio is instantiated.
  ```
- **Root Cause**: A button callback attempted to mutate `st.session_state.sidebar_nav_radio` after the widget was already constructed in that script run.
- **Resolution**:
  1. Inspect the button callback in `app.py`.
  2. Replace direct assignment with:
     ```python
     st.session_state.pending_nav = "📋 Candidate Tracker"
     st.session_state.tracker_reset_filters = True
     st.rerun()
     ```
  3. Verify that `pending_nav` is popped *before* `st.radio(key="sidebar_nav_radio")` is called.

---

### Runbook 2: In-Memory Module Attribute Error
- **Symptom**:
  ```text
  AttributeError: module 'registry' has no attribute 'get_current_ist_str'
  ```
- **Root Cause**: Streamlit's dev server hot-reloaded `app.py`, but Python's `sys.modules['registry']` remained cached from an earlier process execution that lacked the new function.
- **Resolution**:
  1. Ensure defensive reload guards are active in `app.py`:
     ```python
     if not hasattr(registry, "get_current_ist_str"):
         import importlib
         registry = importlib.reload(registry)
     ```
  2. If running locally, stop the terminal with `Ctrl + C` and re-run: `streamlit run app.py`.

---

### Runbook 3: Port 8501 Address Conflict
- **Symptom**:
  ```text
  errno 10048: Only one usage of each socket address is normally permitted
  ```
- **Resolution on Windows (PowerShell)**:
  ```powershell
  # Find PID using port 8501:
  Get-NetTCPConnection -LocalPort 8501 | Select-Object OwningProcess

  # Terminate process:
  Stop-Process -Id <OwningProcessId> -Force

  # Restart Streamlit:
  streamlit run app.py
  ```

---

### Runbook 4: Scanned Image PDF Extraction Failure
- **Symptom**:
  ```text
  EmptyDocumentError: Extracted content is too short or empty (0 chars). Ensure the PDF contains selectable text (not flattened scanned images).
  ```
- **Root Cause**: The uploaded resume is a flattened scanned image (raster bitmap) without an embedded text layer.
- **Resolution**:
  1. Re-export the resume from Word or Google Docs using **"Save As PDF"** (which generates selectable font glyphs).
  2. Alternatively, upload the document in `.docx` format directly.
