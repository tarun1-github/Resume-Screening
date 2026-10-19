# 🔑 Secrets Governance & Configuration Management — FITMENT.AI

> **Audience**: DevOps Engineers, Security Officers, and System Administrators.  
> **Last Reviewed**: 2026-10-19  
> **Primary Source Code**: [`.env.example`](file:///e:/Projects/resume-screening-agent/.env.example), [`llm_manager.py`](file:///e:/Projects/resume-screening-agent/llm_manager.py), [`app.py`](file:///e:/Projects/resume-screening-agent/app.py).

---

## 1. Secrets Management Philosophy

FITMENT.AI follows the Twelve-Factor App methodology for configuration:
1. **Zero Hardcoded Secrets**: No API keys, database connection strings, or authorization tokens are embedded in Python source files.
2. **Strict Git Exclusion**: Local `.env` files are explicitly ignored in `.gitignore`. The repository only tracks `.env.example` with sanitized placeholder tokens.
3. **Volatile UI State**: API keys entered via the Streamlit web sidebar reside strictly in volatile process memory and are **never persisted to the SQLite database or saved to disk**.

---

## 2. Configuration Variables Inventory

| Variable Name | Default Value | Required? | Allowed Values / Format | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `FITMENT_DATA_DIR` | `./data` | Optional | Valid directory path | Root filesystem directory for persistent database, file stores, and logs. |
| `DATABASE_URL` | `sqlite:///./data/fitment.db`| Optional | SQLite URI string | Primary relational database location. |
| `LLM_PROVIDER` | `gemini` | Optional | `gemini` \| `openrouter` \| `nvidia` \| `groq` \| `offline` | Preferred default external AI provider. |
| `LLM_TIMEOUT_SECONDS` | `30` | Optional | Positive integer (e.g. `30`) | Socket timeout budget for external AI calls. |
| `GEMINI_API_KEY` | *(empty)* | Optional | `AIzaSy...` (alphanumeric) | Google Gemini API key. |
| `GOOGLE_API_KEY` | *(empty)* | Optional | `AIzaSy...` (alphanumeric) | Alternative fallback environment variable for Gemini. |
| `OPENROUTER_API_KEY` | *(empty)* | Optional | `sk-or-v1-...` | OpenRouter gateway API key. |
| `NVIDIA_API_KEY` | *(empty)* | Optional | `nvapi-...` | NVIDIA NIM Build API key. |
| `GROQ_API_KEY` | *(empty)* | Optional | `gsk_...` | Groq Cloud API key. |

---

## 3. UI Secrets Masking & Memory Governance

When recruiters configure API keys directly within the Streamlit sidebar settings:
- **Masked Input**: The widget is configured with `type="password"`:
  ```python
  key_input = st.text_input("Enter API Key", type="password", help="Held in volatile session memory only")
  ```
- **Volatile Storage**: The credential is stored only in `st.session_state` for the lifetime of that browser session.
- **Zero Disk Persistence**: Keys are never written to `fitment.db`, never recorded in `stored_files`, and never exported in candidate markdown dossiers.
- **Sanitized Logging**: Log formatters filter out strings matching authorization bearer tokens or API key headers before writing to `data/logs/`.

---

## 4. Credential Rotation & Incident Response Protocol

If an API key is accidentally exposed or suspected of compromise:

1. **Immediate Revocation**: Do not simply delete the key from code or update `.gitignore`. Go directly to the provider console and revoke the key immediately:
   - Google AI Studio: `https://aistudio.google.com/app/apikey`
   - OpenRouter: `https://openrouter.ai/keys`
   - NVIDIA Build: `https://build.nvidia.com/`
   - Groq Console: `https://console.groq.com/keys`
2. **Generate New Key**: Create a fresh credential with appropriate billing limits.
3. **Update Host `.env`**: Replace the revoked key in your local `.env` file.
4. **Git History Inspection**: If a secret was committed to Git history, rewrite history using `git filter-repo` or revoke the repository remote before pushing.
