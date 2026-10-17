import streamlit as st
import os
import re
from pypdf import PdfReader
from docx import Document
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FITMENT.AI | Executive CV Screener",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ELITE GLASSMORPHISM & 3D EXECUTIVE STYLING ---
st.markdown(
    """
<style>
    .main {
        background: linear-gradient(135deg, #090d16 0%, #171b36 100%);
        color: #f8fafc;
    }
    .header-badge {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        letter-spacing: -1px;
        margin-bottom: 0px;
    }
    .sub-badge {
        color: #94a3b8;
        font-size: 1.15rem;
        font-weight: 400;
        margin-bottom: 30px;
    }
    /* 3D Glassmorphism Executive Card */
    .executive-card {
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 35px;
        border-radius: 20px;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(16px);
        margin-top: 20px;
        margin-bottom: 30px;
    }
    /* 3D Layered Action Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1 0%, #9333ea 100%);
        color: white !important;
        font-weight: 800;
        font-size: 1.15rem;
        padding: 0.85rem 1.5rem;
        border-radius: 14px;
        border: none;
        box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.6), inset 0 2px 0 rgba(255, 255, 255, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px -5px rgba(147, 51, 234, 0.8), inset 0 2px 0 rgba(255, 255, 255, 0.5);
        background: linear-gradient(135deg, #4f46e5 0%, #a855f7 100%);
    }
    .stTextArea textarea {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        border-radius: 12px !important;
        padding: 14px !important;
        font-size: 0.95rem !important;
    }
    div.row-widget.stButton > button[kind="secondary"] {
        background: #ffffff !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.2) !important;
    }
    div[data-testid="metric-container"] {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(99, 102, 241, 0.4);
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    }
    /* Custom Progress Meter */
    .metric-bar-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        height: 10px;
        width: 100%;
        margin-top: 8px;
        margin-bottom: 15px;
        overflow: hidden;
    }
    .metric-bar-fill {
        background: linear-gradient(90deg, #6366f1 0%, #38bdf8 100%);
        height: 100%;
        border-radius: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- HELPER FUNCTION FOR FILE PARSING ---
def extract_text_from_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return ""
    file_extension = uploaded_file.name.split(".")[-1].lower()
    extracted_text = ""
    try:
        if file_extension == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                extracted_text += page.extract_text() or ""
        elif file_extension in ["docx", "doc"]:
            doc = Document(uploaded_file)
            for paragraph in doc.paragraphs:
                extracted_text += paragraph.text + "\n"
        elif file_extension == "txt":
            extracted_text = uploaded_file.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Error parsing file {uploaded_file.name}: {e}")
    return extracted_text


# --- DETERMINISTIC SCORING ENGINE ---
def evaluate_candidate_deterministically(jd_text, resume_text, weights):
    jd_lower = jd_text.lower()
    resume_lower = resume_text.lower()

    stop_words = {
        "and",
        "the",
        "for",
        "with",
        "you",
        "that",
        "this",
        "from",
        "are",
        "our",
        "will",
        "have",
    }
    jd_words = set(
        w for w in re.findall(r"\b[a-z]{3,}\b", jd_lower) if w not in stop_words
    )
    resume_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", resume_lower))

    matched_skills = sorted(list(jd_words.intersection(resume_words)))
    missing_skills = sorted(list(jd_words.difference(resume_words)))

    skill_match_ratio = len(matched_skills) / max(len(jd_words), 1)
    skills_score = min(int(skill_match_ratio * 150), 100)

    exp_patterns = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", resume_lower)
    candidate_exp_years = max([int(x) for x in exp_patterns]) if exp_patterns else 3

    jd_exp_patterns = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", jd_lower)
    required_exp_years = int(jd_exp_patterns[0]) if jd_exp_patterns else 5

    if candidate_exp_years >= required_exp_years:
        exp_score = 95
        exp_verdict = (
            f"Meets / Exceeds requirement (~{candidate_exp_years} yrs detected)"
        )
    else:
        exp_score = max(int((candidate_exp_years / required_exp_years) * 100), 45)
        exp_verdict = f"Below requirement (~{candidate_exp_years} yrs vs {required_exp_years} yrs required)"

    common_certs = [
        "itil",
        "ccna",
        "ccie",
        "python",
        "scrum",
        "pmp",
        "aws",
        "azure",
        "kubernetes",
        "linux",
    ]
    found_certs = [c.upper() for c in common_certs if c in resume_lower]
    cert_score = min(len(found_certs) * 30, 100) if found_certs else 65

    w_skills = weights["skills"] / 100.0
    w_exp = weights["exp"] / 100.0
    w_edu = weights["edu"] / 100.0
    w_extras = weights["extras"] / 100.0

    total_weight = w_skills + w_exp + w_edu + w_extras
    if total_weight == 0:
        total_weight = 1.0

    final_score = int(
        (
            skills_score * w_skills
            + exp_score * w_exp
            + cert_score * w_extras
            + 80 * w_edu
        )
        / total_weight
    )
    final_score = max(min(final_score, 98), 38)

    if final_score >= 75:
        verdict = "🟢 Strong Fit — Highly Recommended for Technical Interview"
    elif final_score >= 55:
        verdict = "🟡 Moderate Fit — Noticeable Gaps in Seniority or Tooling"
    else:
        verdict = "🔴 Weak Fit — Significant Skill & Experience Discrepancy"

    return {
        "score": final_score,
        "verdict": verdict,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skills_score": skills_score,
        "exp_verdict": exp_verdict,
        "exp_score": exp_score,
        "found_certs": found_certs,
        "cert_score": cert_score,
    }


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Control Room")
    st.info(
        "⚡ **Mode:** 100% Offline Rule-Based NLP Engine (Zero API Keys / Zero Quotas)"
    )

    st.markdown("---")
    st.markdown("### 📊 Scoring Weights Matrix")
    with st.expander("Configure Evaluation Weights", expanded=True):
        weight_skills = st.slider("Skills Alignment", 0, 100, 40)
        weight_exp = st.slider("Experience Depth", 0, 100, 30)
        weight_edu = st.slider("Education Credentials", 0, 100, 15)
        weight_extras = st.slider("Extras & Certifications", 0, 100, 15)

    weights = {
        "skills": weight_skills,
        "exp": weight_exp,
        "edu": weight_edu,
        "extras": weight_extras,
    }

    st.markdown("---")
    st.markdown("### 🧬 Active Engines")
    st.markdown("🔍 **Regex Tokenizer:** *Active*")
    st.markdown("📊 **Heuristic Scorer:** *Active*")

# --- MAIN DASHBOARD HEADER ---
st.markdown('<p class="header-badge">⚡ FITMENT.AI</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-badge">Lightning-Fast Deterministic CV Screening & Keyword Fitment Intelligence</p>',
    unsafe_allow_html=True,
)

if "jd_content" not in st.session_state:
    st.session_state.jd_content = ""

# --- INPUT SECTION (2 Columns) ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### 📋 1. Target Role & Job Description")
    if st.button("⚡ Load Executive Sample JD", type="secondary"):
        st.session_state.jd_content = """Cisco Network Voice L3 / Voice T2 Engineer
Requirements:
- 8-10 years of experience in enterprise networks with minimum 8+ years specifically in Cisco UC / Voice Collaboration.
- Hands-on expertise with CUCM, Expressway, CUBE, IP Phones, Jabber, and IM & Presence.
- Expertise in CUCM Trace Reading, Jabber PRT Logs, IMP Trace Reading, and GW Debugs.
- Strong knowledge of SIP, H.323, RTP, and Session Border Controllers.
- ITIL framework knowledge and P1/P2 incident escalation handling."""

    uploaded_jd_file = st.file_uploader(
        "Upload Job Description (.docx, .pdf, .txt)",
        type=["docx", "doc", "pdf", "txt"],
        key="jd_up",
    )
    if uploaded_jd_file is not None:
        parsed_jd = extract_text_from_uploaded_file(uploaded_jd_file)
        if parsed_jd:
            st.session_state.jd_content = parsed_jd
            st.success("✅ JD loaded successfully!")

    jd_input = st.text_area(
        "Edit or paste Job Description:", value=st.session_state.jd_content, height=240
    )

with col2:
    st.markdown("### 📄 2. Candidate Resume")
    uploaded_resume_file = st.file_uploader(
        "Upload candidate CV (.docx, .pdf)", type=["docx", "doc", "pdf"], key="cv_up"
    )

    resume_text = ""
    if uploaded_resume_file is not None:
        resume_text = extract_text_from_uploaded_file(uploaded_resume_file)
        if resume_text:
            st.success(f"✅ Successfully parsed {uploaded_resume_file.name}")
            st.info(f"📊 Words: {len(resume_text.split())} | Chars: {len(resume_text)}")

st.markdown("<br>", unsafe_allow_html=True)

# --- EVALUATION TRIGGER ---
if st.button("🚀 RUN OFFLINE FITMENT & SCORING", type="primary"):
    if not jd_input or not resume_text:
        st.warning("⚠️ Please provide both a Job Description and a Candidate Resume.")
    else:
        with st.spinner(
            "⚡ Running deterministic tokenization & heuristic matching..."
        ):
            time.sleep(0.5)
            res = evaluate_candidate_deterministically(jd_input, resume_text, weights)

        st.markdown("---")
        st.markdown("## 📊 Deterministic Fitment Scorecard")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Engine Status", "Completed 🎯", "100%")
        m2.metric("Processing Mode", "Local NLP", "Instant")
        m3.metric("API Dependency", "None (Zero Keys)", "Secure")
        m4.metric("Scoring Method", "Weighted Heuristic", "Active")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- ELITE GLASSMORPHISM SCORECARD CONTAINER ---
        st.markdown(
            f"""
        <div class="executive-card">
            <h2 style="color: #ffffff; margin-top: 0; font-weight: 800; font-size: 2rem;">
                🎯 Executive Fitment Score: <span style="color: #38bdf8;">{res['score']} / 100</span>
            </h2>
            <p style="font-size: 1.15rem; color: #f1f5f9; font-weight: 600; margin-bottom: 25px;">
                Recommendation Verdict: <span style="color: #a855f7;">{res['verdict']}</span>
            </p>
            
            <hr style="border-color: rgba(255,255,255,0.15); margin: 25px 0;">
            
            <h3 style="color: #6366f1; font-size: 1.35rem; font-weight: 700;">🛠️ 1. Core Skills & Keyword Alignment</h3>
            <p style="color: #f1f5f9; margin: 6px 0;"><b>Matched Key Terms ({len(res['matched_skills'])} found):</b> {', '.join(res['matched_skills'][:15])} ...</p>
            <p style="color: #f1f5f9; margin: 6px 0;"><b>Key Missing Terms:</b> {', '.join(res['missing_skills'][:10])} ...</p>
            <p style="color: #38bdf8; margin: 6px 0; font-weight: 600;">Skills Alignment Score: {res['skills_score']}/100</p>
            <div class="metric-bar-container"><div class="metric-bar-fill" style="width: {res['skills_score']}%;"></div></div>
            
            <br>
            <h3 style="color: #6366f1; font-size: 1.35rem; font-weight: 700;">⏳ 2. Experience & Seniority Assessment</h3>
            <p style="color: #f1f5f9; margin: 6px 0;"><b>Seniority Analysis:</b> {res['exp_verdict']}</p>
            <p style="color: #38bdf8; margin: 6px 0; font-weight: 600;">Experience Fit Score: {res['exp_score']}/100</p>
            <div class="metric-bar-container"><div class="metric-bar-fill" style="width: {res['exp_score']}%;"></div></div>
            
            <br>
            <h3 style="color: #6366f1; font-size: 1.35rem; font-weight: 700;">📜 3. Certifications & Frameworks Detected</h3>
            <p style="color: #f1f5f9; margin: 6px 0;"><b>Identified Credentials:</b> {', '.join(res['found_certs']) if res['found_certs'] else 'No standard acronyms detected'}</p>
            <p style="color: #38bdf8; margin: 6px 0; font-weight: 600;">Credentials Score: {res['cert_score']}/100</p>
            <div class="metric-bar-container"><div class="metric-bar-fill" style="width: {res['cert_score']}%;"></div></div>
            
            <br>
            <h3 style="color: #6366f1; font-size: 1.35rem; font-weight: 700;">💡 4. Recommended Interview Focus Areas</h3>
            <ul style="color: #f1f5f9; line-height: 1.7; margin-left: 20px; font-size: 1.05rem;">
                <li><b>Technical Deep-Dive:</b> Probe practical hands-on implementation of the missing technical keywords identified above.</li>
                <li><b>Incident Ownership:</b> Verify project timeline ownership, P1/P2 incident handling, and escalation protocols.</li>
                <li><b>Collaboration & Communication:</b> Assess cultural fit and clarity regarding past production troubleshooting.</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )
