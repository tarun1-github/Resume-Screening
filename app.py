"""
Recruitment Intelligence Platform
Candidate Fitment Screening Portal | AI-Assisted Recruitment Intelligence
High-contrast enterprise light theme, compact space-efficient desktop layout,
persistent file storage in data/, full-registry Fitment Assistant, and deterministic candidate screening.
"""

from __future__ import annotations

import os
import sys
import time
import json
import uuid
import re
import html
import urllib.parse
from datetime import datetime, date, timedelta
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

import parser
import deterministic_engine
import registry
import chatbot
import llm_manager
import storage

load_dotenv()

# Initialize SQLite database
registry.init_db()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Recruitment Intelligence Platform — Candidate Fitment Screening Portal",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- MODERN ENTERPRISE LIGHT THEME WITH SPACE-EFFICIENT LAYOUT ---
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

    :root {
        --bg-main: #F3F6FC;
        --panel-white: #FFFFFF;
        --sidebar-bg: #EAF0FA;
        --card-border: #D7E1F0;
        --primary-blue: #2563EB;
        --cyan-accent: #0891B2;
        --violet-accent: #7C3AED;
        --success: #15803D;
        --warning: #B45309;
        --error: #B91C1C;
        --text-primary: #172033;
        --text-secondary: #475569;
        --text-muted: #64748B;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    }

    .stApp {
        background-color: #F3F6FC !important;
        color: #172033 !important;
    }

    /* ELIMINATE WASTED TOP SPACE WITHOUT CLIPPING HEADER UNDER DEPLOY BAR */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 2.5rem !important;
        z-index: 99 !important;
    }
    .block-container {
        padding-top: 2.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    /* TYPOGRAPHY SCALES */
    h1 {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #172033 !important;
    }
    h2 {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #172033 !important;
    }
    h3 {
        font-size: 19px !important;
        font-weight: 800 !important;
        color: #172033 !important;
    }
    p, span, label, div {
        font-size: 15px;
    }
    .stMarkdown p {
        font-size: 15.5px !important;
        line-height: 1.6 !important;
        color: #172033 !important;
    }

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #EAF0FA !important;
        border-right: 1px solid #D7E1F0 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #172033 !important;
    }

    /* BRAND HEADINGS */
    .brand-title {
        background: linear-gradient(135deg, #0891B2 0%, #2563EB 50%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 30px !important;
        letter-spacing: -0.8px;
        margin: 0;
        padding: 0;
        line-height: 1.2;
    }

    .brand-subtitle {
        color: #475569 !important;
        font-size: 14.5px !important;
        font-weight: 600;
        margin-top: 3px;
        margin-bottom: 8px;
    }

    /* HIGH-CONTRAST NAVIGATION TABS */
    button[data-baseweb="tab"] {
        color: #475569 !important;
        font-size: 15.5px !important;
        font-weight: 700 !important;
        background: transparent !important;
        padding: 10px 18px !important;
        border-radius: 8px 8px 0 0 !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #2563EB !important;
        background: #EAF0FA !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2563EB !important;
        font-weight: 800 !important;
        border-bottom: 3px solid #2563EB !important;
        background: #EFF6FF !important;
    }
    div[data-baseweb="tab-list"] {
        border-bottom: 2px solid #D7E1F0 !important;
        gap: 8px !important;
        margin-bottom: 16px !important;
    }

    /* STATUS BADGES */
    .provider-status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #0891B2;
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 700;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.08);
    }

    .provider-offline-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #FEF3C7;
        border: 1px solid #FCD34D;
        color: #B45309;
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 700;
    }

    /* UPLOAD PANEL CARDS (COMPACT CONTENT-DRIVEN WHITE PANELS) */
    .upload-panel-card {
        background: #FFFFFF !important;
        border: 1px solid #D7E1F0 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        box-shadow: 0 3px 12px -2px rgba(15, 23, 42, 0.05) !important;
        margin-bottom: 6px !important;
    }

    .upload-panel-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 2px;
    }

    .upload-panel-title {
        color: #172033 !important;
        font-size: 18.5px !important;
        font-weight: 800 !important;
        letter-spacing: -0.3px;
        margin: 0;
    }

    .upload-panel-desc {
        color: #475569 !important;
        font-size: 14.5px !important;
        font-weight: 500;
        margin: 0 0 6px 0;
    }

    /* STATUS BADGES */
    .status-badge-blue {
        display: inline-flex;
        align-items: center;
        background: #EFF6FF !important;
        border: 1px solid #BFDBFE !important;
        color: #1D4ED8 !important;
        padding: 3px 12px !important;
        border-radius: 9999px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }
    .status-badge-green {
        display: inline-flex;
        align-items: center;
        background: #DCFCE7 !important;
        border: 1px solid #86EFAC !important;
        color: #15803D !important;
        padding: 3px 12px !important;
        border-radius: 9999px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }
    .status-badge-violet {
        display: inline-flex;
        align-items: center;
        background: #F3E8FF !important;
        border: 1px solid #D8B4FE !important;
        color: #7C3AED !important;
        padding: 3px 12px !important;
        border-radius: 9999px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }
    .status-badge-amber {
        display: inline-flex;
        align-items: center;
        background: #FEF3C7 !important;
        border: 1px solid #FCD34D !important;
        color: #B45309 !important;
        padding: 3px 12px !important;
        border-radius: 9999px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }
    .status-badge-red {
        display: inline-flex;
        align-items: center;
        background: #FEE2E2 !important;
        border: 1px solid #FCA5A5 !important;
        color: #B91C1C !important;
        padding: 3px 12px !important;
        border-radius: 9999px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }

    /* COMPACT CANDIDATE SUMMARY GRID */
    .candidate-summary-grid {
        background: #FFFFFF !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-top: 8px !important;
        margin-bottom: 8px !important;
        display: grid !important;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)) !important;
        gap: 10px !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.06) !important;
    }
    .candidate-grid-item {
        display: flex;
        flex-direction: column;
    }
    .candidate-grid-label {
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .candidate-grid-value {
        font-size: 14.5px !important;
        font-weight: 700 !important;
        color: #172033 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* WHITE CARDS & PANELS */
    .glass-card {
        background: #FFFFFF !important;
        border: 1px solid #D7E1F0 !important;
        padding: 22px 26px !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.06) !important;
        margin-bottom: 18px !important;
        color: #172033 !important;
    }

    .hero-verdict-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F9FF 100%) !important;
        border: 1px solid #BAE6FD !important;
        border-radius: 16px !important;
        padding: 24px 28px !important;
        box-shadow: 0 6px 22px -4px rgba(37, 99, 235, 0.08) !important;
        margin-bottom: 20px !important;
    }

    .profile-card {
        background: #FFFFFF !important;
        border: 1px solid #D7E1F0 !important;
        border-radius: 14px !important;
        padding: 24px 28px !important;
        box-shadow: 0 4px 18px -2px rgba(15, 23, 42, 0.06) !important;
        margin-bottom: 20px !important;
    }

    /* RIGHT-SIDE CHATBOT STYLING */
    .chat-companion-card {
        background: #FFFFFF !important;
        border: 1px solid #D7E1F0 !important;
        border-radius: 16px !important;
        padding: 16px 18px !important;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.07) !important;
        display: flex;
        flex-direction: column;
    }

    .chat-bubble-user {
        background: #EFF6FF !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 14px 14px 2px 14px !important;
        padding: 11px 15px !important;
        margin-bottom: 10px !important;
        color: #172033 !important;
        font-size: 14.5px !important;
        line-height: 1.5 !important;
    }

    .chat-bubble-assistant {
        background: #F8FAFC !important;
        border: 1px solid #D7E1F0 !important;
        border-radius: 14px 14px 14px 2px !important;
        padding: 13px 17px !important;
        margin-bottom: 8px !important;
        color: #172033 !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }

    /* SKILL & CERT PILLS */
    .skill-pill-match {
        display: inline-block;
        background: #DCFCE7 !important;
        border: 1px solid #86EFAC !important;
        color: #15803D !important;
        padding: 5px 12px !important;
        border-radius: 20px !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        margin: 3px 4px !important;
    }

    .skill-pill-gap {
        display: inline-block;
        background: #FEE2E2 !important;
        border: 1px solid #FCA5A5 !important;
        color: #B91C1C !important;
        padding: 5px 12px !important;
        border-radius: 20px !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        margin: 3px 4px !important;
    }

    .cert-badge {
        display: inline-block;
        background: #F3E8FF !important;
        border: 1px solid #D8B4FE !important;
        color: #7C3AED !important;
        padding: 5px 12px !important;
        border-radius: 16px !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        margin: 3px 4px !important;
    }

    /* STREAMLIT INPUTS, METRICS & BUTTONS OVERRIDES */
    div[data-testid="stMetricValue"] {
        font-size: 30px !important;
        font-weight: 900 !important;
        color: #2563EB !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-size: 14.5px !important;
        font-weight: 700 !important;
    }

    .stTextInput input, .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #172033 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-size: 15px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB 0%, #0891B2 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 15.5px !important;
        border-radius: 9px !important;
        padding: 10px 22px !important;
        box-shadow: 0 4px 14px -2px rgba(37, 99, 235, 0.28) !important;
    }

    button[kind="secondary"] {
        background: #FFFFFF !important;
        border: 1.5px solid #2563EB !important;
        color: #2563EB !important;
        font-weight: 700 !important;
        font-size: 15.5px !important;
        border-radius: 9px !important;
        padding: 9px 20px !important;
    }
    button[kind="secondary"]:hover {
        background: #EFF6FF !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- CONTEXTUAL SECTIONS & CLIPBOARD COPY HELPERS ---
def extract_contextual_sections(content: str) -> dict[str, str]:
    """Extract candidate details, fitment summary, or interview questions from markdown message."""
    sections = {}
    lines = content.splitlines()

    # 1. Interview Questions
    iq_lines = []
    in_iq = False
    for line in lines:
        lower = line.lower()
        if "interview question" in lower or "questions to ask" in lower:
            in_iq = True
            iq_lines.append(line)
        elif in_iq:
            if line.startswith("#") and not ("interview" in lower or "question" in lower):
                in_iq = False
            else:
                iq_lines.append(line)
    if iq_lines and len(iq_lines) > 1:
        sections["interview_questions"] = "\n".join(iq_lines).strip()

    # 2. Fitment Summary
    fs_lines = []
    in_fs = False
    for line in lines:
        lower = line.lower()
        if any(k in lower for k in ["fitment score", "fitment summary", "screening verdict", "recommendation:"]):
            in_fs = True
            fs_lines.append(line)
        elif in_fs:
            if line.startswith("## ") and not any(k in lower for k in ["fitment", "score", "verdict", "recommendation", "alignment"]):
                in_fs = False
            else:
                fs_lines.append(line)
    if fs_lines and len(fs_lines) > 1:
        sections["fitment_summary"] = "\n".join(fs_lines).strip()

    # 3. Candidate Details
    cd_lines = []
    in_cd = False
    for line in lines:
        lower = line.lower()
        if any(k in lower for k in ["candidate details", "candidate profile", "candidate information"]) or (("name:" in lower or "👤" in line) and any(x in lower for x in ["designation", "organization", "experience", "mobile"])):
            in_cd = True
            cd_lines.append(line)
        elif in_cd:
            if line.startswith("## ") and not any(k in lower for k in ["candidate", "profile", "contact", "experience"]):
                in_cd = False
            else:
                cd_lines.append(line)
    if cd_lines and len(cd_lines) > 1:
        sections["candidate_details"] = "\n".join(cd_lines).strip()

    return sections


def render_copy_actions(content: str, key_suffix: str):
    """Renders plain-text Copy Response button plus optional contextual copy buttons."""
    clean_text = content.strip()
    encoded_full = urllib.parse.quote(clean_text)
    sections = extract_contextual_sections(clean_text)

    buttons_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 3px 0 6px 0;
            background: transparent;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        .copy-btn-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
        }}
        .copy-btn {{
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            color: #334155;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            transition: all 0.15s ease;
            user-select: none;
        }}
        .copy-btn:hover {{
            background: #F1F5F9;
            border-color: #94A3B8;
            color: #0F172A;
        }}
        .copy-btn-blue {{
            color: #2563EB;
            border-color: #BFDBFE;
            background: #EFF6FF;
        }}
        .copy-btn-cyan {{
            color: #0891B2;
            border-color: #BAE6FD;
            background: #F0F9FF;
        }}
        .copy-btn-violet {{
            color: #7C3AED;
            border-color: #DDD6FE;
            background: #F5F3FF;
        }}
        .copy-btn.copied {{
            background: #DCFCE7 !important;
            border-color: #86EFAC !important;
            color: #15803D !important;
        }}
    </style>
    </head>
    <body>
    <div class="copy-btn-bar">
        <button id="btn_main_{key_suffix}" class="copy-btn" onclick="performCopy('{encoded_full}', 'btn_main_{key_suffix}', '📋 Copy Response')">
            📋 Copy Response
        </button>
    """

    if "candidate_details" in sections:
        enc_cd = urllib.parse.quote(sections["candidate_details"])
        buttons_html += f"""
        <button id="btn_cd_{key_suffix}" class="copy-btn copy-btn-blue" onclick="performCopy('{enc_cd}', 'btn_cd_{key_suffix}', '📄 Copy Candidate Details')">
            📄 Copy Candidate Details
        </button>
        """

    if "fitment_summary" in sections:
        enc_fs = urllib.parse.quote(sections["fitment_summary"])
        buttons_html += f"""
        <button id="btn_fs_{key_suffix}" class="copy-btn copy-btn-cyan" onclick="performCopy('{enc_fs}', 'btn_fs_{key_suffix}', '🎯 Copy Fitment Summary')">
            🎯 Copy Fitment Summary
        </button>
        """

    if "interview_questions" in sections:
        enc_iq = urllib.parse.quote(sections["interview_questions"])
        buttons_html += f"""
        <button id="btn_iq_{key_suffix}" class="copy-btn copy-btn-violet" onclick="performCopy('{enc_iq}', 'btn_iq_{key_suffix}', '🎤 Copy Interview Questions')">
            🎤 Copy Interview Questions
        </button>
        """

    buttons_html += f"""
    </div>
    <script>
    function performCopy(encoded, btnId, originalLabel) {{
        const text = decodeURIComponent(encoded);
        function markSuccess() {{
            const btn = document.getElementById(btnId);
            if (btn) {{
                btn.classList.add('copied');
                btn.innerHTML = '✅ Copied!';
                setTimeout(() => {{
                    btn.classList.remove('copied');
                    btn.innerHTML = originalLabel;
                }}, 2000);
            }}
        }}
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(text).then(markSuccess).catch(() => execFallback(text));
        }} else {{
            execFallback(text);
        }}
        function execFallback(str) {{
            const ta = document.createElement('textarea');
            ta.value = str;
            ta.setAttribute('readonly', '');
            ta.style.position = 'absolute';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            try {{
                document.execCommand('copy');
                markSuccess();
            }} catch (e) {{
                alert('Please select text manually to copy.');
            }}
            document.body.removeChild(ta);
        }}
    }}
    </script>
    </body>
    </html>
    """

    height = 36 if len(sections) == 0 else 68
    components.html(buttons_html, height=height)



# --- HELPER: FILE TEXT EXTRACTION ---
def extract_text_from_file_uploader(uploaded_file) -> str:
    """Extracts text safely using parser module."""
    if uploaded_file is None:
        return ""
    try:
        raw_bytes = uploaded_file.read()
        content, _ = parser.extract_text_from_file(raw_bytes, uploaded_file.name)
        return content
    except Exception as exc:
        st.error(f"Error reading file {uploaded_file.name}: {exc}")
        return ""


def get_status_badge_html(status: str) -> str:
    """Renders recruiter-friendly styled HTML badge for candidate recruitment status."""
    s = status or "Screened"
    if s in ["New", "Screened"]:
        cls = "status-badge-blue"
    elif s in ["Shortlisted", "Selected", "Offer Released", "Joined"]:
        cls = "status-badge-green"
    elif s in ["Recruiter Review", "Interview Scheduled", "Interview Completed"]:
        cls = "status-badge-violet"
    elif s in ["On Hold"]:
        cls = "status-badge-amber"
    elif s in ["Rejected"]:
        cls = "status-badge-red"
    else:
        cls = "status-badge-blue"
    return f'<span class="{cls}">{html.escape(s)}</span>'


# --- SIDEBAR CONFIGURATION (RECRUITER-FACING AI SETTINGS) ---
with st.sidebar:
    st.markdown("### ⚙️ AI Settings")

    active_provider_options = [
        "Google Gemini (gemini-3.5-flash-lite)",
        "OpenRouter (Free / Cloud LLMs)",
        "NVIDIA NIM",
        "⚡ InstantFit Offline Screening",
    ]

    selected_provider_ui = st.selectbox(
        "Select Active AI Service",
        options=active_provider_options,
        index=0,
        help="Select Google Gemini, OpenRouter, NVIDIA NIM, or InstantFit Offline Screening.",
    )

    provider_id_map = {
        "Google Gemini (gemini-3.5-flash-lite)": "gemini",
        "OpenRouter (Free / Cloud LLMs)": "openrouter",
        "NVIDIA NIM": "nvidia",
        "⚡ InstantFit Offline Screening": "offline",
    }
    p_id = provider_id_map[selected_provider_ui]

    user_api_key = ""
    selected_model = ""

    if p_id == "gemini":
        user_api_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            placeholder="AQ.Ab8...",
            help="Google Gemini API Key (Masked).",
        )
        selected_model = st.selectbox(
            "Gemini Model",
            options=["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"],
            index=0,
        )
    elif p_id == "openrouter":
        user_api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=os.getenv("OPENROUTER_API_KEY", ""),
            placeholder="sk-or-v1-...",
            help="OpenRouter API Key (Masked).",
        )
        selected_model = st.selectbox(
            "OpenRouter Model",
            options=[
                "google/gemma-4-26b-a4b-it:free",
                "google/gemma-4-31b-it:free",
                "nvidia/nemotron-3.5-lightning:free",
                "liquid/lfm-2.5-2.6b:free",
            ],
            index=0,
        )
    elif p_id == "nvidia":
        user_api_key = st.text_input(
            "NVIDIA API Key",
            type="password",
            value=os.getenv("NVIDIA_API_KEY", ""),
            placeholder="nvapi-...",
            help="NVIDIA Build API Key (Masked).",
        )
        selected_model = st.selectbox(
            "NVIDIA Model",
            options=[
                "stepfun-ai/step-5-preview",
                "z-ai/glm-5.3",
                "meta/llama-3.1-70b-instruct",
                "mistralai/mistral-large-2-instruct",
            ],
            index=0,
        )

    # Health Validation Badge
    if p_id != "offline":
        val_cache_key = f"{p_id}::{user_api_key.strip()}::{selected_model}"
        if "provider_val_cache" not in st.session_state:
            st.session_state.provider_val_cache = {}

        if val_cache_key in st.session_state.provider_val_cache:
            is_valid, validation_msg = st.session_state.provider_val_cache[val_cache_key]
        else:
            with st.spinner("Checking AI service connectivity..."):
                is_valid, validation_msg = llm_manager.validate_provider_health(
                    p_id, api_key=user_api_key.strip(), model=selected_model, timeout_seconds=8.0
                )
                st.session_state.provider_val_cache[val_cache_key] = (is_valid, validation_msg)

        if is_valid:
            st.success(f"🟢 {validation_msg}")
            provider_status_text = f"✨ AI Service: {selected_provider_ui.split('(')[0].strip()} | Model: {selected_model} | Status: Connected"
            provider_is_connected = True
        else:
            st.warning(f"⚠️ {validation_msg}")
            provider_status_text = "⚡ InstantFit Offline Screening | InstantFit Screening Active"
            provider_is_connected = False
    else:
        st.info("⚡ InstantFit Offline Screening Active (Zero Cloud Calls)")
        provider_status_text = "⚡ InstantFit Offline Screening | InstantFit Screening Active"
        provider_is_connected = False

    st.markdown("---")
    st.markdown("### 📊 Screening Criteria")
    with st.expander("Configure Screening Criteria Matrix", expanded=False):
        w_skills = st.slider("Skills Match Weight", 0, 100, 40)
        w_exp = st.slider("Experience Depth Weight", 0, 100, 30)
        w_edu = st.slider("Education Weight", 0, 100, 15)
        w_extras = st.slider("Certifications Weight", 0, 100, 15)

    scoring_weights = {
        "skills": float(w_skills),
        "exp": float(w_exp),
        "edu": float(w_edu),
        "extras": float(w_extras),
    }

    st.markdown("---")
    st.caption("🔒 **Candidate Privacy & Fairness:** All scores and skill alignments are calculated with zero bias using verified objective criteria. Masked API keys are never stored in candidate records.")


# --- TOP-LEVEL COMPACT HEADER (~80-100px) ---
badge_html = (
    f'<span class="provider-status-badge">{html.escape(provider_status_text)}</span>'
    if provider_is_connected
    else f'<span class="provider-offline-badge">{html.escape(provider_status_text)}</span>'
)

head_left, head_right = st.columns([76, 24])
with head_left:
    st.markdown(
        f"""
        <div style="margin-bottom: 2px;">
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <h1 class="brand-title" style="margin: 0; display: inline;">Recruitment Intelligence Platform</h1>
                {badge_html}
            </div>
            <p class="brand-subtitle">Candidate Fitment Screening Portal | AI-Assisted Recruitment Intelligence</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with head_right:
    btn_r1, btn_r2 = st.columns([1.2, 1])
    with btn_r1:
        if st.button("↻ Refresh Page", key="top_refresh_btn", help="Refresh displayed state and candidate records", use_container_width=True):
            st.toast("✅ Portal refreshed — candidate records up to date.")
            time.sleep(0.15)
            st.rerun()
    with btn_r2:
        if st.button("⚙️ Settings", key="top_settings_btn", help="AI service configuration & connectivity", use_container_width=True):
            st.toast("💡 System & AI Settings available in the ⚙️ Settings tab below.")

