import streamlit as st
import os
import re
import time
import hashlib
from typing import Dict, Any, Optional

import parser
from deterministic_engine import (
    evaluate_candidate_deterministically,
    extract_candidate_metadata,
)

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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main {
        background: radial-gradient(circle at top right, #1e1b4b 0%, #090d16 60%, #030712 100%);
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
        margin-bottom: 25px;
    }

    /* 3D Glassmorphism Cards */
    .glass-card {
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid rgba(99, 102, 241, 0.25);
        padding: 22px 26px;
        border-radius: 18px;
        box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(16px);
        margin-bottom: 20px;
    }

    /* Executive Candidate Profile Card */
    .profile-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 20px;
        padding: 24px 28px;
        margin-bottom: 25px;
        box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(16px);
    }
    .profile-field-item {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(15, 23, 42, 0.55);
        padding: 12px 18px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .profile-field-label {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 2px;
    }
    .profile-field-value {
        color: #f8fafc;
        font-size: 1.02rem;
        font-weight: 700;
        word-break: break-word;
    }

    /* Score Hero Banner */
    .score-card-hero {
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(168, 85, 247, 0.4);
        padding: 26px 30px;
        border-radius: 20px;
        box-shadow: 0 20px 45px -10px rgba(99, 102, 241, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        margin-bottom: 25px;
    }

    /* Skill Badges */
    .skill-pill-match {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.45);
        color: #34d399;
        font-size: 0.88rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        margin: 4px;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15);
    }
    .skill-pill-gap {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.45);
        color: #f87171;
        font-size: 0.88rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        margin: 4px;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.15);
    }
    .cert-pill {
        display: inline-block;
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.45);
        color: #38bdf8;
        font-size: 0.90rem;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 12px;
        margin: 4px;
        box-shadow: 0 3px 10px rgba(56, 189, 248, 0.2);
    }

    /* 3D Action Buttons */
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
    .evidence-card {
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid #38bdf8;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 0.95rem;
        color: #e2e8f0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 23, 42, 0.5);
        padding: 8px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #94a3b8;
        font-weight: 700;
        font-size: 0.95rem;
        padding: 0 16px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(168, 85, 247, 0.25) 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(99, 102, 241, 0.5) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- SESSION STATE INITIALIZATION ---
if "jd_content" not in st.session_state:
    st.session_state.jd_content = ""
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "resume_filename" not in st.session_state:
    st.session_state.resume_filename = ""
if "screening_result" not in st.session_state:
    st.session_state.screening_result = None
if "screened_content_hash" not in st.session_state:
    st.session_state.screened_content_hash = ""


def compute_content_hash(jd: str, resume: str) -> str:
    """Computes a SHA256 digest of input pair to invalidate stale screening results."""
    return hashlib.sha256(f"{jd.strip()}|||{resume.strip()}".encode("utf-8")).hexdigest()


def extract_uploaded_content(uploaded_file) -> str:
    """Parses text from an uploaded file using the shared parser module."""
    if uploaded_file is None:
        return ""
    try:
        text, _ = parser.extract_text_from_file(
            file_source=uploaded_file,
            filename=uploaded_file.name,
            min_characters=20,
        )
        return text
    except parser.EmptyDocumentError as err:
        st.error(f"⚠️ Document Parsing Notice: {err}")
        return ""
    except parser.PDFParsingError as err:
        st.error(f"⚠️ PDF Processing Error: {err}")
        return ""
    except parser.DocumentProcessingError as err:
        st.error(f"⚠️ Document Error: {err}")
        return ""
    except Exception as err:
        st.error(f"⚠️ Unexpected error parsing {uploaded_file.name}: {err}")
        return ""


def sanitize_download_filename(candidate_name: str) -> str:
    """Creates a filesystem-safe filename for Markdown report export."""
    clean = re.sub(r'[^A-Za-z0-9_-]', '_', candidate_name).strip('_')
    return clean if clean else "Candidate"


def generate_markdown_dossier(res: Dict[str, Any]) -> str:
    """Builds a complete, factual Markdown scorecard using canonical result fields."""
    meta = res.get("metadata", {})
    cand_name = res.get("candidate_name") or meta.get("name") or "Candidate"

    matched_skills = res.get("skills_matched", [])
    missing_skills = res.get("missing_skills", [])
    certs = res.get("certifications_detected", [])
    evidence = res.get("supporting_evidence", {})
    questions = res.get("interview_questions", [])

    matched_str = ", ".join(matched_skills) if matched_skills else "None identified"
    missing_str = ", ".join(missing_skills) if missing_skills else "None identified"
    certs_str = ", ".join(certs) if certs else "None explicitly detected"

    evidence_blocks = []
    if evidence:
        for term, snippets in evidence.items():
            evidence_blocks.append(f"#### {term.upper()}\n" + "\n".join([f'- "{s}"' for s in snippets]))
        evidence_text = "\n\n".join(evidence_blocks)
    else:
        evidence_text = "No direct sentence citations captured."

    questions_text = "\n".join([f"{idx+1}. {q}" for idx, q in enumerate(questions)]) if questions else "Standard interview protocol."

    return f"""# FITMENT.AI | Candidate Evaluation Scorecard

## Candidate Executive Profile
- **Candidate Name:** {cand_name}
- **Email ID:** {meta.get('email', 'Not Specified')}
- **Current Location:** {meta.get('location', 'Not Specified')}
- **Date of Birth (DOB):** {meta.get('dob', 'Not Specified')}
- **Total Experience:** {meta.get('total_exp', 'Not Specified')}
- **Relevant Experience:** {meta.get('relevant_exp', 'Not Specified')}
- **Current / Last Organization:** {meta.get('organization', 'Not Specified')}

## Executive Evaluation Summary
- **Overall Fitment Score:** {res.get('match_score', 0)} / 100
- **Scoring Method:** {res.get('score_type', 'Rule-Based Heuristic Match')}
- **Verdict:** {res.get('verdict', 'N/A')}
- **Recommendation:** {res.get('recommendation', 'N/A')}
- **Seniority Assessment:** {res.get('experience_assessment', 'N/A')}
- **Human Review Required:** {'Yes' if res.get('human_review_required', True) else 'No'}

## Core Technical Skills Alignment
### Matched Technical Skills ({len(matched_skills)}):
{matched_str}

### Missing / Gap Requirements ({len(missing_skills)}):
{missing_str}

### Explicit Certifications & Accreditations:
{certs_str}

## Supporting Evidence (Direct Resume Citations)
{evidence_text}

## Recommended Interview Strategy & Focus Areas
{questions_text}

---
*Report Generated via FITMENT.AI Deterministic Screening Engine. This heuristic match indicator is intended for recruiter triage assistance and must not be used as an autonomous hiring decision.*
"""


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Control Room")
    st.info("⚡ **Mode:** 100% Offline Rule-Based NLP Engine (Zero API Keys / Zero Quotas)")

    st.markdown("---")
    st.markdown("### 📊 Scoring Weights Matrix")
    with st.expander("Configure Evaluation Weights", expanded=True):
        weight_skills = st.slider("Skills Alignment", 0, 100, 40)
        weight_exp = st.slider("Experience Depth", 0, 100, 30)
        weight_edu = st.slider("Education Credentials", 0, 100, 15)
        weight_extras = st.slider("Extras & Certifications", 0, 100, 15)

    weights = {
        "skills": float(weight_skills),
        "exp": float(weight_exp),
        "edu": float(weight_edu),
        "extras": float(weight_extras),
    }

    st.markdown("---")
    st.markdown("### 🧬 Active Subsystems")
    st.markdown("🔍 **Shared Parser (`parser.py`):** *Active*")
    st.markdown("📊 **Deterministic Engine (`deterministic_engine.py`):** *Active*")
    st.markdown("🛡️ **LLM API Dependencies:** *None (Zero Keys)*")

    if st.session_state.screening_result is not None:
        if st.button("🔄 Reset Scorecard", type="secondary"):
            st.session_state.screening_result = None
            st.session_state.screened_content_hash = ""
            st.rerun()


# --- MAIN DASHBOARD HEADER ---
st.markdown('<p class="header-badge">⚡ FITMENT.AI</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-badge">Lightning-Fast Deterministic CV Screening & Keyword Fitment Intelligence</p>',
    unsafe_allow_html=True,
)


# --- INPUT SECTION (2 Columns) ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### 📋 1. Target Role & Job Description")
    if st.button("⚡ Load Executive Sample JD", type="secondary"):
        st.session_state.jd_content = (
            "Cisco Network Voice L3 / Voice T2 Engineer\n"
            "Requirements:\n"
            "- 8-10 years of experience in enterprise networks with minimum 8+ years specifically in Cisco UC, CUCM, Expressway, CUBE, SIP, RTP, and Python automation.\n"
            "- Hands-on expertise with CUCM, Expressway, CUBE, IP Phones, Jabber, and IM & Presence.\n"
            "- Expertise in CUCM Trace Reading, Jabber PRT Logs, IMP Trace Reading, and GW Debugs.\n"
            "- Strong knowledge of ITIL incident escalation handling."
        )
        st.rerun()

    uploaded_jd_file = st.file_uploader(
        "Upload Job Description (.docx, .pdf, .txt)",
        type=["docx", "doc", "pdf", "txt"],
        key="jd_up",
    )
    if uploaded_jd_file is not None:
        parsed_jd = extract_uploaded_content(uploaded_jd_file)
        if parsed_jd and parsed_jd != st.session_state.jd_content:
            st.session_state.jd_content = parsed_jd
            st.success("✅ JD loaded and parsed successfully!")
            st.rerun()

    jd_input = st.text_area(
        "Edit or paste Job Description:",
        height=240,
        key="jd_content",
    )

with col2:
    st.markdown("### 📄 2. Candidate Resume")
    uploaded_resume_file = st.file_uploader(
        "Upload candidate CV (.docx, .pdf, .txt)",
        type=["docx", "doc", "pdf", "txt"],
        key="cv_up",
    )

    if uploaded_resume_file is not None:
        # Check if new file uploaded
        if uploaded_resume_file.name != st.session_state.resume_filename:
            parsed_cv = extract_uploaded_content(uploaded_resume_file)
            if parsed_cv:
                st.session_state.resume_text = parsed_cv
                st.session_state.resume_filename = uploaded_resume_file.name
                # Invalidate previous screening result to avoid displaying stale scorecard for new candidate
                st.session_state.screening_result = None
                st.session_state.screened_content_hash = ""

    resume_text = st.session_state.resume_text

    if resume_text:
        preview_meta = extract_candidate_metadata(resume_text)
        st.success(f"✅ Loaded: {st.session_state.resume_filename or 'Resume Text'}")
        st.info(
            f"👤 **{preview_meta['name']}** | 📍 {preview_meta['location']} | "
            f"⏱️ {preview_meta['total_exp']} | 📊 Words: {len(resume_text.split())}"
        )
    else:
        st.info("Upload a candidate CV (.docx or .pdf) to preview candidate profile.")

st.markdown("<br>", unsafe_allow_html=True)


# --- EVALUATION TRIGGER ---
if st.button("🚀 RUN OFFLINE FITMENT & SCORING", type="primary"):
    if not jd_input or not jd_input.strip():
        st.warning("⚠️ Please provide a Job Description before screening.")
    elif not resume_text or not resume_text.strip():
        st.warning("⚠️ Please upload or provide a Candidate Resume before screening.")
    else:
        with st.spinner("⚡ Running deterministic tokenization & evidence mapping..."):
            time.sleep(0.3)
            try:
                res = evaluate_candidate_deterministically(
                    jd_text=jd_input,
                    resume_text=resume_text,
                    weights=weights,
                )
                st.session_state.screening_result = res
                st.session_state.screened_content_hash = compute_content_hash(jd_input, resume_text)
                st.toast("Fitment screening completed!", icon="🎯")
            except parser.EmptyDocumentError as err:
                st.error(f"⚠️ Screening Error: {err}")
            except Exception as exc:
                st.error(f"⚠️ Unexpected error during evaluation: {type(exc).__name__}")


# --- PERSISTENT SCORECARD DISPLAY (Survives Widget Reruns) ---
if st.session_state.screening_result is not None:
    res = st.session_state.screening_result
    meta = res.get("metadata", {})
    cand_name = res.get("candidate_name") or meta.get("name") or "Candidate"

    # Stale content notification check
    current_hash = compute_content_hash(jd_input, resume_text)
    if st.session_state.screened_content_hash and current_hash != st.session_state.screened_content_hash:
        st.warning("⚠️ Inputs have been modified since this evaluation. Click 'Run Offline Fitment & Scoring' to evaluate the updated text.")

    st.markdown("---")

    # --- EXECUTIVE CANDIDATE PROFILE SUMMARY CARD ---
    profile_html = f"""<div class="profile-card">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="font-size: 1.8rem;">👤</span>
<div>
<h3 style="margin: 0; color: #ffffff; font-size: 1.35rem; font-weight: 800;">Candidate Executive Profile</h3>
<p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">Factual Extraction via Heuristic NLP (Zero Cloud Dependency)</p>
</div>
</div>
<span style="background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.5); color: #818cf8; font-size: 0.80rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; text-transform: uppercase;">
Rule-Based
</span>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">
<div class="profile-field-item">
<span style="font-size: 1.3rem;">👤</span>
<div>
<div class="profile-field-label">Candidate Name</div>
<div class="profile-field-value" style="color: #38bdf8;">{meta.get('name', cand_name)}</div>
</div>
</div>
<div class="profile-field-item">
<span style="font-size: 1.3rem;">📧</span>
<div>
<div class="profile-field-label">Email ID</div>
<div class="profile-field-value">{meta.get('email', 'Not Specified')}</div>
</div>
</div>
<div class="profile-field-item">
<span style="font-size: 1.3rem;">📍</span>
<div>
<div class="profile-field-label">Current Location</div>
<div class="profile-field-value">{meta.get('location', 'Not Specified')}</div>
</div>
</div>
<div class="profile-field-item">
<span style="font-size: 1.3rem;">🎂</span>
<div>
<div class="profile-field-label">Date of Birth (DOB)</div>
<div class="profile-field-value">{meta.get('dob', 'Not Specified')}</div>
</div>
</div>
<div class="profile-field-item">
<span style="font-size: 1.3rem;">⏱️</span>
<div>
<div class="profile-field-label">Total Experience</div>
<div class="profile-field-value" style="color: #34d399;">{meta.get('total_exp', res.get('total_experience_detected', 'Not Specified'))}</div>
</div>
</div>
<div class="profile-field-item">
<span style="font-size: 1.3rem;">🎯</span>
<div>
<div class="profile-field-label">Relevant Experience</div>
<div class="profile-field-value" style="color: #a855f7;">{meta.get('relevant_exp', 'Not Specified')}</div>
</div>
</div>
<div class="profile-field-item" style="grid-column: 1 / -1;">
<span style="font-size: 1.3rem;">🏢</span>
<div>
<div class="profile-field-label">Current / Last Organization</div>
<div class="profile-field-value" style="color: #facc15;">{meta.get('organization', 'Not Detected')}</div>
</div>
</div>
</div>
</div>"""
    st.markdown(profile_html, unsafe_allow_html=True)

    # --- TOP KPI METRICS ---
    score_val = res.get("match_score", 0)
    badge_color = "#10b981" if score_val >= 75 else ("#f59e0b" if score_val >= 50 else "#ef4444")
    verdict_icon = "🟢" if score_val >= 75 else ("🟡" if score_val >= 50 else "🔴")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall Fitment", f"{score_val}%", delta="Composite Fit")
    m2.metric("Technical Match", f"{len(res.get('skills_matched', []))} Skills", delta="Keywords Matched")
    m3.metric("Seniority Match", res.get("total_experience_detected", "N/A"), delta="Trajectory")
    m4.metric("Certifications", f"{len(res.get('certifications_detected', []))} Verified", delta="Credentials")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GLOWING HERO SPOTLIGHT ---
    hero_html = f"""<div class="score-card-hero">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
<div style="flex: 1; min-width: 280px;">
<span style="display: inline-block; background: {badge_color}22; border: 1px solid {badge_color}; color: {badge_color}; font-size: 0.85rem; font-weight: 800; padding: 5px 14px; border-radius: 20px; text-transform: uppercase; margin-bottom: 10px;">
{verdict_icon} {res.get('recommendation', 'Human Review Required')}
</span>
<h2 style="color: #ffffff; margin: 0 0 10px 0; font-size: 1.9rem; font-weight: 800;">{res.get('verdict', 'Fitment Verdict')}</h2>
<p style="color: #94a3b8; font-size: 1.0rem; margin: 0;">{res.get('score_type', 'Rule-Based Heuristic Evaluation')}</p>
</div>
<div style="text-align: right; background: rgba(0,0,0,0.35); padding: 18px 26px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.08);">
<span style="color: #94a3b8; font-size: 0.80rem; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 2px;">Fitment Index</span>
<span style="font-size: 3.0rem; font-weight: 900; color: #38bdf8; line-height: 1;">{score_val}<span style="font-size: 1.5rem; color: #64748b;">/100</span></span>
</div>
</div>
</div>"""
    st.markdown(hero_html, unsafe_allow_html=True)

    # --- TABBED DEEP-DIVE ARCHITECTURE ---
    tab_summary, tab_skills, tab_evidence, tab_interview, tab_export = st.tabs([
        "🎯 Executive Summary",
        "🛠️ Skills & Gaps",
        "📑 Supporting Evidence",
        "🎙️ Interview Strategy",
        "💾 Export Scorecard",
    ])

    with tab_summary:
        st.markdown("### 📋 Executive Assessment Briefing")
        st.markdown(
            f"""
            - **Candidate Match Score:** **{score_val} / 100**
            - **Seniority Analysis:** {res.get('experience_assessment', 'N/A')}.
            - **Verified Certifications Detected:** {len(res.get('certifications_detected', []))} credential(s).
            - **Triage Recommendation:** **{res.get('recommendation', 'Human review recommended')}**.
            - **Human Review Mandatory:** `{res.get('human_review_required', True)}` — *Rule-based heuristic evaluation intended for recruiter prioritization.*
            """
        )

    with tab_skills:
        col_m, col_g = st.columns(2, gap="large")
        with col_m:
            matched_list = res.get("skills_matched", [])
            st.markdown(f"#### ✅ Matched Technical Skills ({len(matched_list)})")
            if matched_list:
                pills = "".join([f'<span class="skill-pill-match">✓ {s}</span>' for s in matched_list])
                st.markdown(f'<div style="line-height: 2.2;">{pills}</div>', unsafe_allow_html=True)
            else:
                st.info("No direct technical skill matches identified.")

        with col_g:
            missing_list = res.get("missing_skills", [])
            st.markdown(f"#### ⚠️ Missing / Unverified Skills ({len(missing_list)})")
            if missing_list:
                pills = "".join([f'<span class="skill-pill-gap">✗ {s}</span>' for s in missing_list[:25]])
                st.markdown(f'<div style="line-height: 2.2;">{pills}</div>', unsafe_allow_html=True)
            else:
                st.success("No critical skill gaps found!")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📜 Explicit Industry Certifications")
        certs_list = res.get("certifications_detected", [])
        if certs_list:
            c_html = "".join([f'<span class="cert-pill">🏆 {c}</span>' for c in certs_list])
            st.markdown(f'<div style="margin: 8px 0;">{c_html}</div>', unsafe_allow_html=True)
        else:
            st.info("No explicitly claimed vendor certifications detected in resume.")

    with tab_evidence:
        st.markdown("### 📑 Factual Evidence Citations")
        st.caption("Verifiable sentence citations directly extracted from candidate resume text.")
        evidence_dict = res.get("supporting_evidence", {})
        if evidence_dict:
            for skill, snippets in evidence_dict.items():
                st.markdown(f"**Skill: `{skill.upper()}`**")
                for s in snippets:
                    st.markdown(f'<div class="evidence-card">"{s}"</div>', unsafe_allow_html=True)
        else:
            st.info("No contextual sentence citations available for matched skills.")

    with tab_interview:
        st.markdown("### 🎙️ Targeted Technical Interview Probes")
        st.caption("Custom-generated interview questions addressing candidate-specific skill gaps:")
        questions = res.get("interview_questions", [])
        for idx, q in enumerate(questions):
            st.markdown(
                f"""<div class="glass-card" style="margin-bottom: 12px; border-left: 4px solid #6366f1;">
                <p style="margin: 0; font-size: 1.02rem; color: #f1f5f9;"><b>Question {idx+1}:</b> {q}</p>
                </div>""",
                unsafe_allow_html=True,
            )

    with tab_export:
        st.markdown("### 📥 Export Candidate Fitment Dossier")
        st.caption("Download the complete evaluation dossier as a formatted Markdown scorecard.")
        report_markdown = generate_markdown_dossier(res)
        file_slug = sanitize_download_filename(cand_name)

        st.download_button(
            label=f"💾 Download {cand_name} Scorecard (.md)",
            data=report_markdown,
            file_name=f"FITMENT_AI_{file_slug}_Scorecard.md",
            mime="text/markdown",
            type="primary",
        )
