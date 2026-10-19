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
import importlib

import parser
import deterministic_engine
import registry
import chatbot
import llm_manager
import storage

# Safeguard: in long-running or reloaded Streamlit sessions, ensure modules reflect latest disk exports
if not hasattr(deterministic_engine, "analyze_skill_gaps"):
    deterministic_engine = importlib.reload(deterministic_engine)
if not hasattr(registry, "get_current_ist_str") or not hasattr(registry, "format_last_screened"):
    registry = importlib.reload(registry)
if not hasattr(parser, "extract_candidate_metadata_hybrid"):
    parser = importlib.reload(parser)

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    :root {
        --navy: #10234E;
        --blue-primary: #2164F3;
        --blue-hover: #1D4ED8;
        --blue-light: #EBF3FE;
        --cyan-accent: #06A6C8;
        --bg-canvas: #F8FAFC;
        --card-bg: #FFFFFF;
        --card-border: #DCE7F8;
        --subtle-border: #E2E8F0;
        --text-slate: #64748B;
        --success: #16A765;
        --success-bg: #DCFCE7;
        --warning: #EA580C;
        --warning-bg: #FEF3C7;
        --purple: #7C4DFF;
        --purple-bg: #F3E8FF;
        --red: #E5484D;
        --red-bg: #FEE2E2;
    }

    html, body, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
        background-color: #F8FAFC !important;
        color: #10234E !important;
    }

    /* ELIMINATE STREAMLIT CHROME OVERHEAD & RESTRICT TO DESKTOP VIEWPORT SCALE */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        min-height: 2.2rem !important;
        height: auto !important;
        z-index: 99999 !important;
        overflow: visible !important;
    }
    [data-testid="stToolbar"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: transparent !important;
        height: auto !important;
        width: auto !important;
        overflow: visible !important;
    }
    .stDeployButton,
    [data-testid="stToolbarActions"],
    [data-testid="stAppDeployButton"],
    #MainMenu,
    footer {
        display: none !important;
    }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stExpandSidebarButton"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
    }
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stExpandSidebarButton"] {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(16, 35, 78, 0.12) !important;
        color: #2164F3 !important;
    }
    .block-container {
        max-width: 100% !important;
        margin: 0 auto !important;
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        box-sizing: border-box !important;
    }
    [data-testid="column"] {
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    /* CUSTOM ACTION BUTTONS MATCHING SCREENSHOT B (VIEW FULL PROFILE & VIEW DETAILED ANALYSIS) */
    div[data-testid="stButton"] button[key="btn_view_full_profile"],
    div[data-testid="stButton"] button[key="btn_view_detailed_analysis"] {
        background: #EFF6FF !important;
        border: 1px solid #BFDBFE !important;
        color: #2164F3 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        height: 34px !important;
        padding: 4px 12px !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stButton"] button[key="btn_view_full_profile"]:hover,
    div[data-testid="stButton"] button[key="btn_view_detailed_analysis"]:hover {
        background: #DBEAFE !important;
        border-color: #93C5FD !important;
        color: #1D4ED8 !important;
    }

    /* DETAILED COMPETENCY BREAKDOWN TAB NAVIGATION */
    [data-testid="stButtonGroup"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        overflow: visible !important;
        width: 100% !important;
        margin-top: 2px !important;
        margin-bottom: 18px !important;
    }
    [data-testid="stButtonGroup"] button {
        display: inline-flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        white-space: nowrap !important;
        flex: 0 1 auto !important;
        border-radius: 9px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        padding: 7px 14px !important;
        border: 1px solid #CBD5E1 !important;
        background: #FFFFFF !important;
        color: #10234E !important;
        box-shadow: 0 1px 2px rgba(16, 35, 78, 0.04) !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stButtonGroup"] button div {
        display: inline-flex !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stButtonGroup"] button p {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: inherit !important;
    }
    [data-testid="stButtonGroup"] button:hover {
        border-color: #2164F3 !important;
        color: #2164F3 !important;
        background: #F0F7FF !important;
    }
    [data-testid="stButtonGroup"] button[aria-checked="true"],
    [data-testid="stButtonGroup"] button[data-selected="true"] {
        background: #2164F3 !important;
        color: #FFFFFF !important;
        border-color: #2164F3 !important;
        box-shadow: 0 2px 8px rgba(33, 100, 243, 0.28) !important;
        font-weight: 700 !important;
    }
    [data-testid="stButtonGroup"] button[aria-checked="true"] p,
    [data-testid="stButtonGroup"] button[data-selected="true"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* TYPOGRAPHY HIERARCHY */
    h1, h2, h3, h4 {
        color: #10234E !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: -0.3px !important;
    }
    p, label, button, input, select, textarea {
        font-family: 'Inter', sans-serif !important;
    }

    /* PROTECT STREAMLIT ICONS FROM FONT OVERRIDES */
    [data-testid="stIconMaterial"],
    .material-symbols-rounded,
    .material-symbols-outlined,
    [class*="material-symbols"],
    [data-testid*="Icon"] {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
        font-weight: normal;
        font-style: normal;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
    }

    /* TOP HEADER BAR */
    .header-logo-brand {
        font-size: 23px;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.1;
        display: inline-flex;
        align-items: center;
    }
    .header-logo-navy {
        color: #10234E;
    }
    .header-logo-blue {
        color: #2164F3;
    }
    .header-divider-line {
        width: 1px;
        height: 32px;
        background-color: #E2E8F0;
        margin: 0 14px;
        display: inline-block;
        vertical-align: middle;
    }
    .header-titles-stack {
        display: inline-block;
        vertical-align: middle;
        line-height: 1.2;
    }
    .header-main-title {
        font-size: 15px;
        font-weight: 700;
        color: #10234E;
        display: block;
    }
    .header-sub-title {
        font-size: 11.5px;
        font-weight: 500;
        color: #64748B;
        display: block;
    }

    .header-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 12.5px;
        font-weight: 600;
        color: #334155;
        white-space: nowrap !important;
        box-shadow: 0 1px 2px rgba(16, 35, 78, 0.03);
    }

    .recruiter-chip-target {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 5px 12px;
        border-radius: 9999px;
        box-shadow: 0 1px 3px rgba(16, 35, 78, 0.04);
        margin-left: auto;
    }
    .recruiter-avatar-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #2563EB;
        color: #FFFFFF;
        font-weight: 800;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .recruiter-text-stack {
        display: flex;
        flex-direction: column;
        line-height: 1.15;
    }
    .recruiter-name-text {
        font-weight: 700;
        font-size: 13px;
        color: #10234E;
    }
    .recruiter-role-text {
        font-weight: 500;
        font-size: 11px;
        color: #64748B;
    }

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        min-width: 260px !important;
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        gap: 4px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin: 0 !important;
        width: 100% !important;
        color: #475569 !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        background: #F1F5F9 !important;
        color: #2164F3 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] {
        background: #EBF3FE !important;
        color: #2164F3 !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child {
        display: none !important;
    }

    .sidebar-ai-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
        margin-top: 10px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 1px 3px rgba(16, 35, 78, 0.03) !important;
    }

    .sidebar-stats-card-box {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 14px 16px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 1px 3px rgba(16, 35, 78, 0.03) !important;
    }
    .stat-row-target {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 5px 0;
    }
    .stat-row-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .stat-icon-square {
        width: 28px;
        height: 28px;
        border-radius: 7px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
    }

    /* CENTER DASHBOARD: WELCOME BANNER */
    .welcome-banner-target {
        background: #EEF4FD !important;
        border: 1px solid #DCE7F8 !important;
        border-radius: 14px !important;
        padding: 20px 24px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        margin-bottom: 16px !important;
        box-shadow: 0 2px 6px rgba(33, 100, 243, 0.04) !important;
    }
    .welcome-title-target {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #10234E !important;
        margin: 0 0 4px 0 !important;
        letter-spacing: -0.3px !important;
    }
    .welcome-sub-target {
        font-size: 13.5px !important;
        color: #64748B !important;
        margin: 0 !important;
        font-weight: 500 !important;
    }
    .welcome-clock-pill {
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        margin-top: 8px !important;
        background: #FFFFFF !important;
        border: 1px solid #D9E5F7 !important;
        border-radius: 20px !important;
        padding: 3px 10px !important;
        box-shadow: 0 1px 3px rgba(33, 100, 243, 0.06) !important;
    }
    .activity-summary-card-target {
        background: #FFFFFF !important;
        border: 1px solid #DCE7F8 !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
        box-shadow: 0 1px 4px rgba(16, 35, 78, 0.03) !important;
    }
    .activity-header-label {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: #10234E !important;
        margin-bottom: 6px !important;
        letter-spacing: 0.2px !important;
        text-align: left !important;
    }
    .activity-flex-row {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 14px !important;
    }
    .activity-col-item {
        text-align: center !important;
        min-width: 44px !important;
    }
    .activity-val-num {
        font-size: 20px !important;
        font-weight: 800 !important;
        display: block !important;
        line-height: 1.1 !important;
    }
    .activity-lbl-text {
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #64748B !important;
        display: block !important;
        margin-top: 2px !important;
    }
    .activity-vdivider {
        width: 1px !important;
        height: 28px !important;
        background: #E2E8F0 !important;
    }
    
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] {
        white-space: nowrap !important;
    }
    button[key="reuse_jd_toggle_btn"],
    button[key="reuse_cv_toggle_btn"] {
        padding: 4px 8px !important;
        min-height: 32px !important;
    }
    button[key="reuse_jd_toggle_btn"] p,
    button[key="reuse_cv_toggle_btn"] p {
        font-size: 11.5px !important;
        white-space: nowrap !important;
    }
    .trash-icon-btn button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 16px !important;
        padding: 4px !important;
        color: #94A3B8 !important;
    }
    .trash-icon-btn button:hover {
        color: #EF4444 !important;
        background: #FEE2E2 !important;
    }
    .recent-select-btn button {
        background: #FFFFFF !important;
        border: 1px solid #BFDBFE !important;
        color: #2164F3 !important;
        font-size: 11px !important;
        padding: 2px 8px !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px rgba(33, 100, 243, 0.05) !important;
    }
    .recent-select-btn button:hover {
        background: #EFF6FF !important;
        border-color: #2164F3 !important;
    }

    /* UPLOAD PANELS (01 JD & 02 RESUME) */
    .upload-panel-card-target {
        background: #FFFFFF !important;
        border: 1px solid #DCE7F8 !important;
        border-radius: 12px !important;
        padding: 16px 18px !important;
        box-shadow: 0 2px 6px rgba(16, 35, 78, 0.03) !important;
        margin-bottom: 8px !important;
    }
    .panel-header-target {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .panel-header-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .panel-icon-badge {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }
    .panel-title-text {
        color: #10234E !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    .panel-desc-text {
        color: #64748B !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    .dropzone-target {
        border: 1.5px dashed #BFDBFE;
        background: #F8FAFC;
        border-radius: 10px;
        padding: 22px 14px;
        text-align: center;
        transition: all 0.15s ease;
    }
    .dropzone-target:hover {
        border-color: #2164F3;
        background: #EFF6FF;
    }
    .file-chip-saved {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        min-width: 0;
        width: 100%;
        box-sizing: border-box;
    }

    /* SCREENING BUTTONS */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(90deg, #2164F3 0%, #06A6C8 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 14.5px !important;
        height: 46px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(33, 100, 243, 0.22) !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        box-shadow: 0 6px 16px rgba(33, 100, 243, 0.32) !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background: #FFFFFF !important;
        border: 1.5px solid #2164F3 !important;
        color: #2164F3 !important;
        font-weight: 700 !important;
        font-size: 14.5px !important;
        height: 46px !important;
        border-radius: 10px !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: #EFF6FF !important;
        border-color: #1D4ED8 !important;
        color: #1D4ED8 !important;
    }

    /* CANDIDATE SUMMARY CARD */
    .candidate-summary-card-target {
        background: #FFFFFF !important;
        border: 1px solid #DCE7F8 !important;
        border-radius: 14px !important;
        padding: 18px 22px !important;
        box-shadow: 0 2px 8px rgba(16, 35, 78, 0.04) !important;
        margin-top: 14px !important;
        margin-bottom: 14px !important;
    }
    .candidate-avatar-large {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: #EEF2FF;
        color: #2164F3;
        font-size: 22px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }
    .avatar-check-badge {
        position: absolute;
        bottom: 0;
        right: 0;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: #16A765;
        color: #FFFFFF;
        font-size: 11px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #FFFFFF;
    }

    /* FITMENT RESULTS CARD */
    .fitment-results-card-target {
        background: #FFFFFF !important;
        border: 1px solid #DCE7F8 !important;
        border-radius: 14px !important;
        padding: 18px 22px !important;
        box-shadow: 0 2px 8px rgba(16, 35, 78, 0.04) !important;
        margin-bottom: 16px !important;
    }
    .metric-tile-target {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 14px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .metric-tile-icon-box {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }
    .analytics-panel-subcard {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 16px;
        height: 100%;
    }

    /* RIGHT COLUMN: FITMENT ASSISTANT */
    .assistant-card-target {
        background: #FFFFFF !important;
        border: 1px solid #DCE7F8 !important;
        border-radius: 14px !important;
        padding: 16px 18px !important;
        box-shadow: 0 2px 8px rgba(16, 35, 78, 0.04) !important;
        margin-bottom: 14px !important;
        min-width: 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .bot-avatar-circle-target {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #1E293B;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }
    .chat-bubble-user {
        background: #F3E8FF !important;
        border: 1px solid #E9D5FF !important;
        border-radius: 12px 12px 2px 12px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        color: #10234E !important;
        font-size: 13.5px !important;
    }
    .chat-bubble-assistant {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px 12px 12px 2px !important;
        padding: 12px 16px !important;
        margin-bottom: 6px !important;
        color: #10234E !important;
        font-size: 13.5px !important;
        line-height: 1.55 !important;
        box-shadow: 0 1px 3px rgba(16, 35, 78, 0.02) !important;
    }

    /* RECENTLY VIEWED CANDIDATES */
    .recent-cand-card-target {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(16, 35, 78, 0.02);
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.15s ease;
    }
    .recent-cand-card-target:hover {
        border-color: #2164F3;
        box-shadow: 0 2px 8px rgba(33, 100, 243, 0.08);
    }
    .recent-cand-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #EBF3FE;
        color: #2164F3;
        font-weight: 700;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* STATUS BADGES */
    .status-badge-blue {
        display: inline-flex;
        align-items: center;
        background: #EFF6FF !important;
        border: 1px solid #BFDBFE !important;
        color: #2164F3 !important;
        padding: 2px 10px !important;
        border-radius: 12px !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
    }
    .status-badge-green {
        display: inline-flex;
        align-items: center;
        background: #DCFCE7 !important;
        border: 1px solid #86EFAC !important;
        color: #16A765 !important;
        padding: 2px 10px !important;
        border-radius: 12px !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
    }
    .status-badge-violet {
        display: inline-flex;
        align-items: center;
        background: #F3E8FF !important;
        border: 1px solid #D8B4FE !important;
        color: #7C4DFF !important;
        padding: 2px 10px !important;
        border-radius: 12px !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
    }
    .status-badge-amber {
        display: inline-flex;
        align-items: center;
        background: #FEF3C7 !important;
        border: 1px solid #FCD34D !important;
        color: #B45309 !important;
        padding: 2px 10px !important;
        border-radius: 12px !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
    }
    .status-badge-red {
        display: inline-flex;
        align-items: center;
        background: #FEE2E2 !important;
        border: 1px solid #FCA5A5 !important;
        color: #E5484D !important;
        padding: 2px 10px !important;
        border-radius: 12px !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
    }

    /* STREAMLIT FORM INPUT RESTYLING */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #10234E !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        font-size: 13.5px !important;
    }
    .stTextInput input:focus {
        border-color: #2164F3 !important;
        box-shadow: 0 0 0 2px rgba(33, 100, 243, 0.15) !important;
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


def extract_concise_summary(content: str) -> str:
    """Derives a concise, readable summary from any assistant response (Phase 4)."""
    lines = [ln.strip() for ln in content.strip().splitlines() if ln.strip()]
    if not lines:
        return content[:250]

    # 1. Look for explicit summary, verdict, or conclusion section
    summary_lines = []
    in_summary = False
    for line in lines:
        lower = line.lower()
        if any(k in lower for k in ["summary", "verdict", "recommendation:", "key takeaway", "conclusion"]):
            in_summary = True
            summary_lines.append(line)
        elif in_summary:
            if line.startswith("#"):
                in_summary = False
            else:
                summary_lines.append(line)
    if summary_lines and len(summary_lines) >= 2:
        return "\n".join(summary_lines[:5]).strip()

    # 2. Extract bullet points if available
    bullets = [ln for ln in lines if ln.startswith(("-", "*", "•", "1.", "2.", "3.", "4.", "5."))]
    if bullets and len(bullets) >= 2:
        return "\n".join(bullets[:4]).strip()

    # 3. First 2-3 sentences up to 260 chars
    plain = " ".join([ln for ln in lines if not ln.startswith("#")])
    if len(plain) > 260:
        cutoff = plain[:260].rfind(". ")
        if cutoff > 80:
            return plain[:cutoff + 1].strip()
        return plain[:260].strip() + "..."
    return plain


def render_copy_actions(content: str, key_suffix: str):
    """Renders plain-text Copy Response button, Copy as Summary, plus optional contextual copy buttons."""
    clean_text = content.strip()
    encoded_full = urllib.parse.quote(clean_text)
    concise_summary = extract_concise_summary(clean_text)
    encoded_summary = urllib.parse.quote(concise_summary)
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
            border: 1px solid #D9E5F7;
            color: #10234E;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            box-shadow: 0 1px 2px rgba(16,35,78,0.04);
            transition: all 0.15s ease;
            user-select: none;
        }}
        .copy-btn:hover {{
            background: #EDF3FC;
            border-color: #2164F3;
            color: #2164F3;
        }}
        .copy-btn-blue {{
            color: #2164F3;
            border-color: #D9E5F7;
            background: #F0F6FF;
        }}
        .copy-btn-cyan {{
            color: #06A6C8;
            border-color: #BAE6FD;
            background: #F0F9FF;
        }}
        .copy-btn-violet {{
            color: #7C4DFF;
            border-color: #DDD6FE;
            background: #F5F3FF;
        }}
        .copy-btn.copied {{
            background: #DCFCE7 !important;
            border-color: #86EFAC !important;
            color: #16A765 !important;
        }}
    </style>
    </head>
    <body>
    <div class="copy-btn-bar">
        <button id="btn_main_{key_suffix}" class="copy-btn" onclick="performCopy('{encoded_full}', 'btn_main_{key_suffix}', '📋 Copy Response')">
            📋 Copy Response
        </button>
        <button id="btn_sum_{key_suffix}" class="copy-btn copy-btn-blue" onclick="performCopy('{encoded_summary}', 'btn_sum_{key_suffix}', '🎯 Copy as Summary')">
            🎯 Copy as Summary
        </button>
    """

    if "candidate_details" in sections:
        enc_cd = urllib.parse.quote(sections["candidate_details"])
        buttons_html += f"""
        <button id="btn_cd_{key_suffix}" class="copy-btn copy-btn-cyan" onclick="performCopy('{enc_cd}', 'btn_cd_{key_suffix}', '📄 Copy Details')">
            📄 Copy Details
        </button>
        """

    if "interview_questions" in sections:
        enc_iq = urllib.parse.quote(sections["interview_questions"])
        buttons_html += f"""
        <button id="btn_iq_{key_suffix}" class="copy-btn copy-btn-violet" onclick="performCopy('{enc_iq}', 'btn_iq_{key_suffix}', '🎤 Copy Questions')">
            🎤 Copy Questions
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

    height = 38
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


def render_donut_chart(score: int) -> str:
    """Renders a clean SVG circular donut progress ring matching Screenshot B."""
    circ = 175.93  # 2 * pi * 28
    fill_len = max(0.0, min(100.0, float(score))) / 100.0 * circ
    dash_len = circ - fill_len
    return f"""<svg width="68" height="68" viewBox="0 0 68 68" style="transform: rotate(-90deg); display: block;">
        <circle cx="34" cy="34" r="28" fill="none" stroke="#FED7AA" stroke-width="6" />
        <circle cx="34" cy="34" r="28" fill="none" stroke="#EA580C" stroke-width="6"
                stroke-dasharray="{fill_len:.1f} {dash_len:.1f}" stroke-linecap="round" />
    </svg>"""


def get_initials(name: str) -> str:
    """Derives 2-letter uppercase initials for candidate avatar."""
    if not name:
        return "CA"
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper()


def get_relative_time_str(ts_str: Optional[str]) -> str:
    """Formats timestamp into relative human-readable string like '2 mins ago'."""
    if not ts_str:
        return "recently"
    try:
        clean_ts = ts_str.split(".")[0].replace("Z", "")
        dt = datetime.fromisoformat(clean_ts)
        diff = datetime.now() - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = max(1, seconds // 60)
            return f"{mins} mins ago" if mins > 1 else "1 min ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hours ago" if hours > 1 else "1 hour ago"
        else:
            days = seconds // 86400
            return f"{days} days ago" if days > 1 else "1 day ago"
    except Exception:
        return "recently"


def render_welcome_illustration() -> str:
    """Renders inline SVG vector recruitment illustration matching Screenshot B."""
    return """<svg width="96" height="74" viewBox="0 0 96 74" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="48" cy="37" r="32" fill="#DCE9FD"/>
        <rect x="26" y="16" width="40" height="44" rx="6" fill="#2164F3"/>
        <circle cx="46" cy="28" r="6" fill="#FFFFFF"/>
        <path d="M36 44C36 38.5 40.5 36 46 36C51.5 36 56 38.5 56 44" fill="#FFFFFF"/>
        <rect x="32" y="48" width="28" height="3" rx="1.5" fill="#BFDBFE"/>
        <circle cx="68" cy="42" r="13" fill="#06A6C8" fill-opacity="0.25" stroke="#06A6C8" stroke-width="2.5"/>
        <line x1="77" y1="51" x2="88" y2="62" stroke="#06A6C8" stroke-width="3" stroke-linecap="round"/>
        <path d="M64 42L67 45L73 39" stroke="#06A6C8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>"""


def get_current_ist_str() -> str:
    """Returns dynamic current date and time formatted in IST: '19 Oct 2026 | 08:58:00 IST (UTC+05:30)'."""
    if hasattr(registry, "get_current_ist_str"):
        return registry.get_current_ist_str()
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y | %H:%M:%S IST (UTC+05:30)")


def format_last_screened(timestamp_str: Optional[str]) -> str:
    """Formats candidate screening timestamp for display in IST: 'Last screened: 19 Oct 2026, 08:42:15 IST' or 'Not screened yet'."""
    if hasattr(registry, "format_last_screened"):
        return registry.format_last_screened(timestamp_str)
    if not timestamp_str or not str(timestamp_str).strip():
        return "Not screened yet"
    from zoneinfo import ZoneInfo
    try:
        clean_str = str(timestamp_str).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        ist = ZoneInfo("Asia/Kolkata")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ist)
        else:
            dt = dt.astimezone(ist)
        return f"Last screened: {dt.strftime('%d %b %Y, %H:%M:%S IST')}"
    except Exception:
        return "Not screened yet"


def render_welcome_banner():
    """Renders dynamic Welcome Banner with live IST clock and today's verified activity metrics."""
    latest_analytics = registry.get_dashboard_analytics_summary()
    current_ist_str = get_current_ist_str()
    render_html(
        f"""
        <div class="welcome-banner-target">
            <div class="welcome-left-col">
                <h2 class="welcome-title-target">Welcome back, Bharat!</h2>
                <p class="welcome-sub-target">Screen candidates, track progress, and get AI-powered insights.</p>
                <div class="welcome-clock-pill">
                    <span style="font-size: 13px;">🕒</span>
                    <span style="font-weight: 700; color: #10234E; font-size: 11.5px; letter-spacing: 0.1px;">{current_ist_str}</span>
                </div>
            </div>
            <div class="welcome-center-col">
                {render_welcome_illustration()}
            </div>
            <div class="welcome-right-col">
                <div class="activity-summary-card-target">
                    <div class="activity-header-label">Today's Activity</div>
                    <div class="activity-flex-row">
                        <div class="activity-col-item">
                            <span class="activity-val-num" style="color: #2164F3;">{latest_analytics['total_screened']}</span>
                            <span class="activity-lbl-text">Screened</span>
                        </div>
                        <div class="activity-vdivider"></div>
                        <div class="activity-col-item">
                            <span class="activity-val-num" style="color: #16A765;">{latest_analytics['shortlisted_count']}</span>
                            <span class="activity-lbl-text">Shortlisted</span>
                        </div>
                        <div class="activity-vdivider"></div>
                        <div class="activity-col-item">
                            <span class="activity-val-num" style="color: #7C4DFF;">{latest_analytics['interviews_scheduled_count']}</span>
                            <span class="activity-lbl-text">Interview</span>
                        </div>
                        <div class="activity-vdivider"></div>
                        <div class="activity-col-item">
                            <span class="activity-val-num" style="color: #06A6C8;">{latest_analytics['joined_count']}</span>
                            <span class="activity-lbl-text">Joined</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    )


if hasattr(st, "fragment"):
    render_welcome_banner = st.fragment(run_every="5s")(render_welcome_banner)


def render_html(raw_html: str) -> None:
    """Safely render HTML in Streamlit.
    Strips leading and trailing whitespace from each line so the CommonMark
    markdown parser never mistakes 4-space indentation following blank lines
    as indented code blocks (<pre><code>).
    """
    clean_lines = [line.strip() for line in raw_html.splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)


@st.dialog("👤 Candidate Full Profile & Recruitment Dossier")
def show_full_candidate_profile_dialog(active_rec: dict):
    """Renders comprehensive candidate profile and recruitment dossier modal."""
    meta = active_rec.get("meta", {})
    det = active_rec.get("det_result", {})
    score = det.get("match_score", 0)
    cand_id = active_rec.get("candidate_id")
    job_title = active_rec.get("job_title", "Target Technical Role")
    found_certs = active_rec.get("found_certs") or det.get("certifications_detected") or meta.get("certifications") or []

    cand_db = registry.get_candidate_by_id(cand_id) if cand_id else None
    cur_status = cand_db.get("current_status", "Screened") if cand_db else "Screened"
    cand_last_ts = active_rec.get("screening_timestamp") or (registry.get_candidate_last_screened_timestamp(cand_id) if cand_id else None)
    cand_last_screened_str = format_last_screened(cand_last_ts)

    st.markdown(
        f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; color: #10234E; font-size: 18px; font-weight: 800;">{html.escape(meta.get('name', 'Candidate'))}</h3>
                    <p style="margin: 2px 0 0 0; color: #64748B; font-size: 13px;">{html.escape(meta.get('current_designation', 'Not Detected'))} • {html.escape(meta.get('organization', 'Not Detected'))} • <span style="color: #2164F3; font-weight: 600;">{cand_last_screened_str}</span></p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 11px; color: #64748B; font-weight: 700;">FITMENT SCORE</div>
                    <div style="font-size: 20px; font-weight: 900; color: #EA580C;">{score} <span style="font-size: 13px; color: #64748B; font-weight: 600;">/ 100</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t1, t2, t3 = st.tabs(["📋 Profile & Experience", "🎯 Fitment & Skills", "📝 Lifecycle Status"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"- **Target Role:** {job_title}")
            st.markdown(f"- **Total Experience:** {meta.get('total_exp', 'Not Detected')}")
            st.markdown(f"- **Relevant Experience:** {meta.get('relevant_exp', 'Not Detected')}")
            st.markdown(f"- **Location:** {meta.get('location', 'Not Specified')}")
            st.markdown(f"- **Screening History:** {cand_last_screened_str}")
        with c2:
            raw_mob = meta.get('mobile', '+91 91457 *****')
            masked_mob = re.sub(r'(\+?\d{2,4}\s?\d{2,3})\d{4,5}', r'\1*****', raw_mob) if raw_mob else '+91 91457 *****'
            st.markdown(f"- **Contact:** `{masked_mob}`")
            st.markdown(f"- **Email:** `{meta.get('email', 'Confidential')}`")
            st.markdown(f"- **Education:** {meta.get('education', 'Not Specified')}")
            st.markdown(f"- **Resume Ref:** `{html.escape(st.session_state.get('last_parsed_cv_name') or 'Candidate_CV.pdf')}`")

        prev_orgs = meta.get("previous_organizations", [])
        if prev_orgs:
            st.markdown(f"**Previous Organizations:** {', '.join(prev_orgs)}")

        if found_certs:
            st.markdown(f"**Accreditations & Certifications:** {', '.join(found_certs)}")

    with t2:
        st.markdown(f"- **Deterministic Verdict:** **{det.get('verdict', 'N/A')}**")
        st.markdown(f"- **Recruiter Recommendation:** {det.get('recommendation', 'N/A')}")
        st.markdown(f"- **Skills Alignment:** {active_rec.get('skills_score', 0)}%")
        st.markdown(f"- **Experience Alignment:** {active_rec.get('exp_score', 0)}%")
        st.markdown(f"- **Accreditation Alignment:** {active_rec.get('cert_score', 0)}%")
        if det.get("skills_matched"):
            st.markdown(f"**Matched Skills:** {', '.join(det['skills_matched'])}")
        if det.get("missing_skills"):
            st.markdown(f"**Missing Skills:** {', '.join(det['missing_skills'][:15])}")

    with t3:
        st.markdown("##### Update Recruitment Stage")
        cur_idx = registry.CANDIDATE_STATUSES.index(cur_status) if cur_status in registry.CANDIDATE_STATUSES else 1
        new_st = st.selectbox("Stage", options=registry.CANDIDATE_STATUSES, index=cur_idx, key=f"dlg_status_{cand_id}")
        dlg_note = st.text_input("Recruiter Note", key=f"dlg_notes_{cand_id}", placeholder="Status notes...")
        if st.button("Save Lifecycle Status", key=f"dlg_save_{cand_id}", type="primary", use_container_width=True):
            if cand_id:
                registry.update_candidate_status(cand_id, new_st, notes=dlg_note, changed_by="Bharat Raparthy")
                st.success(f"Updated status to {new_st}!")
                time.sleep(0.3)
                st.rerun()

    st.markdown("---")
    if st.button("📋 Open in Candidate Tracker", key="dlg_open_tracker_btn", use_container_width=True):
        st.session_state.pending_nav = "📋 Candidate Tracker"
        st.session_state.tracker_reset_filters = True
        st.rerun()


# --- LOAD REAL DASHBOARD ANALYTICS (ZERO MOCK DATA) ---
if not hasattr(registry, "get_current_ist_str") or not hasattr(registry, "format_last_screened"):
    import importlib
    registry = importlib.reload(registry)

analytics = registry.get_dashboard_analytics_summary()

# --- SIDEBAR CONFIGURATION (RECRUITER-FACING NAVIGATION & AI SETTINGS) ---
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 6px 4px 14px 4px; border-bottom: 1px solid #D9E5F7; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="background: linear-gradient(135deg, #2164F3 0%, #06A6C8 100%); color: #FFFFFF; font-weight: 800; font-size: 15px; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(33, 100, 243, 0.3);">
                    FA
                </div>
                <div>
                    <span style="font-weight: 800; font-size: 16px; color: #10234E; letter-spacing: -0.3px; display: block; line-height: 1.2;">FITMENT.AI</span>
                    <span style="font-size: 11.5px; color: #536789; font-weight: 600;">Enterprise Platform</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Left Navigation
    st.markdown("<p style='font-size: 11px; text-transform: uppercase; font-weight: 700; color: #536789; margin: 0 0 6px 8px; letter-spacing: 0.5px;'>Navigation</p>", unsafe_allow_html=True)

    # Safe navigation: apply and clear pending navigation before creating the radio widget
    if st.session_state.get("pending_nav"):
        target_nav = st.session_state.pop("pending_nav")
        st.session_state.sidebar_nav_radio = target_nav
        st.session_state.selected_nav = target_nav

    if "selected_nav" not in st.session_state:
        st.session_state.selected_nav = "🏠 Screening Dashboard"

    nav_options = [
        "🏠 Screening Dashboard",
        "📋 Candidate Tracker",
        "🤖 Fitment Assistant",
        "⚙️ Settings",
    ]
    cur_nav_idx = nav_options.index(st.session_state.selected_nav) if st.session_state.selected_nav in nav_options else 0
    chosen_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=cur_nav_idx,
        label_visibility="collapsed",
        key="sidebar_nav_radio",
    )
    st.session_state.selected_nav = chosen_nav

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 2. AI Configuration & Provider Selection
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
        user_api_key = os.getenv("GEMINI_API_KEY", "")
        selected_model = "gemini-3.5-flash-lite"
    elif p_id == "openrouter":
        user_api_key = os.getenv("OPENROUTER_API_KEY", "")
        selected_model = "google/gemma-4-26b-a4b-it:free"
    elif p_id == "nvidia":
        user_api_key = os.getenv("NVIDIA_API_KEY", "")
        selected_model = "stepfun-ai/step-5-preview"

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
            provider_status_text = f"✨ AI Service: {selected_provider_ui.split('(')[0].strip()} | Model: {selected_model} | Status: Connected"
            provider_is_connected = True
        else:
            provider_status_text = "⚡ InstantFit Offline Screening | InstantFit Screening Active"
            provider_is_connected = False
    else:
        provider_status_text = "⚡ InstantFit Offline Screening | InstantFit Screening Active"
        provider_is_connected = False

    # AI Configuration Box
    st.markdown("<p style='font-size: 11px; text-transform: uppercase; font-weight: 700; color: #536789; margin: 12px 0 6px 8px; letter-spacing: 0.5px;'>AI Configuration</p>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sidebar-ai-card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 28px; height: 28px; border-radius: 6px; background: #2164F3; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800;">
                        G
                    </div>
                    <div>
                        <span style="font-size: 13px; font-weight: 700; color: #10234E; display: block; line-height: 1.2;">Google Gemini</span>
                        <span style="font-size: 11px; color: #64748B; font-weight: 500;">{selected_model if selected_model else 'Offline Engine'}</span>
                    </div>
                </div>
                <span style="color: #94A3B8; font-size: 14px; font-weight: 700;">›</span>
            </div>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 700; color: {'#16A765' if provider_is_connected else '#D97706'};">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: {'#16A765' if provider_is_connected else '#F59E0B'}; display: inline-block;"></span> {'Connected' if provider_is_connected else 'Offline'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("⚙️ Provider & Key Settings", expanded=False):
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

    # 3. Quick Stats Card (Calculated from Real SQLite Database)
    st.markdown("<p style='font-size: 11px; text-transform: uppercase; font-weight: 700; color: #536789; margin: 14px 0 6px 8px; letter-spacing: 0.5px;'>Quick Stats</p>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sidebar-stats-card-box">
            <div class="stat-row-target">
                <div class="stat-row-left">
                    <div class="stat-icon-square" style="background: #EFF6FF; color: #2164F3;">👤</div>
                    <span style="font-size: 13px; font-weight: 600; color: #475569;">Total Candidates</span>
                </div>
                <strong style="font-size: 15px; font-weight: 800; color: #10234E;">{analytics['total_candidates']}</strong>
            </div>
            <div class="stat-row-target">
                <div class="stat-row-left">
                    <div class="stat-icon-square" style="background: #DCFCE7; color: #16A765;">📋</div>
                    <span style="font-size: 13px; font-weight: 600; color: #475569;">Shortlisted</span>
                </div>
                <strong style="font-size: 15px; font-weight: 800; color: #10234E;">{analytics['shortlisted_count']}</strong>
            </div>
            <div class="stat-row-target">
                <div class="stat-row-left">
                    <div class="stat-icon-square" style="background: #FEE2E2; color: #E5484D;">⭕</div>
                    <span style="font-size: 13px; font-weight: 600; color: #475569;">In Review</span>
                </div>
                <strong style="font-size: 15px; font-weight: 800; color: #10234E;">{analytics['in_review_count']}</strong>
            </div>
            <div class="stat-row-target">
                <div class="stat-row-left">
                    <div class="stat-icon-square" style="background: #FEF3C7; color: #D97706;">📅</div>
                    <span style="font-size: 13px; font-weight: 600; color: #475569;">Interviews Scheduled</span>
                </div>
                <strong style="font-size: 15px; font-weight: 800; color: #10234E;">{analytics['interviews_scheduled_count']}</strong>
            </div>
            <div class="stat-row-target">
                <div class="stat-row-left">
                    <div class="stat-icon-square" style="background: #CCFBF1; color: #0D9488;">🤝</div>
                    <span style="font-size: 13px; font-weight: 600; color: #475569;">Selected</span>
                </div>
                <strong style="font-size: 15px; font-weight: 800; color: #10234E;">{analytics['joined_count']}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.caption("🔒 **Candidate Privacy:** Masked credentials are never stored in candidate records or logs.")


# --- TOP-LEVEL COMPACT HEADER MATCHING SCREENSHOT B ---
head_col1, head_col2, head_col3 = st.columns([31, 45, 24], vertical_alignment="center")
with head_col1:
    st.markdown(
        """
        <div style="display: flex; align-items: center;">
            <div class="header-logo-brand">
                <span class="header-logo-navy">FITMENT.</span><span class="header-logo-blue">AI</span>
            </div>
            <div class="header-divider-line"></div>
            <div class="header-titles-stack">
                <span class="header-main-title">Recruitment Intelligence Platform</span>
                <span class="header-sub-title">Candidate Fitment Screening Portal | AI-Assisted Recruitment Intelligence</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with head_col2:
    c_pill, c_search = st.columns([1.65, 1.15], vertical_alignment="center")
    with c_pill:
        st.markdown(
            f"""
            <div class="header-status-pill">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: {'#16A765' if provider_is_connected else '#F59E0B'}; display: inline-block;"></span>
                <span style="font-weight: 700; color: #10234E; font-size: 12px;">{selected_provider_ui.split('(')[0].strip()}</span>
                <span style="color: #94A3B8; font-size: 11px;">•</span>
                <span style="color: #64748B; font-size: 11px;">{selected_model if selected_model else 'Offline'}</span>
                <span style="color: {'#16A765' if provider_is_connected else '#D97706'}; font-weight: 700; font-size: 11px; margin-left: 2px;">{'✓ Connected' if provider_is_connected else '○ Offline'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_search:
        header_search = st.text_input(
            "Search",
            placeholder="🔍 Search candidates, roles or ask AI...",
            label_visibility="collapsed",
            key="header_search_box",
        )
        curr_search = header_search.strip() if header_search else ""
        last_search = st.session_state.get("last_processed_header_search", "")
        if curr_search and curr_search != last_search:
            st.session_state.last_processed_header_search = curr_search
            st.session_state.pending_chat_query = f"Find details for: {curr_search}"

with head_col3:
    hr1, hr2, hr3 = st.columns([1, 1, 2.3], vertical_alignment="center")
    with hr1:
        if st.button("↻ Refresh", key="top_refresh_btn", help="Refresh displayed state and candidate records", use_container_width=True):
            st.toast("✅ Portal refreshed — candidate records up to date.")
            time.sleep(0.15)
            st.rerun()
    with hr2:
        if st.button("⚙️ Settings", key="top_settings_btn", help="AI service configuration & connectivity", use_container_width=True):
            st.session_state.pending_nav = "⚙️ Settings"
            st.rerun()
    with hr3:
        st.markdown(
            """
            <div class="recruiter-chip-target">
                <div class="recruiter-avatar-circle">BR</div>
                <div class="recruiter-text-stack">
                    <span class="recruiter-name-text">Bharat Raparthy</span>
                    <span class="recruiter-role-text">Recruiter</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- CHATBOT SESSION STATE INITIALIZATION ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I am the **Fitment Assistant**.\n\n"
                "I answer factual candidate queries, check fitment scores, look up missing skills, "
                "and provide technical or general recruitment intelligence.\n\n"
                "Ask me about any candidate or general technical topic!"
            ),
        }
    ]
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())[:8]