# --- CHATBOT SESSION STATE INITIALIZATION ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I am the **Fitment Assistant**.\n\n"
                "I answer factual candidate queries, check fitment scores, look up missing skills, "
                "and track follow-ups directly from your candidate records.\n\n"
                "Ask me about any candidate or choose a suggested inquiry below!"
            ),
        }
    ]
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())[:8]

# --- TOP LEVEL WORKSPACE & CHATBOT TWO-COLUMN LAYOUT ---
# Main screening workspace ~74% width, right chatbot panel ~26% width
col_workspace, col_chat = st.columns([74, 26], gap="large")

# ==============================================================================
# MAIN WORKSPACE (LEFT COLUMN)
# ==============================================================================
with col_workspace:
    tab_dashboard, tab_tracker, tab_assistant_full, tab_system = st.tabs(
        [
            "🎯 Screening Dashboard",
            "📋 Candidate Tracker",
            "🤖 Fitment Assistant",
            "⚙️ Settings",
        ]
    )

    # --------------------------------------------------------------------------
    # TAB 1: SCREENING DASHBOARD
    # --------------------------------------------------------------------------
    with tab_dashboard:
        if "jd_text_val" not in st.session_state:
            st.session_state.jd_text_val = ""
        if "cv_text_val" not in st.session_state:
            st.session_state.cv_text_val = ""
        if "active_screening_record" not in st.session_state:
            st.session_state.active_screening_record = None

        # --- COMPACT UPLOAD AREA (TWO CONTENT-DRIVEN PANELS) ---
        col_p1, col_p2 = st.columns(2, gap="medium")

        # PANEL 1: JOB DESCRIPTION
        with col_p1:
            st.markdown(
                """
                <div class="upload-panel-card" style="border-left: 4px solid #0891B2;">
                    <div class="upload-panel-header">
                        <span style="font-size: 22px; color: #0891B2;">📄</span>
                        <h3 class="upload-panel-title">01 — Job Description</h3>
                    </div>
                    <p class="upload-panel-desc">Upload or select target role specifications.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            uploaded_jd = st.file_uploader(
                "Upload Job Description (.pdf, .docx, .txt)",
                type=["pdf", "docx", "doc", "txt"],
                key="jd_file_upload",
                label_visibility="collapsed",
            )
            if uploaded_jd is not None:
                upload_sig = f"{uploaded_jd.name}_{uploaded_jd.size}"
                if st.session_state.get("last_saved_jd_sig") != upload_sig:
                    try:
                        raw_bytes = uploaded_jd.read()
                        saved_jd_meta = storage.save_job_description_file(raw_bytes, uploaded_jd.name)
                        if saved_jd_meta.get("status") == "error":
                            st.session_state.jd_status = ("error", f"❌ {saved_jd_meta.get('message', 'The job description could not be saved.')}")
                        else:
                            st.session_state.active_jd_file_id = saved_jd_meta.get("file_id")
                            st.session_state.active_jd_file_path = saved_jd_meta.get("stored_path") or saved_jd_meta.get("stored_relative_path")
                            st.session_state.last_saved_jd_sig = upload_sig

                            extracted_jd, _ = parser.extract_text_from_file(raw_bytes, uploaded_jd.name)
                            if extracted_jd and extracted_jd.strip():
                                st.session_state.jd_text_val = extracted_jd
                                st.session_state.last_parsed_jd_name = uploaded_jd.name
                                st.session_state.jd_file_size_kb = round(len(raw_bytes) / 1024, 1)
                                st.session_state.jd_status = ("success", f"✅ JD — {uploaded_jd.name} loaded successfully!")
                                st.session_state.active_screening_record = None
                            else:
                                st.session_state.jd_status = ("error", "❌ The file was saved, but text extraction failed. Check the file format and try again.")
                    except Exception as exc:
                        st.session_state.jd_status = ("error", "❌ The job description could not be loaded. Please try uploading it again.")

            # Reusable Saved JD Selector
            saved_jds = storage.list_saved_job_descriptions()
            if saved_jds:
                with st.expander("📂 Reuse Previously Saved Job Description", expanded=False):
                    jd_choices = {f"{j['original_filename']} ({str(j.get('upload_timestamp') or j.get('uploaded_at') or '')[:10]}) [ID:{str(j.get('file_id') or '')[:8]}]": j for j in saved_jds}
                    sel_saved_jd_key = st.selectbox("Select saved JD", options=["-- Select to Load --"] + list(jd_choices.keys()), key="sel_saved_jd_opt")
                    if sel_saved_jd_key != "-- Select to Load --":
                        chosen_jd = jd_choices[sel_saved_jd_key]
                        if st.button("Load This Saved JD", key="load_saved_jd_act_btn", use_container_width=True):
                            try:
                                stored_p = chosen_jd.get("stored_path") or chosen_jd.get("stored_relative_path")
                                if not stored_p:
                                    st.error("The saved job description file is missing its storage path.")
                                else:
                                    raw_bytes = storage.read_stored_file_bytes(stored_p)
                                    extracted_jd, _ = parser.extract_text_from_file(raw_bytes, chosen_jd["original_filename"])
                                    if not extracted_jd or not extracted_jd.strip():
                                        st.error("The file was saved, but text extraction failed. Check the file format and try again.")
                                    else:
                                        st.session_state.jd_text_val = extracted_jd
                                        st.session_state.last_parsed_jd_name = chosen_jd["original_filename"]
                                        st.session_state.active_jd_file_id = chosen_jd.get("file_id")
                                        st.session_state.active_jd_file_path = stored_p
                                        st.session_state.jd_file_size_kb = round(len(raw_bytes) / 1024, 1)
                                        st.session_state.jd_status = ("success", f"✅ Loaded saved JD — {chosen_jd['original_filename']}")
                                        st.session_state.active_screening_record = None
                                        st.rerun()
                            except FileNotFoundError:
                                st.error("The saved job description file is missing. Please upload the JD again.")
                            except Exception as err:
                                st.error("The job description could not be loaded. Please try uploading it again.")

            # Selected filename and file size
            if st.session_state.get("last_parsed_jd_name") and st.session_state.jd_text_val.strip():
                st.caption(f"📄 **Active JD:** `{html.escape(st.session_state.last_parsed_jd_name)}` ({st.session_state.get('jd_file_size_kb', 0)} KB)")

            # Validation status message
            if "jd_status" in st.session_state:
                st_type, st_msg = st.session_state.jd_status
                if st_type == "success":
                    st.success(st_msg)
                else:
                    st.error(st_msg)

            # Expandable JD Preview
            with st.expander("📝 View / Edit Job Description Text", expanded=False):
                jd_text = st.text_area(
                    "Job Description Content",
                    value=st.session_state.jd_text_val,
                    height=160,
                    placeholder="Paste target job requirements and qualifications here...",
                    label_visibility="collapsed",
                )
                if jd_text != st.session_state.jd_text_val:
                    st.session_state.jd_text_val = jd_text
                    st.session_state.active_screening_record = None
                    if not jd_text.strip():
                        st.session_state.pop("jd_status", None)
                        st.session_state.pop("last_parsed_jd_name", None)

        # PANEL 2: CANDIDATE RESUME
        with col_p2:
            st.markdown(
                """
                <div class="upload-panel-card" style="border-left: 4px solid #7C3AED;">
                    <div class="upload-panel-header">
                        <span style="font-size: 22px; color: #7C3AED;">📎</span>
                        <h3 class="upload-panel-title">02 — Candidate Resume</h3>
                    </div>
                    <p class="upload-panel-desc">Upload or select candidate CV/resume.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            uploaded_cv = st.file_uploader(
                "Upload Candidate CV (.pdf, .docx, .txt)",
                type=["pdf", "docx", "doc", "txt"],
                key="cv_file_upload",
                label_visibility="collapsed",
            )
            if uploaded_cv is not None:
                upload_sig_cv = f"{uploaded_cv.name}_{uploaded_cv.size}"
                if st.session_state.get("last_saved_cv_sig") != upload_sig_cv:
                    try:
                        raw_bytes = uploaded_cv.read()
                        extracted_cv, _ = parser.extract_text_from_file(raw_bytes, uploaded_cv.name)
                        cand_name = None
                        if extracted_cv and extracted_cv.strip():
                            p_meta = deterministic_engine.extract_candidate_metadata(extracted_cv)
                            cand_name = p_meta.get("name")

                        saved_cv_meta = storage.save_resume_file(raw_bytes, uploaded_cv.name, candidate_name=cand_name)
                        if saved_cv_meta.get("status") == "error":
                            st.session_state.cv_status = ("error", f"❌ {saved_cv_meta.get('message', 'The candidate resume could not be saved.')}")
                        else:
                            st.session_state.active_resume_file_id = saved_cv_meta.get("file_id")
                            st.session_state.active_resume_file_path = saved_cv_meta.get("stored_path") or saved_cv_meta.get("stored_relative_path")
                            st.session_state.last_saved_cv_sig = upload_sig_cv

                            if extracted_cv and extracted_cv.strip():
                                st.session_state.cv_text_val = extracted_cv
                                st.session_state.last_parsed_cv_name = uploaded_cv.name
                                st.session_state.cv_file_size_kb = round(len(raw_bytes) / 1024, 1)
                                st.session_state.cv_status = ("success", f"✅ Resume — {uploaded_cv.name} loaded successfully!")
                                st.session_state.active_screening_record = None
                            else:
                                st.session_state.cv_status = ("error", "❌ The file was saved, but text extraction failed. Check the file format and try again.")
                    except Exception as exc:
                        st.session_state.cv_status = ("error", "❌ The candidate resume could not be loaded. Please try uploading it again.")

            # Reusable Saved Resume Selector
            saved_resumes = storage.list_saved_resumes()
            if saved_resumes:
                with st.expander("📂 Reuse Previously Saved Candidate Resume", expanded=False):
                    res_choices = {f"{r.get('candidate_name') or r['original_filename']} — {r['original_filename']} ({str(r.get('upload_timestamp') or r.get('uploaded_at') or '')[:10]}) [ID:{str(r.get('file_id') or '')[:8]}]": r for r in saved_resumes}
                    sel_saved_res_key = st.selectbox("Select saved Resume", options=["-- Select to Load --"] + list(res_choices.keys()), key="sel_saved_res_opt")
                    if sel_saved_res_key != "-- Select to Load --":
                        chosen_res = res_choices[sel_saved_res_key]
                        if st.button("Load This Saved Resume", key="load_saved_res_act_btn", use_container_width=True):
                            try:
                                stored_p = chosen_res.get("stored_path") or chosen_res.get("stored_relative_path")
                                if not stored_p:
                                    st.error("The saved resume record is missing its storage path.")
                                else:
                                    raw_bytes = storage.read_stored_file_bytes(stored_p)
                                    extracted_cv, _ = parser.extract_text_from_file(raw_bytes, chosen_res["original_filename"])
                                    if not extracted_cv or not extracted_cv.strip():
                                        st.error("The file was saved, but text extraction failed. Check the file format and try again.")
                                    else:
                                        st.session_state.cv_text_val = extracted_cv
                                        st.session_state.last_parsed_cv_name = chosen_res["original_filename"]
                                        st.session_state.active_resume_file_id = chosen_res.get("file_id")
                                        st.session_state.active_resume_file_path = stored_p
                                        st.session_state.cv_file_size_kb = round(len(raw_bytes) / 1024, 1)
                                        st.session_state.cv_status = ("success", f"✅ Resume — {chosen_res['original_filename']} loaded successfully!")
                                        st.session_state.active_screening_record = None
                                        st.rerun()
                            except FileNotFoundError:
                                st.error("The saved resume file is missing. Please upload the resume again.")
                            except Exception as err:
                                st.error("The candidate resume could not be loaded. Please try uploading it again.")

            # Selected filename and file size
            if st.session_state.get("last_parsed_cv_name") and st.session_state.cv_text_val.strip():
                st.caption(f"📎 **Active Resume:** `{html.escape(st.session_state.last_parsed_cv_name)}` ({st.session_state.get('cv_file_size_kb', 0)} KB)")

            # Validation status message
            if "cv_status" in st.session_state:
                st_type, st_msg = st.session_state.cv_status
                if st_type == "success":
                    st.success(st_msg)
                else:
                    st.error(st_msg)

            # Compact Candidate Summary Grid beneath resume panel
            if st.session_state.cv_text_val.strip():
                cand_name_preview = preview_meta.get("name") if preview_meta else None
                existing_cand = registry.find_candidate_by_name(cand_name_preview) if cand_name_preview else None
                prev_status = existing_cand.get("current_status", "New") if existing_cand else "New"
                prev_score = f"{existing_cand['deterministic_score']}/100" if existing_cand and existing_cand.get("deterministic_score") is not None else "Pending"

                first_jd_line = [l.strip() for l in st.session_state.jd_text_val.splitlines() if l.strip()]
                target_role_preview = first_jd_line[0][:35] if first_jd_line else (existing_cand.get("job_title", "Unassigned") if existing_cand else "Unassigned")

                st.markdown(
                    f"""
                    <div class="candidate-summary-grid">
                        <div class="candidate-grid-item">
                            <span class="candidate-grid-label">Candidate Name</span>
                            <span class="candidate-grid-value">👤 {html.escape(preview_meta['name'] or 'Not Detected')}</span>
                        </div>
                        <div class="candidate-grid-item">
                            <span class="candidate-grid-label">Current Designation</span>
                            <span class="candidate-grid-value">💼 {html.escape(preview_meta['current_designation'] or 'Not Detected')}</span>
                        </div>
                        <div class="candidate-grid-item">
                            <span class="candidate-grid-label">Current Organization</span>
                            <span class="candidate-grid-value">🏢 {html.escape(preview_meta.get('organization') or 'Not Detected')}</span>
                        </div>
                        <div class="candidate-grid-item">
                            <span class="candidate-grid-label">Mobile Number</span>
                            <span class="candidate-grid-value">📱 {html.escape(preview_meta['mobile'] or 'Not available')}</span>
                        </div>
                        <div class="candidate-grid-item">
                            <span class="candidate-grid-label">Total Experience</span>
                            <span class="candidate-grid-value">⏳ {html.escape(preview_meta['total_exp'] or 'Not Detected')}</span>
                        </div>
                        <div class="candidate-grid-item">
                            <span class="candidate-grid-label">Target Role</span>
                            <span class="candidate-grid-value">🎯 {html.escape(target_role_preview)}</span>
                        </div>
                        <div class="candidate-grid-item">
                            <span class="candidate-grid-label">Recruitment Status</span>
                            <span class="candidate-grid-value">{get_status_badge_html(prev_status)}</span>
                        </div>
                        <div class="candidate-grid-item">
                            <span class="candidate-grid-label">Latest Fitment</span>
                            <span class="candidate-grid-value" style="color: #2563EB;">⚡ {prev_score}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Expandable Resume Preview
            with st.expander("📝 View / Edit Candidate Resume Text", expanded=False):
                cv_text = st.text_area(
                    "Candidate Resume Content",
                    value=st.session_state.cv_text_val,
                    height=160,
                    placeholder="Paste candidate resume or CV text here...",
                    label_visibility="collapsed",
                )
                if cv_text != st.session_state.cv_text_val:
                    st.session_state.cv_text_val = cv_text
                    st.session_state.active_screening_record = None
                    if not cv_text.strip():
                        st.session_state.pop("cv_status", None)
                        st.session_state.pop("last_parsed_cv_name", None)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- SCREENING TRIGGER BUTTONS ---
        btn_col1, btn_col2 = st.columns(2, gap="medium")
        with btn_col1:
            trigger_ai = st.button("🚀 Run InstantFit AI Screening", type="primary", use_container_width=True)
        with btn_col2:
            trigger_offline = st.button("⚡ Run Instant Offline Screening", type="secondary", use_container_width=True)

        if trigger_ai or trigger_offline:
            curr_jd = st.session_state.jd_text_val.strip()
            curr_cv = st.session_state.cv_text_val.strip()

            if not curr_jd or not curr_cv:
                st.warning("⚠️ Please provide both a Job Description and a Candidate Resume to initiate screening.")
            else:
                with st.spinner("⚡ Running authoritative deterministic evaluation..."):
                    det_result = deterministic_engine.evaluate_candidate_deterministically(
                        curr_jd, curr_cv, weights=scoring_weights
                    )
                    meta = det_result["metadata"]

                # Sub-scores
                matched_skills = det_result["skills_matched"]
                missing_skills = det_result["missing_skills"]
                total_skills = len(matched_skills) + len(missing_skills)
                skills_score = int((len(matched_skills) / max(total_skills, 1)) * 100) if total_skills > 0 else 0

                # Numeric experience score
                exp_detected_str = det_result["total_experience_detected"]
                exp_num = 5
                try:
                    exp_num = int(re.search(r"\d+", exp_detected_str).group(0))
                except Exception:
                    pass
                exp_score = min(int((exp_num / 8) * 100), 100)

                # Authoritative Certifications Extraction
                found_certs = det_result.get("certifications_detected") or meta.get("certifications") or []
                cert_score = min(len(found_certs) * 50, 100)

                ai_text = ""
                active_provider_name = "Offline / Deterministic"
                active_model_name = "None"

                # Run AI qualitative assessment if requested
                if trigger_ai:
                    if provider_is_connected:
                        with st.spinner(f"🤖 Generating qualitative fitment insights via {selected_provider_ui.split('(')[0].strip()} ({selected_model})..."):
                            ai_res = llm_manager.generate_qualitative_assessment(
                                job_description=curr_jd,
                                resume_text=curr_cv,
                                preferred_provider=p_id,
                                preferred_model=selected_model,
                                timeout_seconds=35.0,
                            )
                            if ai_res["status"] == "success":
                                ai_text = ai_res["text"]
                                active_provider_name = ai_res["provider"]
                                active_model_name = ai_res["model"]
                            else:
                                st.warning(f"⚠️ {ai_res.get('message', 'AI analysis timed out. Falling back to offline assessment.')}")
                    else:
                        st.info("ℹ️ AI Provider is not connected or in offline mode. Running Instant Offline Screening with deterministic engine.")

                # Automated SQLite Persistence
                cand_id = registry.upsert_candidate(
                    name=meta["name"],
                    email=meta["email"],
                    mobile=meta["mobile"],
                    location=meta["location"],
                    current_organization=meta["organization"],
                    current_designation=meta["current_designation"],
                    previous_organizations=meta.get("previous_organizations", []),
                    education=meta.get("education", "Not Specified"),
                    certifications=found_certs,
                    total_experience=meta["total_exp"],
                    relevant_experience=meta["relevant_exp"],
                    resume_reference=uploaded_cv.name if uploaded_cv else "Pasted Text",
                )

                # Determine job title
                first_jd_line = [l.strip() for l in curr_jd.splitlines() if l.strip()]
                job_title = first_jd_line[0][:60] if first_jd_line else "Target Technical Role"

                job_id = registry.upsert_job(
                    job_title=job_title,
                    job_description=curr_jd,
                    required_skills=matched_skills + missing_skills,
                )

                screening_id = registry.save_screening(
                    candidate_id=cand_id,
                    job_id=job_id,
                    deterministic_score=det_result["match_score"],
                    verdict=det_result["verdict"],
                    recommendation=det_result["recommendation"],
                    skills_score=skills_score,
                    exp_score=exp_score,
                    cert_score=cert_score,
                    matched_skills=matched_skills,
                    missing_skills=missing_skills,
                    evidence=det_result.get("supporting_evidence", {}),
                    interview_questions=det_result.get("interview_questions", []),
                    llm_analysis=ai_text,
                    llm_provider=active_provider_name,
                    llm_model=active_model_name,
                )

                # Maintain relationship between stored files and screening record
                registry.associate_screening_files(
                    screening_id=screening_id,
                    jd_file_id=st.session_state.get("active_jd_file_id"),
                    resume_file_id=st.session_state.get("active_resume_file_id"),
                )

                # Store complete active record in session state with found_certs explicitly saved
                st.session_state.active_screening_record = {
                    "candidate_id": cand_id,
                    "screening_id": screening_id,
                    "meta": meta,
                    "det_result": det_result,
                    "skills_score": skills_score,
                    "exp_score": exp_score,
                    "cert_score": cert_score,
                    "found_certs": found_certs,
                    "job_title": job_title,
                    "ai_text": ai_text,
                    "provider": active_provider_name,
                    "model": active_model_name,
                }
                st.session_state.active_candidate_id = cand_id
                st.session_state.active_candidate_name = meta["name"]

        # --- DISPLAY SCREENING RESULTS ---
        active_rec = st.session_state.active_screening_record
        if active_rec:
            meta = active_rec["meta"]
            det = active_rec["det_result"]
            score = det["match_score"]
            job_title = active_rec["job_title"]
            ai_text = active_rec.get("ai_text", "")

            # SAFE CERTIFICATIONS RESOLUTION (Fix for NameError: found_certs is not defined)
            found_certs = active_rec.get("found_certs") or det.get("certifications_detected") or meta.get("certifications") or []

            st.markdown("---")

            # Fetch persisted candidate record for current saved status
            cand_db_record = registry.get_candidate_by_id(active_rec['candidate_id'])
            current_saved_status = cand_db_record.get('current_status', 'Screened') if cand_db_record else 'Screened'

            # Prominent Recruitment Status bar at the top of candidate profile
            stat_c1, stat_c2, stat_c3 = st.columns([3, 2, 2])
            with stat_c1:
                st_idx = registry.CANDIDATE_STATUSES.index(current_saved_status) if current_saved_status in registry.CANDIDATE_STATUSES else 1
                new_cand_status = st.selectbox(
                    "📌 Recruitment Status",
                    options=registry.CANDIDATE_STATUSES,
                    index=st_idx,
                    key=f"prof_status_sel_{active_rec['candidate_id']}",
                    help="Update candidate's recruitment lifecycle status.",
                )
            with stat_c2:
                prof_notes = st.text_input(
                    "Recruiter Note",
                    key=f"prof_notes_{active_rec['candidate_id']}",
                    placeholder="e.g. Shortlisted for technical interview...",
                )
            with stat_c3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Save Status", key=f"prof_save_btn_{active_rec['candidate_id']}", type="primary", use_container_width=True):
                    if new_cand_status != current_saved_status:
                        ok = registry.update_candidate_status(
                            candidate_id=active_rec['candidate_id'],
                            new_status=new_cand_status,
                            notes=prof_notes,
                            changed_by="Recruiter",
                            screening_id=active_rec.get("screening_id"),
                        )
                        if ok:
                            st.success(f"✅ Candidate status updated to {new_cand_status}.")
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to update status to {new_cand_status}.")
                    else:
                        st.info(f"Candidate is already marked as '{current_saved_status}'.")

            # 1. CANDIDATE EXECUTIVE PROFILE CARD
            prev_orgs_str = ", ".join(meta.get("previous_organizations", [])) if meta.get("previous_organizations") else "None recorded"
            certs_str = ", ".join(found_certs) if found_certs else "None detected"

            status_badge_html = get_status_badge_html(current_saved_status)

            profile_html = f"""
            <div class="profile-card">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #D7E1F0; padding-bottom: 14px; margin-bottom: 18px;">
                    <div>
                        <h3 style="margin: 0; color: #172033; font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">👤 {meta['name']}</h3>
                        <p style="margin: 4px 0 0 0; color: #0891B2; font-size: 15px; font-weight: 700;">Role: {meta['current_designation']}</p>
                    </div>
                    <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
                        {status_badge_html}
                        <p style="margin: 0; color: #64748B; font-size: 13px;">Screening Reference: <code>{active_rec['candidate_id']}</code></p>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; font-size: 15px;">
                    <div>
                        <span style="color: #64748B; display: block; font-size: 13px; text-transform: uppercase; font-weight: 700;">Current Designation</span>
                        <strong style="color: #172033; font-size: 16px;">{meta['current_designation']}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; display: block; font-size: 13px; text-transform: uppercase; font-weight: 700;">Current Organization</span>
                        <strong style="color: #172033; font-size: 16px;">{meta['organization']}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; display: block; font-size: 13px; text-transform: uppercase; font-weight: 700;">Mobile / Contact Number</span>
                        <strong style="color: {'#15803D' if meta['mobile'] != 'Not available in CV' else '#B45309'}; font-size: 16px;">{meta['mobile']}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; display: block; font-size: 13px; text-transform: uppercase; font-weight: 700;">Email Address</span>
                        <strong style="color: #172033; font-size: 16px;">{meta['email']}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; display: block; font-size: 13px; text-transform: uppercase; font-weight: 700;">Location</span>
                        <strong style="color: #172033; font-size: 16px;">{meta['location']}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; display: block; font-size: 13px; text-transform: uppercase; font-weight: 700;">Total Experience</span>
                        <strong style="color: #172033; font-size: 16px;">{meta['total_exp']}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; display: block; font-size: 13px; text-transform: uppercase; font-weight: 700;">Target Role</span>
                        <strong style="color: #2563EB; font-size: 16px;">{job_title}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; display: block; font-size: 13px; text-transform: uppercase; font-weight: 700;">Education</span>
                        <strong style="color: #172033; font-size: 16px;">{meta.get('education', 'Not Detected')}</strong>
                    </div>
                </div>
                <div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid #D7E1F0; font-size: 14px; color: #475569;">
                    <span>🏢 <strong>Previous Orgs & Projects:</strong> {prev_orgs_str}</span> |
                    <span style="margin-left: 10px;">🏆 <strong>Accreditations:</strong> {certs_str}</span>
                </div>
            </div>
            """
            st.markdown(profile_html, unsafe_allow_html=True)

            # 2. HERO FITMENT SCORECARD
            verdict_color = "#15803D" if score >= 75 else ("#B45309" if score >= 50 else "#B91C1C")
            verdict_icon = "🟢" if score >= 75 else ("🟡" if score >= 50 else "🔴")

            hero_html = f"""
            <div class="hero-verdict-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
                    <div style="flex: 1; min-width: 280px;">
                        <span style="display: inline-block; background: {verdict_color}18; border: 1px solid {verdict_color}55; color: {verdict_color}; font-size: 13px; font-weight: 800; padding: 6px 14px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;">
                            {verdict_icon} Executive Fitment Summary & Verdict
                        </span>
                        <h2 style="color: #172033; margin: 0 0 8px 0; font-size: 24px; font-weight: 800;">{det['verdict']}</h2>
                        <p style="color: #475569; font-size: 16px; margin: 0; line-height: 1.5;">{det['recommendation']}</p>
                    </div>
                    <div style="text-align: right; background: #FFFFFF; padding: 18px 28px; border-radius: 16px; border: 1px solid #BAE6FD; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);">
                        <span style="color: #64748B; font-size: 13px; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 4px;">Fitment Index</span>
                        <span style="font-size: 42px; font-weight: 900; color: #2563EB; line-height: 1;">{score}<span style="font-size: 20px; color: #64748B;">/100</span></span>
                    </div>
                </div>
            </div>
            """
            st.markdown(hero_html, unsafe_allow_html=True)

            # 3. STRUCTURED REPORT TABS
            sub_tab_ai, sub_tab_sum, sub_tab_skills, sub_tab_exp, sub_tab_questions, sub_tab_export = st.tabs(
                [
                    "🤖 InstantFit AI Screening",
                    "🎯 Executive Summary & Verdict",
                    "🛠️ Technical Skills Alignment",
                    "⏳ Experience & Seniority",
                    "🎤 Interview Strategy",
                    "📥 Export Fitment Dossier",
                ]
            )

            with sub_tab_ai:
                st.markdown("### 🤖 InstantFit AI Screening Analysis")
                st.caption(f"Provider: **{active_rec['provider']}** | Model: `{active_rec['model']}` | Persistent Screening ID: `{active_rec['screening_id']}`")
                if ai_text:
                    st.markdown(
                        f"""<div class="glass-card" style="border-left: 4px solid #2563EB;">
                        <div style="font-size: 16px; line-height: 1.7; color: #172033;">
                        {ai_text}
                        </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.info(
                        "⚡ Qualitative AI insights were not requested or provider is currently offline. "
                        "Deterministic evaluation metrics, keyword coverage, and interview probes are displayed in the adjacent tabs."
                    )

            with sub_tab_sum:
                st.markdown("### 📋 Executive Summary & Fitment Matrix")
                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.metric("Technical Competency", f"{active_rec['skills_score']}%", f"{len(det['skills_matched'])} Matched Skills")
                    st.progress(active_rec['skills_score'] / 100)
                with mcol2:
                    st.metric("Seniority Alignment", f"{active_rec['exp_score']}%", det['total_experience_detected'])
                    st.progress(active_rec['exp_score'] / 100)
                with mcol3:
                    st.metric("Certifications & Accreditations", f"{active_rec['cert_score']}%", f"{len(found_certs)} Verified")
                    st.progress(active_rec['cert_score'] / 100)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    - **Authoritative Deterministic Verdict:** **{det['verdict']}**
                    - **Recruiter Next Step:** {det['recommendation']}
                    - **Experience Assessment:** {det.get('experience_assessment', 'Verified through career tenure timeline')}
                    """
                )

            with sub_tab_skills:
                col_match, col_gap = st.columns(2, gap="large")
                with col_match:
                    st.markdown(f"#### ✅ Matched Core Skills ({len(det['skills_matched'])})")
                    if det["skills_matched"]:
                        pills = "".join([f'<span class="skill-pill-match">✓ {s}</span>' for s in det["skills_matched"]])
                        st.markdown(f'<div style="line-height: 2.2;">{pills}</div>', unsafe_allow_html=True)
                    else:
                        st.info("No direct skill matches identified.")

                with col_gap:
                    st.markdown(f"#### ⚠️ Missing / Unverified Skills ({len(det['missing_skills'])})")
                    if det["missing_skills"]:
                        gap_pills = "".join([f'<span class="skill-pill-gap">✗ {s}</span>' for s in det["missing_skills"][:28]])
                        st.markdown(f'<div style="line-height: 2.2;">{gap_pills}</div>', unsafe_allow_html=True)
                    else:
                        st.success("No critical skill gaps identified!")

                # Supporting Evidence Snippets
                if det.get("supporting_evidence"):
                    st.markdown("#### 🔍 Verifiable Evidence Snippets (Exact Substrings from CV)")
                    for skill_name, snippets in list(det["supporting_evidence"].items())[:6]:
                        with st.expander(f"Evidence for: {skill_name}", expanded=False):
                            for snip in snippets:
                                st.markdown(f"> *\"{snip}\"*")

            with sub_tab_exp:
                st.markdown("#### ⏳ Seniority & Experience Breakdown")
                st.info(f"**Tenure Assessment:** {det.get('experience_assessment', 'Analyzed by deterministic engine')}")
                st.markdown(f"- **Total Experience:** {meta['total_exp']}")
                st.markdown(f"- **Relevant Domain Experience:** {meta['relevant_exp']}")
                st.markdown(f"- **Current Role:** {meta['current_designation']}")
                st.markdown(f"- **Current Organization:** {meta['organization']}")

                st.markdown("#### 📜 Verified Credentials & Accreditations")
                if found_certs:
                    c_badges = "".join([f'<span class="cert-badge">🏆 {c}</span>' for c in found_certs])
                    st.markdown(f'<div style="margin: 10px 0;">{c_badges}</div>', unsafe_allow_html=True)
                else:
                    st.warning("No standard recognized Cisco, Cloud, or ITIL certifications found in candidate text.")

            with sub_tab_questions:
                st.markdown("#### 🎙️ Targeted Technical Interview Probes")
                probes = det.get("interview_questions", [])
                for idx, p_text in enumerate(probes):
                    st.markdown(
                        f"""<div class="glass-card" style="border-left: 4px solid #2563EB; margin-bottom: 12px;">
                        <strong>Question {idx+1}:</strong> {p_text}
                        </div>""",
                        unsafe_allow_html=True,
                    )

            with sub_tab_export:
                st.markdown("#### 📥 Export Candidate Fitment Dossier")
                clean_name = meta["name"].replace(" ", "_").replace(".", "")
                dossier_md = f"""# Recruitment Intelligence Platform — Candidate Fitment Dossier
**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Screening ID:** {active_rec['screening_id']}

## Candidate Executive Profile
- **Candidate Full Name:** {meta['name']}
- **Current Designation:** {meta['current_designation']}
- **Current Organization:** {meta['organization']}
- **Contact Number:** {meta['mobile']}
- **Email:** {meta['email']}
- **Location:** {meta['location']}
- **Total Experience:** {meta['total_exp']}
- **Relevant Experience:** {meta['relevant_exp']}
- **Target Role:** {job_title}

## Deterministic Screening Results
- **Overall Fitment Score:** {score}/100
- **Executive Verdict:** {det['verdict']}
- **Recommendation:** {det['recommendation']}
- **Skills Alignment:** {active_rec['skills_score']}%
- **Experience Alignment:** {active_rec['exp_score']}%
- **Certifications Alignment:** {active_rec['cert_score']}%

## Technical Skills Alignment
### Matched Skills:
{', '.join(det['skills_matched'])}

### Missing Skills:
{', '.join(det['missing_skills'])}

### Verified Accreditations:
{', '.join(found_certs) if found_certs else 'None detected'}

## Recommended Interview Questions
"""
                for i, q in enumerate(det.get("interview_questions", [])):
                    dossier_md += f"{i+1}. {q}\n"

                if ai_text:
                    dossier_md += f"\n## InstantFit AI Screening Analysis ({active_rec['provider']} — {active_rec['model']})\n{ai_text}\n"

                st.download_button(
                    label=f"💾 Download {meta['name']} Fitment Dossier (.md)",
                    data=dossier_md,
                    file_name=f"Recruitment_Intelligence_{clean_name}_Dossier.md",
                    mime="text/markdown",
                )

    # --------------------------------------------------------------------------
    # TAB 2: CANDIDATE TRACKER
    # --------------------------------------------------------------------------
    with tab_tracker:
        st.markdown("### 📋 Candidate Status & Pipeline Tracker")
        st.caption("Persistent candidate lifecycle management, screening history, follow-up alerts, and status transitions.")

        # Overview Follow-Up Alerts
        follow_up_overview = registry.get_follow_ups_overview()
        overdue_list = follow_up_overview["overdue"]
        due_today_list = follow_up_overview["due_today"]

        if overdue_list or due_today_list:
            alert_col1, alert_col2 = st.columns(2)
            with alert_col1:
                if overdue_list:
                    st.error(f"⚠️ **{len(overdue_list)} Overdue Follow-up(s):** " + ", ".join([f"{f['candidate_name']} ({f['follow_up_date']})" for f in overdue_list[:3]]))
            with alert_col2:
                if due_today_list:
                    st.warning(f"⚡ **{len(due_today_list)} Follow-up(s) Due Today:** " + ", ".join([f"{f['candidate_name']}" for f in due_today_list[:3]]))

        # Filters and Search Bar
        fcol1, fcol2, fcol3 = st.columns([3, 2, 2])
        with fcol1:
            search_query = st.text_input("🔍 Search Candidates", placeholder="Search by name, email, phone, or role...")
        with fcol2:
            status_options = ["All"] + registry.CANDIDATE_STATUSES
            filter_status = st.selectbox("📌 Recruitment Status Filter", options=status_options, index=0)
        with fcol3:
            distinct_jobs = ["All"] + registry.get_distinct_target_jobs()
            filter_job = st.selectbox("🎯 Target Role Filter", options=distinct_jobs, index=0)

        fcol4, fcol5, fcol6 = st.columns([2, 2, 3])
        with fcol4:
            score_range = st.slider("Min Fitment Score", 0, 100, 0)
        with fcol5:
            filter_fu = st.selectbox(
                "📅 Follow-Up Filter",
                options=["All", "Overdue", "Due Today", "Upcoming", "Has Follow-up", "No Follow-up"],
                index=0,
            )
        with fcol6:
            st.markdown("<br>", unsafe_allow_html=True)
            csv_data = registry.export_candidates_csv()
            st.download_button("📥 Export Candidate Records (CSV)", data=csv_data, file_name="fitment_candidates_records.csv", mime="text/csv", use_container_width=True)

        candidates_list = registry.search_candidates_portal_wide(
            query_term=search_query,
            status_filter=filter_status,
            min_score=score_range if score_range > 0 else None,
            target_job=filter_job,
            follow_up_filter=filter_fu,
        )

        if not candidates_list:
            st.info("No candidate records found matching the current criteria. Run a screening to register candidates.")
        else:
            st.markdown(f"**Found {len(candidates_list)} Candidate Record(s)**")

            for cand in candidates_list:
                c_score = cand.get("deterministic_score")
                score_badge = f"🎯 {c_score}/100" if c_score is not None else "⚡ Not Screened"
                c_status = cand.get("current_status", "Screened")
                badge_html = get_status_badge_html(c_status)

                with st.expander(f"👤 {cand['name']} | Role: {cand.get('current_designation', 'N/A')} | {score_badge} | Status: {c_status}", expanded=False):
                    pcol1, pcol2 = st.columns([2, 1])

                    with pcol1:
                        st.markdown(
                            f"""
                            - **Candidate ID:** `{cand['candidate_id']}`
                            - **Current Designation:** {cand.get('current_designation', 'Not Detected')}
                            - **Current Organization:** {cand.get('current_organization', 'Not Detected')}
                            - **Mobile / Contact:** `{cand.get('mobile', 'Not available in CV')}`
                            - **Email:** {cand.get('email', 'Not Specified')}
                            - **Location:** {cand.get('location', 'Not Specified')}
                            - **Total Experience:** {cand.get('total_experience', 'Not Detected')}
                            - **Latest Fitment Verdict:** {cand.get('verdict', 'N/A')}
                            - **Target Role:** {cand.get('job_title', 'Not specified')}
                            """
                        )

                        # Set as active candidate for chatbot
                        if st.button("💬 Ask Fitment Assistant about this Candidate", key=f"sel_cand_{cand['candidate_id']}"):
                            st.session_state.active_candidate_id = cand["candidate_id"]
                            st.session_state.active_candidate_name = cand["name"]
                            st.success(f"Selected {cand['name']} for Fitment Assistant queries!")

                        # Screening History for this candidate
                        screenings = registry.get_candidate_screenings(cand["candidate_id"])
                        if screenings:
                            st.markdown(f"**📜 Screening History ({len(screenings)} record{'s' if len(screenings) > 1 else ''}):**")
                            for s in screenings:
                                st.caption(f"- `{s['screening_timestamp'][:10]}`: **{s.get('job_title', 'Role')}** ➔ Score: **{s['deterministic_score']}/100** ({s['verdict']})")
                                sc_files = registry.get_screening_files(s["screening_id"])
                                norm_files = registry.normalize_screening_files(sc_files)
                                if norm_files:
                                    f_str = " | ".join([f"📄 `{f.get('original_filename', 'Document')}` ({f.get('file_role', 'File')})" for f in norm_files])
                                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;↳ *Source files:* {f_str}")

                        # Status Transition History Timeline Table
                        status_history = registry.get_candidate_status_history(cand["candidate_id"])
                        if status_history:
                            st.markdown("**📜 Status Transition History:**")
                            hist_table = "| Date & Time | Previous Status | New Status | Changed By | Notes |\n|---|---|---|---|---|\n"
                            for h in status_history[:5]:
                                dt = h['changed_at'][:16].replace('T', ' ')
                                prev_s = h.get('previous_status') or 'None'
                                new_s = h.get('new_status', 'Screened')
                                by = h.get('changed_by') or 'Recruiter'
                                n = h.get('notes') or '-'
                                hist_table += f"| {dt} | {prev_s} | **{new_s}** | {by} | {n} |\n"
                            st.markdown(hist_table)

                    with pcol2:
                        st.markdown("#### 📌 Candidate Status Management")

                        # Prominent Status Dropdown
                        curr_idx = registry.CANDIDATE_STATUSES.index(c_status) if c_status in registry.CANDIDATE_STATUSES else 1
                        new_status = st.selectbox(
                            "📌 Recruitment Status",
                            options=registry.CANDIDATE_STATUSES,
                            index=curr_idx,
                            key=f"status_sel_{cand['candidate_id']}",
                            help="Update candidate's hiring stage.",
                        )
                        recruiter_notes = st.text_input("Recruiter Notes", key=f"notes_{cand['candidate_id']}", placeholder="e.g. Cleared round 1...")

                        if st.button("Save Status Change", key=f"save_btn_{cand['candidate_id']}", type="primary", use_container_width=True):
                            if new_status != c_status:
                                ok = registry.update_candidate_status(
                                    candidate_id=cand["candidate_id"],
                                    new_status=new_status,
                                    notes=recruiter_notes,
                                    changed_by="Recruiter",
                                )
                                if ok:
                                    st.success(f"✅ Candidate status updated to {new_status}.")
                                    time.sleep(0.4)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to update status to {new_status}.")
                            else:
                                st.info(f"Candidate is already marked as '{c_status}'.")

                        st.markdown("---")
                        st.markdown("#### 📅 Schedule Follow-Up")
                        fu_preset = st.selectbox(
                            "Follow-Up Date",
                            options=["Tomorrow", "In 3 Days", "In 7 Days", "In 14 Days", "Custom Date"],
                            key=f"fu_preset_{cand['candidate_id']}",
                        )
                        if fu_preset == "Tomorrow":
                            target_date = (date.today() + timedelta(days=1)).isoformat()
                        elif fu_preset == "In 3 Days":
                            target_date = (date.today() + timedelta(days=3)).isoformat()
                        elif fu_preset == "In 7 Days":
                            target_date = (date.today() + timedelta(days=7)).isoformat()
                        elif fu_preset == "In 14 Days":
                            target_date = (date.today() + timedelta(days=14)).isoformat()
                        else:
                            cust_d = st.date_input("Select Custom Date", key=f"cust_d_{cand['candidate_id']}")
                            target_date = cust_d.isoformat()

                        fu_note = st.text_input("Follow-Up Reminder Note", key=f"fu_note_{cand['candidate_id']}", placeholder="e.g. Send interview invite...")
                        if st.button("Schedule Follow-Up", key=f"fu_btn_{cand['candidate_id']}", use_container_width=True):
                            registry.add_follow_up(
                                candidate_id=cand["candidate_id"],
                                follow_up_date=target_date,
                                notes=fu_note,
                            )
                            st.success(f"Follow-up scheduled for {target_date}!")
                            time.sleep(0.4)
                            st.rerun()

    # --------------------------------------------------------------------------
    # TAB 3: FITMENT ASSISTANT
    # --------------------------------------------------------------------------
    with tab_assistant_full:
        st.markdown("### 🤖 Fitment Assistant")
        st.caption("Conversational recruitment intelligence assistant grounded in verified Candidate Records.")

        bot_full = chatbot.FitmentAssistant()

        # Render Full Chat History
        for idx, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    render_copy_actions(msg["content"], f"tab3_{idx}")

        full_chat_in = st.chat_input("Ask a question about candidate statuses, screening metrics, or follow-ups...", key="full_chat_input")
        if full_chat_in:
            st.session_state.chat_history.append({"role": "user", "content": full_chat_in})
            with st.chat_message("user"):
                st.markdown(full_chat_in)

            with st.spinner("Consulting Candidate Records..."):
                active_cid = st.session_state.get("active_candidate_id")
                res = bot_full.ask(full_chat_in, selected_candidate_id=active_cid)
                bot_ans = res["answer"]
                if res.get("candidate_id"):
                    st.session_state.active_candidate_id = res["candidate_id"]
                    cand_rec = registry.get_candidate_by_id(res["candidate_id"])
                    if cand_rec:
                        st.session_state.active_candidate_name = cand_rec["name"]

            st.session_state.chat_history.append({"role": "assistant", "content": bot_ans})
            st.rerun()

    # --------------------------------------------------------------------------
    # TAB 4: SETTINGS
    # --------------------------------------------------------------------------
    with tab_system:
        st.markdown("### ⚙️ Settings")
        st.caption("AI service configuration, availability probes, and system settings.")

        st.markdown("#### 🌐 AI Service Availability")
        active_provs = llm_manager.get_active_providers()
        if active_provs:
            for p in active_provs:
                st.markdown(f"- **{p['display_name']}** — Default Model: `{p['default_model']}` | Status: *{p['free_tier_status']}*")
        else:
            st.info("No external AI service keys detected in `.env`. The portal operates 100% reliably in InstantFit Offline Screening mode.")

        st.markdown("---")
        st.markdown("#### 🧪 AI Service Connectivity Probe")
        test_p_col1, test_p_col2 = st.columns(2)
        with test_p_col1:
            test_provider_id = st.selectbox("Select AI Service to Test", options=["gemini", "openrouter", "nvidia", "groq"])
        with test_p_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Run Connectivity Probe", use_container_width=True):
                with st.spinner(f"Testing {test_provider_id}..."):
                    ok, msg = llm_manager.validate_provider_health(test_provider_id, timeout_seconds=10.0)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ AI Service Temporarily Unavailable: {msg}")

        st.markdown("---")
        st.markdown("#### 🔒 Candidate Privacy & Fairness Notice")
        st.markdown(
            """
            - **InstantFit Screening Engine:** Numerical scores, matched skills, missing skills, and experience calculations are computed locally via objective pattern matching.
            - **Zero Data Leakage:** API keys are stored in `.env` or password-masked in memory and are never written to candidate records.
            - **Offline Availability:** If any external AI service is disconnected or rate-limited, the application automatically maintains 100% screening functionality.
            """
        )


# ==============================================================================
# RIGHT-SIDE FITMENT ASSISTANT CHATBOT PANEL (CLEAN WHITE CARD)
# ==============================================================================
with col_chat:
    st.markdown(
        """
        <div class="chat-companion-card">
            <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #D7E1F0; padding-bottom: 8px; margin-bottom: 10px;">
                <div>
                    <h3 style="margin: 0; color: #172033; font-size: 19px; font-weight: 800; letter-spacing: -0.4px;">🤖 Fitment Assistant</h3>
                    <p style="margin: 2px 0 0 0; color: #0891B2; font-size: 13px; font-weight: 600;">Your recruitment intelligence companion</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Active Candidate Context Indicator
    active_c_name = st.session_state.get("active_candidate_name")
    if active_c_name:
        st.caption(f"🎯 **Context:** Focused on `{active_c_name}`")

    # Header Action Buttons
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    with c_btn1:
        if st.button("＋ New Chat", help="Start a new conversation (resets active candidate context)", use_container_width=True):
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": "👋 New chat started. Ask me about any registered candidate, screening records, or pipeline follow-ups!",
                }
            ]
            st.session_state.chat_session_id = str(uuid.uuid4())[:8]
            st.session_state.active_candidate_id = None
            st.session_state.active_candidate_name = None
            st.rerun()
    with c_btn2:
        if st.button("↻ Refresh", help="Reload candidate data from registry", use_container_width=True):
            st.toast("✅ Candidate data refreshed from registry!")
            time.sleep(0.2)
            st.rerun()
    with c_btn3:
        if st.button("🗑️ Clear", help="Clear conversation messages", use_container_width=True):
            st.session_state.confirm_clear_chat = True

    if st.session_state.get("confirm_clear_chat"):
        st.warning("Clear conversation messages? Stored candidate records will not be deleted.")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Yes, Clear", key="confirm_clear_btn", type="primary", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.confirm_clear_chat = False
                st.rerun()
        with cc2:
            if st.button("Cancel", key="cancel_clear_btn", use_container_width=True):
                st.session_state.confirm_clear_chat = False
                st.rerun()

    # Suggested Question Chips (Global Portal-Wide Queries adhering to Section 9)
    with st.expander("💡 Suggested Questions", expanded=False):
        if st.button("📋 Show All Screened Candidates", use_container_width=True):
            st.session_state.chat_query_preset = "Show all screened candidates."
        if st.button("🔍 Find Candidate by Name", use_container_width=True):
            st.session_state.chat_query_preset = "What is Tarun's profile?"
        if st.button("⭐ Show Shortlisted Candidates", use_container_width=True):
            st.session_state.chat_query_preset = "Show shortlisted candidates."
        if st.button("📅 Show Today's Follow-ups", use_container_width=True):
            st.session_state.chat_query_preset = "Which candidate follow-ups are due?"
        if st.button("⚖️ Compare Candidate Screening Results", use_container_width=True):
            st.session_state.chat_query_preset = "Show all roles for which Shubhangi has been screened."
        if st.button("🎤 Generate Interview Questions", use_container_width=True):
            st.session_state.chat_query_preset = "Generate interview questions for the selected candidate."

    # Scrollable Chat Container (Stable Height with light theme)
    chat_container = st.container(height=450)
    with chat_container:
        if not st.session_state.chat_history:
            st.info("Start a conversation by typing a question below.")
        for idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble-assistant">{msg["content"]}</div>', unsafe_allow_html=True)
                render_copy_actions(msg["content"], f"side_{idx}")

    # Chat Composer Form (Enter-to-send support)
    preset_q = st.session_state.pop("chat_query_preset", None)

    with st.form("sidebar_chat_form", clear_on_submit=True):
        chat_user_input = st.text_input(
            "Ask Fitment Assistant",
            value=preset_q if preset_q else "",
            placeholder="Type a question (e.g. What is Tarun's mobile number?)...",
            label_visibility="collapsed",
        )
        submit_chat = st.form_submit_button("Send Question ➔", use_container_width=True)

    # Handle preset trigger outside form or form submit
    final_query = chat_user_input.strip() if submit_chat and chat_user_input else (preset_q if preset_q else "")

    if final_query:
        st.session_state.chat_history.append({"role": "user", "content": final_query})

        bot_engine = chatbot.FitmentAssistant()
        active_cid = st.session_state.get("active_candidate_id")

        try:
            with st.spinner("Consulting candidate registry..."):
                reply = bot_engine.ask(final_query, selected_candidate_id=active_cid)
                bot_response = reply["answer"]
                if reply.get("candidate_id"):
                    st.session_state.active_candidate_id = reply["candidate_id"]
                    cand_rec = registry.get_candidate_by_id(reply["candidate_id"])
                    if cand_rec:
                        st.session_state.active_candidate_name = cand_rec["name"]
        except Exception as query_err:
            bot_response = f"⚠️ Could not complete query: {query_err}. Please retry."

        st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
        st.rerun()
