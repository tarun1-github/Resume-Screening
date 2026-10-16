# ⚡ FITMENT.AI | Executive CV Screener & Multi-Agent Fitment Engine

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI%20GPT--4o-412991.svg)](https://openai.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama--3.3-F05A28.svg)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**FITMENT.AI** is an advanced executive CV screener, multi-agent fitment scorer, and LLM evaluation dashboard. Built with a luxurious **3D glassmorphism interface**, it coordinates four specialized AI agents to analyze job descriptions, map technical competencies, detect career gaps/red flags, and compute weighted fitment scores with targeted interview questions.

---

## 🏛️ System Architecture

FITMENT.AI employs a sequential multi-agent orchestration pipeline to evaluate candidate resumes with zero hallucinations and deep forensic rigor:

```mermaid
graph TD
    A[📄 Candidate Resume PDF] -->|parser.py: Extract & Sanitize| B[Clean Candidate Text]
    C[📋 Job Description] -->|parser.py: Validate & Normalize| D[Sanitized JD Mandates]
    
    subgraph MultiAgentEngine ["⚡ Autonomous Multi-Agent Engine (agent_engine.py)"]
        E["🤖 Agent 1: JD Analyst<br/>• Extracts core technical requirements<br/>• Identifies seniority & must-haves"]
        F["🔍 Agent 2: CV Skill Matcher<br/>• Maps candidate competencies<br/>• Highlights direct & missing capabilities"]
        G["🚩 Agent 3: RedFlag & Anomaly Auditor<br/>• Detects employment gaps & job hopping<br/>• Flags unverified technical claims"]
        H["⚖️ Agent 4: Executive Recruiter & Scorer<br/>• Computes weighted fitment score (0-100)<br/>• Generates scorecard & interview probes"]
        
        E --> F
        F --> G
        G --> H
    end
    
    B --> E
    D --> E
    B --> F
    B --> G
    
    H --> I[📊 Executive Dashboard UI (app.py)]
    I --> J[🎯 Overall Fitment Score & Verdict]
    I --> K[🛠️ Technical Alignment Matrix]
    I --> L[🚩 Forensic Risk & Anomaly Audit]
    I --> M[🎙️ Dynamic Interview Probing Questions]
    I --> N[💾 Exportable Markdown Scorecard]
```

---

## ✨ Key Features

- **Executive 3D Glassmorphism UI**: Custom CSS design featuring dark luxury palettes, neon glowing cards, tactile 3D buttons, and responsive metric containers.
- **Synchronized Multi-Agent Chaining**:
  1. **JD Analyst Agent**: Extracts must-have proficiencies and role mandates.
  2. **Resume & Skill Matcher Agent**: Performs semantic alignment and capability mapping.
  3. **RedFlag Auditor Agent**: Identifies career timeline anomalies, short tenures, and unverified buzzwords.
  4. **Executive Recruiter Agent**: Synthesizes the weighted fitment score (0–100) and recommendation.
- **Dual LLM Provider Support**:
  - **OpenAI**: `gpt-4o` and `gpt-4o-mini`
  - **Groq**: Ultra-fast inference with `llama-3.3-70b-versatile` and `llama-3.1-8b-instant`
- **Configurable Scoring Weights**: Fine-tune weight allocations across Skills (30%), Experience (40%), Education (15%), and Accreditations (15%).
- **Interactive Session State**: Uploaded documents and screening results persist during tab switches, configuration updates, and filter interactions.
- **Robust Error Handling**: Graceful degradation and descriptive error banners for missing API keys, encrypted PDFs, empty inputs, or API limits.
- **One-Click Export**: Instant download of candidate scorecard in Markdown format.

---

## 📂 Repository Structure

```plaintext
resume-screening-agent/
├── app.py               # Executive Streamlit frontend & UI dashboard
├── parser.py            # Robust PDF text extraction & JD sanitization
├── agent_engine.py      # Multi-agent orchestration, scoring & LLM engine
├── requirements.txt     # Production dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules for virtual environments & secrets
└── README.md            # Architecture documentation & setup guide
```

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/tarun1-github/Resume-Screening.git
cd Resume-Screening
```

### 2. Set Up a Virtual Environment

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Add your API keys:

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
```

*(Note: API keys can also be entered directly in the Streamlit sidebar during runtime.)*

### 5. Launch the Application

```bash
streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## 📊 Evaluation Criteria & Scoring

FITMENT.AI uses an objective multi-parameter weighted scoring model:

| Category | Default Weight | Evaluation Focus |
| :--- | :--- | :--- |
| **Technical Skills Alignment** | `30%` | Direct stack alignment, modern frameworks, tooling proficiency |
| **Experience Depth** | `40%` | Relevant years, enterprise impact, project complexity, leadership |
| **Education & Credentials** | `15%` | Degree relevancy (CS / Data Science / STEM) and academic background |
| **Extras & Certifications** | `15%` | Industry certs (AWS, GCP, CKA), open-source contributions, awards |

### Verdict Thresholds:
- 🟢 **Strong Fit (`Score ≥ 78`)**: Candidate meets core requirements and exceeds technical benchmarks. Recommended for immediate interview.
- 🟡 **Moderate Fit (`55 ≤ Score < 78`)**: Candidate displays relevant foundational abilities with minor gaps or adjacent experience.
- 🔴 **Weak Fit (`Score < 55`)**: Significant discrepancies in critical mandates, experience depth, or excessive red flags.

---

## 🔒 Security & Privacy

- PDF processing occurs completely in-memory using `pypdf`.
- API keys provided in the sidebar are held strictly in temporary session state and are never written to disk or logged.
- The `.gitignore` prevents inadvertent commits of `.env` files or candidate resumes.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).