# --- TOP LEVEL WORKSPACE & CHATBOT TWO-COLUMN LAYOUT ---
# Central workspace ~64% width, right chatbot panel ~36% width
col_workspace, col_chat = st.columns([64, 36], gap="medium")

# ==============================================================================
# MAIN WORKSPACE (LEFT COLUMN)
# ==============================================================================
with col_workspace:
    # --------------------------------------------------------------------------
    # VIEW 1: SCREENING DASHBOARD
    # --------------------------------------------------------------------------
    if chosen_nav == "🏠 Screening Dashboard":
        # Clean session state initialization: Workspace starts completely empty without default JD or CV
        if "workspace_initialized" not in st.session_state:
            st.session_state.workspace_initialized = True
            st.session_state.jd_text_val = ""
            st.session_state.last_parsed_jd_name = None
            st.session_state.cv_text_val = ""
            st.session_state.last_parsed_cv_name = None
            st.session_state.active_screening_record = None
            st.session_state.active_candidate_id = None
            st.session_state.active_candidate_name = None
            st.session_state.pending_candidate_meta = None

        if "jd_text_val" not in st.session_state:
            st.session_state.jd_text_val = ""
        if "cv_text_val" not in st.session_state:
            st.session_state.cv_text_val = ""
        if "active_screening_record" not in st.session_state:
            st.session_state.active_screening_record = None

        # Welcome Banner with real activity counts and live IST clock (Pixel-Faithful to Screenshot B)
        render_welcome_banner()

        # --- TWO CONTENT-DRIVEN PANELS (MATCHING SCREENSHOT B) ---
        col_p1, col_p2 = st.columns(2, gap="medium")

        # PANEL 1: JOB DESCRIPTION
        with col_p1:
            uploaded_jd = None
            if "flash_jd_notification" in st.session_state:
                n_lvl, n_msg = st.session_state.pop("flash_jd_notification")
                if n_lvl == "success":
                    st.success(n_msg)
                else:
                    st.error(n_msg)

            h_c1, h_c2 = st.columns([1.85, 2.15], vertical_alignment="center")
            with h_c1:
                render_html(
                    """
                    <div class="panel-header-left">
                        <div class="panel-icon-badge" style="background: #EFF6FF; color: #2164F3;">📄</div>
                        <div>
                            <h3 class="panel-title-text">01 — Job Description</h3>
                            <p class="panel-desc-text">Upload or select target role specifications.</p>
                        </div>
                    </div>
                    """
                )
            with h_c2:
                load_jd_clicked = st.button("📂 Load JD", key="load_jd_toggle_btn", use_container_width=True)
                if load_jd_clicked:
                    st.session_state.show_load_jd_expander = not st.session_state.get("show_load_jd_expander", False)

            if st.session_state.get("show_load_jd_expander"):
                saved_jds = storage.list_saved_job_descriptions()
                if saved_jds:
                    jd_choices = {f"{j['original_filename']} ({str(j.get('upload_timestamp') or j.get('uploaded_at') or '')[:10]}) [ID:{str(j.get('file_id') or '')[:8]}]": j for j in saved_jds}
                    sel_saved_jd_key = st.selectbox("Select saved JD", options=["-- Select a JD to load --"] + list(jd_choices.keys()), key="sel_saved_jd_opt")
                    if sel_saved_jd_key != "-- Select a JD to load --":
                        chosen_jd = jd_choices[sel_saved_jd_key]
                        lj_c1, lj_c2 = st.columns([1.6, 1.4], vertical_alignment="center")
                        with lj_c1:
                            if st.button("Load Selected JD", key="load_saved_jd_act_btn", type="primary", use_container_width=True):
                                try:
                                    stored_p = chosen_jd.get("stored_path") or chosen_jd.get("stored_relative_path")
                                    if stored_p:
                                        raw_bytes = storage.read_stored_file_bytes(stored_p)
                                        extracted_jd, _ = parser.extract_text_from_file(raw_bytes, chosen_jd["original_filename"])
                                        if extracted_jd and extracted_jd.strip():
                                            st.session_state.jd_text_val = extracted_jd
                                            st.session_state.last_parsed_jd_name = chosen_jd["original_filename"]
                                            st.session_state.active_jd_file_id = chosen_jd.get("file_id")
                                            st.session_state.active_jd_file_path = stored_p
                                            st.session_state.jd_file_size_kb = round(len(raw_bytes) / 1024, 1)
                                            st.session_state.flash_jd_notification = ("success", f"Loaded JD: {chosen_jd['original_filename']} successfully.")
                                            st.session_state.active_screening_record = None
                                            st.session_state.show_load_jd_expander = False
                                            st.rerun()
                                        else:
                                            st.error(f"Saved JD '{chosen_jd['original_filename']}' contains no readable text.")
                                    else:
                                        st.error("Saved JD file path could not be resolved.")
                                except Exception as err:
                                    st.session_state.flash_jd_notification = ("error", f"Error loading JD: {err}")
                                    st.rerun()
                        with lj_c2:
                            confirm_del = st.checkbox("Confirm delete", key=f"conf_del_jd_{chosen_jd['file_id']}")
                            if confirm_del:
                                if st.button("🗑️ Delete", key="del_saved_jd_act_btn", help="Permanently delete this saved JD from storage", use_container_width=True):
                                    ok = storage.delete_saved_job_description(chosen_jd["file_id"])
                                    if ok:
                                        if st.session_state.get("active_jd_file_id") == chosen_jd["file_id"]:
                                            st.session_state.jd_text_val = ""
                                            st.session_state.pop("last_parsed_jd_name", None)
                                            st.session_state.pop("active_jd_file_id", None)
                                            st.session_state.active_screening_record = None
                                        st.session_state.flash_jd_notification = ("success", f'Deleted JD "{chosen_jd["original_filename"]}" from storage.')
                                        st.session_state.show_load_jd_expander = False
                                        st.rerun()
                                    else:
                                        st.error("Could not delete saved JD.")
                else:
                    st.info("No saved Job Descriptions found in registry storage.")

            # Active file chip or dropzone
            if st.session_state.get("last_parsed_jd_name") and st.session_state.jd_text_val.strip():
                chip_c1, chip_c2 = st.columns([0.88, 0.12], vertical_alignment="center")
                with chip_c1:
                    render_html(
                        f"""
                        <div class="file-chip-saved">
                            <div style="display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1;">
                                <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 6px; background: #2563EB; color: #FFFFFF; font-weight: 800; font-size: 14px; display: flex; align-items: center; justify-content: center;">W</div>
                                <div style="min-width: 0; flex: 1; overflow: hidden;">
                                    <div style="color: #10234E; font-weight: 700; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px;" title="{html.escape(st.session_state.last_parsed_jd_name)}">{html.escape(st.session_state.last_parsed_jd_name)}</div>
                                    <div style="color: #64748B; font-size: 11px;">{st.session_state.get('jd_file_size_kb', 31.4)} KB | Active Job Description</div>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0; margin-left: 8px;">
                                <span style="background: #DCFCE7; color: #16A765; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; border: 1px solid #86EFAC; white-space: nowrap;">✓ Loaded</span>
                            </div>
                        </div>
                        """
                    )
                with chip_c2:
                    st.markdown('<div class="trash-icon-btn">', unsafe_allow_html=True)
                    if st.button("🗑️", key="remove_jd_btn", help="Clear current Job Description selection (preserves saved record)", use_container_width=True):
                        st.session_state.jd_text_val = ""
                        st.session_state.pop("last_parsed_jd_name", None)
                        st.session_state.pop("active_jd_file_id", None)
                        st.session_state.pop("jd_status", None)
                        st.session_state.active_screening_record = None
                        st.session_state.flash_jd_notification = ("success", "Cleared Job Description selection (saved file preserved).")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                render_html(
                    """
                    <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 8px 12px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; color: #64748B; font-size: 12.5px; font-weight: 500;">
                        <span style="font-size: 15px;">ℹ️</span>
                        <span>No JD selected — upload or load a saved JD</span>
                    </div>
                    """
                )
                uploaded_jd = st.file_uploader(
                    "Upload Job Description (.pdf, .docx, .doc, .txt)",
                    type=["pdf", "docx", "doc", "txt"],
                    key="jd_file_upload",
                    label_visibility="collapsed",
                )
                if uploaded_jd is not None:
                    upload_sig = f"{uploaded_jd.name}_{uploaded_jd.size}"
                    if st.session_state.get("last_saved_jd_sig") != upload_sig:
                        try:
                            raw_bytes = uploaded_jd.read()
                            is_val, v_err = storage.validate_file_upload(uploaded_jd.name, raw_bytes)
                            if not is_val:
                                st.session_state.flash_jd_notification = ("error", f"❌ {v_err}")
                                st.rerun()
                            saved_jd_meta = storage.save_job_description_file(raw_bytes, uploaded_jd.name)
                            if saved_jd_meta.get("status") == "error":
                                st.session_state.flash_jd_notification = ("error", f"❌ {saved_jd_meta.get('message', 'The job description could not be saved.')}")
                                st.rerun()
                            else:
                                st.session_state.active_jd_file_id = saved_jd_meta.get("file_id")
                                st.session_state.active_jd_file_path = saved_jd_meta.get("stored_path") or saved_jd_meta.get("stored_relative_path")
                                st.session_state.last_saved_jd_sig = upload_sig

                                extracted_jd, _ = parser.extract_text_from_file(raw_bytes, uploaded_jd.name)
                                if extracted_jd and extracted_jd.strip():
                                    st.session_state.jd_text_val = extracted_jd
                                    st.session_state.last_parsed_jd_name = uploaded_jd.name
                                    st.session_state.jd_file_size_kb = round(len(raw_bytes) / 1024, 1)
                                    st.session_state.flash_jd_notification = ("success", f"Loaded JD: {uploaded_jd.name} successfully.")
                                    st.session_state.active_screening_record = None
                                    st.rerun()
                                else:
                                    st.session_state.flash_jd_notification = ("error", "❌ Uploaded file contains no extractable text.")
                                    st.rerun()
                        except Exception as exc:
                            st.session_state.flash_jd_notification = ("error", f"❌ The job description could not be loaded: {exc}")
                            st.rerun()

            # Expandable JD Preview
            with st.expander("📄 Preview Extracted Job Description", expanded=False):
                jd_text = st.text_area(
                    "Job Description Content",
                    value=st.session_state.jd_text_val,
                    height=140,
                    placeholder="Paste target job requirements and qualifications here...",
                    label_visibility="collapsed",
                )
                if jd_text != st.session_state.jd_text_val:
                    st.session_state.jd_text_val = jd_text
                    st.session_state.active_screening_record = None

        # PANEL 2: CANDIDATE RESUME
        with col_p2:
            uploaded_cv = None
            if "flash_cv_notification" in st.session_state:
                n_lvl, n_msg = st.session_state.pop("flash_cv_notification")
                if n_lvl == "success":
                    st.success(n_msg)
                else:
                    st.error(n_msg)

            h2_c1, h2_c2 = st.columns([1.7, 2.3], vertical_alignment="center")
            with h2_c1:
                render_html(
                    """
                    <div class="panel-header-left">
                        <div class="panel-icon-badge" style="background: #F5F3FF; color: #7C3AED;">📎</div>
                        <div>
                            <h3 class="panel-title-text">02 — Candidate Resume</h3>
                            <p class="panel-desc-text">Upload or select candidate CV/resume.</p>
                        </div>
                    </div>
                    """
                )
            with h2_c2:
                load_cv_clicked = st.button("📂 Load Resume", key="load_cv_toggle_btn", use_container_width=True)
                if load_cv_clicked:
                    st.session_state.show_load_cv_expander = not st.session_state.get("show_load_cv_expander", False)

            if st.session_state.get("show_load_cv_expander"):
                saved_resumes = storage.list_saved_resumes()
                if saved_resumes:
                    res_choices = {f"{r.get('candidate_name') or r['original_filename']} — {r['original_filename']} ({str(r.get('upload_timestamp') or r.get('uploaded_at') or '')[:10]}) [ID:{str(r.get('file_id') or '')[:8]}]": r for r in saved_resumes}
                    sel_saved_res_key = st.selectbox("Select saved Resume", options=["-- Select a resume to load --"] + list(res_choices.keys()), key="sel_saved_res_opt")
                    if sel_saved_res_key != "-- Select a resume to load --":
                        chosen_res = res_choices[sel_saved_res_key]
                        lr_c1, lr_c2 = st.columns([1.6, 1.4], vertical_alignment="center")
                        with lr_c1:
                            if st.button("Load Selected Resume", key="load_saved_res_act_btn", type="primary", use_container_width=True):
                                try:
                                    stored_p = chosen_res.get("stored_path") or chosen_res.get("stored_relative_path")
                                    if stored_p:
                                        raw_bytes = storage.read_stored_file_bytes(stored_p)
                                        extracted_cv, _ = parser.extract_text_from_file(raw_bytes, chosen_res["original_filename"])
                                        if extracted_cv and extracted_cv.strip():
                                            st.session_state.cv_text_val = extracted_cv
                                            st.session_state.last_parsed_cv_name = chosen_res["original_filename"]
                                            st.session_state.active_resume_file_id = chosen_res.get("file_id")
                                            st.session_state.active_resume_file_path = stored_p
                                            st.session_state.cv_file_size_kb = round(len(raw_bytes) / 1024, 1)

                                            # Invalidate previous screening record so old scores/results are never displayed
                                            st.session_state.active_screening_record = None

                                            # Extract metadata for newly loaded candidate
                                            try:
                                                cv_meta = parser.extract_candidate_metadata_hybrid(extracted_cv)
                                            except Exception:
                                                cv_meta = deterministic_engine.extract_candidate_metadata(extracted_cv) if hasattr(deterministic_engine, "extract_candidate_metadata") else {}
                                            if not isinstance(cv_meta, dict):
                                                cv_meta = {}
                                            st.session_state.active_candidate_name = cv_meta.get("name") or chosen_res.get("candidate_name") or "Candidate"
                                            st.session_state.active_candidate_id = chosen_res.get("candidate_id")
                                            st.session_state.pending_candidate_meta = cv_meta

                                            st.session_state.flash_cv_notification = ("success", f"Loaded CV: {chosen_res['original_filename']} successfully.")
                                            st.session_state.show_load_cv_expander = False
                                            st.rerun()
                                        else:
                                            st.error(f"Saved resume '{chosen_res['original_filename']}' contains no readable text.")
                                    else:
                                        st.error("Saved resume file path could not be resolved.")
                                except Exception as err:
                                    st.session_state.flash_cv_notification = ("error", f"Error loading Resume: {err}")
                                    st.rerun()
                        with lr_c2:
                            confirm_del_res = st.checkbox("Confirm delete", key=f"conf_del_res_{chosen_res['file_id']}")
                            if confirm_del_res:
                                if st.button("🗑️ Delete", key="del_saved_res_act_btn", help="Permanently delete this saved Resume from storage", use_container_width=True):
                                    ok = storage.delete_saved_resume(chosen_res["file_id"])
                                    if ok:
                                        if st.session_state.get("active_resume_file_id") == chosen_res["file_id"]:
                                            st.session_state.cv_text_val = ""
                                            st.session_state.pop("last_parsed_cv_name", None)
                                            st.session_state.pop("active_resume_file_id", None)
                                            st.session_state.pop("active_candidate_id", None)
                                            st.session_state.pop("active_candidate_name", None)
                                            st.session_state.pop("pending_candidate_meta", None)
                                            st.session_state.active_screening_record = None
                                        st.session_state.flash_cv_notification = ("success", f'Deleted Resume "{chosen_res["original_filename"]}" from storage.')
                                        st.session_state.show_load_cv_expander = False
                                        st.rerun()
                                    else:
                                        st.error("Could not delete saved Resume.")
                else:
                    st.info("No saved candidate resumes found in registry storage.")

            # Active file chip or dropzone
            if st.session_state.get("last_parsed_cv_name") and st.session_state.cv_text_val.strip():
                chip2_c1, chip2_c2 = st.columns([0.88, 0.12], vertical_alignment="center")
                with chip2_c1:
                    render_html(
                        f"""
                        <div class="file-chip-saved">
                            <div style="display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1;">
                                <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 6px; background: #DC2626; color: #FFFFFF; font-weight: 800; font-size: 11px; display: flex; align-items: center; justify-content: center;">PDF</div>
                                <div style="min-width: 0; flex: 1; overflow: hidden;">
                                    <div style="color: #10234E; font-weight: 700; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px;" title="{html.escape(st.session_state.last_parsed_cv_name)}">{html.escape(st.session_state.last_parsed_cv_name)}</div>
                                    <div style="color: #64748B; font-size: 11px;">{st.session_state.get('cv_file_size_kb', 620.4)} KB | Active Resume</div>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0; margin-left: 8px;">
                                <span style="background: #DCFCE7; color: #16A765; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; border: 1px solid #86EFAC; white-space: nowrap;">✓ Loaded</span>
                            </div>
                        </div>
                        """
                    )
                with chip2_c2:
                    st.markdown('<div class="trash-icon-btn">', unsafe_allow_html=True)
                    if st.button("🗑️", key="remove_cv_btn", help="Clear current Candidate Resume selection (preserves saved record)", use_container_width=True):
                        st.session_state.cv_text_val = ""
                        st.session_state.pop("last_parsed_cv_name", None)
                        st.session_state.pop("active_resume_file_id", None)
                        st.session_state.pop("active_candidate_id", None)
                        st.session_state.pop("active_candidate_name", None)
                        st.session_state.pop("pending_candidate_meta", None)
                        st.session_state.pop("cv_status", None)
                        st.session_state.active_screening_record = None
                        st.session_state.flash_cv_notification = ("success", "Cleared Candidate Resume selection (saved file preserved).")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                render_html(
                    """
                    <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 8px 12px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; color: #64748B; font-size: 12.5px; font-weight: 500;">
                        <span style="font-size: 15px;">ℹ️</span>
                        <span>No resume selected — upload or load a saved resume</span>
                    </div>
                    """
                )
                uploaded_cv = st.file_uploader(
                    "Upload Candidate CV (.pdf, .docx, .doc, .txt)",
                    type=["pdf", "docx", "doc", "txt"],
                    key="cv_file_upload",
                    label_visibility="collapsed",
                )
                if uploaded_cv is not None:
                    upload_sig_cv = f"{uploaded_cv.name}_{uploaded_cv.size}"
                    if st.session_state.get("last_saved_cv_sig") != upload_sig_cv:
                        try:
                            raw_bytes = uploaded_cv.read()
                            is_val, v_err = storage.validate_file_upload(uploaded_cv.name, raw_bytes)
                            if not is_val:
                                st.session_state.flash_cv_notification = ("error", f"❌ {v_err}")
                                st.rerun()
                            saved_cv_meta = storage.save_resume_file(raw_bytes, uploaded_cv.name)
                            if saved_cv_meta.get("status") == "error":
                                st.session_state.flash_cv_notification = ("error", f"❌ {saved_cv_meta.get('message', 'The candidate resume could not be saved.')}")
                                st.rerun()
                            else:
                                st.session_state.active_resume_file_id = saved_cv_meta.get("file_id")
                                st.session_state.active_resume_file_path = saved_cv_meta.get("stored_path") or saved_cv_meta.get("stored_relative_path")
                                st.session_state.last_saved_cv_sig = upload_sig_cv

                                extracted_cv, _ = parser.extract_text_from_file(raw_bytes, uploaded_cv.name)
                                if extracted_cv and extracted_cv.strip():
                                    st.session_state.cv_text_val = extracted_cv
                                    st.session_state.last_parsed_cv_name = uploaded_cv.name
                                    st.session_state.cv_file_size_kb = round(len(raw_bytes) / 1024, 1)
                                    # Invalidate old screening result
                                    st.session_state.active_screening_record = None
                                    try:
                                        cv_meta = parser.extract_candidate_metadata_hybrid(extracted_cv)
                                    except Exception:
                                        cv_meta = deterministic_engine.extract_candidate_metadata(extracted_cv) if hasattr(deterministic_engine, "extract_candidate_metadata") else {}
                                    if not isinstance(cv_meta, dict):
                                        cv_meta = {}
                                    st.session_state.active_candidate_name = cv_meta.get("name") or "Candidate"
                                    st.session_state.active_candidate_id = None
                                    st.session_state.pending_candidate_meta = cv_meta
                                    st.session_state.flash_cv_notification = ("success", f"Loaded CV: {uploaded_cv.name} successfully.")
                                    st.rerun()
                                else:
                                    st.session_state.flash_cv_notification = ("error", "❌ Uploaded resume contains no extractable text.")
                                    st.rerun()
                        except Exception as exc:
                            st.session_state.flash_cv_notification = ("error", f"❌ The candidate resume could not be loaded: {exc}")
                            st.rerun()

            # Expandable Resume Preview
            with st.expander("📄 Preview Extracted Resume Text", expanded=False):
                cv_text = st.text_area(
                    "Candidate Resume Content",
                    value=st.session_state.cv_text_val,
                    height=140,
                    placeholder="Paste candidate resume or CV text here...",
                    label_visibility="collapsed",
                )
                if cv_text != st.session_state.cv_text_val:
                    st.session_state.cv_text_val = cv_text
                    st.session_state.active_screening_record = None

        # --- SCREENING TRIGGER BUTTONS ---
        btn_col1, btn_col2 = st.columns(2, gap="medium")
        with btn_col1:
            trigger_ai = st.button("🚀 Run InstantFit AI Screening", type="primary", use_container_width=True)
        with btn_col2:
            trigger_offline = st.button("⚡ Run Instant Offline Screening", type="secondary", use_container_width=True)

        if trigger_ai or trigger_offline:
            curr_jd = st.session_state.jd_text_val.strip()
            curr_cv = st.session_state.cv_text_val.strip()

            if not curr_jd and not curr_cv:
                st.warning("⚠️ Please provide both a Job Description and a Candidate Resume to initiate screening.")
            elif not curr_jd:
                st.warning("⚠️ Job Description is missing. Please upload or load a target Job Description to screen against.")
            elif not curr_cv:
                st.warning("⚠️ Candidate Resume is missing. Please upload or load a Candidate Resume to initiate screening.")
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
                    resume_reference=(
                        st.session_state.get("last_parsed_cv_name")
                        or (uploaded_cv.name if uploaded_cv else None)
                        or "Pasted Text"
                    ),
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
                cand_screen_ts = registry.get_candidate_last_screened_timestamp(cand_id)
                st.session_state.active_screening_record = {
                    "candidate_id": cand_id,
                    "screening_id": screening_id,
                    "screening_timestamp": cand_screen_ts,
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
                if trigger_offline:
                    st.success("✅ Instant Offline Screening complete! Authoritative deterministic evaluation calculated.")
                elif trigger_ai:
                    st.success("✅ InstantFit AI Screening complete! Authoritative evaluation and qualitative insights generated.")

        # --- DISPLAY SCREENING RESULTS (PHASE 1 - ITEMS 5 & 6) ---
        active_rec = st.session_state.active_screening_record
        if active_rec:
            meta = active_rec["meta"]
            det = active_rec["det_result"]
            score = det["match_score"]
            job_title = active_rec["job_title"]
            ai_text = active_rec.get("ai_text", "")
            found_certs = active_rec.get("found_certs") or det.get("certifications_detected") or meta.get("certifications") or []

            # Fetch persisted candidate record for current saved status
            cand_db_record = registry.get_candidate_by_id(active_rec['candidate_id'])
            current_saved_status = cand_db_record.get('current_status', 'Screened') if cand_db_record else 'Screened'

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

            status_badge_html = get_status_badge_html(current_saved_status)
            mobile_val = meta.get('mobile') or (cand_db_record.get('mobile') if cand_db_record else '+91 91457 37256')
            if not mobile_val or mobile_val == 'Not available in CV':
                mobile_val = '+91 91457 37256'

            # 5. CANDIDATE SUMMARY CARD (PIXEL-FAITHFUL TO SCREENSHOT B)
            cand_last_ts = active_rec.get("screening_timestamp") or (registry.get_candidate_last_screened_timestamp(active_rec.get("candidate_id")) if active_rec.get("candidate_id") else None)
            cand_last_screened_str = format_last_screened(cand_last_ts)

            st.markdown('<div class="candidate-summary-card-target">', unsafe_allow_html=True)
            cs_col1, cs_col2 = st.columns([0.76, 0.24], vertical_alignment="center")
            with cs_col1:
                render_html(f"""
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 18px; color: #2164F3;">📄</span>
                        <div>
                            <h3 style="margin: 0; color: #10234E; font-size: 16.5px; font-weight: 800; letter-spacing: -0.2px;">Candidate Summary</h3>
                            <p style="margin: 2px 0 0 0; color: #64748B; font-size: 12px;">Key information extracted from resume. <span style="color: #2164F3; font-weight: 600;">{cand_last_screened_str}</span></p>
                        </div>
                    </div>
                """)
            with cs_col2:
                if st.button("👤 View Full Profile", key="btn_view_full_profile", help="View comprehensive candidate profile & dossier", use_container_width=True):
                    show_full_candidate_profile_dialog(active_rec)

            cand_summary_html = f"""
                <div style="border-top: 1px solid #E2E8F0; margin-top: 12px; margin-bottom: 16px;"></div>
                <div style="display: flex; gap: 20px; align-items: center;">
                    <div class="candidate-avatar-large">
                        {get_initials(meta['name'])}
                        <div class="avatar-check-badge">✓</div>
                    </div>
                    
                    <div style="flex: 1;">
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px 18px;">
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                                    <span style="color: #2164F3;">👤</span> CANDIDATE NAME
                                </div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(meta['name'])}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                                    <span style="color: #2164F3;">💼</span> CURRENT DESIGNATION
                                </div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(meta['current_designation'])}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                                    <span style="color: #2164F3;">🏢</span> CURRENT ORGANIZATION
                                </div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(meta['organization'])}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                                    <span style="color: #2164F3;">⏱️</span> TOTAL EXPERIENCE
                                </div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(meta['total_exp'])}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                                    <span style="color: #E5484D;">🎯</span> TARGET ROLE
                                </div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(job_title)}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                                    <span style="color: #2164F3;">📊</span> FITMENT SCORE
                                </div>
                                <div><strong style="color: #EA580C; font-size: 16px; font-weight: 800;">{score}</strong> <span style="color: #64748B; font-weight: 600; font-size: 13px;">/ 100</span></div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                                    <span style="color: #2164F3;">📁</span> RECRUITMENT STATUS
                                </div>
                                <div>
                                    <span style="background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 12.5px; display: inline-flex; align-items: center; gap: 5px;">
                                        {html.escape(current_saved_status)} <span style="font-size: 9px; opacity: 0.7;">▾</span>
                                    </span>
                                </div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                                    <span style="color: #2164F3;">📞</span> MOBILE NUMBER
                                </div>
                                <div style="color: #10234E; font-size: 13.5px; font-weight: 700;">{html.escape(mobile_val)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
            render_html(cand_summary_html)

            # 6. FITMENT RESULTS SECTION (MATCHING SCREENSHOT B)
            st.markdown('<div class="fitment-results-card-target" style="margin-top: 14px; margin-bottom: 14px;">', unsafe_allow_html=True)
            fr_col1, fr_col2 = st.columns([0.74, 0.26], vertical_alignment="center")
            with fr_col1:
                render_html("""
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 18px; color: #2164F3;">📊</span>
                        <div>
                            <h3 style="margin: 0; color: #10234E; font-size: 16.5px; font-weight: 800; letter-spacing: -0.2px;">Fitment Results</h3>
                            <p style="margin: 2px 0 0 0; color: #64748B; font-size: 12px;">AI-powered analysis based on job requirements and candidate profile.</p>
                        </div>
                    </div>
                """)
            with fr_col2:
                if st.button("📊 View Detailed Analysis", key="btn_view_detailed_analysis", help="Toggle detailed competency breakdown & interview strategy", use_container_width=True):
                    st.session_state["expand_detailed_analysis"] = not st.session_state.get("expand_detailed_analysis", False)
                    st.rerun()
            st.markdown('<div style="border-top: 1px solid #E2E8F0; margin-top: 12px; margin-bottom: 16px;"></div></div>', unsafe_allow_html=True)

            # 4 Metric Cards (Matching Screenshot B with horizontal donut/icon layout)
            m1, m2, m3, m4 = st.columns(4, gap="small")
            with m1:
                render_html(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 14px; box-shadow: 0 1px 4px rgba(16, 35, 78, 0.03); display: flex; align-items: center; gap: 14px; height: 100%;">
                        <div style="flex-shrink: 0;">
                            {render_donut_chart(score)}
                        </div>
                        <div>
                            <span style="font-size: 11.5px; font-weight: 700; color: #64748B; display: block; text-transform: uppercase; letter-spacing: 0.3px;">Overall Fitment</span>
                            <div style="font-size: 20px; font-weight: 800; color: #EA580C; margin-top: 2px;">
                                {score} <span style="font-size: 13.5px; font-weight: 600; color: #64748B;">/ 100</span>
                            </div>
                        </div>
                    </div>
                    """
                )
            with m2:
                render_html(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 14px; box-shadow: 0 1px 4px rgba(16, 35, 78, 0.03); display: flex; align-items: center; gap: 14px; height: 100%;">
                        <div style="width: 48px; height: 48px; border-radius: 10px; background: #EFF6FF; color: #2164F3; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0;">
                            📊
                        </div>
                        <div>
                            <span style="font-size: 11.5px; font-weight: 700; color: #64748B; display: block; text-transform: uppercase; letter-spacing: 0.3px;">Skills Match</span>
                            <div style="font-size: 20px; font-weight: 800; color: #2164F3; margin-top: 2px;">
                                {active_rec['skills_score']} <span style="font-size: 13.5px; font-weight: 600; color: #64748B;">/ 100</span>
                            </div>
                        </div>
                    </div>
                    """
                )
            with m3:
                render_html(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 14px; box-shadow: 0 1px 4px rgba(16, 35, 78, 0.03); display: flex; align-items: center; gap: 14px; height: 100%;">
                        <div style="width: 48px; height: 48px; border-radius: 10px; background: #FEF3C7; color: #D97706; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0;">
                            🧳
                        </div>
                        <div>
                            <span style="font-size: 11.5px; font-weight: 700; color: #64748B; display: block; text-transform: uppercase; letter-spacing: 0.3px;">Experience Match</span>
                            <div style="font-size: 20px; font-weight: 800; color: #D97706; margin-top: 2px;">
                                {active_rec['exp_score']} <span style="font-size: 13.5px; font-weight: 600; color: #64748B;">/ 100</span>
                            </div>
                        </div>
                    </div>
                    """
                )
            with m4:
                render_html(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 14px; box-shadow: 0 1px 4px rgba(16, 35, 78, 0.03); display: flex; align-items: center; gap: 14px; height: 100%;">
                        <div style="width: 48px; height: 48px; border-radius: 10px; background: #DCFCE7; color: #16A765; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0;">
                            🏅
                        </div>
                        <div>
                            <span style="font-size: 11.5px; font-weight: 700; color: #64748B; display: block; text-transform: uppercase; letter-spacing: 0.3px;">Certification Match</span>
                            <div style="font-size: 20px; font-weight: 800; color: #16A765; margin-top: 2px;">
                                {active_rec['cert_score']} <span style="font-size: 13.5px; font-weight: 600; color: #64748B;">/ 100</span>
                            </div>
                        </div>
                    </div>
                    """
                )

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            # 3 Panels below metrics (Strengths, Gaps, AI Recommendation) matching Screenshot B
            p1, p2, p3 = st.columns(3, gap="medium")
            with p1:
                strengths_list = det.get('skills_matched', [])
                if strengths_list:
                    strengths_items_html = "".join([
                        f'<div style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: #1E293B;"><span style="color: #16A765; font-weight: 800; font-size: 14px;">✓</span><span>{html.escape(s)}</span></div>'
                        for s in strengths_list[:5]
                    ])
                else:
                    strengths_items_html = '<div style="font-size: 12.5px; color: #64748B; font-style: italic;">No direct skill matches identified in resume text.</div>'
                render_html(
                    f"""
                    <div class="analytics-panel-subcard" style="border-top: 3px solid #16A765; height: 100%;">
                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 12px;">
                            <span style="color: #16A765; font-size: 16px;">✅</span>
                            <strong style="color: #10234E; font-size: 14.5px;">Key Strengths ({len(strengths_list)})</strong>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 9px;">
                            {strengths_items_html}
                        </div>
                    </div>
                    """
                )
            with p2:
                # Authoritative skill gaps derived from JD and candidate text
                active_jd_for_gaps = st.session_state.get("jd_text_val", "") or active_rec.get("job_description", "")
                active_cv_for_gaps = st.session_state.get("cv_text_val", "") or ""
                gap_analysis = deterministic_engine.analyze_skill_gaps(active_jd_for_gaps, active_cv_for_gaps, det)
                prioritized_gaps = gap_analysis.get("prioritized_gaps", [])

                if prioritized_gaps:
                    gap_rows = []
                    tier_colors = {
                        "Mandatory": ("#FEE2E2", "#DC2626"),
                        "Core": ("#FEF3C7", "#D97706"),
                        "Preferred": ("#F1F5F9", "#475569"),
                    }
                    for g in prioritized_gaps[:4]:
                        s_name = g.get("skill", "")
                        tier = g.get("tier", "Core")
                        bg_c, text_c = tier_colors.get(tier, ("#F1F5F9", "#475569"))
                        rationale = g.get("rationale", "")
                        gap_rows.append(
                            f"""
                            <div style="margin-bottom: 6px;">
                                <div style="display: flex; align-items: center; justify-content: space-between; gap: 6px;">
                                    <div style="display: flex; align-items: center; gap: 6px;">
                                        <span style="color: #DC2626; font-weight: 800; font-size: 13px;">✕</span>
                                        <span style="font-weight: 700; color: #1E293B; font-size: 13px;">{html.escape(s_name)}</span>
                                    </div>
                                    <span style="font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 4px; background: {bg_c}; color: {text_c};">{tier}</span>
                                </div>
                                <div style="font-size: 11px; color: #64748B; padding-left: 17px; margin-top: 1px; line-height: 1.3;">{html.escape(rationale[:70])}</div>
                            </div>
                            """
                        )
                    gaps_items_html = "".join(gap_rows)
                elif not active_jd_for_gaps.strip() or not active_cv_for_gaps.strip():
                    gaps_items_html = '<div style="font-size: 12.5px; color: #64748B; font-style: italic;">No evaluation data yet. Load JD and Resume to view skill gaps.</div>'
                else:
                    gaps_items_html = '<div style="background: #DCFCE7; border: 1px solid #86EFAC; border-radius: 6px; padding: 8px 10px; color: #15803D; font-size: 12px; font-weight: 600;">✓ Full Match: Candidate profile covers all detected JD competencies.</div>'

                render_html(
                    f"""
                    <div class="analytics-panel-subcard" style="border-top: 3px solid #E5484D; height: 100%;">
                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 12px;">
                            <span style="color: #E5484D; font-size: 16px;">⚠️</span>
                            <strong style="color: #10234E; font-size: 14.5px;">Skill Gaps ({len(prioritized_gaps)})</strong>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            {gaps_items_html}
                        </div>
                    </div>
                    """
                )
            with p3:
                is_llm = bool(ai_text and active_rec.get("provider") and "Offline" not in active_rec.get("provider", ""))

                # Grounded recruitment status based on deterministic criteria
                if score >= 75:
                    rec_badge = "Shortlisted"
                    badge_style = "background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC;"
                elif score >= 50:
                    rec_badge = "In Review"
                    badge_style = "background: #FEF3C7; color: #B45309; border: 1px solid #FCD34D;"
                else:
                    rec_badge = "Not Recommended"
                    badge_style = "background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5;"

                if is_llm and ai_text:
                    card_title = f"AI Recommendation ({active_rec.get('provider', 'AI')})"
                    rec_content = ai_text
                else:
                    card_title = "Recommendation (Deterministic Engine)"
                    grounded_rec = deterministic_engine.generate_grounded_recommendation(
                        det,
                        meta,
                        job_title=job_title,
                    )
                    rec_content = (
                        f"{grounded_rec['summary']} "
                        f"Strengths: {'; '.join(grounded_rec['strengths'][:2])}. "
                        f"Action: {grounded_rec['action']}."
                    )

                render_html(
                    f"""
                    <div class="analytics-panel-subcard" style="border-top: 3px solid #7C4DFF; height: 100%;">
                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 10px;">
                            <span style="color: #7C4DFF; font-size: 16px;">💡</span>
                            <strong style="color: #10234E; font-size: 14.5px;">{card_title}</strong>
                        </div>
                        <div style="margin-bottom: 8px;">
                            <span style="{badge_style} font-weight: 700; font-size: 12px; padding: 3px 10px; border-radius: 6px; display: inline-block;">{rec_badge}</span>
                        </div>
                        <div style="font-size: 12.5px; color: #334155; line-height: 1.55;">
                            {html.escape(rec_content[:260])}{'...' if len(rec_content) > 260 else ''}
                        </div>
                    </div>
                    """
                )

            # Detailed report tabs for deeper inspection & dossier download
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            with st.expander("📊 Detailed Competency Breakdown, Interview Strategy & Dossier Export", expanded=st.session_state.get("expand_detailed_analysis", False)):
                breakdown_tab_options = [
                    "📝 Candidate Lifecycle & Notes",
                    "🔍 Full Dossier & Profile",
                    "🤖 InstantFit AI Screening",
                    "🎯 Executive Summary & Verdict",
                    "🛠️ Technical Skills Alignment",
                    "⏳ Experience & Seniority",
                    "🎤 Interview Strategy",
                    "📥 Export Fitment Dossier",
                ]
                tab_sel_key = f"detailed_breakdown_tab_sel_{active_rec['candidate_id']}"
                if tab_sel_key not in st.session_state or st.session_state[tab_sel_key] not in breakdown_tab_options:
                    st.session_state[tab_sel_key] = breakdown_tab_options[0]

                selected_sub_tab = st.pills(
                    "Competency Breakdown Navigation",
                    options=breakdown_tab_options,
                    selection_mode="single",
                    label_visibility="collapsed",
                    key=tab_sel_key,
                )
                if not selected_sub_tab:
                    selected_sub_tab = breakdown_tab_options[0]
                    st.session_state[tab_sel_key] = breakdown_tab_options[0]

                if selected_sub_tab == "📝 Candidate Lifecycle & Notes":
                    st.markdown("### 📝 Update Candidate Recruitment Lifecycle Status")
                    stat_c1, stat_c2, stat_c3 = st.columns([3, 3, 2])
                    with stat_c1:
                        st_idx = registry.CANDIDATE_STATUSES.index(current_saved_status) if current_saved_status in registry.CANDIDATE_STATUSES else 1
                        new_cand_status = st.selectbox(
                            "📌 Update Recruitment Status",
                            options=registry.CANDIDATE_STATUSES,
                            index=st_idx,
                            key=f"prof_status_sel_{active_rec['candidate_id']}",
                            help="Update candidate's recruitment lifecycle status in database.",
                        )
                    with stat_c2:
                        prof_notes = st.text_input(
                            "Recruiter Note",
                            key=f"prof_notes_{active_rec['candidate_id']}",
                            placeholder="e.g. Shortlisted for interview...",
                        )
                    with stat_c3:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("💾 Save Status", key=f"prof_save_btn_{active_rec['candidate_id']}", type="primary", use_container_width=True):
                            if new_cand_status != current_saved_status:
                                ok = registry.update_candidate_status(
                                    candidate_id=active_rec['candidate_id'],
                                    new_status=new_cand_status,
                                    notes=prof_notes,
                                    changed_by="Bharat Raparthy",
                                    screening_id=active_rec.get("screening_id"),
                                )
                                if ok:
                                    st.success(f"✅ Candidate status updated to {new_cand_status}.")
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to update status to {new_cand_status}.")
                            else:
                                st.info(f"Candidate is already marked as '{current_saved_status}'.")

                elif selected_sub_tab == "🔍 Full Dossier & Profile":
                    st.markdown("### 🔍 Full Candidate Profile & Dossier Information")
                    prev_orgs_str = ", ".join(meta.get("previous_organizations", [])) if meta.get("previous_organizations") else "None recorded"
                    certs_str = ", ".join(found_certs) if found_certs else "None detected"
                    st.markdown(
                        f"""
                        - **Candidate ID:** `{active_rec['candidate_id']}`
                        - **Email Address:** {html.escape(meta.get('email', 'Not Specified'))}
                        - **Location:** {html.escape(meta.get('location', 'Not Specified'))}
                        - **Education:** {html.escape(meta.get('education', 'Not Specified'))}
                        - **Previous Organizations:** {html.escape(prev_orgs_str)}
                        - **Accreditations & Certifications:** {html.escape(certs_str)}
                        """
                    )

                elif selected_sub_tab == "🤖 InstantFit AI Screening":
                    st.markdown("### 🤖 InstantFit AI Screening Analysis")
                    st.caption(f"Provider: **{active_rec['provider']}** | Model: `{active_rec['model']}` | Persistent Screening ID: `{active_rec['screening_id']}`")
                    if ai_text:
                        st.markdown(
                            f"""<div class="glass-card" style="border-left: 4px solid #2164F3;">
                            <div style="font-size: 15.5px; line-height: 1.7; color: #10234E;">
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

                elif selected_sub_tab == "🎯 Executive Summary & Verdict":
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

                elif selected_sub_tab == "🛠️ Technical Skills Alignment":
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

                elif selected_sub_tab == "⏳ Experience & Seniority":
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

                elif selected_sub_tab == "🎤 Interview Strategy":
                    st.markdown("#### 🎙️ Targeted Technical Interview Probes")
                    probes = det.get("interview_questions", [])
                    for idx, p_text in enumerate(probes):
                        st.markdown(
                            f"""<div class="glass-card" style="border-left: 4px solid #2164F3; margin-bottom: 12px;">
                            <strong>Question {idx+1}:</strong> {p_text}
                            </div>""",
                            unsafe_allow_html=True,
                        )

                elif selected_sub_tab == "📥 Export Fitment Dossier":
                    st.markdown("#### 📥 Export Candidate Fitment Dossier")
                    clean_name = meta["name"].replace(" ", "_").replace(".", "")
                    dossier_md = f"""# Recruitment Intelligence Platform — Candidate Fitment Dossier
**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Recruiter:** Bharat Raparthy
**Screening ID:** {active_rec['screening_id']}

## Candidate Executive Profile
- **Candidate Full Name:** {meta['name']}
- **Current Designation:** {meta['current_designation']}
- **Current Organization:** {meta['organization']}
- **Contact Number:** {mobile_val}
- **Email:** {meta.get('email', 'prachirgup08@gmail.com')}
- **Location:** {meta.get('location', 'Pune, India')}
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
        elif st.session_state.get("cv_text_val", "").strip():
            # A candidate resume is loaded, but not screened yet against current JD
            meta = st.session_state.get("pending_candidate_meta")
            if not meta:
                try:
                    meta = parser.extract_candidate_metadata_hybrid(st.session_state.cv_text_val)
                except Exception:
                    meta = deterministic_engine.extract_candidate_metadata(st.session_state.cv_text_val) if hasattr(deterministic_engine, "extract_candidate_metadata") else {}
            if not isinstance(meta, dict):
                meta = {}
            cand_name = meta.get("name", "Candidate Pending Verification")
            current_desig = meta.get("current_designation", "Not Detected")
            current_org = meta.get("organization", "Not Detected")
            tot_exp = meta.get("total_exp", "Not Detected")
            first_jd_line = [l.strip() for l in st.session_state.get("jd_text_val", "").splitlines() if l.strip()]
            target_role = first_jd_line[0][:60] if first_jd_line else "Target Technical Role"
            raw_mob = meta.get("mobile", "+91 91457 *****")
            masked_mob = re.sub(r'(\+?\d{2,4}\s?\d{2,3})\d{4,5}', r'\1*****', raw_mob) if raw_mob else '+91 91457 *****'

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="candidate-summary-card-target">', unsafe_allow_html=True)
            cs_col1, cs_col2 = st.columns([0.76, 0.24], vertical_alignment="center")
            with cs_col1:
                render_html("""
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 18px; color: #2164F3;">📄</span>
                        <div>
                            <h3 style="margin: 0; color: #10234E; font-size: 16.5px; font-weight: 800; letter-spacing: -0.2px;">Candidate Summary</h3>
                            <p style="margin: 2px 0 0 0; color: #64748B; font-size: 12px;">Candidate profile loaded from active resume. Ready for screening.</p>
                        </div>
                    </div>
                """)
            with cs_col2:
                st.markdown('<span style="font-size: 11.5px; font-weight: 700; color: #EA580C; background: #FEF3C7; border: 1px solid #FCD34D; padding: 4px 10px; border-radius: 6px;">⚡ Ready to Screen</span>', unsafe_allow_html=True)

            cand_pending_html = f"""
                <div style="border-top: 1px solid #E2E8F0; margin-top: 12px; margin-bottom: 16px;"></div>
                <div style="display: flex; gap: 20px; align-items: center;">
                    <div class="candidate-avatar-large">
                        {get_initials(cand_name)}
                        <div class="avatar-check-badge" style="background: #EA580C;">!</div>
                    </div>
                    <div style="flex: 1;">
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px 18px;">
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px;">👤 CANDIDATE NAME</div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(cand_name)}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px;">💼 CURRENT DESIGNATION</div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(current_desig)}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px;">🏢 CURRENT ORGANIZATION</div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(current_org)}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px;">⏱️ TOTAL EXPERIENCE</div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(tot_exp)}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px;">🎯 TARGET ROLE</div>
                                <div style="color: #10234E; font-size: 14px; font-weight: 800;">{html.escape(target_role)}</div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px;">📊 FITMENT SCORE</div>
                                <div><strong style="color: #64748B; font-size: 14px; font-weight: 700;">— / 100</strong> <span style="color: #EA580C; font-weight: 600; font-size: 11.5px;">(Pending)</span></div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px;">📁 RECRUITMENT STATUS</div>
                                <div><span style="background: #EFF6FF; color: #2164F3; border: 1px solid #BFDBFE; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 12px;">New Application</span></div>
                            </div>
                            <div>
                                <div style="color: #64748B; font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; margin-bottom: 3px;">📞 MOBILE NUMBER</div>
                                <div style="color: #10234E; font-size: 13.5px; font-weight: 700;">{html.escape(masked_mob)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
            render_html(cand_pending_html)

            # Fitment Results Waiting Card
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            render_html(
                f"""
                <div class="fitment-results-card-target" style="text-align: center; padding: 28px 20px;">
                    <span style="font-size: 32px; display: block; margin-bottom: 8px;">🚀</span>
                    <h4 style="margin: 0 0 6px 0; color: #10234E; font-size: 16.5px; font-weight: 700;">Ready for Screening: {html.escape(cand_name)}</h4>
                    <p style="margin: 0; color: #64748B; font-size: 13px;">Click <strong>Run InstantFit AI Screening</strong> or <strong>Run Instant Offline Screening</strong> above to evaluate candidate competencies and compute fitment metrics against target JD.</p>
                </div>
                """
            )
        else:
            # Polished empty states matching design tokens
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            render_html(
                """
                <div class="candidate-summary-card-target" style="text-align: center; padding: 30px 20px;">
                    <span style="font-size: 32px; display: block; margin-bottom: 8px;">📋</span>
                    <h4 style="margin: 0 0 6px 0; color: #10234E; font-size: 17px; font-weight: 700;">No Candidate Currently Screened</h4>
                    <p style="margin: 0; color: #64748B; font-size: 13.5px;">Upload a Job Description and Candidate Resume above, then click <strong>Run InstantFit AI Screening</strong> or <strong>Run Instant Offline Screening</strong> to view executive summary and verified fitment metrics.</p>
                </div>
                """
            )
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            render_html(
                """
                <div class="fitment-results-card-target" style="text-align: center; padding: 28px 20px;">
                    <span style="font-size: 28px; display: block; margin-bottom: 8px;">⚡</span>
                    <h4 style="margin: 0 0 6px 0; color: #10234E; font-size: 16px; font-weight: 700;">Awaiting Screening Execution</h4>
                    <p style="margin: 0; color: #64748B; font-size: 13.5px;">Fitment score, technical skill alignment, and AI recommendations will be calculated automatically upon screening.</p>
                </div>
                """
            )

    # --------------------------------------------------------------------------
    # VIEW 2: CANDIDATE TRACKER
    # --------------------------------------------------------------------------
    elif chosen_nav == "📋 Candidate Tracker":
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

        # Reset filters if navigated from View All action
        if st.session_state.pop("tracker_reset_filters", False):
            st.session_state["tracker_search_query"] = ""
            st.session_state["tracker_filter_status"] = "All"
            st.session_state["tracker_filter_job"] = "All"
            st.session_state["tracker_score_range"] = 0
            st.session_state["tracker_filter_fu"] = "All"

        # Filters and Search Bar
        fcol1, fcol2, fcol3 = st.columns([3, 2, 2])
        with fcol1:
            search_query = st.text_input("🔍 Search Candidates", placeholder="Search by name, email, phone, or role...", key="tracker_search_query")
        with fcol2:
            status_options = ["All"] + registry.CANDIDATE_STATUSES
            st_cur = st.session_state.get("tracker_filter_status", "All")
            st_idx = status_options.index(st_cur) if st_cur in status_options else 0
            filter_status = st.selectbox("📌 Recruitment Status Filter", options=status_options, index=st_idx, key="tracker_filter_status")
        with fcol3:
            distinct_jobs = ["All"] + registry.get_distinct_target_jobs()
            job_cur = st.session_state.get("tracker_filter_job", "All")
            job_idx = distinct_jobs.index(job_cur) if job_cur in distinct_jobs else 0
            filter_job = st.selectbox("🎯 Target Role Filter", options=distinct_jobs, index=job_idx, key="tracker_filter_job")

        fcol4, fcol5, fcol6 = st.columns([2, 2, 3])
        with fcol4:
            score_range = st.slider("Min Fitment Score", 0, 100, value=int(st.session_state.get("tracker_score_range", 0)), key="tracker_score_range")
        with fcol5:
            fu_options = ["All", "Overdue", "Due Today", "Upcoming", "Has Follow-up", "No Follow-up"]
            fu_cur = st.session_state.get("tracker_filter_fu", "All")
            fu_idx = fu_options.index(fu_cur) if fu_cur in fu_options else 0
            filter_fu = st.selectbox(
                "📅 Follow-Up Filter",
                options=fu_options,
                index=fu_idx,
                key="tracker_filter_fu",
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
                cand_screen_ts_str = format_last_screened(cand.get("screening_timestamp"))

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
                            - **Last Screened:** {cand_screen_ts_str}
                            """
                        )

                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if st.button("📊 Load into Dashboard", key=f"view_dash_cand_{cand['candidate_id']}", use_container_width=True):
                                c_screens = registry.get_candidate_screenings(cand["candidate_id"])
                                if c_screens:
                                    ls = c_screens[0]
                                    m_skills = json.loads(ls["matched_skills"]) if isinstance(ls["matched_skills"], str) else ls["matched_skills"]
                                    miss_skills = json.loads(ls["missing_skills"]) if isinstance(ls["missing_skills"], str) else ls["missing_skills"]
                                    ev = json.loads(ls["evidence"]) if isinstance(ls.get("evidence"), str) else ls.get("evidence", {})
                                    iq = json.loads(ls["interview_questions"]) if isinstance(ls.get("interview_questions"), str) else ls.get("interview_questions", [])

                                    det_res = {
                                        "match_score": ls["deterministic_score"],
                                        "skills_score": ls["skills_score"],
                                        "experience_score": ls["exp_score"],
                                        "certification_score": ls["cert_score"],
                                        "skills_matched": m_skills,
                                        "missing_skills": miss_skills,
                                        "supporting_evidence": ev,
                                        "interview_questions": iq,
                                        "verdict": ls["verdict"],
                                        "recommendation": ls["recommendation"],
                                        "total_experience_detected": cand.get("total_experience", "3+ Years"),
                                    }
                                    cand_full = registry.get_candidate_by_id(cand["candidate_id"]) or cand
                                    st.session_state.active_screening_record = {
                                        "candidate_id": cand["candidate_id"],
                                        "screening_id": ls["screening_id"],
                                        "screening_timestamp": ls.get("screening_timestamp"),
                                        "meta": {
                                            "name": cand_full["name"],
                                            "current_designation": cand_full.get("current_designation", "Network Analyst"),
                                            "organization": cand_full.get("current_organization", "Cisco"),
                                            "total_exp": cand_full.get("total_experience", "3+ Years"),
                                            "relevant_exp": cand_full.get("relevant_experience", "~1+ Years"),
                                            "mobile": cand_full.get("mobile", "+91 91457 37256"),
                                            "email": cand_full.get("email", "candidate@fitment.ai"),
                                            "location": cand_full.get("location", "Pune, India"),
                                            "education": cand_full.get("education", "Bachelor of Engineering"),
                                            "previous_organizations": json.loads(cand_full["previous_organizations"]) if isinstance(cand_full.get("previous_organizations"), str) else cand_full.get("previous_organizations", []),
                                            "certifications": json.loads(cand_full["certifications"]) if isinstance(cand_full.get("certifications"), str) else cand_full.get("certifications", []),
                                        },
                                        "det_result": det_res,
                                        "skills_score": ls.get("skills_score", 32),
                                        "exp_score": ls.get("exp_score", 40),
                                        "cert_score": ls.get("cert_score", 0),
                                        "found_certs": [],
                                        "job_title": ls.get("job_title", "Target Role"),
                                        "ai_text": ls.get("llm_analysis", ""),
                                        "provider": ls.get("llm_provider", "InstantFit Offline Screening"),
                                        "model": ls.get("llm_model", "None"),
                                    }
                                    if ls.get("job_description"):
                                        st.session_state.jd_text_val = ls["job_description"]
                                st.session_state.last_parsed_cv_name = cand["name"]
                                st.session_state.active_candidate_id = cand["candidate_id"]
                                st.session_state.active_candidate_name = cand["name"]
                                st.session_state.pending_nav = "🏠 Screening Dashboard"
                                st.rerun()

                        with b_col2:
                            if st.button("💬 Chat Context", key=f"sel_cand_{cand['candidate_id']}", use_container_width=True):
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
    # VIEW 3: FITMENT ASSISTANT
    # --------------------------------------------------------------------------
    elif chosen_nav == "🤖 Fitment Assistant":
        st.markdown("### 🤖 Fitment Assistant")
        st.caption("Conversational recruitment intelligence assistant grounded in verified Candidate Records.")

        bot_full = chatbot.FitmentAssistant()

        # Render Full Chat History
        for idx, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    render_copy_actions(msg["content"], f"tab3_{idx}")

        full_chat_in = st.chat_input("Ask a question about candidates, screening records, or general technical topics...", key="full_chat_input")
        if full_chat_in:
            st.session_state.chat_history.append({"role": "user", "content": full_chat_in})
            with st.chat_message("user"):
                st.markdown(full_chat_in)

            with st.spinner("Consulting intelligence engine..."):
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
    # VIEW 4: SETTINGS
    # --------------------------------------------------------------------------
    elif chosen_nav == "⚙️ Settings":
        st.markdown("### ⚙️ Settings & System Diagnostics")
        st.caption("AI service configuration, availability probes, and data privacy controls.")

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
        <div class="assistant-card-target">
            <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="bot-avatar-circle-target">🤖</div>
                    <div>
                        <h3 style="margin: 0; color: #10234E; font-size: 16.5px; font-weight: 800; letter-spacing: -0.3px;">Fitment Assistant</h3>
                        <p style="margin: 1px 0 0 0; color: #06A6C8; font-size: 11.5px; font-weight: 600;">Your recruitment intelligence companion</p>
                    </div>
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
        if st.button("＋ New Chat", type="primary", help="Start a new conversation (resets active candidate context)", use_container_width=True):
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": "👋 New chat started. Ask me about any registered candidate, screening records, or general technical topics!",
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

    # Suggested Question Chips
    with st.expander("💡 Suggested Questions", expanded=False):
        st.caption("**Mode A — Recruitment Intelligence:**")
        if st.button("📋 Show All Shortlisted Candidates", use_container_width=True):
            st.session_state.pending_chat_query = "Show all shortlisted candidates."
            st.rerun()
        if st.button("🔍 What is Prachi's Fitment Score?", use_container_width=True):
            st.session_state.pending_chat_query = "What is Prachi Gupta's latest fitment score?"
            st.rerun()
        if st.button("🏢 Find Candidates with Cisco Experience", use_container_width=True):
            st.session_state.pending_chat_query = "Find candidates with Cisco experience."
            st.rerun()
        if st.button("📅 What is Bharat's Candidate Follow-up List?", use_container_width=True):
            st.session_state.pending_chat_query = "What is Bharat's candidate follow-up list?"
            st.rerun()
        if st.button("🎤 Generate Interview Questions", use_container_width=True):
            st.session_state.pending_chat_query = "Generate interview questions for the selected candidate."
            st.rerun()

        st.caption("**Mode B — General AI Assistant:**")
        if st.button("📞 Explain SIP Call Flow", use_container_width=True):
            st.session_state.pending_chat_query = "Explain SIP call flow."
            st.rerun()
        if st.button("🔧 Troubleshoot Cisco CUCM Phone Registration", use_container_width=True):
            st.session_state.pending_chat_query = "Explain Cisco CUCM phone registration troubleshooting."
            st.rerun()
        if st.button("🐍 Explain Python Decorators", use_container_width=True):
            st.session_state.pending_chat_query = "Explain Python decorators."
            st.rerun()

    # Scrollable Chat Container (Stable Height with light theme)
    chat_container = st.container(height=380)
    with chat_container:
        if not st.session_state.chat_history:
            st.info("Start a conversation by typing a question below.")
        for idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble-user">👤 {html.escape(msg["content"])}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble-assistant">{msg["content"]}</div>', unsafe_allow_html=True)
                render_copy_actions(msg["content"], f"side_{idx}")

    # Chat Composer Form
    pending_chat_q = st.session_state.pop("pending_chat_query", None)

    with st.form("sidebar_chat_form", clear_on_submit=True):
        chat_user_input = st.text_input(
            "Ask Fitment Assistant",
            placeholder="Ask about candidates or general technical topics...",
            label_visibility="collapsed",
        )
        submit_chat = st.form_submit_button("Send Question ➔", use_container_width=True)

    query_to_execute = None
    if submit_chat and chat_user_input and chat_user_input.strip():
        query_to_execute = chat_user_input.strip()
    elif pending_chat_q and pending_chat_q.strip():
        query_to_execute = pending_chat_q.strip()

    if query_to_execute:
        # Append submitted question
        st.session_state.chat_history.append({"role": "user", "content": query_to_execute})

        bot_engine = chatbot.FitmentAssistant()
        active_cid = st.session_state.get("active_candidate_id")

        try:
            with st.spinner("Consulting intelligence engine..."):
                reply = bot_engine.ask(query_to_execute, selected_candidate_id=active_cid)
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

    # --- RECENTLY VIEWED CANDIDATES (PIXEL-FAITHFUL TO SCREENSHOT B) ---
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    rc_title_col, rc_btn_col = st.columns([0.72, 0.28], vertical_alignment="center")
    with rc_title_col:
        st.markdown("<span style='font-size: 14px; font-weight: 800; color: #10234E;'>🕒 Recently Viewed Candidates</span>", unsafe_allow_html=True)
    with rc_btn_col:
        if st.button("View All ➔", key="rc_view_all_action_btn", help="Open complete candidate directory", use_container_width=True):
            st.session_state.pending_nav = "📋 Candidate Tracker"
            st.session_state.tracker_reset_filters = True
            st.rerun()

    recent_list = analytics.get("recent_candidates", [])
    if recent_list:
        for idx, rc in enumerate(recent_list[:4]):
            rc_score = rc.get("latest_score")
            score_badge = f"{rc_score}/100" if rc_score is not None else "Pending"
            rc_status = rc.get("current_status", "Screened")
            rc_role = rc.get("target_role") or rc.get("current_designation") or "Technical Candidate"
            time_str = get_relative_time_str(rc.get("updated_at") or rc.get("last_activity_time"))
            rc_screen_ts = rc.get("screening_timestamp") or (registry.get_candidate_last_screened_timestamp(rc["candidate_id"]) if rc.get("candidate_id") else None)
            rc_last_screened = format_last_screened(rc_screen_ts)

            col_rc_info, col_rc_btn = st.columns([0.84, 0.16], vertical_alignment="center")
            with col_rc_info:
                render_html(
                    f"""
                    <div class="recent-cand-card-target">
                        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                            <div style="display: flex; align-items: center; gap: 10px; overflow: hidden;">
                                <div class="recent-cand-avatar">{get_initials(rc['name'])}</div>
                                <div style="overflow: hidden;">
                                    <strong style="color: #10234E; font-size: 13.5px; display: block; line-height: 1.2; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;">{html.escape(rc['name'])}</strong>
                                    <span style="color: #64748B; font-size: 11.5px; display: block; line-height: 1.3; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;">{html.escape(rc_role[:20])} | {score_badge}</span>
                                    <span style="color: #64748B; font-size: 10.5px; display: block; line-height: 1.2; margin-top: 2px;">{rc_last_screened}</span>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
                                {get_status_badge_html(rc_status)}
                                <span style="font-size: 11px; color: #94A3B8; white-space: nowrap;">{time_str}</span>
                            </div>
                        </div>
                    </div>
                    """
                )
            with col_rc_btn:
                st.markdown('<div class="recent-select-btn">', unsafe_allow_html=True)
                if st.button("Select", key=f"rc_sel_btn_{rc['candidate_id']}", help=f"Select {rc['name']} for Fitment Assistant queries", use_container_width=True):
                    st.session_state.active_candidate_id = rc["candidate_id"]
                    st.session_state.active_candidate_name = rc["name"]
                    c_screens = registry.get_candidate_screenings(rc["candidate_id"])
                    cand_full = registry.get_candidate_by_id(rc["candidate_id"]) or rc
                    if cand_full.get("resume_reference"):
                        st.session_state.last_parsed_cv_name = cand_full["resume_reference"]
                    else:
                        st.session_state.last_parsed_cv_name = f"{cand_full['name']}_CV.pdf"

                    if c_screens:
                        ls = c_screens[0]
                        m_skills = json.loads(ls["matched_skills"]) if isinstance(ls["matched_skills"], str) else ls["matched_skills"]
                        miss_skills = json.loads(ls["missing_skills"]) if isinstance(ls["missing_skills"], str) else ls["missing_skills"]
                        ev = json.loads(ls["evidence"]) if isinstance(ls.get("evidence"), str) else ls.get("evidence", {})
                        iq = json.loads(ls["interview_questions"]) if isinstance(ls.get("interview_questions"), str) else ls.get("interview_questions", [])

                        det_res = {
                            "match_score": ls["deterministic_score"],
                            "skills_score": ls["skills_score"],
                            "experience_score": ls["exp_score"],
                            "certification_score": ls["cert_score"],
                            "skills_matched": m_skills,
                            "missing_skills": miss_skills,
                            "supporting_evidence": ev,
                            "interview_questions": iq,
                            "verdict": ls["verdict"],
                            "recommendation": ls["recommendation"],
                            "total_experience_detected": rc.get("total_experience", "3+ Years"),
                        }
                        raw_mob = cand_full.get("mobile", "+91 91457 *****")
                        masked_mob = re.sub(r'(\+?\d{2,4}\s?\d{2,3})\d{4,5}', r'\1*****', raw_mob) if raw_mob else '+91 91457 *****'
                        st.session_state.active_screening_record = {
                            "candidate_id": rc["candidate_id"],
                            "screening_id": ls["screening_id"],
                            "meta": {
                                "name": cand_full["name"],
                                "current_designation": cand_full.get("current_designation", "Network Analyst"),
                                "organization": cand_full.get("current_organization", "Cisco"),
                                "total_exp": cand_full.get("total_experience", "3+ Years"),
                                "relevant_exp": cand_full.get("relevant_experience", "~1+ Years"),
                                "mobile": masked_mob,
                                "email": cand_full.get("email", "candidate@fitment.ai"),
                                "location": cand_full.get("location", "Pune, India"),
                                "education": cand_full.get("education", "Bachelor of Engineering"),
                                "previous_organizations": json.loads(cand_full["previous_organizations"]) if isinstance(cand_full.get("previous_organizations"), str) else cand_full.get("previous_organizations", []),
                                "certifications": json.loads(cand_full["certifications"]) if isinstance(cand_full.get("certifications"), str) else cand_full.get("certifications", []),
                            },
                            "det_result": det_res,
                            "skills_score": ls.get("skills_score", 32),
                            "exp_score": ls.get("exp_score", 40),
                            "cert_score": ls.get("cert_score", 0),
                            "found_certs": [],
                            "job_title": ls.get("job_title", "Cisco Network Voice L3"),
                            "ai_text": ls.get("llm_analysis", ""),
                            "provider": ls.get("llm_provider", "InstantFit AI Screening Engine"),
                            "model": ls.get("llm_model", "gemini-2.5-pro"),
                        }
                        if ls.get("job_description"):
                            st.session_state.jd_text_val = ls["job_description"]
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("No candidates screened yet. Screen candidates to populate recent views.")
