"""
⚡ FITMENT.AI | Executive CV Screener & Multi-Agent Fitment Engine
An executive Streamlit frontend with 3D Glassmorphism styling, animated multi-agent chaining,
and persistent session-state screening analytics.
"""

from __future__ import annotations

import os
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

from parser import (
    DocumentProcessingError,
    extract_text_from_pdf,
    get_document_statistics,
    sanitize_job_description,
)
from agent_engine import (
    AgentEngineError,
    FitmentReport,
    MultiAgentEngine,
    ScoringWeights,
)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FITMENT.AI | Executive CV Screener",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 3D GLASSMORPHISM & EXECUTIVE STYLING ---
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    /* Global Typography & Deep Luxury Canvas */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(30, 27, 75, 0.95) 0%, rgba(15, 23, 42, 1) 90.2%);
        color: #f1f5f9;
    }

    /* Executive Gradient Header */
    .brand-title {
        background: linear-gradient(135deg, #60a5fa 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.7rem;
        letter-spacing: -0.03em;
        margin-bottom: 0.1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .brand-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 1.8rem;
        letter-spacing: -0.01em;
    }

    /* 3D Glassmorphism Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 22px 24px;
        border-radius: 18px;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(16px);
        margin-bottom: 1.2rem;
    }

    /* Stat & Metric Chips */
    .stat-chip {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 20px;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.35);
        color: #c7d2fe;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }

    /* 3D Neumorphic Button Styling */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #9333ea 100%);
        color: #ffffff;
        font-weight: 700;
        font-size: 1.05rem;
        padding: 0.8rem 1.8rem;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 10px 25px -5px rgba(124, 58, 237, 0.5), inset 0 2px 0 rgba(255, 255, 255, 0.25);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 16px 32px -6px rgba(147, 51, 234, 0.7), inset 0 2px 0 rgba(255, 255, 255, 0.4);
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        color: #ffffff;
    }

    div.stButton > button:active {
        transform: translateY(1px);
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
    }

    /* Metric Container Overrides */
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.25);
        padding: 16px 20px;
        border-radius: 16px;
        box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.4);
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Tab Custom Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 23, 42, 0.5);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        padding: 8px 16px;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.25) !important;
        color: #ffffff !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
    }

    /* Agent Pulse Animation */
    .agent-pulse {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse 1.8s infinite;
        margin-right: 6px;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- INITIALIZE SESSION STATE ---
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "resume_pages" not in st.session_state:
    st.session_state.resume_pages = 0
if "resume_filename" not in st.session_state:
    st.session_state.resume_filename = ""
if "fitment_report" not in st.session_state:
    st.session_state.fitment_report = None
if "agent_progress_status" not in st.session_state:
    st.session_state.agent_progress_status = ""


# --- SAMPLE DATA HELPER ---
SAMPLE_JD = """Role: Lead Full-Stack AI Engineer
Company: Apex Systems (AI & Cloud Platforms)
Location: Remote / Hybrid

Key Responsibilities:
- Architect and develop high-throughput, agentic AI workflows and LLM orchestration systems.
- Build modern, interactive micro-frontends (Streamlit, React, or Next.js) with real-time streaming.
- Integrate vector databases (Pinecone, ChromaDB, Weaviate) and implement production RAG pipelines.
- Deploy robust backend microservices using FastAPI, Python 3.11+, and Docker.
- Implement CI/CD pipelines, automated testing, and observability (LangSmith, OpenTelemetry).

Required Qualifications:
- 5+ years of full-stack software development experience.
- Strong proficiency with Python, modern async programming, and API architecture.
- Demonstrated hands-on experience building multi-agent systems with LangGraph or AutoGen.
- Experience with OpenAI, Anthropic, or Groq LLM inference pipelines.
- Bachelor's or Master's degree in Computer Science, Software Engineering, or equivalent STEM field.
"""


def load_sample_jd():
    st.session_state.jd_text = SAMPLE_JD


# --- SIDEBAR: ENGINE SETTINGS ---
with st.sidebar:
    st.markdown("### ⚡ Engine Control Room")

    provider = st.selectbox(
        "LLM Provider",
        options=["OpenAI", "Groq"],
        index=0,
        help="Select OpenAI for GPT-4o or Groq for ultra-low latency Llama 3 models.",
    )

    if provider == "OpenAI":
        model_options = ["gpt-4o", "gpt-4o-mini"]
        env_key = os.getenv("OPENAI_API_KEY", "")
    else:
        model_options = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        env_key = os.getenv("GROQ_API_KEY", "")

    selected_model = st.selectbox("Inference Model", options=model_options, index=0)

    api_key_input = st.text_input(
        f"{provider} API Key",
        value=env_key,
        type="password",
        placeholder=f"Enter {provider} API key...",
        help="Keys are used strictly in-session and never stored on disk.",
    )

    st.markdown("---")
    st.markdown("### 🎛️ Scoring Weights Matrix")
    with st.expander("Configure Evaluation Weights", expanded=False):
        w_skills = st.slider("Skills Alignment", 10, 60, 30, 5, format="%d%%") / 100.0
        w_exp = st.slider("Experience Depth", 10, 60, 40, 5, format="%d%%") / 100.0
        w_edu = st.slider("Education Credentials", 5, 30, 15, 5, format="%d%%") / 100.0
        w_extras = st.slider("Extras & Certifications", 5, 30, 15, 5, format="%d%%") / 100.0

        weights = ScoringWeights(
            skills=w_skills,
            experience=w_exp,
            education=w_edu,
            extras=w_extras,
        ).normalize()

    st.markdown("---")
    st.markdown("### 🧬 Orchestrated Agents")
    st.markdown('<div><span class="agent-pulse"></span><b>Agent 1:</b> JD Mandate Analyst</div>', unsafe_allow_html=True)
    st.markdown('<div><span class="agent-pulse"></span><b>Agent 2:</b> CV Skill & Profile Matcher</div>', unsafe_allow_html=True)
    st.markdown('<div><span class="agent-pulse"></span><b>Agent 3:</b> RedFlag & Gap Auditor</div>', unsafe_allow_html=True)
    st.markdown('<div><span class="agent-pulse"></span><b>Agent 4:</b> Executive Fitment Scorer</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🧹 Reset Screening Session", use_container_width=True):
        st.session_state.jd_text = ""
        st.session_state.resume_text = ""
        st.session_state.resume_pages = 0
        st.session_state.resume_filename = ""
        st.session_state.fitment_report = None
        st.rerun()


# --- HEADER ---
st.markdown('<div class="brand-title">⚡ FITMENT.AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="brand-subtitle">Executive CV Screening & Autonomous Multi-Agent Fitment Intelligence</div>',
    unsafe_allow_html=True,
)

# --- INPUT CONTAINERS ---
col_jd, col_resume = st.columns(2, gap="large")

with col_jd:
    st.markdown("#### 📋 1. Target Role & Job Description")
    st.button(
        "⚡ Load Executive Sample JD",
        on_click=load_sample_jd,
        help="Quickly populate a standard Senior AI Engineer Job Description.",
    )

    jd_area = st.text_area(
        "Job Description text",
        value=st.session_state.jd_text,
        height=300,
        placeholder="Paste full Job Description (role requirements, must-haves, stack)...",
        label_visibility="collapsed",
    )
    # Sync with session state
    st.session_state.jd_text = jd_area

    if st.session_state.jd_text:
        jd_stats = get_document_statistics(st.session_state.jd_text)
        st.markdown(
            f'<span class="stat-chip">Words: {jd_stats["word_count"]}</span>'
            f'<span class="stat-chip">Chars: {jd_stats["character_count"]}</span>',
            unsafe_allow_html=True,
        )

with col_resume:
    st.markdown("#### 📄 2. Candidate Resume (PDF)")
    uploaded_pdf = st.file_uploader(
        "Upload candidate CV (.pdf)",
        type=["pdf"],
        help="Upload candidate PDF resume for semantic multi-agent screening.",
    )

    if uploaded_pdf is not None:
        if uploaded_pdf.name != st.session_state.resume_filename:
            try:
                extracted_text, total_pages = extract_text_from_pdf(uploaded_pdf)
                st.session_state.resume_text = extracted_text
                st.session_state.resume_pages = total_pages
                st.session_state.resume_filename = uploaded_pdf.name
            except DocumentProcessingError as doc_err:
                st.error(f"❌ Resume Parsing Error: {doc_err}")
                st.session_state.resume_text = ""
                st.session_state.resume_pages = 0
            except Exception as unk_err:
                st.error(f"❌ Unexpected Error: {unk_err}")

    if st.session_state.resume_text:
        cv_stats = get_document_statistics(st.session_state.resume_text)
        st.success(
            f"✅ Loaded: **{st.session_state.resume_filename}** ({st.session_state.resume_pages} pages)"
        )
        st.markdown(
            f'<span class="stat-chip">Pages: {st.session_state.resume_pages}</span>'
            f'<span class="stat-chip">Words: {cv_stats["word_count"]}</span>'
            f'<span class="stat-chip">Chars: {cv_stats["character_count"]}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.info("💡 Upload a readable PDF to extract candidate experience and skill sets.")

st.markdown("<br>", unsafe_allow_html=True)

# --- RUN EVALUATION TRIGGER ---
run_btn = st.button("🚀 Run Multi-Agent Fitment & Scoring", use_container_width=True)

if run_btn:
    # 1. Validation Checks
    active_key = api_key_input.strip() or env_key.strip()
    if not active_key:
        st.error(f"⚠️ Please enter your {provider} API key in the sidebar to proceed.")
        st.stop()

    try:
        sanitized_jd = sanitize_job_description(st.session_state.jd_text)
    except DocumentProcessingError as jd_err:
        st.warning(f"⚠️ Job Description Issue: {jd_err}")
        st.stop()

    if not st.session_state.resume_text:
        st.warning("⚠️ Please upload a valid candidate resume PDF to continue.")
        st.stop()

    # 2. Live Agent Orchestration Progress
    progress_container = st.container()
    with progress_container:
        p_bar = st.progress(0)
        p_status = st.empty()

        def on_progress(step_desc: str, pct: float):
            p_bar.progress(int(pct * 100))
            p_status.markdown(
                f'<div class="glass-card" style="padding: 12px 18px; margin: 10px 0;">'
                f'<span class="agent-pulse"></span> <b>{step_desc}</b>'
                f'</div>',
                unsafe_allow_html=True,
            )

        try:
            engine = MultiAgentEngine(
                provider=provider,
                api_key=active_key,
                model=selected_model,
            )

            report: FitmentReport = engine.run_evaluation(
                jd_text=sanitized_jd,
                resume_text=st.session_state.resume_text,
                progress_callback=on_progress,
                weights=weights,
            )

            # Persist in session state
            st.session_state.fitment_report = report
            p_bar.empty()
            p_status.empty()
            st.balloons()

        except AgentEngineError as engine_err:
            p_bar.empty()
            p_status.empty()
            st.error(f"❌ Multi-Agent Execution Failed: {engine_err}")
        except Exception as unexpected:
            p_bar.empty()
            p_status.empty()
            st.error(f"❌ Unexpected Error during screening: {unexpected}")


# --- RESULTS DISPLAY (SESSION PERSISTENT) ---
if st.session_state.fitment_report is not None:
    report: FitmentReport = st.session_state.fitment_report

    st.markdown("---")
    st.markdown(
        f"### 📊 Executive Fitment Scorecard: <span style='color: #a855f7;'>{report.candidate_name}</span>",
        unsafe_allow_html=True,
    )

    # 4 Key Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="Overall Fitment Index",
            value=f"{report.overall_score} / 100",
            delta=report.verdict,
            delta_color="normal" if report.verdict == "Strong Fit" else ("off" if report.verdict == "Moderate Fit" else "inverse"),
        )
    with m2:
        st.metric(
            label="Skills Alignment",
            value=f"{report.skills_score}%",
            delta="Technical Match",
        )
    with m3:
        st.metric(
            label="Experience Match",
            value=f"{report.experience_score}%",
            delta="Seniority & Depth",
        )
    with m4:
        st.metric(
            label="Anomalies / Flags",
            value=f"{len(report.red_flags)} Detected",
            delta="Forensic Audit",
            delta_color="inverse" if len(report.red_flags) > 1 else "normal",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Deep-Dive Tabs
    tab_summary, tab_skills, tab_redflags, tab_interview, tab_export = st.tabs(
        [
            "🎯 Executive Summary",
            "🛠️ Technical & Experience Alignment",
            "🚩 Red Flags & Career Audit",
            "🎙️ Interview Focus Strategy",
            "💾 Export & Raw Agent Audit",
        ]
    )

    with tab_summary:
        st.markdown(
            f"""
            <div class="glass-card">
                <h4 style="margin-top: 0; color: #38bdf8;">Executive Decision Briefing</h4>
                <p style="font-size: 1.1rem; line-height: 1.6; color: #f1f5f9;">{report.summary}</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div><b>Verdict:</b> <span style="color: {'#10b981' if report.verdict == 'Strong Fit' else ('#f59e0b' if report.verdict == 'Moderate Fit' else '#ef4444')}; font-weight: 700;">{report.verdict}</span></div>
                    <div><b>Education Alignment:</b> {report.education_score}/100</div>
                    <div><b>Extras & Accreditations:</b> {report.extras_score}/100</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_skills:
        col_str, col_gap = st.columns(2, gap="medium")
        with col_str:
            st.markdown("#### 🌟 Candidate Strengths & Direct Matches")
            for strength in report.strengths:
                st.markdown(f"- ✅ **{strength}**")
        with col_gap:
            st.markdown("#### ⚠️ Identified Competency Gaps")
            for gap in report.critical_gaps:
                st.markdown(f"- ⚠️ {gap}")

    with tab_redflags:
        st.markdown("#### 🔍 Career Trajectory & Forensic Anomaly Audit")
        if not report.red_flags or (len(report.red_flags) == 1 and "no critical" in report.red_flags[0].lower()):
            st.success("🟢 No severe employment gaps or candidate red flags detected.")
        else:
            for flag in report.red_flags:
                st.markdown(
                    f'<div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 12px 16px; margin-bottom: 8px; border-radius: 4px;">'
                    f'🚩 {flag}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    with tab_interview:
        st.markdown("#### 🎙️ Targeted Technical & Behavioral Probing Questions")
        st.info("💡 These questions are dynamically tailored to probe the candidate's exact competency gaps and verify claimed production experience.")
        for idx, question in enumerate(report.interview_questions, 1):
            st.markdown(
                f"""
                <div class="glass-card" style="padding: 14px 18px; margin-bottom: 10px;">
                    <b style="color: #a855f7;">Question {idx}:</b><br>
                    <span style="font-size: 1.05rem; font-style: italic;">"{question}"</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_export:
        st.markdown("#### 📥 Export Candidate Scorecard")
        st.download_button(
            label="💾 Download Scorecard Report (Markdown)",
            data=report.raw_markdown,
            file_name=f"FITMENT_AI_{report.candidate_name.replace(' ', '_')}_Report.md",
            mime="text/markdown",
            use_container_width=True,
        )

        with st.expander("🔍 View Raw Agent Logs & Execution Trace"):
            st.json(report.agent_logs)
