# 🔒 Security & Privacy Policy — Recruitment Intelligence Platform

## 1. Overview & Security Posture

The **Recruitment Intelligence Platform** processes Personally Identifiable Information (PII) including candidate names, contact phone numbers, email addresses, career histories, and technical evaluations.

Maintaining enterprise data privacy, secure local file storage, and API credential protection is paramount. This document defines our security controls, threat mitigations, and operational policies.

---

## 2. Secrets Management & API Key Governance

### A. Environment Configuration (`.env`)
- API credentials (for Google Gemini, OpenRouter, NVIDIA NIM, Groq, etc.) must reside exclusively in a local `.env` file.
- The `.env` file is explicitly ignored in `.gitignore` and must **never** be staged or committed to source control.
- A sanitized `.env.example` template is provided in the repository with placeholder values only.

### B. UI Input Protection
- When recruiters input API keys directly through the Streamlit sidebar, the input widgets use `type="password"`.
- API keys are held in volatile session memory during execution and are **never** persisted to the SQLite database or written to disk.
- Keys are omitted from all exported candidate dossiers and application diagnostics.

### C. Credential Rotation Policy
- API keys should be rotated every 90 days or immediately if exposure is suspected.
- If a secret is inadvertently committed to Git history, it must be considered compromised. Simply deleting the file or adding it to `.gitignore` does not remove it from Git commit history. Revoke the key immediately at the provider's console and generate a replacement.

---

## 3. Candidate Data Privacy & File Storage Security

### A. Local Storage Boundaries (`data/` Directory)
- All uploaded Job Descriptions and Candidate Resumes are stored under:
  ```text
  data/
  ├── job_descriptions/
  └── resumes/
  ```
- **Git Exclusion**: The `.gitignore` file enforces that all files matching `data/*.pdf`, `data/*.docx`, `data/*.doc`, `data/*.txt`, `data/job_descriptions/*`, and `data/resumes/*` are excluded from version control. Only empty `.gitkeep` files are tracked.
- **Deduplication**: Files are indexed by SHA-256 hashes to prevent redundant storage and collision risks while preserving original file bytes.

### B. Path Traversal Defenses
- The file storage subsystem (`storage.py`) validates every target file path before saving or reading.
- It computes the canonical path via `os.path.abspath` and verifies that:
  ```python
  os.path.commonpath([base_directory, canonical_target_path]) == base_directory
  ```
- Any attempt to escape the configured data directory (e.g., using `../../` or Windows absolute drive paths) is rejected with an explicit security exception.

### C. File Upload Validation
- Only verified file extensions (`.pdf`, `.docx`, `.doc`, `.txt`) are permitted.
- The maximum file size is restricted to 15 MB per upload by default.
- Files are parsed purely for plain text; no macros, executable code, or embedded scripts are executed.

---

## 4. Database Security & Query Hygiene

### A. Parameterized SQL Queries
- Every database interaction in `registry.py` is implemented using parameterized queries (e.g. `cursor.execute("SELECT * FROM candidates WHERE candidate_id = ?", (cid,))`).
- **Zero Raw String Interpolation**: String concatenation or f-strings are strictly forbidden in SQL queries, completely eliminating SQL Injection (SQLi) vulnerabilities.

### B. Audit Trail & Immutability
- Candidate status changes write immutable log records to `candidate_status_history` recording the previous status, new status, timestamp, recruiter notes, and changing actor.

---

## 5. Logging & Diagnostics Hygiene

- Application logs stored under `data/logs/` are strictly sanitized.
- API keys, authorization bearer tokens, and unmasked candidate mobile numbers are excluded from general system log streams.
- Error handlers sanitize stack traces before rendering them in the recruiter-facing user interface to prevent information disclosure.

---

## 6. Pre-Commit & GitHub Publication Checklist

Before staging or pushing changes to GitHub, developers and operators must verify:

- [ ] `git status` does not show `.env`, `fitment.db`, or untracked candidate CV files.
- [ ] No API keys exist in committed code or configuration files.
- [ ] `.gitignore` contains active patterns for `.env`, `*.db`, and `data/*`.
- [ ] Automated tests pass with synthetic, non-PII test fixtures (`python -m unittest discover tests`).

---

## 7. Vulnerability Reporting

If you discover a security vulnerability or credential leak within this repository, please do not open a public GitHub issue.

Please report the issue responsibly to the project maintainers:
- **Repository**: [https://github.com/tarun1-github/Resume-Screening](https://github.com/tarun1-github/Resume-Screening)
- **Maintainer**: Project Engineering Team
