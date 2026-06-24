"""Global look-and-feel: CSS design system + reusable layout helpers.

Centralizing styling here keeps every screen consistent and the codebase
maintainable (PRD §3.3.2(vi)). Colours follow the theme in
``.streamlit/config.toml``; custom CSS adds the branded header, product cards,
pills and hero that native widgets don't provide.
"""
from __future__ import annotations

import streamlit as st

BRAND = "Caleb Marketplace"
PRIMARY = "#4f46e5"
ACCENT = "#f59e0b"

_CSS = """
<style>
/* ---- Base typography & layout -------------------------------------- */
html, body, [class*="css"] { font-family: 'Inter','Segoe UI',sans-serif; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1200px; }

/* Trim Streamlit chrome for an app-like feel */
#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"] { right: 1rem; }

/* ---- Sidebar ------------------------------------------------------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#1e1b4b 0%,#312e81 100%);
}
[data-testid="stSidebar"] * { color: #e7e9ff !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25);
    color: #fff !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,.22); border-color: #fff;
}
[data-testid="stSidebarNav"] a span { color:#e7e9ff !important; }

/* ---- Buttons ------------------------------------------------------- */
.stButton > button, .stFormSubmitButton > button {
    border-radius: 10px; font-weight: 600; transition: all .15s ease;
    border: 1px solid #e3e5ee;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    transform: translateY(-1px); box-shadow: 0 4px 14px rgba(79,70,229,.18);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button {
    background: linear-gradient(135deg,#4f46e5,#6366f1); color:#fff; border:none;
}

/* ---- Cards (bordered containers) ----------------------------------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important; border-color:#eceef5 !important;
    box-shadow: 0 1px 3px rgba(16,24,40,.06); transition: box-shadow .18s ease,
        transform .18s ease; background:#fff;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 10px 28px rgba(16,24,40,.10); transform: translateY(-2px);
}

/* ---- Metrics ------------------------------------------------------- */
[data-testid="stMetric"] {
    background:#fff; border:1px solid #eceef5; border-radius:14px;
    padding:14px 16px; box-shadow:0 1px 3px rgba(16,24,40,.05);
}

/* ---- Inputs -------------------------------------------------------- */
[data-baseweb="input"], [data-baseweb="select"] > div, .stTextArea textarea {
    border-radius:10px !important;
}

/* ---- Custom components --------------------------------------------- */
.cm-topbar {
    display:flex; align-items:center; justify-content:space-between;
    padding:14px 22px; border-radius:18px; margin-bottom:1.4rem;
    background:linear-gradient(120deg,#312e81 0%,#4f46e5 55%,#6366f1 100%);
    color:#fff; box-shadow:0 8px 24px rgba(79,70,229,.25);
}
.cm-topbar .cm-brand { font-size:1.25rem; font-weight:800; letter-spacing:.2px; }
.cm-topbar .cm-tag { font-size:.82rem; opacity:.85; }
.cm-pill {
    display:inline-block; padding:2px 10px; border-radius:999px; font-size:.72rem;
    font-weight:600; background:#eef0fb; color:#4f46e5; margin-right:6px;
}
.cm-pill.accent { background:#fff5e6; color:#b45309; }
.cm-price { font-size:1.35rem; font-weight:800; color:#111827; }
.cm-muted { color:#6b7280; font-size:.85rem; }
.cm-hero {
    background:linear-gradient(135deg,#312e81 0%,#4f46e5 100%); color:#fff;
    border-radius:22px; padding:42px 38px; height:100%;
    box-shadow:0 16px 40px rgba(49,46,129,.30);
}
.cm-hero h1 { color:#fff; font-size:2.1rem; line-height:1.18; margin:0 0 .6rem; }
.cm-hero p { color:#dfe1ff; font-size:1.02rem; }
.cm-feat { display:flex; gap:10px; align-items:flex-start; margin:14px 0; }
.cm-feat .ic {
    background:rgba(255,255,255,.16); border-radius:10px; width:34px; height:34px;
    display:flex; align-items:center; justify-content:center; flex:none;
    font-size:1.05rem;
}
.cm-feat .tx b { display:block; }
.cm-feat .tx span { color:#cfd2ff; font-size:.86rem; }
.cm-thumb {
    height:170px; border-radius:12px; display:flex; align-items:center;
    justify-content:center; color:#fff; font-weight:700; font-size:1.1rem;
    text-align:center; padding:10px;
}
</style>
"""


def inject_global_styles() -> None:
    # Streamlit rebuilds the DOM each rerun, so inject on every run.
    st.markdown(_CSS, unsafe_allow_html=True)


def topbar(subtitle: str = "Verified student-to-student marketplace") -> None:
    st.markdown(
        f"""
        <div class="cm-topbar">
            <div>
                <div class="cm-brand">🎓 {BRAND}</div>
                <div class="cm-tag">{subtitle}</div>
            </div>
            <div class="cm-tag">Caleb University</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<div class='cm-muted'>{subtitle}</div>", unsafe_allow_html=True)
    st.write("")
