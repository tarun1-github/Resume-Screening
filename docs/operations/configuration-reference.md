# ⚙️ Configuration Reference — FITMENT.AI

> **Audience**: Systems Administrators, DevOps Engineers, and Platform Architects.  
> **Last Reviewed**: 2026-10-19  
> **Primary Source Code**: [`.env.example`](file:///e:/Projects/resume-screening-agent/.env.example), [`.streamlit/config.toml`](file:///e:/Projects/resume-screening-agent/.streamlit/config.toml).

---

## 1. Environment Variables Reference (`.env`)

Configuration parameters are loaded automatically via `python-dotenv` at application startup:

| Environment Variable | Default Value | Format / Type | Description |
| :--- | :--- | :--- | :--- |
| **`FITMENT_DATA_DIR`** | `./data` | Filepath string | Directory root for SQLite database, stored files, and application logs. |
| **`DATABASE_URL`** | `sqlite:///./data/fitment.db`| URI string | Connection URI for the SQLite candidate registry. |
| **`LLM_PROVIDER`** | `gemini` | `gemini` \| `openrouter` \| `nvidia` \| `groq` \| `offline` | Preferred default AI provider for qualitative synthesis. |
| **`LLM_TIMEOUT_SECONDS`**| `30` | Positive integer | Timeout budget in seconds for external AI socket connections. |
| **`GEMINI_API_KEY`** | *(empty)* | String (`AIzaSy...`) | Google Gemini API key. |
| **`GOOGLE_API_KEY`** | *(empty)* | String (`AIzaSy...`) | Fallback key name for Google Gemini integration. |
| **`OPENROUTER_API_KEY`** | *(empty)* | String (`sk-or-...`)| OpenRouter AI gateway key. |
| **`NVIDIA_API_KEY`** | *(empty)* | String (`nvapi-...`)| NVIDIA NIM Build API key. |
| **`GROQ_API_KEY`** | *(empty)* | String (`gsk_...`) | Groq Cloud inference key. |

---

## 2. Streamlit Configuration ([`.streamlit/config.toml`](file:///e:/Projects/resume-screening-agent/.streamlit/config.toml))

FITMENT.AI ships with a pre-tuned configuration enforcing light theme aesthetics, upload limits, and CSRF protection:

```toml
[theme]
base = "light"
primaryColor = "#2563EB"
backgroundColor = "#F3F6FC"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#172033"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 15
```

### Parameter Explanations
- **`primaryColor = "#2563EB"`**: Enterprise blue brand accent applied to primary action buttons and active indicators.
- **`backgroundColor = "#F3F6FC"`**: High-contrast, clean grey-blue workspace canvas.
- **`secondaryBackgroundColor = "#FFFFFF"`**: Pure white card background for panels, containers, and data grids.
- **`textColor = "#172033"`**: Deep slate typography ensuring AAA accessibility contrast ratios.
- **`maxUploadSize = 15`**: Restricts individual file uploads to 15 MB to safeguard against memory exhaustion attacks.
- **`enableXsrfProtection = true`**: Enforces Cross-Site Request Forgery tokens on WebSocket stream connections.

---

## 3. Command-Line Flag Overrides

All server settings can be overridden on the command line at startup:

```powershell
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.maxUploadSize 20
```
