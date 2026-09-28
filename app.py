"""
ReviewMind: A Code Review Agent that learns how your team reviews code.
Premium Dark AI Developer Dashboard Interface.
"""

import os
import re
from datetime import datetime
import streamlit as st
from typing import List, Optional, Dict, Any

from src.config import Settings, get_settings, update_settings
from src.models import ReviewResult, ReviewIssue, MemoryItem
from src.memory import HindsightMemoryManager
from src.reviewer import CodeReviewer
from demo_samples import DEMO_SAMPLES, SAMPLES_BY_ID, get_sample_by_id

# Configure page
st.set_page_config(
    page_title="ReviewMind | Team Memory Code Review Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Dark AI / SaaS Dashboard Styling
st.markdown(
    """
    <style>
    /* Global Background and Typography */
    .stApp {
        background-color: #090514;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Header branding */
    .brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #FFFFFF 30%, #E879F9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }
    .brand-tagline {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-top: 4px;
        margin-bottom: 20px;
    }
    
    /* Dashboard Cards */
    .dash-card {
        background-color: #120C24;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
    }
    
    .dash-card-glow {
        background-color: #130D26;
        border: 1px solid rgba(217, 70, 239, 0.28);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 0 25px rgba(217, 70, 239, 0.12), 0 4px 20px rgba(0, 0, 0, 0.4);
    }

    /* Metric Box */
    .metric-card {
        background-color: #160F2E;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 14px 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94A3B8;
        margin-top: 4px;
        font-weight: 600;
    }
    
    /* Badges */
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.16);
        color: #FCA5A5 !important;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.2);
    }
    .badge-high {
        background-color: rgba(249, 115, 22, 0.16);
        color: #FDBA74 !important;
        border: 1px solid rgba(249, 115, 22, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        box-shadow: 0 0 10px rgba(249, 115, 22, 0.2);
    }
    .badge-medium {
        background-color: rgba(234, 179, 8, 0.16);
        color: #FDE047 !important;
        border: 1px solid rgba(234, 179, 8, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        box-shadow: 0 0 10px rgba(234, 179, 8, 0.2);
    }
    .badge-low {
        background-color: rgba(34, 197, 94, 0.16);
        color: #86EFAC !important;
        border: 1px solid rgba(34, 197, 94, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        box-shadow: 0 0 10px rgba(34, 197, 94, 0.2);
    }
    .badge-magenta {
        background-color: rgba(217, 70, 239, 0.15);
        color: #F472B6 !important;
        border: 1px solid rgba(217, 70, 239, 0.45);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        box-shadow: 0 0 12px rgba(217, 70, 239, 0.25);
    }
    
    /* Hindsight Memory Used - Prominent Showcase Card */
    .memory-applied-container {
        background: linear-gradient(135deg, rgba(217, 70, 239, 0.08) 0%, rgba(139, 92, 246, 0.06) 100%);
        border: 1px solid rgba(217, 70, 239, 0.4);
        border-radius: 14px;
        padding: 16px 20px;
        margin-top: 14px;
        margin-bottom: 18px;
        box-shadow: 0 0 30px rgba(217, 70, 239, 0.15);
    }
    .memory-rule-card {
        background-color: #0E081D;
        border: 1px solid rgba(217, 70, 239, 0.25);
        border-left: 4px solid #D946EF;
        border-radius: 10px;
        padding: 14px 16px;
        margin-top: 10px;
        margin-bottom: 8px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35);
    }
    
    /* Issue Card */
    .issue-card {
        background-color: #120C24;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    
    /* Memory Item Card */
    .memory-item-card {
        background-color: #140E29;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    
    /* Streamlit Input & Widget Dark Styling */
    .stTextArea textarea {
        background-color: #0D081B !important;
        color: #F8FAFC !important;
        border: 1px solid rgba(217, 70, 239, 0.22) !important;
        border-radius: 10px !important;
        font-family: "JetBrains Mono", Menlo, Consolas, Monaco, monospace !important;
        font-size: 0.9rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #D946EF !important;
        box-shadow: 0 0 15px rgba(217, 70, 239, 0.3) !important;
    }
    
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #140E29 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
        color: #F8FAFC !important;
    }
    
    /* Primary Action Buttons */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #D946EF 0%, #8B5CF6 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        box-shadow: 0 0 20px rgba(217, 70, 239, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    .stButton button[kind="primary"]:hover {
        box-shadow: 0 0 28px rgba(217, 70, 239, 0.6) !important;
        transform: translateY(-1px);
    }
    
    /* Secondary Buttons */
    .stButton button[kind="secondary"] {
        background-color: #171030 !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
    }
    .stButton button[kind="secondary"]:hover {
        border-color: #D946EF !important;
        color: #FFFFFF !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0C0719 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    
    /* Sidebar radio navigation */
    div[data-testid="stSidebar"] .stRadio > div {
        gap: 6px;
    }
    div[data-testid="stSidebar"] .stRadio label {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 2px;
        transition: all 0.15s ease;
    }
    div[data-testid="stSidebar"] .stRadio label:hover {
        background-color: rgba(217, 70, 239, 0.08);
        border-color: rgba(217, 70, 239, 0.25);
    }
    
    /* Pipeline Step Box */
    .pipe-step {
        background: #110B24;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 10px 14px;
        text-align: center;
        flex: 1;
        min-width: 120px;
    }
    .pipe-step-active {
        background: rgba(217, 70, 239, 0.09);
        border: 1px solid rgba(217, 70, 239, 0.4);
        border-radius: 10px;
        padding: 10px 14px;
        text-align: center;
        flex: 1;
        min-width: 120px;
        box-shadow: 0 0 15px rgba(217, 70, 239, 0.15);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def resolve_team_rule_text(rule_ref: str, recalled_memories: List[str]) -> str:
    """
    Resolve a team rule reference (e.g. 'RULE-1', '[RULE-1]', or partial citation)
    to the authentic recalled Hindsight memory text.
    """
    if not recalled_memories:
        return rule_ref

    # 1. Match explicit index patterns like 'RULE-1', 'RULE_1', '[RULE-1]'
    match = re.search(r"RULE[-_ ]?(\d+)", rule_ref, re.IGNORECASE)
    if match:
        idx = int(match.group(1)) - 1
        if 0 <= idx < len(recalled_memories):
            return recalled_memories[idx]

    # 2. Check if rule_ref matches any recalled memory directly or partially
    cleaned_ref = rule_ref.strip().lower()
    for mem in recalled_memories:
        cleaned_mem = mem.strip().lower()
        if cleaned_ref == cleaned_mem or cleaned_ref in cleaned_mem or cleaned_mem in cleaned_ref:
            return mem

    # 3. Match numeric reference like '#1', 'Rule 1', '(1)'
    num_match = re.search(r"\b(\d+)\b", rule_ref)
    if num_match:
        idx = int(num_match.group(1)) - 1
        if 0 <= idx < len(recalled_memories):
            return recalled_memories[idx]

    # 4. If rule_ref has substantial text, return it directly; otherwise fallback to first recalled memory
    if len(rule_ref.strip()) > 30:
        return rule_ref

    return recalled_memories[0] if recalled_memories else rule_ref


def get_severity_badge(severity: str) -> str:
    """Return styled HTML badge for issue severity."""
    sev = severity.lower()
    if sev == "critical":
        return '<span class="badge-critical">CRITICAL</span>'
    elif sev == "high":
        return '<span class="badge-high">HIGH</span>'
    elif sev == "medium":
        return '<span class="badge-medium">MEDIUM</span>'
    return '<span class="badge-low">LOW</span>'


def get_risk_badge(risk: str) -> str:
    """Return styled HTML badge for overall risk."""
    r = risk.lower()
    if r == "critical":
        return '<span class="badge-critical">RISK: CRITICAL</span>'
    elif r == "high":
        return '<span class="badge-high">RISK: HIGH</span>'
    elif r == "medium":
        return '<span class="badge-medium">RISK: MEDIUM</span>'
    return '<span class="badge-low">RISK: LOW</span>'


# Initialize session state variables
if "config" not in st.session_state:
    st.session_state.config = get_settings()

if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = HindsightMemoryManager(st.session_state.config)

if "reviewer" not in st.session_state:
    st.session_state.reviewer = CodeReviewer(
        config=st.session_state.config,
        memory_manager=st.session_state.memory_manager,
    )

if "last_review" not in st.session_state:
    st.session_state.last_review = None

if "last_generic_review" not in st.session_state:
    st.session_state.last_generic_review = None

if "review_logs" not in st.session_state:
    st.session_state.review_logs = []

if "review_history" not in st.session_state:
    st.session_state.review_history = []


# ==============================================================================
# SIDEBAR - COMPACT MODERN DEVELOPER NAVIGATION
# ==============================================================================
with st.sidebar:
    # Logo & Brand Header
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 18px;">
            <div style="width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #EC4899, #8B5CF6); display: flex; align-items: center; justify-content: center; font-size: 20px; box-shadow: 0 0 16px rgba(236, 72, 153, 0.45);">
                🧠
            </div>
            <div>
                <div style="font-weight: 800; font-size: 1.25rem; letter-spacing: -0.02em; color: #FFFFFF; line-height: 1.1;">ReviewMind</div>
                <div style="font-size: 0.7rem; color: #D946EF; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px;">Organizational Memory</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation Menu
    nav_option = st.radio(
        "NAVIGATION",
        options=[
            "🔍 Code Review",
            "🧠 Team Memory",
            "📜 Review History",
            "📊 Analytics",
            "🧪 Interactive Demo",
            "⚙️ Settings",
            "ℹ️ Architecture",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Service Health Status Block
    groq_ready = st.session_state.config.is_groq_ready()
    hindsight_ready = st.session_state.config.is_hindsight_ready()

    groq_dot = "#22C55E" if groq_ready else "#EF4444"
    groq_label = "Ready" if groq_ready else "No Key"
    hs_dot = "#22C55E" if hindsight_ready else "#EF4444"
    hs_label = "Ready" if hindsight_ready else "No Key"

    st.markdown(
        f"""
        <div style="background: rgba(255, 255, 255, 0.025); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 12px 14px; margin-bottom: 18px;">
            <div style="font-size: 0.7rem; text-transform: uppercase; color: #64748B; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">INTELLIGENCE ENGINE</div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem; margin-bottom: 6px;">
                <span style="color: #CBD5E1;">Groq LLM</span>
                <span style="display: flex; align-items: center; gap: 6px; color: {groq_dot}; font-weight: 600; font-size: 0.8rem;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background-color: {groq_dot}; box-shadow: 0 0 8px {groq_dot}; display: inline-block;"></span>
                    {groq_label}
                </span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem;">
                <span style="color: #CBD5E1;">Hindsight Bank</span>
                <span style="display: flex; align-items: center; gap: 6px; color: {hs_dot}; font-weight: 600; font-size: 0.8rem;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background-color: {hs_dot}; box-shadow: 0 0 8px {hs_dot}; display: inline-block;"></span>
                    {hs_label}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bank Quick Action
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("🔌 Ping Test", use_container_width=True, type="secondary"):
            with st.spinner("Pinging..."):
                ok, msg = st.session_state.memory_manager.test_connection()
                if ok:
                    st.toast(msg, icon="🟢")
                else:
                    st.toast(msg, icon="🔴")
    with col_sb2:
        if st.button("🌱 Seed Rules", use_container_width=True, type="secondary"):
            with st.spinner("Seeding..."):
                count, msgs = st.session_state.memory_manager.seed_default_standards()
                if count > 0:
                    st.toast(f"Seeded {count} rules in Hindsight!", icon="🌱")
                else:
                    st.toast(msgs[0] if msgs else "No rules seeded.", icon="⚠️")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.caption("Active Bank: `" + st.session_state.config.hindsight_bank_id + "`")
    st.caption("Model: `" + st.session_state.config.groq_model + "`")


# ==============================================================================
# VIEW 1: CODE REVIEW (PRIMARY SCREEN)
# ==============================================================================
if nav_option == "🔍 Code Review":
    st.markdown('<div class="brand-title">Code Review Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tagline">Persistent organizational memory that accumulates and recalls team-specific review knowledge across review sessions.</div>',
        unsafe_allow_html=True,
    )

    col_code, col_review = st.columns([1.05, 1.15], gap="large")

    # LEFT COLUMN: Code Input & Options
    with col_code:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 700; font-size: 1.05rem; color: #FFFFFF;">1. Source Code Input</span>
                <span style="font-size: 0.78rem; color: #94A3B8;">Treats submitted code as data</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Preset Selector
        sample_options = ["Custom Code"] + [s.title for s in DEMO_SAMPLES]
        selected_sample_title = st.selectbox(
            "Load Demo Scenario:",
            options=sample_options,
            index=1,  # Default to SQL Injection demo
            help="Choose a pre-configured educational demo scenario or write custom code",
        )

        initial_code = ""
        initial_lang = "python"
        selected_sample = None

        if selected_sample_title != "Custom Code":
            for s in DEMO_SAMPLES:
                if s.title == selected_sample_title:
                    selected_sample = s
                    initial_code = s.vulnerable_code
                    initial_lang = s.language
                    break

        col_cfg1, col_cfg2 = st.columns([1, 1.3])
        with col_cfg1:
            language = st.selectbox(
                "Language",
                options=["python", "javascript", "typescript", "go", "java", "sql", "c++", "rust"],
                index=0,
            )
        with col_cfg2:
            mode_choice = st.radio(
                "Memory Mode",
                options=["🧠 With Hindsight Memory", "⚡ Generic Review"],
                index=0,
                horizontal=True,
                help="With Memory recalls team standards from Hindsight; Generic performs textbook LLM review.",
            )

        if selected_sample:
            st.markdown(
                f"""
                <div style="background: rgba(147, 51, 234, 0.08); border: 1px solid rgba(147, 51, 234, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; font-size: 0.84rem; color: #E2E8F0;">
                    <span style="color: #E879F9; font-weight: 700;">Scenario:</span> {selected_sample.description}<br/>
                    <span style="color: #A78BFA; font-weight: 700;">Hindsight Target Standard:</span> <i>{selected_sample.expected_team_rule}</i>
                </div>
                """,
                unsafe_allow_html=True,
            )

        code_input = st.text_area(
            "Editor",
            value=initial_code,
            height=280,
            label_visibility="collapsed",
            help="Paste source code snippet here",
        )

        col_b_run, col_b_auto = st.columns([1.5, 1])
        with col_b_run:
            run_btn = st.button(
                "🚀 Execute ReviewMind Review",
                type="primary",
                use_container_width=True,
                disabled=not code_input.strip(),
            )
        with col_b_auto:
            auto_retain_toggle = st.checkbox(
                "Auto-retain lessons in Hindsight",
                value=True,
                help="Automatically stores newly identified reusable rules back into Hindsight",
            )

    # EXECUTE REVIEW
    if run_btn:
        with st.spinner("Querying Hindsight memory bank & generating grounded review findings..."):
            use_memory = "With Hindsight Memory" in mode_choice

            result, logs = st.session_state.reviewer.review(
                code=code_input,
                language=language,
                use_memory=use_memory,
                auto_retain=auto_retain_toggle,
            )

            st.session_state.last_review = result
            st.session_state.review_logs = logs

            # Record in session history
            history_entry = {
                "id": len(st.session_state.review_history) + 1,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "date": datetime.now().strftime("%b %d, %Y"),
                "title": selected_sample_title if selected_sample_title != "Custom Code" else "Custom Code Snippet",
                "language": language,
                "risk": result.risk,
                "issues_count": len(result.issues),
                "used_memory": result.used_memory,
                "rules_used_count": len(result.team_rules_used),
                "rules_used": result.team_rules_used,
                "learning_count": len(result.learning),
                "result": result,
                "code": code_input,
            }
            st.session_state.review_history.insert(0, history_entry)

    # RIGHT COLUMN: Review Results & Findings
    with col_review:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 700; font-size: 1.05rem; color: #FFFFFF;">2. Grounded Findings & Analysis</span>
                <span style="font-size: 0.78rem; color: #94A3B8;">Structured JSON Engine</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.last_review:
            res: ReviewResult = st.session_state.last_review

            # Summary Header Card
            st.markdown(
                f"""
                <div class="dash-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div>{get_risk_badge(res.risk)}</div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <span class="{'badge-magenta' if res.used_memory else 'badge-low'}">
                                {'🧠 HINDSIGHT ACTIVE' if res.used_memory else '⚡ GENERIC REVIEW'}
                            </span>
                            <span style="font-size: 0.8rem; color: #94A3B8;">{res.model}</span>
                        </div>
                    </div>
                    <div style="font-size: 0.95rem; color: #F1F5F9; line-height: 1.55; margin-bottom: 12px;">
                        {res.summary}
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 14px;">
                        <div class="metric-card">
                            <div class="metric-value" style="color: #F87171;">{len([i for i in res.issues if i.severity == 'critical'])}</div>
                            <div class="metric-label">Critical</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" style="color: #FB923C;">{len([i for i in res.issues if i.severity == 'high'])}</div>
                            <div class="metric-label">High</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" style="color: #FBBF24;">{len([i for i in res.issues if i.severity == 'medium'])}</div>
                            <div class="metric-label">Medium</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" style="color: #4ADE80;">{len([i for i in res.issues if i.severity == 'low'])}</div>
                            <div class="metric-label">Low</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # PROMINENT SHOWCASE: HINDSIGHT MEMORY USED
            if res.team_rules_used:
                resolved_rules = []
                seen_rules = set()
                for rule in res.team_rules_used:
                    actual_text = resolve_team_rule_text(rule, res.recalled_memories)
                    if actual_text and actual_text not in seen_rules:
                        seen_rules.add(actual_text)
                        resolved_rules.append(actual_text)

                rules_html = "".join([
                    f"""
                    <div class="memory-rule-card">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                            <div style="color: #E879F9; font-weight: 800; font-size: 0.92rem; display: flex; align-items: center; gap: 6px;">
                                <span>📌</span> Team Standard Enforced
                            </div>
                            <span style="font-size: 0.72rem; color: #C084FC; font-weight: 700; text-transform: uppercase; background: rgba(192, 132, 252, 0.15); border: 1px solid rgba(192, 132, 252, 0.3); padding: 2px 8px; border-radius: 999px;">Hindsight Bank</span>
                        </div>
                        <div style="color: #F8FAFC; font-size: 0.95rem; line-height: 1.55; padding-left: 20px;">
                            "{rule_text}"
                        </div>
                    </div>
                    """
                    for rule_text in resolved_rules
                ])

                st.markdown(
                    f"""
                    <div class="memory-applied-container">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 1.3rem;">🧠</span>
                                <span style="color: #FFFFFF; font-size: 1.05rem; font-weight: 800; letter-spacing: -0.01em;">HINDSIGHT MEMORY APPLIED</span>
                            </div>
                            <span class="badge-magenta">{len(resolved_rules)} RULES ENFORCED</span>
                        </div>
                        <div style="color: #CBD5E1; font-size: 0.88rem; margin-bottom: 10px;">
                            The agent recalled organizational memory from Hindsight and enforced your team's specific standards:
                        </div>
                        {rules_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif res.used_memory:
                st.markdown(
                    """
                    <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 12px 16px; margin: 12px 0; color: #94A3B8; font-size: 0.88rem;">
                        🧠 <b>Hindsight Memory Checked:</b> Connected to bank, but no team-specific rules matched this specific snippet.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ISSUES LIST
            if res.issues:
                st.markdown("<div style='font-weight: 700; font-size: 0.98rem; color: #FFFFFF; margin: 14px 0 8px 0;'>Identified Review Findings</div>", unsafe_allow_html=True)
                for idx, issue in enumerate(res.issues, start=1):
                    badge_html = get_severity_badge(issue.severity)
                    with st.expander(f"{idx}. [{issue.severity.upper()}] {issue.title} ({issue.line})", expanded=(idx == 1)):
                        st.markdown(
                            f"""
                            <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 8px;">
                                {badge_html}
                                <span style="color: #E879F9; font-size: 0.85rem; font-weight: 600;">Location: {issue.line}</span>
                            </div>
                            <div style="color: #E2E8F0; font-size: 0.92rem; line-height: 1.5; margin-bottom: 10px;">
                                {issue.why}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if issue.suggestion:
                            st.markdown(
                                f"""
                                <div style="font-size: 0.82rem; color: #A78BFA; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">Recommended Fix:</div>
                                """,
                                unsafe_allow_html=True,
                            )
                            st.code(issue.suggestion, language="python")
            else:
                st.markdown(
                    """
                    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 10px; padding: 16px; text-align: center; color: #86EFAC;">
                        🎉 No issues detected! Code adheres to all team standards and quality baselines.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Continuous Learning Loop
            if res.learning:
                st.markdown(
                    """
                    <div style="background: #110B22; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px 16px; margin-top: 16px;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <div style="color: #F8FAFC; font-weight: 700; font-size: 0.92rem; display: flex; align-items: center; gap: 6px;">
                                <span>🎓</span> Continuous Learning Loop (Extracted Lessons)
                            </div>
                            <span class="badge-magenta">Hindsight Retain</span>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )
                for lesson in res.learning:
                    st.markdown(f"<div style='color: #CBD5E1; font-size: 0.9rem; padding: 4px 0 4px 14px;'>• <i>{lesson}</i></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Recalled Raw Memories & Trace
            with st.expander("🔍 Recalled Hindsight Memories & Trace"):
                st.caption(f"Bank ID: {st.session_state.config.hindsight_bank_id}")
                if res.recalled_memories:
                    for m_idx, m_text in enumerate(res.recalled_memories, start=1):
                        st.markdown(f"**[Fact {m_idx}]:** {m_text}")
                else:
                    st.info("No memories recalled for this run.")
                st.divider()
                st.caption("Execution Trace:")
                for log_line in st.session_state.review_logs:
                    st.text(log_line)

        else:
            # Clean Empty State
            st.markdown(
                """
                <div class="dash-card" style="text-align: center; padding: 48px 24px;">
                    <div style="font-size: 2.5rem; margin-bottom: 12px;">🧠</div>
                    <div style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF; margin-bottom: 6px;">Awaiting Review Execution</div>
                    <div style="color: #94A3B8; font-size: 0.9rem; max-width: 400px; margin: 0 auto 20px auto;">
                        Select a demo scenario or paste your source code on the left, then click <b>Execute ReviewMind Review</b>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # MEMORY VISUALIZATION PIPELINE (Always visible beneath editor)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="dash-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <div style="font-weight: 800; font-size: 0.95rem; color: #FFFFFF; letter-spacing: -0.01em;">
                    🔄 ORGANIZATIONAL MEMORY PIPELINE
                </div>
                <span class="badge-magenta">Hindsight Closed-Loop</span>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; justify-content: space-between;">
                <div class="pipe-step">
                    <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 700;">STEP 1</div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.88rem; margin: 2px 0;">Source Code</div>
                    <div style="font-size: 0.76rem; color: #A78BFA;">Language & AST</div>
                </div>
                <div style="display: flex; align-items: center; color: #D946EF;">➔</div>
                <div class="pipe-step-active">
                    <div style="font-size: 0.72rem; color: #E879F9; font-weight: 700;">STEP 2</div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.88rem; margin: 2px 0;">Hindsight Recall</div>
                    <div style="font-size: 0.76rem; color: #F472B6;">Semantic Search</div>
                </div>
                <div style="display: flex; align-items: center; color: #D946EF;">➔</div>
                <div class="pipe-step">
                    <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 700;">STEP 3</div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.88rem; margin: 2px 0;">Team Knowledge</div>
                    <div style="font-size: 0.76rem; color: #A78BFA;">Standards & History</div>
                </div>
                <div style="display: flex; align-items: center; color: #D946EF;">➔</div>
                <div class="pipe-step">
                    <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 700;">STEP 4</div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.88rem; margin: 2px 0;">Groq Review</div>
                    <div style="font-size: 0.76rem; color: #A78BFA;">Grounded LLM</div>
                </div>
                <div style="display: flex; align-items: center; color: #D946EF;">➔</div>
                <div class="pipe-step-active">
                    <div style="font-size: 0.72rem; color: #E879F9; font-weight: 700;">STEP 5</div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.88rem; margin: 2px 0;">Lesson Synthesizer</div>
                    <div style="font-size: 0.76rem; color: #F472B6;">Reusable Rules</div>
                </div>
                <div style="display: flex; align-items: center; color: #D946EF;">➔</div>
                <div class="pipe-step">
                    <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 700;">STEP 6</div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.88rem; margin: 2px 0;">Hindsight Retain</div>
                    <div style="font-size: 0.76rem; color: #A78BFA;">Persistent Bank</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# VIEW 2: TEAM MEMORY (HINDSIGHT DASHBOARD)
# ==============================================================================
elif nav_option == "🧠 Team Memory":
    st.markdown('<div class="brand-title">Team Organizational Memory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tagline">Manage and explore accumulated team engineering standards, architectural decisions, and past review lessons stored in Hindsight.</div>',
        unsafe_allow_html=True,
    )

    # Top Metric Bar
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-value" style="color: #E879F9;">reviewmind-team</div>
                <div class="metric-label">Active Bank ID</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_m2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-value" style="color: #4ADE80;">Active</div>
                <div class="metric-label">Hindsight Status</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(st.session_state.review_history)}</div>
                <div class="metric-label">Reviews in Session</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_m4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-value" style="color: #F472B6;">Semantic</div>
                <div class="metric-label">Recall Engine</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    col_t_left, col_t_right = st.columns([1.8, 1.2], gap="large")

    with col_t_left:
        st.markdown("#### 🔍 Real-Time Semantic Memory Recall")
        search_query = st.text_input(
            "Search Knowledge Bank:",
            value="SQL database queries and parameterized statements",
            help="Query Hindsight semantic index",
        )
        if st.button("Query Hindsight Bank", type="primary") or search_query:
            if not st.session_state.memory_manager.is_available():
                st.warning("⚠️ HINDSIGHT_API_KEY is not configured in `.env` or sidebar.")
            else:
                with st.spinner(f"Querying memory bank '{st.session_state.config.hindsight_bank_id}'..."):
                    memories, err = st.session_state.memory_manager.recall_memories(
                        query=search_query,
                        budget="high",
                    )
                    if err:
                        st.error(err)
                    elif memories:
                        st.markdown(f"<div style='font-size: 0.88rem; color: #A78BFA; margin-bottom: 10px;'>Found <b>{len(memories)}</b> relevant memory units:</div>", unsafe_allow_html=True)
                        for idx, mem in enumerate(memories, start=1):
                            score_tag = f"<span class='badge-magenta'>Score: {mem.score:.2f}</span>" if mem.score else ""
                            st.markdown(
                                f"""
                                <div class="memory-item-card">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                        <span style="color: #E879F9; font-weight: 700; font-size: 0.85rem;">#{idx} [{mem.category.upper()}]</span>
                                        {score_tag}
                                    </div>
                                    <div style="color: #F8FAFC; font-size: 0.95rem; line-height: 1.5; margin-bottom: 8px;">
                                        {mem.text}
                                    </div>
                                    <div style="font-size: 0.78rem; color: #94A3B8;">
                                        Tags: {', '.join(mem.tags) if mem.tags else 'standards'}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("No matching memories in bank. Click 'Seed Standards Now' to populate baseline engineering rules.")

    with col_t_right:
        st.markdown("#### ⚡ Bank Actions")
        with st.container():
            st.markdown(
                """
                <div class="dash-card">
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem; margin-bottom: 6px;">Seed Baseline Standards</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-bottom: 12px;">Populates Hindsight with core rules for SQL, Exception exposure, Layering, and Validation.</div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("🌱 Seed Standards Now", use_container_width=True, type="secondary"):
                with st.spinner("Seeding..."):
                    count, msgs = st.session_state.memory_manager.seed_default_standards()
                    if count > 0:
                        st.success(f"Seeded {count} rules in '{st.session_state.config.hindsight_bank_id}'!")
                    for m in msgs:
                        st.caption(f"• {m}")
            st.markdown("</div>", unsafe_allow_html=True)

        with st.container():
            st.markdown(
                """
                <div class="dash-card">
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem; margin-bottom: 6px;">Add Custom Team Standard</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-bottom: 12px;">Store a new engineering standard or architectural policy directly into Hindsight.</div>
                """,
                unsafe_allow_html=True,
            )
            custom_rule = st.text_area("Rule Statement:", placeholder="e.g. Always use ISO-8601 for timestamp formatting.", height=80)
            c_cat = st.selectbox("Category:", ["team_standard", "common_mistake", "architectural_preference", "review_lesson"])
            c_lang = st.selectbox("Language:", ["general", "python", "javascript", "go", "sql"])
            c_tags = st.text_input("Tags:", value="standards, convention")

            if st.button("Save Rule to Hindsight", use_container_width=True, type="primary"):
                if custom_rule.strip():
                    tags_list = [t.strip() for t in c_tags.split(",") if t.strip()]
                    ok, msg = st.session_state.memory_manager.retain_knowledge(
                        content=custom_rule,
                        category=c_cat,
                        language=c_lang,
                        source="manual_policy",
                        tags=tags_list,
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please provide rule text.")
            st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# VIEW 3: REVIEW HISTORY
# ==============================================================================
elif nav_option == "📜 Review History":
    st.markdown('<div class="brand-title">Session Review History</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tagline">Log of all code reviews conducted in the current session. Grounded with Hindsight memory.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.review_history:
        st.markdown(
            """
            <div class="dash-card" style="text-align: center; padding: 48px 24px;">
                <div style="font-size: 2.5rem; margin-bottom: 12px;">📜</div>
                <div style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF; margin-bottom: 6px;">No Reviews in Session Yet</div>
                <div style="color: #94A3B8; font-size: 0.9rem; max-width: 400px; margin: 0 auto 20px auto;">
                    Navigate to <b>Code Review</b> in the sidebar and run your first code review to begin logging history.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<div style='font-size: 0.9rem; color: #A78BFA; margin-bottom: 14px;'>Displaying <b>{len(st.session_state.review_history)}</b> completed reviews:</div>", unsafe_allow_html=True)

        for item in st.session_state.review_history:
            badge_r = get_risk_badge(item["risk"])
            mem_tag = "<span class='badge-magenta'>🧠 HINDSIGHT APPLIED</span>" if item["used_memory"] else "<span class='badge-low'>⚡ GENERIC</span>"
            with st.expander(f"Review #{item['id']} • {item['title']} • {item['timestamp']} • {item['language'].upper()}", expanded=(item["id"] == 1)):
                col_h1, col_h2, col_h3 = st.columns([1, 1, 1])
                with col_h1:
                    st.markdown(f"**Risk Level:** {badge_r}", unsafe_allow_html=True)
                with col_h2:
                    st.markdown(f"**Mode:** {mem_tag}", unsafe_allow_html=True)
                with col_h3:
                    st.markdown(f"**Issues Detected:** `{item['issues_count']}`")

                res_obj: ReviewResult = item["result"]
                st.markdown(f"**Summary:** {res_obj.summary}")

                if res_obj.team_rules_used:
                    st.markdown("**🛡️ Team Rules Applied:**")
                    for r in res_obj.team_rules_used:
                        resolved = resolve_team_rule_text(r, res_obj.recalled_memories)
                        st.markdown(f"- 📌 *{resolved}*")

                st.markdown("**Source Code Analyzed:**")
                st.code(item["code"], language=item["language"])


# ==============================================================================
# VIEW 4: ANALYTICS
# ==============================================================================
elif nav_option == "📊 Analytics":
    st.markdown('<div class="brand-title">Review Quality Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tagline">Real-time statistics derived strictly from actual review executions in the current session.</div>',
        unsafe_allow_html=True,
    )

    history = st.session_state.review_history
    total_reviews = len(history)

    if total_reviews == 0:
        st.markdown(
            """
            <div class="dash-card" style="text-align: center; padding: 48px 24px;">
                <div style="font-size: 2.5rem; margin-bottom: 12px;">📊</div>
                <div style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF; margin-bottom: 6px;">No Analytics Data Available</div>
                <div style="color: #94A3B8; font-size: 0.9rem; max-width: 400px; margin: 0 auto 20px auto;">
                    Run at least one code review in <b>Code Review</b> to generate live telemetry and statistics.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Calculate real metrics
        critical_count = sum(len([i for i in h["result"].issues if i.severity == "critical"]) for h in history)
        high_count = sum(len([i for i in h["result"].issues if i.severity == "high"]) for h in history)
        med_count = sum(len([i for i in h["result"].issues if i.severity == "medium"]) for h in history)
        low_count = sum(len([i for i in h["result"].issues if i.severity == "low"]) for h in history)
        total_issues = critical_count + high_count + med_count + low_count

        memory_reviews_count = sum(1 for h in history if h["used_memory"])
        memory_application_rate = int((memory_reviews_count / total_reviews) * 100) if total_reviews else 0
        total_rules_enforced = sum(h["rules_used_count"] for h in history)
        total_lessons_retained = sum(h["learning_count"] for h in history)

        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        with col_a1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{total_reviews}</div>
                    <div class="metric-label">Reviews Run</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_a2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #E879F9;">{memory_application_rate}%</div>
                    <div class="metric-label">Memory Utilization</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_a3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #F87171;">{total_issues}</div>
                    <div class="metric-label">Total Issues Found</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_a4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #4ADE80;">{total_rules_enforced}</div>
                    <div class="metric-label">Team Rules Enforced</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        col_g1, col_g2 = st.columns([1, 1], gap="large")
        with col_g1:
            st.markdown("#### 🚨 Issues Breakdown by Severity")
            st.markdown(
                f"""
                <div class="dash-card">
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                            <span style="color: #F87171; font-weight: 700;">Critical Severity</span>
                            <span style="color: #FFFFFF;">{critical_count}</span>
                        </div>
                        <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
                            <div style="width: {int((critical_count/total_issues)*100) if total_issues else 0}%; height: 100%; background: #EF4444;"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                            <span style="color: #FB923C; font-weight: 700;">High Severity</span>
                            <span style="color: #FFFFFF;">{high_count}</span>
                        </div>
                        <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
                            <div style="width: {int((high_count/total_issues)*100) if total_issues else 0}%; height: 100%; background: #F97316;"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                            <span style="color: #FBBF24; font-weight: 700;">Medium Severity</span>
                            <span style="color: #FFFFFF;">{med_count}</span>
                        </div>
                        <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
                            <div style="width: {int((med_count/total_issues)*100) if total_issues else 0}%; height: 100%; background: #EAB308;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                            <span style="color: #4ADE80; font-weight: 700;">Low Severity</span>
                            <span style="color: #FFFFFF;">{low_count}</span>
                        </div>
                        <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
                            <div style="width: {int((low_count/total_issues)*100) if total_issues else 0}%; height: 100%; background: #22C55E;"></div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_g2:
            st.markdown("#### 🧠 Hindsight Organizational Retention")
            st.markdown(
                f"""
                <div class="dash-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="color: #CBD5E1; font-size: 0.92rem;">Total Rules Recalled & Applied:</span>
                        <span style="font-weight: 800; color: #E879F9; font-size: 1.1rem;">{total_rules_enforced}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="color: #CBD5E1; font-size: 0.92rem;">Total New Lessons Retained:</span>
                        <span style="font-weight: 800; color: #4ADE80; font-size: 1.1rem;">{total_lessons_retained}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #CBD5E1; font-size: 0.92rem;">Average Issues per Review:</span>
                        <span style="font-weight: 800; color: #FFFFFF; font-size: 1.1rem;">{(total_issues/total_reviews):.1f}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==============================================================================
# VIEW 5: INTERACTIVE DEMO (WITHOUT MEMORY VS WITH MEMORY)
# ==============================================================================
elif nav_option == "🧪 Interactive Demo":
    st.markdown('<div class="brand-title">Hackathon Demo: Before & After Memory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tagline">Visualizing the exact difference between generic AI code review and memory-augmented review.</div>',
        unsafe_allow_html=True,
    )

    col_demo_l, col_demo_r = st.columns(2, gap="large")

    with col_demo_l:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #CBD5E1; font-size: 1rem; margin-bottom: 4px;">⚡ WITHOUT MEMORY (GENERIC)</div>
                <div style="font-size: 0.82rem; color: #94A3B8;">Textbook general code review. Has zero awareness of your team policies or past PR decisions.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        d_code_generic = st.text_area("Generic Sample Code", value=DEMO_SAMPLES[0].vulnerable_code, height=180, key="d_code_generic")
        if st.button("Run Generic Review", key="btn_run_gen", use_container_width=True, type="secondary"):
            with st.spinner("Running generic review..."):
                g_res, _ = st.session_state.reviewer.review(
                    code=d_code_generic,
                    language="python",
                    use_memory=False,
                    auto_retain=False,
                )
                st.session_state.last_generic_review = g_res

        if st.session_state.last_generic_review:
            g = st.session_state.last_generic_review
            st.markdown(f"**Risk:** {get_risk_badge(g.risk)}", unsafe_allow_html=True)
            st.markdown(f"**Summary:** {g.summary}")
            st.markdown(
                """
                <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 10px; color: #FCA5A5; font-size: 0.85rem; margin-top: 8px;">
                    ⚠️ <b>Team Rules Applied: NONE</b><br/>Generic reviewer lacks persistent organizational memory.
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_demo_r:
        st.markdown(
            """
            <div style="background: rgba(217, 70, 239, 0.06); border: 1px solid rgba(217, 70, 239, 0.3); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #F472B6; font-size: 1rem; margin-bottom: 4px;">🧠 WITH MEMORY (HINDSIGHT)</div>
                <div style="font-size: 0.82rem; color: #E879F9;">Recalls team coding standards, enforces exact conventions, and retains newly learned lessons.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        d_code_mem = st.text_area("Memory-Augmented Sample Code", value=DEMO_SAMPLES[0].vulnerable_code, height=180, key="d_code_mem")
        if st.button("Run Hindsight Memory Review", key="btn_run_mem_demo", use_container_width=True, type="primary"):
            with st.spinner("Recalling from Hindsight..."):
                m_res, _ = st.session_state.reviewer.review(
                    code=d_code_mem,
                    language="python",
                    use_memory=True,
                    auto_retain=True,
                )
                st.session_state.last_review = m_res

        if st.session_state.last_review and st.session_state.last_review.used_memory:
            m = st.session_state.last_review
            st.markdown(f"**Risk:** {get_risk_badge(m.risk)}", unsafe_allow_html=True)
            st.markdown(f"**Summary:** {m.summary}")
            if m.team_rules_used:
                resolved_m_rules = [resolve_team_rule_text(r, m.recalled_memories) for r in m.team_rules_used]
                rules_block = "".join([f"<div style='margin-top: 4px; padding-left: 8px;'>• {r}</div>" for r in resolved_m_rules])
                st.markdown(
                    f"""
                    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 8px; padding: 12px; color: #86EFAC; font-size: 0.88rem; margin-top: 8px;">
                        🛡️ <b>Team Rules Enforced ({len(resolved_m_rules)}):</b><br/>
                        {rules_block}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ==============================================================================
# VIEW 6: SETTINGS
# ==============================================================================
elif nav_option == "⚙️ Settings":
    st.markdown('<div class="brand-title">System Configuration</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tagline">Manage Groq inference credentials, Hindsight memory bank endpoints, and model settings.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown("#### 🔑 API Credentials")

    cfg_groq = st.text_input(
        "Groq API Key:",
        value=st.session_state.config.groq_api_key,
        type="password",
        help="Required for Groq LLM inference",
    )
    cfg_hs_key = st.text_input(
        "Hindsight API Key:",
        value=st.session_state.config.hindsight_api_key,
        type="password",
        help="Required for Hindsight persistent memory layer",
    )
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cfg_hs_url = st.text_input("Hindsight API Host URL:", value=st.session_state.config.hindsight_api_url)
    with col_c2:
        cfg_hs_bank = st.text_input("Team Memory Bank ID:", value=st.session_state.config.hindsight_bank_id)

    cfg_model = st.selectbox(
        "Configurable Groq Model:",
        options=[
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
        index=0,
    )

    if st.button("Apply and Save Settings", type="primary"):
        st.session_state.config = update_settings(
            groq_api_key=cfg_groq,
            hindsight_api_key=cfg_hs_key,
            hindsight_api_url=cfg_hs_url,
            hindsight_bank_id=cfg_hs_bank,
            groq_model=cfg_model,
        )
        st.session_state.reviewer.refresh_clients()
        st.success("Configuration updated successfully!")
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# VIEW 7: ARCHITECTURE & ABOUT
# ==============================================================================
elif nav_option == "ℹ️ Architecture":
    st.markdown('<div class="brand-title">Architecture & System Design</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tagline">How ReviewMind integrates Hindsight persistent organizational memory with high-speed LLM inference.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="dash-card">
            <div style="font-weight: 800; font-size: 1.1rem; color: #FFFFFF; margin-bottom: 8px;">The Core Problem & Differentiation</div>
            <div style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6;">
                Every software engineering team accumulates institutional knowledge—conventions, recurring security pitfalls, and architectural standards.
                Traditional AI code reviewers treat every review as a clean slate, repeating the same generic feedback.<br/><br/>
                <b>ReviewMind's differentiation:</b> <i>Persistent organizational memory that accumulates and recalls team-specific review knowledge across review sessions.</i>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ```
        ==============================================================================
                                REVIEWMIND SYSTEM ARCHITECTURE
        ==============================================================================
        
                                  Developer
                                      │
                                      ▼
                           Streamlit Dashboard UI
                                      │
                                      ▼
                              ReviewMind Agent
                                 /        \\
                                /          \\
                         Recall             Prompt + Code
                              /              \\
                             ▼                ▼
                       ┌───────────┐    ┌───────────┐
                       │ Hindsight │    │ Groq LLM  │ (openai/gpt-oss-120b)
                       │  Memory   │    └─────┬─────┘
                       └─────┬─────┘          │
                             │                │
                             └───────┬────────┘
                                     │
                                     ▼
                            Structured Findings
                         (Issues, Risk, Rules Used)
                                     │
                                     ▼
                            Learning Extraction
                                     │
                                     ▼
                             Hindsight Retain
                       (Stores lessons for future)
        ==============================================================================
        ```
        """
    )
