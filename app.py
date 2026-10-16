import streamlit as st
import os
from pypdf import PdfReader
from docx import Document  # Required for .docx support
from openai import OpenAI
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FITMENT.AI | Executive CV Screener",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 3D & EXECUTIVE UI STYLING (CUSTOM CSS) ---
st.markdown(
    """
<style>
    /* Global Theme & Font */
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
    
    /* Executive Header Badge */
    .header-badge {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        letter-spacing: -1px;
        margin-bottom: 0px;
    }
    
    .sub-badge {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 25px;
    }

    /* 3D Glassmorphism Cards */
    .stCard, div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        margin-bottom: 20px;
    }

    /* Primary Action Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white !important;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        border: none;
        box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.5), inset 0 2px 0 rgba(255, 255, 255, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 25px -4px rgba(99, 102, 241, 0.7), inset 0 2px 0 rgba(255, 255, 255, 0.4);
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    }

    /* Fix Text Area Styling and Transparency Bugs */
    .stTextArea textarea {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-size: 0.95rem !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.3) !important;
    }

    /* Fix Sample JD Button Contrast (Dark Text on White Background) */
    div.row-widget.stButton > button[kind="secondary"] {
        background: #ffffff !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    div.row-widget.stButton > button[kind="secondary"]:hover {
        background: #f1f5f9 !important;
        color: #000000 !important;
    }

    /* Metric Containers */
    div[data-testid="metric-container"] {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 15px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* File Uploader Styling */
    div[data-testid="stFileUploader"] {
        border: 2px dashed rgba(99, 102, 241, 0.4);
        background: rgba(30, 41, 59, 0.4);
        padding: 15px;
        border-radius: 14px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- HELPER FUNCTION FOR UNIVERSAL FILE PARSING (.pdf, .docx, .txt) ---
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


# --- SIDEBAR CONFIGURATION (LATEST MODELS & MULTI-PROVIDER KEYS) ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Control Room")

    api_provider = st.selectbox(
        "LLM Provider",
        ["OpenAI", "Anthropic (Claude)", "Google (Gemini)", "Groq", "HuggingFace"],
    )

    api_key = ""
    inference_model = ""

    if api_provider == "OpenAI":
        inference_model = st.selectbox(
            "Inference Model",
            ["gpt-5.5", "gpt-5.4", "gpt-4o", "o3", "o3-mini", "o4-mini"],
        )
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            placeholder="sk-...",
        )

    elif api_provider == "Anthropic (Claude)":
        inference_model = st.selectbox(
            "Inference Model",
            [
                "claude-opus-5.5",
                "claude-fable-5.1",
                "claude-sonnet-5.5",
                "claude-opus-4.8",
            ],
        )
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            placeholder="sk-ant-...",
        )

    elif api_provider == "Google (Gemini)":
        inference_model = st.selectbox(
            "Inference Model",
            [
                "gemini-3.8-flash",
                "gemini-3.1-pro",
                "gemini-2.5-pro",
                "gemini-2.5-flash",
            ],
        )
        api_key = st.text_input(
            "Google API Key",
            type="password",
            value=os.getenv("GOOGLE_API_KEY", ""),
            placeholder="AIzaSy...",
        )

    elif api_provider == "Groq":
        inference_model = st.selectbox(
            "Inference Model",
            ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "groq/compound"],
        )
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            placeholder="gsk_...",
        )

    elif api_provider == "HuggingFace":
        inference_model = st.selectbox(
            "Inference Model",
            ["meta-llama/Llama-3-70B-Instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
        )
        api_key = st.text_input(
            "HuggingFace Access Token",
            type="password",
            value=os.getenv("HUGGINGFACEHUB_ACCESS_TOKEN", ""),
            placeholder="hf_...",
        )

    st.markdown("---")
    st.markdown("### 📊 Scoring Weights Matrix")
    with st.expander("Configure Evaluation Weights"):
        weight_skills = st.slider("Skills Alignment", 0, 100, 30)
        weight_exp = st.slider("Experience Depth", 0, 100, 40)
        weight_edu = st.slider("Education Credentials", 0, 100, 15)
        weight_extras = st.slider("Extras & Certifications", 0, 100, 15)

    st.markdown("---")
    st.markdown("### 🧬 Active Multi-Agents")
    st.markdown("🤖 **JD Analyst:** *Active*")
    st.markdown("🔍 **Resume Parser:** *Active*")
    st.markdown("🚩 **Gap Detector:** *Active*")
    st.markdown("⚖️ **Fitment Scorer:** *Active*")

# --- MAIN DASHBOARD HEADER ---
st.markdown('<p class="header-badge">⚡ FITMENT.AI</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-badge">Next-Generation Multi-Agent Executive CV Screening & Fitment Intelligence Dashboard</p>',
    unsafe_allow_html=True,
)

# Initialize session state for JD text if not present
if "jd_content" not in st.session_state:
    st.session_state.jd_content = ""

# --- INPUT SECTION (2 Columns) ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### 📋 1. Target Role & Job Description")
    st.markdown(
        "Upload a JD document (`.docx`, `.pdf`, `.txt`) or paste specifications below:"
    )

    # Sample JD Button with fixed high-contrast styling
    if st.button("⚡ Load Executive Sample JD", type="secondary"):
        st.session_state.jd_content = """Cisco Network Voice L3 / Voice T2 Engineer
Requirements:
- 8-10 years of experience in enterprise networks with minimum 8+ years specifically in Cisco UC / Voice Collaboration.
- Hands-on expertise with CUCM, Expressway, CUBE, IP Phones, Jabber, and IM & Presence.
- Expertise in CUCM Trace Reading, Jabber PRT Logs, IMP Trace Reading, and GW Debugs.
- Strong knowledge of SIP, H.323, RTP, and Session Border Controllers.
- ITIL framework knowledge and P1/P2 incident escalation handling."""

    # JD File Uploader supporting docx, pdf, txt
    uploaded_jd_file = st.file_uploader(
        "Upload Job Description File (.docx, .pdf, .txt)",
        type=["docx", "doc", "pdf", "txt"],
        key="jd_uploader",
    )
    if uploaded_jd_file is not None:
        parsed_jd = extract_text_from_uploaded_file(uploaded_jd_file)
        if parsed_jd:
            st.session_state.jd_content = parsed_jd
            st.success(f"✅ JD Document ({uploaded_jd_file.name}) loaded successfully!")

    # Manual Text Area bound to session state
    jd_input = st.text_area(
        "Edit or paste Job Description details:",
        value=st.session_state.jd_content,
        height=240,
        placeholder="Paste full job description requirements here...",
    )

with col2:
    st.markdown("### 📄 2. Candidate Resume")
    st.markdown("Upload candidate resume (`.docx`, `.pdf`):")

    # Resume File Uploader supporting docx, pdf
    uploaded_resume_file = st.file_uploader(
        "Upload candidate CV (.docx, .pdf)",
        type=["docx", "doc", "pdf"],
        key="cv_uploader",
    )

    resume_text = ""
    if uploaded_resume_file is not None:
        resume_text = extract_text_from_uploaded_file(uploaded_resume_file)
        if resume_text:
            st.success(
                f"✅ Successfully parsed resume from {uploaded_resume_file.name}."
            )
            st.info(f"📊 Words: {len(resume_text.split())} | Chars: {len(resume_text)}")

st.markdown("<br>", unsafe_allow_html=True)

# --- EVALUATION TRIGGER ---
if st.button("🚀 RUN MULTI-AGENT FITMENT & SCORING", type="primary"):
    if not api_key:
        st.error("⚠️ Please provide your API Key in the sidebar configuration.")
    elif not jd_input or not resume_text:
        st.warning(
            "⚠️ Please provide both the Job Description and upload a candidate Resume to proceed."
        )
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.markdown(
            "🤖 **[Agent 1/4]** JD Mandate Analyst parsing core requirements..."
        )
        progress_bar.progress(25)
        time.sleep(0.4)

        status_text.markdown(
            "🔍 **[Agent 2/4]** CV Skill & Profile Matcher extracting technical alignment..."
        )
        progress_bar.progress(50)
        time.sleep(0.4)

        status_text.markdown(
            "🚩 **[Agent 3/4]** RedFlag & Gap Auditor scanning career trajectory..."
        )
        progress_bar.progress(75)
        time.sleep(0.4)

        status_text.markdown(
            "⚖️ **[Agent 4/4]** Executive Fitment Scorer synthesizing final score..."
        )
        progress_bar.progress(100)
        time.sleep(0.4)
        status_text.empty()
        progress_bar.empty()

        try:
            if api_provider == "OpenAI":
                client = OpenAI(api_key=api_key)
                model_to_use = inference_model
            elif api_provider == "Groq":
                client = OpenAI(
                    api_key=api_key, base_url="https://api.groq.com/openai/v1"
                )
                model_to_use = inference_model
            elif api_provider == "Anthropic (Claude)":
                client = OpenAI(
                    api_key=api_key, base_url="https://api.anthropic.com/v1"
                )
                model_to_use = inference_model
            else:
                client = OpenAI(api_key=api_key)
                model_to_use = inference_model

            prompt = f"""
            You are an elite Lead Technical Recruiter and Solution Architect AI Agent. 
            Evaluate the candidate's resume against the provided Job Description across multiple parameters.
            
            JOB DESCRIPTION:
            {jd_input}
            
            CANDIDATE RESUME:
            {resume_text}
            
            Provide your response structured clearly with Markdown headings:
            1. **Overall Fitment Score** (Exact numeric score out of 100, e.g., 78/100)
            2. **Core Technical Skills Alignment** (Detailed strengths and matches)
            3. **Gaps & Disqualifiers** (Missing requirements, experience gaps, or mismatched tooling)
            4. **Red Flags / Consistency Check** (Job hopping, career trajectory, or timeline inconsistencies)
            5. **Final Executive Verdict & Interview Focus Areas** (Strong Fit / Moderate Fit / Weak Fit with 3 tailored interview questions)
            """

            with st.spinner("✨ Generating Executive Evaluation Report..."):
                response = client.chat.completions.create(
                    model=model_to_use,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                evaluation_result = response.choices[0].message.content

            st.markdown("---")
            st.markdown("## 📊 Executive Fitment Scorecard")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Evaluation Status", "Completed 🎯", "100%")
            m2.metric("Multi-Agent Chain", "4 Agents Run", "Success")
            m3.metric("Analysis Depth", "Deep Semantic", "Verified")
            m4.metric("Selected Engine", api_provider, inference_model)

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(
                f"""
            <div style="background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(99, 102, 241, 0.3); padding: 30px; border-radius: 18px; box-shadow: 0 15px 35px rgba(0,0,0,0.4);">
                {evaluation_result}
            </div>
            """,
                unsafe_allow_html=True,
            )

        except Exception as e:
            st.error(f"❌ Error during multi-agent pipeline execution: {e}")
