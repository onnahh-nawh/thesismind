import os
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "thesismind")

import streamlit as st

from core.storage import init_db

init_db()

from ui import render_analysis_tab, render_chat_tab, render_sidebar

st.set_page_config(
    page_title="ThesisMind - AI Thesis Companion",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1F2937;
}

.element-container, .stMarkdown, p {
    color: #1F2937;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 700;
    color: #111827;
}

.stApp {
    background-color: #F8FAFC;
}

.main > .block-container {
    padding: 2rem 2.5rem;
    max-width: 1200px;
}

section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E5E7EB;
}

section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1.25rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background-color: #F1F5F9;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #E5E7EB;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 0.5rem 1.25rem;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 0.875rem;
    color: #6B7280;
    transition: all 0.15s ease;
}

.stTabs [aria-selected="true"] {
    background-color: #FFFFFF;
    color: #8B5CF6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border: 1px solid #E5E7EB;
}

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1rem;
}

div.stButton > button {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    border-radius: 10px;
    padding: 0.5rem 1rem;
    transition: all 0.15s ease;
}

div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8B5CF6, #7C3AED);
    color: white;
    border: none;
    box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
}

div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
    transform: translateY(-1px);
}

div.stButton > button[kind="secondary"] {
    background: #FFFFFF;
    color: #6B7280;
    border: 1px solid #E5E7EB;
}

div.stButton > button[kind="secondary"]:hover {
    border-color: #8B5CF6;
    color: #8B5CF6;
}

/* === File Uploader === */
div[data-testid="stFileUploader"] {
    margin-bottom: 0.5rem;
}

div[data-testid="stFileUploader"] section {
    border: 2px dashed #C4B5FD !important;
    border-radius: 12px !important;
    background: #F5F3FF !important;
    padding: 1.5rem 1rem !important;
    transition: all 0.15s ease;
}

div[data-testid="stFileUploader"] section:hover {
    border-color: #8B5CF6 !important;
    background: #EDE9FE !important;
}

div[data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, #8B5CF6, #7C3AED) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.375rem 1rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    box-shadow: 0 2px 6px rgba(139, 92, 246, 0.2) !important;
}

div[data-testid="stFileUploader"] button:hover {
    box-shadow: 0 3px 10px rgba(139, 92, 246, 0.3) !important;
}

div[data-testid="stFileUploader"] span[data-testid="stFileUploaderFileName"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
    color: #6B7280 !important;
}

div[data-testid="stFileUploader"] small,
div[data-testid="stFileUploader"] span,
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderFileLimit"],
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderMsg"] {
    color: #7C3AED !important;
    font-weight: 600 !important;
    font-size: 0.7rem !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Chat input */
.stChatInputContainer {
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}

.stChatInputContainer:focus-within {
    border-color: #8B5CF6 !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.12) !important;
}

div.stAlert {
    border-radius: 12px;
    border: 1px solid #E5E7EB;
}

div.stInfo {
    background: #F0F0FF;
    border: 1px solid #E0D7FF;
    color: #5B21B6;
}

div.stSuccess {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    color: #166534;
}

div.stWarning {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    color: #92400E;
}

div.stError {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    color: #991B1B;
}

hr {
    border-color: #E5E7EB;
    margin: 1.5rem 0;
}

div[data-testid="stMetricValue"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1.5rem;
    color: #111827;
}

div[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 0.75rem;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

code {
    background: #F1F5F9;
    border-radius: 6px;
    padding: 0.125rem 0.375rem;
    font-size: 0.85em;
    color: #8B5CF6;
}

blockquote {
    border-left: 3px solid #8B5CF6;
    padding-left: 1rem;
    color: #6B7280;
    margin: 1rem 0;
}

.custom-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.custom-card-header {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    color: #111827;
    margin-bottom: 0.75rem;
}

.custom-badge {
    display: inline-block;
    background: #F0F0FF;
    color: #7C3AED;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    border: 1px solid #E0D7FF;
}

.logo-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.5rem;
    color: #111827;
    letter-spacing: -0.03em;
}

.logo-accent {
    color: #8B5CF6;
}

.sidebar-section-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 600;
    font-size: 0.75rem;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.75rem;
}
"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

if "pdf_id" not in st.session_state:
    st.session_state.pdf_id = ""
if "pdf_loaded" not in st.session_state:
    st.session_state.pdf_loaded = False
if "documents" not in st.session_state:
    st.session_state.documents = None
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "full_text" not in st.session_state:
    st.session_state.full_text = ""
if "cover_text" not in st.session_state:
    st.session_state.cover_text = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""
if "pdf_pages" not in st.session_state:
    st.session_state.pdf_pages = 0
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "validation_result" not in st.session_state:
    st.session_state.validation_result = None

render_sidebar()

tabs = st.tabs(["Analisis", "Chat"])

with tabs[0]:
    render_analysis_tab()

with tabs[1]:
    render_chat_tab()

st.divider()
st.markdown(
    '<p style="color: #9CA3AF; font-size: 0.75rem; text-align: center;">'
    "ThesisMind v1.0 &mdash; Built with LangChain, LangGraph, Streamlit & Google Gemini</p>",
    unsafe_allow_html=True,
)
