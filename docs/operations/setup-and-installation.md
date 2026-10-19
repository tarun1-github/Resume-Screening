# 🛠️ Setup & Installation Guide — FITMENT.AI

> **Audience**: Systems Administrators, DevOps Engineers, and Developers.  
> **Last Reviewed**: 2026-10-19  

---

## 1. System Requirements

### Minimum Hardware Specifications
- **Operating System**: Windows 10/11 (64-bit), Ubuntu 20.04/22.04 LTS, or macOS 12+ (Apple Silicon or Intel).
- **Python**: Version 3.10, 3.11, or 3.12 (64-bit).
- **Memory (RAM)**: 4 GB minimum (8 GB recommended for concurrent multi-page PDF/DOCX parsing).
- **Disk Space**: 2 GB free space (accommodates Python virtual environment, SQLite registry, and stored resumes).

---

## 2. Step-by-Step Installation Procedure

### Step 1: Clone the Repository
```powershell
git clone https://github.com/tarun1-github/Resume-Screening.git
cd Resume-Screening
```

### Step 2: Create Isolated Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv .venv

# Linux / macOS
python3 -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```
*(If you encounter execution policy restrictions on Windows PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

### Step 4: Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure Environment
Copy the sanitized environment configuration template:
```powershell
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```
*(Note: An active API key is optional. The platform operates 100% reliably in Offline Mode without any external keys.)*

---

## 3. Launching and Verifying the Platform

### Launch the Streamlit Portal
```powershell
streamlit run app.py
```
- Open your browser at: `http://localhost:8501`.
- Verify that the Welcome Banner loads displaying the live IST clock pill (`DD Mon YYYY, HH:MM:SS IST`).
- Verify that the sidebar displays `⚡ InstantFit Offline Screening Active` (or `✨ AI Service: Connected` if keys are configured).

### Run the Verification Test Suite
```powershell
python -m unittest discover tests
```
- Expected output: `Ran 155 tests in ~28s ... OK`.
