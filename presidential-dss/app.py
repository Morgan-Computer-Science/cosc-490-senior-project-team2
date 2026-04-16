import os
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai as _genai

from agents import run_decision_support
import db
import html as _html

load_dotenv()

# ── Session persistence across page refreshes ─────────────────
import hashlib, secrets, tempfile, pathlib

_SESSION_DIR = pathlib.Path(tempfile.gettempdir()) / "pdss_sessions"
_SESSION_DIR.mkdir(exist_ok=True)

def _save_session(token: str, username: str):
    (_SESSION_DIR / f"{token}.json").write_text(
        json.dumps({"username": username}), encoding="utf-8"
    )

def _load_session(token: str) -> str | None:
    p = _SESSION_DIR / f"{token}.json"
    if p.exists():
        try:
            return json.loads(p.read_text())["username"]
        except Exception:
            return None
    return None

def _delete_session(token: str):
    p = _SESSION_DIR / f"{token}.json"
    if p.exists():
        p.unlink()

st.set_page_config(
    page_title="PDSS — Situation Room",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ============================================================
# CSS — full cosmetic overhaul
# ============================================================
st.markdown("""
<style>

/* ── Logout button — small ── */
div[data-testid="column"] button[kind="secondary"] {
    font-size: 0.60rem !important;
    padding: 3px 8px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    opacity: 0.7;
}
div[data-testid="column"] button[kind="secondary"]:hover {
    opacity: 1;
}

/* ── Hide Streamlit chrome ── */
header, #MainMenu, [data-testid="collapsedControl"] {
    visibility: hidden !important;
    height: 0 !important;
}

/* ── Background with noise texture ── */
.stApp {
    background-color: #070e18;
    background-image:
        url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E"),
        radial-gradient(ellipse at 20% 0%, rgba(26,79,160,0.12) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 0%, rgba(10,40,90,0.10) 0%, transparent 50%),
        linear-gradient(180deg, #060c14 0%, #070d16 100%);
    color: #c8d8ec;
}

/* Scanline overlay */
.stApp::after {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

.block-container {
    max-width: 1500px;
    padding: 1rem 2rem 3rem 2rem;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #050c16;
    border-right: 1px solid #0a1a30;
}
section[data-testid="stSidebar"] * { color: #7a9fc4 !important; }
section[data-testid="stSidebar"] h3 {
    color: #c8d8ec !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    border-bottom: 1px solid #0a1a30;
    padding-bottom: 6px;
    margin-bottom: 8px;
}

/* Sidebar severity dots */
.sev-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
}
.dot-green  { background: #3ddc6e; box-shadow: 0 0 4px #3ddc6e; }
.dot-blue   { background: #4a9eff; box-shadow: 0 0 4px #4a9eff; }
.dot-yellow { background: #ffb84d; box-shadow: 0 0 4px #ffb84d; }
.dot-red    { background: #ff5c5c; box-shadow: 0 0 4px #ff5c5c; }

/* ── Classification banner with pulse ── */
.classbar {
    background: linear-gradient(90deg, #4a0000, #800000, #4a0000);
    border: 1px solid #cc0000;
    border-radius: 6px;
    text-align: center;
    padding: 7px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.24em;
    color: #ffaaaa;
    margin-bottom: 1rem;
    text-transform: uppercase;
    animation: classbar-pulse 3s ease-in-out infinite;
    position: relative;
    overflow: hidden;
}
.classbar::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,80,80,0.08), transparent);
    animation: classbar-sweep 3s linear infinite;
}
@keyframes classbar-pulse {
    0%, 100% { border-color: #6b0000; box-shadow: 0 0 8px rgba(139,0,0,0.3); }
    50%       { border-color: #a00000; box-shadow: 0 0 18px rgba(180,0,0,0.5); }
}
@keyframes classbar-sweep {
    0%   { left: -100%; }
    100% { left: 100%; }
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0d2040 0%, #050e1a 60%, #020810 100%);
    border: 1px solid #1a3060;
    border-top: 3px solid #2a6fdf;
    border-radius: 12px;
    padding: 22px 30px;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    gap: 24px;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(26,79,160,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.hero-seal { font-size: 3.2rem; flex-shrink: 0; }
.hero-eyebrow {
    font-size: 0.72rem;
    color: #3a6fa0;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 5px;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
    margin-bottom: 6px;
}
.hero-meta {
    font-size: 0.80rem;
    color: #3a6fa0;
    letter-spacing: 0.06em;
}
.hero-clock {
    margin-left: auto;
    text-align: right;
    flex-shrink: 0;
}
.hero-clock-time {
    font-size: 2rem;
    font-weight: 800;
    color: #60c0ff;
    text-shadow: 0 0 20px rgba(74,158,255,0.5);
    letter-spacing: 0.08em;
    line-height: 1;
}
.hero-clock-label {
    font-size: 0.60rem;
    color: #3a6fa0;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}
.live-dot {
    display: inline-block;
    width: 7px; height: 7px;
    background: #3ddc6e;
    border-radius: 50%;
    margin-right: 5px;
    vertical-align: middle;
    box-shadow: 0 0 6px #3ddc6e;
    animation: live-blink 1.4s ease-in-out infinite;
}
@keyframes live-blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.2; }
}

/* ── Status strip ── */
.status-strip { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.status-chip {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    padding: 5px 13px;
    border-radius: 4px;
    text-transform: uppercase;
}
.chip-green  { background: #041510; border: 1px solid #0d6028; color: #50ff90; text-shadow: 0 0 8px rgba(61,220,110,0.4); }
.chip-blue   { background: #030e22; border: 1px solid #0d3a70; color: #60b8ff; }
.chip-yellow { background: #160a00; border: 1px solid #603000; color: #ffc860; text-shadow: 0 0 8px rgba(255,184,77,0.3); }
.chip-red    { background: #140000; border: 1px solid #700a0a; color: #ff7070; text-shadow: 0 0 8px rgba(255,92,92,0.3); }

/* ── Severity-driven accent color (injected dynamically) ── */
.accent-blue   { --accent: #4a9eff; }
.accent-yellow { --accent: #ffb84d; }
.accent-red    { --accent: #ff5c5c; }
.accent-green  { --accent: #3ddc6e; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #040a10;
    border-bottom: 1px solid #0a1a30;
    gap: 0;
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    color: #3a6fa0 !important;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 11px 18px;
    border-bottom: 2px solid transparent;
    transition: all 0.15s;
}
.stTabs [data-baseweb="tab"]:hover { color: #6a9fd4 !important; background: rgba(26,79,160,0.05) !important; }
.stTabs [aria-selected="true"] {
    color: #7ab8ff !important;
    border-bottom: 2px solid #1a6fdf !important;
    background: rgba(26,79,160,0.08) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #060e1a !important;
    color: #c8d8ec !important;
    border: 1px solid #0d1e36 !important;
    border-radius: 6px !important;
    font-size: 0.92rem !important;
    transition: border-color 0.2s !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #1a4fa0 !important;
    box-shadow: 0 0 0 2px rgba(26,79,160,0.2) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0d2a56, #1a4fa0);
    color: #d0e8ff;
    border: 1px solid #1a50a0;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    padding: 0.48rem 1.1rem;
    transition: all 0.15s;
    text-transform: uppercase;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #153572, #2060c0);
    border-color: #2a80ff;
    box-shadow: 0 0 14px rgba(26,111,255,0.25);
    transform: translateY(-1px);
}
.stButton > button:active { transform: scale(0.97) translateY(0); }

/* ── Panel cards ── */
.panel {
    background: #080f1e;
    border: 1px solid #162840;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.panel:hover { border-color: #1a3060; }
.panel-title {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #2a5a8a;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #0d1e36;
}
.panel p, .panel li { color: #9ab8d4; font-size: 0.88rem; line-height: 1.7; }

/* ── KPI row ── */
.kpi-row { display: flex; gap: 10px; margin-bottom: 1rem; flex-wrap: wrap; }
.kpi {
    flex: 1;
    min-width: 110px;
    background: #070e1a;
    border: 1px solid #0d1e36;
    border-top: 2px solid #1a4fa0;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: center;
    transition: border-color 0.2s, transform 0.15s;
}
.kpi:hover { border-color: #1a4fa0; transform: translateY(-2px); }
.kpi-val {
    font-size: 2.2rem;
    font-weight: 800;
    color: #60c0ff;
    text-shadow: 0 0 12px rgba(74,158,255,0.3);
    line-height: 1;
    margin-bottom: 5px;
}
.kpi-label {
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #2a5a8a;
}

/* ── Severity badge ── */
.sev-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 6px 14px;
    border-radius: 5px;
    margin-bottom: 6px;
}
.sev-low      { background:#020c06; border:1px solid #0d5028; color:#50ff90; box-shadow: 0 0 10px rgba(61,220,110,0.15); }
.sev-moderate { background:#020814; border:1px solid #0d3a70; color:#60b8ff; box-shadow: 0 0 10px rgba(74,158,255,0.15); }
.sev-high     { background:#120700; border:1px solid #5c3000; color:#ffc860; box-shadow: 0 0 10px rgba(255,184,77,0.2); }
.sev-severe   {
    background:#0e0000;
    border:1px solid #480606;
    color:#ff5c5c;
    animation: sev-severe-pulse 1.5s ease-in-out infinite;
}
@keyframes sev-severe-pulse {
    0%, 100% { box-shadow: 0 0 0 rgba(255,92,92,0); }
    50%       { box-shadow: 0 0 14px rgba(255,92,92,0.35); }
}

/* ── Verdict ── */
.verdict {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 11px 16px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.88rem;
    margin: 10px 0;
}
.v-approved { background:#020c06; border:1px solid #083018; color:#3ddc6e; }
.v-concerns { background:#0e0600; border:1px solid #3c1e00; color:#ffb84d; }
.v-revision { background:#0e0000; border:1px solid #480606; color:#ff5c5c; }

/* ── Domain badge ── */
.dom-badge {
    display: inline-block;
    background: #020814;
    border: 1px solid #0a2448;
    border-radius: 5px;
    padding: 5px 12px;
    font-size: 0.68rem;
    font-weight: 700;
    color: #4a9eff;
    margin: 3px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.dom-badge:hover { border-color: #1a6fdf; box-shadow: 0 0 8px rgba(26,111,255,0.2); }

/* ── Intel feed ── */
.intel-item {
    background: #050c16;
    border-left: 3px solid #0a2448;
    border-radius: 0 6px 6px 0;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.83rem;
    color: #9ab8d4;
    line-height: 1.55;
    transition: border-left-color 0.2s, background 0.2s;
}
.intel-item:hover { background: #070f1c; }
.intel-item.news   { border-left-color: #1a5fcf; }
.intel-item.news:hover { border-left-color: #2a80ff; }
.intel-item.health { border-left-color: #0a7030; }
.intel-item.health:hover { border-left-color: #0daa48; }
.intel-item.cyber  { border-left-color: #7a0a0a; }
.intel-item.cyber:hover { border-left-color: #cc1010; }
.feed-header {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 10px;
    padding-bottom: 6px;
}
.feed-news   { color: #4a9eff; border-bottom: 1px solid #0a2448; }
.feed-health { color: #3ddc6e; border-bottom: 1px solid #083018; }
.feed-cyber  { color: #ff5c5c; border-bottom: 1px solid #480606; }

/* ── Agency card ── */
.agency-card {
    background: #050c16;
    border: 1px solid #0d1e36;
    border-radius: 8px;
    padding: 13px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s, transform 0.15s;
    cursor: default;
}
.agency-card:hover { border-color: #1a3a6a; transform: translateX(3px); }
.agency-name {
    font-size: 0.72rem;
    font-weight: 700;
    color: #4a9eff;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 5px;
}
.agency-desc { font-size: 0.82rem; color: #7a9fc4; line-height: 1.5; }

/* ── Chat ── */
.chat-msg {
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
    font-size: 0.87rem;
    line-height: 1.65;
    animation: chat-fadein 0.3s ease;
}
@keyframes chat-fadein { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.chat-user {
    background: #030c1e;
    border: 1px solid #0a2448;
    color: #9ab8d4;
    margin-left: 8%;
}
.chat-ai {
    background: #050c16;
    border: 1px solid #0d1e36;
    color: #c0d4ec;
    margin-right: 8%;
}
.chat-label {
    font-size: 0.60rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 5px;
    font-weight: 700;
}
.chat-label-user { color: #1a5fcf; }
.chat-label-ai   { color: #2a5a8a; }

/* ── Login ── */
.login-wrap {
    max-width: 400px;
    margin: 7rem auto 0 auto;
    background: #070e1a;
    border: 1px solid #0d1e36;
    border-top: 2px solid #1a4fa0;
    border-radius: 12px;
    padding: 40px 44px;
    text-align: center;
    box-shadow: 0 24px 60px rgba(0,0,0,0.6);
    animation: login-appear 0.4s ease;
}
@keyframes login-appear {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
.login-seal  { font-size: 2.8rem; margin-bottom: 0.5rem; }
.login-title { font-size: 1.25rem; font-weight: 700; color: #e0ecff; margin-bottom: 0.2rem; }
.login-sub   { font-size: 0.65rem; color: #2a5a8a; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 1.6rem; }
.login-scanning {
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1a5fcf;
    margin-top: 12px;
    animation: scan-blink 1s step-end infinite;
}
@keyframes scan-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.login-attempts {
    font-size: 0.68rem;
    color: #cc3030;
    margin-top: 8px;
    letter-spacing: 0.06em;
}

/* ── Redacted placeholder ── */
.redacted {
    display: inline-block;
    background: #1a2a3a;
    color: transparent;
    border-radius: 3px;
    user-select: none;
    letter-spacing: 0.05em;
}
.placeholder-panel {
    background: #070e1a;
    border: 1px solid #0d1e36;
    border-radius: 10px;
    padding: 52px 32px;
    text-align: center;
    margin-top: 1rem;
}
.placeholder-seal {
    font-size: 3rem;
    opacity: 0.25;
    margin-bottom: 1rem;
    animation: seal-float 4s ease-in-out infinite;
}
@keyframes seal-float {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-6px); }
}
.placeholder-label {
    font-size: 0.70rem;
    color: #1a3a5a;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}
.redacted-line {
    display: block;
    height: 10px;
    border-radius: 3px;
    background: #0d1e30;
    margin: 8px auto;
    animation: redact-shimmer 2.5s ease-in-out infinite;
}
@keyframes redact-shimmer {
    0%, 100% { opacity: 0.4; }
    50%       { opacity: 0.7; }
}

/* ── Expander ── */
.stExpander {
    background: #070e1a !important;
    border: 1px solid #0d1e36 !important;
    border-radius: 8px !important;
}
.stExpander:hover { border-color: #1a3060 !important; }

/* ── Dataframe ── */
.stDataFrame { border: 1px solid #0d1e36 !important; border-radius: 8px !important; }

/* ── Divider ── */
hr { border-color: #0d1e36 !important; margin: 1rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #040a10; }
::-webkit-scrollbar-thumb { background: #0d1e36; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #1a4fa0; }

/* ── Metric ── */
[data-testid="stMetric"] {
    background: #070e1a;
    border: 1px solid #0d1e36;
    border-radius: 8px;
    padding: 10px 14px;
}
[data-testid="stMetricValue"] { color: #4a9eff !important; }
[data-testid="stMetricLabel"] { color: #2a5a8a !important; font-size: 0.72rem !important; }

/* ── Slider ── */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #1a4fa0 !important;
    border-color: #2a7fff !important;
}

/* ── Severity-conditional app border ── */
.sev-border-severe .stApp { border-left: 3px solid #ff5c5c !important; }
.sev-border-high   .stApp { border-left: 3px solid #ffb84d !important; }


/* ── Threat ticker ── */
.ticker-wrap {
    background: #030810;
    border-top: 1px solid #0a1a30;
    border-bottom: 1px solid #0a1a30;
    overflow: hidden;
    padding: 6px 0;
    margin-bottom: 1rem;
    white-space: nowrap;
    margin-left: -2rem;
    margin-right: -2rem;
}
.ticker-inner {
    display: inline-block;
    animation: ticker-scroll 30s linear infinite;
    font-size: 0.70rem;
    color: #4a7fc1;
    letter-spacing: 0.08em;
    padding-left: 100%;
}
@keyframes ticker-scroll {
    0%   { transform: translateX(0); }
    100% { transform: translateX(-100%); }
}
.ticker-sep { color: #1a4fa0; margin: 0 16px; }

/* ── Scenario panel overhaul ── */
.scenario-panel {
    background: #070e1a;
    border: 1px solid #162840;
    border-radius: 10px;
    padding: 0;
    margin-bottom: 1rem;
    overflow: hidden;
}
.scenario-panel-header {
    background: #050c16;
    border-bottom: 1px solid #0d1e36;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.scenario-panel-title {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    color: #2a5a8a;
}
.terminal-cursor {
    display: inline-block;
    width: 8px; height: 12px;
    background: #1a6fdf;
    vertical-align: middle;
    animation: cursor-blink 1s step-end infinite;
    border-radius: 1px;
}
@keyframes cursor-blink { 0%,100%{opacity:1} 50%{opacity:0} }
.scenario-panel-body { padding: 12px 16px 16px 16px; }

/* ── Generate button — alert style ── */
.stButton > button.generate-btn {
    background: linear-gradient(135deg, #5a0a0a, #8b0000) !important;
    border: 1px solid #cc1010 !important;
    color: #ffcccc !important;
    box-shadow: 0 0 12px rgba(180,0,0,0.2);
}
.stButton > button.generate-btn:hover {
    background: linear-gradient(135deg, #7a0a0a, #aa0000) !important;
    border-color: #ff3030 !important;
    box-shadow: 0 0 20px rgba(220,0,0,0.35) !important;
}

/* ── Last run card ── */
.last-run-card {
    display: flex;
    gap: 0;
    background: #050c16;
    border: 1px solid #0d1e36;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 1rem;
}
.last-run-accent {
    width: 4px;
    flex-shrink: 0;
}
.last-run-body {
    padding: 12px 16px;
    flex: 1;
}
.last-run-label {
    font-size: 0.58rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #2a5a8a;
    margin-bottom: 6px;
}
.last-run-scenario {
    font-size: 0.84rem;
    color: #9ab8d4;
    margin-bottom: 8px;
    line-height: 1.4;
}
.last-run-meta {
    font-size: 0.68rem;
    color: #2a5a8a;
    letter-spacing: 0.06em;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}
.last-run-meta span { color: #5a8ab4; }


/* ── Brief watermark ── */
.brief-container {
    position: relative;
    overflow: hidden;
}
.brief-watermark {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}
.brief-watermark-text {
    font-size: 1.1rem;
    font-weight: 800;
    color: rgba(74,158,255,0.045);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    white-space: nowrap;
    transform: rotate(-35deg);
    user-select: none;
    text-shadow:
        0 -120px 0 rgba(74,158,255,0.045),
        0 120px 0 rgba(74,158,255,0.045),
        0 -240px 0 rgba(74,158,255,0.045),
        0 240px 0 rgba(74,158,255,0.045),
        0 -360px 0 rgba(74,158,255,0.045),
        0 360px 0 rgba(74,158,255,0.045);
}
.brief-content { position: relative; z-index: 1; }

/* ── Brief memo header ── */
.brief-memo-header {
    border-bottom: 1px solid #1a3060;
    margin-bottom: 16px;
    padding-bottom: 14px;
}
.brief-memo-row {
    display: flex;
    gap: 8px;
    font-size: 0.72rem;
    line-height: 2;
    letter-spacing: 0.06em;
}
.brief-memo-key {
    color: #2a5a8a;
    font-weight: 700;
    text-transform: uppercase;
    min-width: 110px;
    flex-shrink: 0;
}
.brief-memo-val { color: #8ab4d4; }
.brief-memo-subject {
    font-size: 0.82rem;
    font-weight: 700;
    color: #c8d8ec;
    margin-top: 6px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* ── Footnotes ── */
.footnotes-block {
    margin-top: 20px;
    border-top: 1px solid #0d1e36;
    padding-top: 14px;
}
.footnotes-title {
    font-size: 0.60rem;
    font-weight: 700;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    color: #2a5a8a;
    margin-bottom: 10px;
}
.footnote-item {
    font-size: 0.72rem;
    color: #4a7a9a;
    line-height: 1.7;
    display: flex;
    gap: 8px;
}
.footnote-num {
    color: #1a6fdf;
    font-weight: 700;
    flex-shrink: 0;
    min-width: 18px;
}
.footnote-domain { color: #4a9eff; font-weight: 700; }
.footnote-desc   { color: #4a7a9a; }

/* ── Signature block ── */
.sig-block {
    margin-top: 24px;
    border: 1px solid #0d1e36;
    border-top: 2px solid #1a3060;
    border-radius: 0 0 8px 8px;
    padding: 14px 20px;
    background: #040c16;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
}
.sig-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 20px;
}
.sig-col { flex: 1; min-width: 160px; }
.sig-field-label {
    font-size: 0.58rem;
    color: #1a4060;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 4px;
    font-weight: 700;
}
.sig-field-value {
    color: #5a8ab4;
    font-size: 0.72rem;
    padding-bottom: 4px;
    border-bottom: 1px solid #0d1e36;
    min-width: 140px;
    display: inline-block;
}
.sig-field-value.signed { color: #4a9eff; border-bottom-color: #1a4fa0; }
.sig-divider {
    border: none;
    border-top: 1px solid #0a1a2a;
    margin: 12px 0 10px 0;
}
.sig-id-row {
    display: flex;
    justify-content: space-between;
    color: #1a4060;
    font-size: 0.62rem;
    letter-spacing: 0.10em;
}
.sig-id-val { color: #2a6090; }


/* ── Inbox card container ── */
div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"].inbox-card-wrap {
    background: #050c16;
    border: 1px solid #0d1e36;
    border-radius: 8px;
    padding: 12px 16px 8px 16px;
    margin-bottom: 10px;
}
/* ── Small action buttons via wrapper ── */
div.small-btn > div > button {
    font-size: 0.60rem !important;
    padding: 1px 10px !important;
    min-height: 26px !important;
    height: 26px !important;
    line-height: 1 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# CREDENTIALS & CONSTANTS
# ============================================================
DOMAINS = [
    "Defense", "Economy", "Healthcare", "Foreign Policy",
    "Environment", "Education", "Energy",
    "Homeland Security", "Technology", "Justice",
]

SCENARIO_EXAMPLES = {
    "Cyberattack on Power Grid": "A coordinated cyberattack disables multiple regional power grids across the United States, disrupting hospitals, transportation, and communications.",
    "Economic Recession":        "Leading indicators show a deep recession is underway with rising unemployment, banking stress, and consumer confidence collapse.",
    "Pandemic Outbreak":         "A novel respiratory virus with high transmissibility is spreading rapidly across several states with uncertain fatality rates.",
    "Nuclear Threat":            "An adversarial nation has elevated nuclear readiness and issued ambiguous strategic warnings amid a regional military crisis.",
    "Climate Disaster":          "A series of climate-driven extreme weather events has caused nationwide infrastructure damage, displacement, and agricultural disruption.",
    "Border Emergency":          "A sudden regional conflict has driven a major humanitarian surge toward the U.S. border, straining processing capacity and diplomatic coordination.",
}

SEVERITY_META = {
    "Low":      ("sev-low",      "LOW",      "chip-green",  "dot-green",  "#3ddc6e"),
    "Moderate": ("sev-moderate", "MODERATE", "chip-blue",   "dot-blue",   "#4a9eff"),
    "High":     ("sev-high",     "HIGH",     "chip-yellow", "dot-yellow", "#ffb84d"),
    "Severe":   ("sev-severe",   "SEVERE",   "chip-red",    "dot-red",    "#ff5c5c"),
}
SEVERITY_MODIFIERS = {
    "Low":      "The situation is localized, early-stage, and still partially containable with targeted action.",
    "Moderate": "The situation is expanding across multiple regions and requires coordinated federal action within days.",
    "High":     "The situation is severe, fast-moving, and creating visible national disruption across multiple systems.",
    "Severe":   "The situation is critical, national in scope, and presents cascading risks to public safety, governance, and economic stability.",
}

# ============================================================
# SESSION STATE
# ============================================================
for k, v in [("authenticated", False), ("login_attempts", 0), ("chat_history", []),
             ("current_result", None), ("current_user", ""), ("user_info", {}),
             ("archive", []), ("compose_to", ""), ("compose_subject", ""), ("inbox_view", None),
             ("session_token", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Restore session from token on refresh ─────────────────────
if not st.session_state.authenticated:
    _token_from_url = st.query_params.get("token", "")
    if _token_from_url and not st.query_params.get("logout"):
        _restored_user = _load_session(_token_from_url)
        if _restored_user:
            _user_info = db.get_user(_restored_user)
            if _user_info:
                st.session_state.authenticated  = True
                st.session_state.current_user   = _restored_user
                st.session_state.user_info      = _user_info
                st.session_state.session_token  = _token_from_url
                st.rerun()

# ============================================================
# LOGIN
# ============================================================
if not st.session_state.authenticated:
    st.markdown('<div class="classbar">RESTRICTED SYSTEM — AUTHORIZED ACCESS ONLY</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="login-wrap">
            <div class="login-seal">🦅</div>
            <div class="login-title">Situation Room Access</div>
            <div class="login-sub">Presidential Decision Support System</div>
        </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        username = st.text_input("Username", placeholder="Username", key="lu")
        password = st.text_input("Password", type="password", placeholder="Password", key="lp")

        authenticating = st.session_state.get("authenticating", False)
        btn_label = "VERIFYING CREDENTIALS..." if authenticating else "AUTHENTICATE"
        login_btn = st.button(btn_label, use_container_width=True)

        if st.session_state.login_attempts >= 3:
            st.markdown(
                f'<div class="login-attempts">WARNING: {st.session_state.login_attempts} failed attempt(s). '
                f'Account may be locked after further failures.</div>',
                unsafe_allow_html=True,
            )

        if login_btn:
            _auth = db.authenticate(username, password)
            if _auth:
                _new_token = secrets.token_hex(24)
                _save_session(_new_token, username)
                st.session_state.authenticated  = True
                st.session_state.current_user   = username
                st.session_state.user_info      = _auth
                st.session_state.login_attempts = 0
                st.session_state.chat_history   = []
                st.session_state.current_result = None
                st.session_state.session_token  = _new_token
                st.query_params["token"] = _new_token
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"Access denied. Invalid credentials. ({st.session_state.login_attempts} failed attempt(s))")
    st.stop()

# ============================================================
# GENAI CLIENT — module-level singleton
# ============================================================
_genai_client = _genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)

# ============================================================
# AI FUNCTIONS
# ============================================================
def ai_severity(scenario: str) -> dict:
    try:
        r = _genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"You are a national security threat analyst. Assess the severity.\n\nScenario: {scenario}\n\n"
            'Return ONLY valid JSON: {"level": "Low|Moderate|High|Severe", "rationale": "one sentence"}'
        )
        d = json.loads(r.text.strip().replace("```json","").replace("```","").strip())
        if d.get("level") not in SEVERITY_META: d["level"] = "Moderate"
        return d
    except Exception:
        return {"level": "Moderate", "rationale": "Unable to assess severity automatically."}

def ai_intel_feeds(scenario: str) -> dict:
    try:
        r = _genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Generate 4 simulated intelligence feed items per category for this scenario.\n\nScenario: {scenario}\n\n"
            'Return ONLY valid JSON: {"news": [...], "health": [...], "cyber": [...]}'
        )
        return json.loads(r.text.strip().replace("```json","").replace("```","").strip())
    except Exception:
        return {"news": ["Feed unavailable."], "health": ["Feed unavailable."], "cyber": ["Feed unavailable."]}

def ai_map_points(scenario: str) -> list:
    try:
        r = _genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Identify 6 real geographic hotspots for this crisis.\n\nScenario: {scenario}\n\n"
            'Return ONLY valid JSON list: [{"lat": 0.0, "lon": 0.0, "label": "City — reason"}]'
        )
        pts = json.loads(r.text.strip().replace("```json","").replace("```","").strip())
        return pts if isinstance(pts, list) else []
    except Exception:
        return [
            {"lat": 38.9072, "lon": -77.0369, "label": "Washington D.C. — Command Center"},
            {"lat": 40.7128, "lon": -74.0060, "label": "New York — Financial Hub"},
            {"lat": 34.0522, "lon": -118.2437, "label": "Los Angeles — West Coast Ops"},
            {"lat": 41.8781, "lon": -87.6298, "label": "Chicago — Midwest Coordination"},
            {"lat": 29.7604, "lon": -95.3698, "label": "Houston — Energy Infrastructure"},
            {"lat": 47.6062, "lon": -122.3321, "label": "Seattle — Pacific Gateway"},
        ]

def ai_simulate_policy(scenario: str, brief: str) -> list:
    try:
        r = _genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Generate 4 distinct policy options and simulate outcomes.\n\nScenario: {scenario}\n\nBrief:\n{brief[:1500]}\n\n"
            'Return ONLY valid JSON list: [{"option": "title", "description": "1 sentence", '
            '"success_prob": "65%", "economic_impact": "Moderate contraction", '
            '"public_trust": "High", "time_horizon": "30 days", "risk_level": "High"}]'
        )
        return json.loads(r.text.strip().replace("```json","").replace("```","").strip())
    except Exception:
        return []

def ai_agencies(scenario: str, domains: list) -> list:
    try:
        r = _genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Identify 6 critical U.S. federal agencies to activate. Priority domains: {', '.join(domains)}.\n\nScenario: {scenario}\n\n"
            'Return ONLY valid JSON list: [{"agency": "Name", "abbreviation": "ABC", '
            '"role": "one sentence", "priority": "Immediate|24hr|72hr"}]'
        )
        return json.loads(r.text.strip().replace("```json","").replace("```","").strip())
    except Exception:
        return []

def ai_chain_of_command(scenario: str) -> list:
    try:
        r = _genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Generate the chain of command for this scenario.\n\nScenario: {scenario}\n\n"
            'Return ONLY valid JSON list: [{"role": "President", "action": "Declare national emergency", '
            '"authority": "Constitutional", "timeline": "Immediate"}]'
        )
        return json.loads(r.text.strip().replace("```json","").replace("```","").strip())
    except Exception:
        return []

def ai_advisor_reply(question: str, context: str, history: list) -> str:
    try:
        hist_text = "\n".join([f"Q: {h['q']}\nA: {h['a']}" for h in history[-4:]])
        r = _genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"You are the President's Chief Strategic Advisor. Answer concisely and directly.\n\n"
            f"Briefing Context:\n{context}\n\nPrior Exchange:\n{hist_text}\n\nQuestion: {question}"
        )
        return (r.text or "").strip()
    except Exception:
        return "Advisor system temporarily unavailable."

def apply_domain_weighting(scenario: str, weights: dict) -> str:
    boosted = [d for d, w in weights.items() if w >= 4]
    deprioritized = [d for d, w in weights.items() if w <= 2]
    parts = []
    if boosted: parts.append(f"Elevated weight domains: {', '.join(boosted)}.")
    if deprioritized: parts.append(f"Lower priority domains: {', '.join(deprioritized)}.")
    return scenario + ("\n\n" + " ".join(parts) if parts else "")

def ai_footnotes(brief: str, domain_analyses: list) -> list:
    footnotes = []
    domain_keywords = {
        "Defense":           ["military","force","troops","defense","weapon","armed","combat","threat","attack","missile","nuclear"],
        "Economy":           ["economic","gdp","market","trade","financial","inflation","recession","unemployment","treasury","bank"],
        "Healthcare":        ["health","medical","hospital","disease","pandemic","cdc","fda","vaccine","public health","outbreak"],
        "Foreign Policy":    ["diplomatic","allies","nato","un","foreign","international","embassy","sanction","treaty","bilateral"],
        "Environment":       ["climate","environment","disaster","flood","wildfire","hurricane","epa","emissions","infrastructure"],
        "Education":         ["education","school","student","workforce","training","university","research"],
        "Energy":            ["energy","oil","gas","grid","power","electricity","fuel","pipeline","opec","renewable"],
        "Homeland Security": ["homeland","border","fema","fbi","domestic","infrastructure","terrorism","cyber","dhs"],
        "Technology":        ["cyber","technology","ai","digital","data","hack","network","surveillance","satellite"],
        "Justice":           ["law","justice","court","legal","constitution","enforcement","fbi","doj","rights","criminal"],
    }
    brief_lower = brief.lower()
    for i, entry in enumerate(domain_analyses):
        domain = entry.get("domain","")
        keywords = domain_keywords.get(domain, [])
        hits = [kw for kw in keywords if kw in brief_lower]
        if hits or entry.get("priority"):
            contrib_type = "primary contributor" if entry.get("priority") else "supporting analysis"
            top_hits = hits[:3]
            desc = f"{'Priority domain — ' if entry.get('priority') else ''}{contrib_type}"
            if top_hits:
                desc += f" · key terms: {', '.join(top_hits)}"
            footnotes.append({
                "num": len(footnotes) + 1,
                "domain": domain,
                "desc": desc,
                "priority": entry.get("priority", False),
            })
    return footnotes

def _fmt_text(text: str) -> str:
    import html as _h, re
    t = _h.escape(text)
    t = t.replace("\n", "<br>")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong style='color:#c8d8ec;'>\1</strong>", t)
    t = re.sub(r"<br>\s*\*\s+", "<br>&nbsp;&nbsp;• ", t)
    t = re.sub(r"<br>\s*-\s+", "<br>&nbsp;&nbsp;• ", t)
    t = re.sub(r"\*([^*]+?)\*", r"<em>\1</em>", t)
    return t

def _parse_brief(text: str) -> list:
    import re
    text = re.sub(r'^#+\s*PRESIDENTIAL BRIEF\s*', '', text, flags=re.IGNORECASE|re.MULTILINE)
    text = re.sub(r'^(DATE|SUBJECT|CLASSIFICATION|TO|FROM)\s*:.*$', '', text, flags=re.IGNORECASE|re.MULTILINE)
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[ \t]*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    section_defs = [
        ("SITUATION SUMMARY",        "SITUATION SUMMARY",     "◉", "#4a9eff"),
        ("KEY POLICY OPTIONS",        "KEY POLICY OPTIONS",    "⚙", "#60c0ff"),
        ("PRINCIPAL RISKS",           "PRINCIPAL RISKS",       "⚠", "#ff7070"),
        ("MAJOR TRADEOFFS",           "MAJOR TRADEOFFS",       "⇄", "#ffb84d"),
        ("CRITICAL UNCERTAINTIES",    "CRITICAL UNCERTAINTIES","?", "#ffb84d"),
        ("RECOMMENDED NEXT STEPS",    "RECOMMENDED NEXT STEPS","→", "#3ddc6e"),
        ("PRIORITY DOMAIN DEEP DIVES","PRIORITY DOMAINS",      "★", "#4a9eff"),
        ("SUPPORTING DOMAIN",         "SUPPORTING DOMAINS",    "◇", "#2a6080"),
    ]
    pattern = "|".join(r"(?:\*\*|##\s*)?" + re.escape(s[0]) + r"(?:\*\*)?" for s in section_defs)
    parts = re.split(f"({pattern})", text, flags=re.IGNORECASE)
    sections = []
    if parts[0].strip():
        sections.append({"title": "Overview", "body": parts[0].strip(), "icon": "◉", "color": "#4a9eff"})
    i = 1
    while i < len(parts):
        header = parts[i].strip().upper()
        body   = parts[i+1].strip() if i+1 < len(parts) else ""
        i += 2
        matched = next((s for s in section_defs if s[0] in header), None)
        if matched:
            sections.append({"title": matched[1], "body": body, "icon": matched[2], "color": matched[3]})
        else:
            sections.append({"title": header.title(), "body": body, "icon": "◇", "color": "#2a6080"})
    return sections

def _fmt_brief(text: str) -> str:
    return _fmt_text(text)

# ============================================================
# MAIN UI
# ============================================================
user      = st.session_state.current_user
user_info = st.session_state.get("user_info", db.get_user(user) or {})
user_role = user_info.get("role", "chain")
user_title= user_info.get("title", user.upper())
user_disp = user_info.get("display", user.upper())
from datetime import timedelta as _td
_utc_now  = datetime.now(timezone.utc)
_est_off  = -4 if 3 <= _utc_now.month <= 11 else -5
_est_now  = _utc_now + _td(hours=_est_off)
_tz_lbl   = "EDT" if _est_off == -4 else "EST"
now       = _est_now.strftime(f"%B %d, %Y — %H:%M {_tz_lbl}")
res       = st.session_state.current_result

_unread_msgs   = db.get_unread_message_count(user)
_unread_briefs = db.get_unread_brief_count(user)

st.markdown('<div class="classbar">SIMULATED EXERCISE — NOT REAL INTELLIGENCE — FOR DEMONSTRATION PURPOSES ONLY</div>', unsafe_allow_html=True)

import streamlit.components.v1 as _components

if res:
    _sev_h = res.get("severity", "Moderate")
    _sev_css_h, _sev_lbl_h, _chip_cls_h, _, _ = SEVERITY_META.get(_sev_h, SEVERITY_META["Moderate"])
    _verdict_h = res.get("verdict", "—")
    _vchip_h = "chip-green" if _verdict_h == "APPROVED" else ("chip-yellow" if "CONCERNS" in _verdict_h else "chip-red")
    _status_html = f'''<span class="status-chip chip-green"><span class="live-dot"></span>Online</span>
        <span class="status-chip {_chip_cls_h}">Sev: {_sev_h}</span>
        <span class="status-chip {_vchip_h}">{_verdict_h}</span>
        <span class="status-chip chip-blue">Runs: {len(db.list_briefs(operator=user))}</span>'''
else:
    _status_html = '''<span class="status-chip chip-green"><span class="live-dot"></span>Online</span>
        <span class="status-chip chip-blue">Awaiting Input</span>
        <span class="status-chip chip-blue">10 Agents Standby</span>'''

_seal_svg = (
    '<svg width="100" height="100" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">'
    '<defs><radialGradient id="sg" cx="50%" cy="50%" r="50%">'
    '<stop offset="0%" stop-color="#0d2a50"/><stop offset="100%" stop-color="#040e1c"/>'
    '</radialGradient>'
    '<filter id="gl"><feGaussianBlur stdDeviation="2" result="cb"/>'
    '<feMerge><feMergeNode in="cb"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
    '<circle cx="60" cy="60" r="58" fill="none" stroke="#1a4fa0" stroke-width="1.5" opacity="0.6"/>'
    '<circle cx="60" cy="60" r="55" fill="url(#sg)"/>'
    '<circle cx="60" cy="60" r="50" fill="none" stroke="#1a4fa0" stroke-width="0.8" opacity="0.4"/>'
    '<g fill="#4a9eff" filter="url(#gl)" opacity="0.9">'
    + "".join(f'<circle cx="60" cy="8" r="2.5" transform="rotate({round(i*27.7,1)} 60 60)"/>' for i in range(13))
    + "</g>"
    '<path d="M60 22 L82 34 L82 62 Q82 80 60 92 Q38 80 38 62 L38 34 Z" fill="#0a1e3a" stroke="#1a4fa0" stroke-width="1.5"/>'
    '<path d="M60 28 L77 38 L77 62 Q77 76 60 86 Q43 76 43 62 L43 38 Z" fill="none" stroke="#1a3060" stroke-width="0.8"/>'
    '<path d="M38 52 Q48 44 60 48 Q72 44 82 52 Q72 50 60 54 Q48 50 38 52Z" fill="#4a9eff" opacity="0.9"/>'
    '<ellipse cx="60" cy="60" rx="7" ry="10" fill="#4a9eff" opacity="0.95"/>'
    '<circle cx="60" cy="50" r="5" fill="#4a9eff" opacity="0.95"/>'
    '<path d="M63 50 L67 52 L63 53Z" fill="#60c0ff"/>'
    '<path d="M55 68 L60 75 L65 68Z" fill="#4a9eff" opacity="0.8"/>'
    '<path id="ba" d="M 18,75 A 45,45 0 0,0 102,75" fill="none"/>'
    '<text font-size="6.5" fill="#2a5a8a" letter-spacing="1.2" font-family="monospace">'
    '<textPath href="#ba" startOffset="3%">PRESIDENTIAL DECISION SUPPORT SYSTEM</textPath>'
    "</text></svg>"
)

st.markdown(f"""<div class="hero">
  <div style="flex:1;">
    <div class="hero-eyebrow">White House Situation Room / Presidential Decision Support System</div>
    <div class="hero-title">{user_disp} — Command Interface</div>
    <div class="hero-meta">
      <span class="live-dot"></span>LIVE &nbsp;|&nbsp;
      OPERATOR: {user_disp} — {user_title.upper()} &nbsp;|&nbsp;
      SESSION: <span id="inline-clock">--:--:--</span>
      <span id="inline-tz" style="color:#2a5a8a;">EDT</span>
    </div>
    <div class="status-strip" style="margin-top:8px;">{_status_html}</div>
  </div>
  <div style="flex-shrink:0;display:flex;flex-direction:column;align-items:center;
              justify-content:space-between;gap:8px;padding-left:20px;">
    {_seal_svg}
    <a href="?logout=1" target="_self" style="font-size:0.60rem;color:#2a4a6a;letter-spacing:0.12em;
       text-transform:uppercase;text-decoration:none;border:1px solid #0d1e36;
       border-radius:4px;padding:3px 10px;background:#040c16;white-space:nowrap;"
       onmouseover="this.style.color='#4a9eff';this.style.borderColor='#1a4fa0'"
       onmouseout="this.style.color='#2a4a6a';this.style.borderColor='#0d1e36'">
      ⎋ Log Out
    </a>
  </div>
</div>""", unsafe_allow_html=True)

if st.query_params.get("logout") and st.session_state.get("authenticated"):
    _tok = st.session_state.get("session_token", "")
    if _tok:
        _delete_session(_tok)
    st.query_params.clear()
    for k in ["authenticated","current_user","user_info","chat_history","current_result","inbox_view","archive","session_token"]:
        st.session_state.pop(k, None)
    st.rerun()
elif st.query_params.get("logout"):
    st.query_params.clear()

_components.html("""
<script>
  function tick() {
    const time = new Date().toLocaleTimeString('en-US', {
      timeZone: 'America/New_York',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
    const tz = new Date().toLocaleDateString('en-US', {
      timeZone: 'America/New_York', timeZoneName: 'short'
    }).split(', ').pop() || 'EDT';
    const doc = window.parent.document;
    const el = doc.getElementById('inline-clock');
    const tl = doc.getElementById('inline-tz');
    if (el) el.textContent = time;
    if (tl) tl.textContent = tz;
  }
  setInterval(tick, 1000);
  tick();
</script>
""", height=0)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    _badge_color = "#4a9eff" if user_role == "president" else ("#ffb84d" if user_role == "admin" else "#3ddc6e")
    st.markdown(f"""
    <div style="background:#040c16;border:1px solid #0d1e36;border-left:3px solid {_badge_color};
                border-radius:8px;padding:12px 14px;margin-bottom:10px;">
        <div style="font-size:0.58rem;color:#2a5a8a;letter-spacing:0.16em;text-transform:uppercase;margin-bottom:3px;">Authenticated Operator</div>
        <div style="font-size:0.92rem;font-weight:700;color:#c8d8ec;">{user_disp}</div>
        <div style="font-size:0.72rem;color:#4a7a9a;margin-top:2px;">{user_title}</div>
        <div style="font-size:0.62rem;color:{_badge_color};margin-top:4px;text-transform:uppercase;letter-spacing:0.10em;">
            {'COMMAND AUTHORITY' if user_role == 'president' else 'READ ACCESS' if user_role == 'chain' else 'SYSTEM ADMIN'}
        </div>
    </div>""", unsafe_allow_html=True)

    if st.button("Log Out", use_container_width=True, key="sidebar_logout", type="primary"):
        _tok = st.session_state.get("session_token", "")
        if _tok: _delete_session(_tok)
        for k in ["authenticated","current_user","user_info","chat_history","current_result","inbox_view","archive","session_token"]:
            st.session_state.pop(k, None)
        st.query_params.clear()
        st.rerun()
    if st.button("Clear Brief", use_container_width=True, key="sidebar_clear"):
        st.session_state.current_result = None
        st.session_state.chat_history   = []
        st.rerun()

    st.divider()

    _prev_briefs = db.list_briefs(operator=user if user_role == "president" else None, limit=20)
    if _prev_briefs:
        st.markdown("### Previous Briefs")
        for br in _prev_briefs[:8]:
            _dot = SEVERITY_META.get(br["severity"], SEVERITY_META["Moderate"])[3]
            _label = f"{br['id'][-9:]} — {br['scenario'][:28]}..."
            if st.button(_label, use_container_width=True, key=f"load_{br['id']}"):
                _loaded = db.load_brief(br["id"])
                if _loaded:
                    st.session_state.current_result = _loaded
                    st.session_state.chat_history   = []
                    st.rerun()
        st.divider()

    if user_role == "president":
        st.markdown("### Scenarios")
        _scenario_labels = list(SCENARIO_EXAMPLES.keys())
        _sc_cols = st.columns(2)
        for i, label in enumerate(_scenario_labels):
            with _sc_cols[i % 2]:
                if st.button(label, use_container_width=True, key=f"sc_{label}"):
                    st.session_state["scenario_text"] = SCENARIO_EXAMPLES[label]
                    st.rerun()

        st.divider()
        st.markdown("### Domain Weights")
        st.caption("1 = deprioritize  /  5 = elevate")

    domain_weights = {}
    if user_role == "president":
        for domain in DOMAINS:
            w = st.slider(domain, 1, 5, 3, key=f"w_{domain}")
            domain_weights[domain] = w
        st.divider()
        st.markdown("### Pipeline")
        st.markdown(
            "<small style='color:#2a5a8a;line-height:2;'>"
            "1. Control Agent → top 3 domains<br>"
            "2. 10 Domain Agents (parallel)<br>"
            "3. Synthesizer → executive brief<br>"
            "4. Critic → audit & revise<br>"
            "5. Memory → archive</small>",
            unsafe_allow_html=True,
        )

# ── Threat ticker ────────────────────────────────────────────
_db_archive = db.list_briefs(operator=user if user_role == "president" else None, limit=10)
if _db_archive:
    _items = [f"BRIEF {e['id'][-9:]} &nbsp;|&nbsp; {e['scenario'][:60]} &nbsp;|&nbsp; SEVERITY: {e['severity'].upper()} &nbsp;|&nbsp; VERDICT: {e['verdict']}" for e in _db_archive]
    _ticker_text = ' <span class="ticker-sep">///</span> '.join(_items * 3)
else:
    _ticker_text = 'PDSS ONLINE <span class="ticker-sep">///</span> ALL SYSTEMS NOMINAL <span class="ticker-sep">///</span> 10 DOMAIN AGENTS ON STANDBY <span class="ticker-sep">///</span> AWAITING SCENARIO INPUT <span class="ticker-sep">///</span> CLASSIFIED SYSTEM — AUTHORIZED PERSONNEL ONLY'
st.markdown(f'<div class="ticker-wrap"><div class="ticker-inner">{_ticker_text}</div></div>', unsafe_allow_html=True)

if _db_archive:
    _last = _db_archive[0]
    _lsev    = _last.get("severity", "Moderate")
    _lcolor  = SEVERITY_META.get(_lsev, SEVERITY_META["Moderate"])[4]
    _lverdict = _last.get("verdict", "—")
    st.markdown(f"""
    <div class="last-run-card">
        <div class="last-run-accent" style="background:{_lcolor};"></div>
        <div class="last-run-body">
            <div class="last-run-label">Last Brief — {_last.get('id','')}</div>
            <div class="last-run-scenario">{_last['scenario'][:120]}</div>
            <div class="last-run-meta">
                <span>{_last['timestamp']}</span>
                <span>SEVERITY: {_lsev.upper()}</span>
                <span>VERDICT: {_lverdict}</span>
                <span>OPERATOR: {_last.get('operator','—').upper()}</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

_prev = db.list_briefs(operator=user, limit=20) if user_role == "president" else []
if _prev:
    with st.expander(f"Previous Briefs ({len(_prev)})", expanded=False):
        for _br in _prev:
            _br_sev_color = SEVERITY_META.get(_br["severity"], SEVERITY_META["Moderate"])[4]
            _br_col1, _br_col2, _br_col3 = st.columns([5, 1, 1])
            with _br_col1:
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#2a5a8a;letter-spacing:0.08em;padding:4px 0;">' +
                    f'<span style="color:{_br_sev_color};">●</span> ' +
                    f'<strong style="color:#7ab8ff;">{_br["id"]}</strong> &nbsp;|&nbsp; ' +
                    f'{_br["scenario"][:80]}... &nbsp;|&nbsp; ' +
                    f'<span style="color:#4a7a9a;">{_br["timestamp"]}</span></div>',
                    unsafe_allow_html=True
                )
            with _br_col2:
                if st.button("Load", key=f"mainload_{_br['id']}"):
                    _loaded = db.load_brief(_br["id"])
                    if _loaded:
                        st.session_state.current_result = _loaded
                        st.session_state.chat_history   = []
                        st.rerun()
            with _br_col3:
                if st.button("Delete", key=f"maindel_{_br['id']}"):
                    if (st.session_state.get("current_result") or {}).get("briefing_id") == _br["id"]:
                        st.session_state.current_result = None
                    db.delete_brief(_br["id"])
                    st.rerun()

if user_role == "president":
    st.markdown('''<div style="font-size:0.88rem;font-weight:700;color:#4a7fc1;letter-spacing:0.14em;
text-transform:uppercase;margin-bottom:6px;">
  <span style="border-bottom:2px solid #1a4fa0;padding-bottom:3px;">Scenario Input</span>
</div>''', unsafe_allow_html=True)

    scenario = st.text_area(
        "scenario",
        height=120,
        label_visibility="collapsed",
        placeholder="Describe the national security or policy scenario in detail...",
        key="scenario_text",
    )

    col_spacer, col_btn = st.columns([3, 1])
    with col_btn:
        run_btn = st.button("INITIATE BRIEF", use_container_width=True, key="run_btn")
else:
    scenario = ""
    run_btn  = False

# ============================================================
# RUN PIPELINE
# ============================================================
if run_btn:
    if not scenario.strip():
        st.warning("Enter a scenario before generating a brief.")
        st.stop()

    with st.status("Initializing situation room systems...", expanded=True) as status:
        st.write("Assessing threat severity...")
        sev_result = ai_severity(scenario)
        severity   = sev_result["level"]

        st.write("Generating intelligence feeds...")
        intel = ai_intel_feeds(scenario)

        st.write("Mapping geographic hotspots...")
        map_pts = ai_map_points(scenario)

        st.write("Dispatching domain agents...")
        sev_note       = f"\n\nThreat Severity: {severity}. {SEVERITY_MODIFIERS[severity]}"
        final_scenario = apply_domain_weighting(scenario + sev_note, domain_weights)

        logs = []
        prog = st.empty()
        def cb(msg):
            logs.append(msg)
            prog.markdown(f"`{logs[-1]}`")

        result = run_decision_support(final_scenario, progress_callback=cb)
        prog.empty()

        st.write("Building agency activation list...")
        agencies    = ai_agencies(scenario, result["priority_domains"])

        st.write("Running policy simulations...")
        simulations = ai_simulate_policy(scenario, result["executive_brief"])

        st.write("Generating chain of command...")
        chain = ai_chain_of_command(scenario)

        status.update(label="Briefing complete — all systems nominal", state="complete")

    _bid_ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    _bid_seq = str(len(db.list_briefs()) + 1).zfill(4)
    briefing_id = f"PDSS-{_bid_ts}-{_bid_seq}"
    result.update({
        "severity": severity, "sev_rationale": sev_result["rationale"],
        "intel": intel, "map_pts": map_pts, "agencies": agencies,
        "simulations": simulations, "chain": chain,
        "scenario_raw": scenario, "timestamp": now, "operator": user,
        "briefing_id": briefing_id,
    })
    db.save_brief(result)
    st.session_state.current_result = result
    st.session_state.chat_history   = []
    st.rerun()

# ============================================================
# RESULTS
# ============================================================
_inbox_badge = f" ({_unread_briefs})" if _unread_briefs > 0 else ""
_msg_badge   = f" ({_unread_msgs})" if _unread_msgs > 0 else ""
tabs = st.tabs([
    "PDB",
    "SIGINT / HUMINT",
    "GEOINT",
    "COA Analysis",
    "Chain of Command",
    "Analyst Reports",
    "NSC Advisor",
    f"Inbox{_inbox_badge}",
    f"Messages{_msg_badge}",
    "Archive",
])

if st.session_state.current_result:
    res = st.session_state.current_result
    sev = res["severity"]
    sev_css, sev_label, chip_cls, dot_cls, sev_color = SEVERITY_META.get(sev, SEVERITY_META["Moderate"])
    verdict = res["verdict"]
    v_css   = "v-approved" if verdict == "APPROVED" else ("v-concerns" if "CONCERNS" in verdict else "v-revision")
    v_icon  = "APPROVED" if verdict == "APPROVED" else ("CONCERNS" if "CONCERNS" in verdict else "REVISION REQUIRED")

    with tabs[0]:
        st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi"><div class="kpi-val">{len(res["priority_domains"])}</div><div class="kpi-label">Priority Domains</div></div>
            <div class="kpi"><div class="kpi-val">{len(res["domain_analyses"])}</div><div class="kpi-label">Agents Deployed</div></div>
            <div class="kpi"><div class="kpi-val">{len(res.get("simulations",[]))}</div><div class="kpi-label">Policy Options</div></div>
            <div class="kpi"><div class="kpi-val">{len(res.get("agencies",[]))}</div><div class="kpi-label">Agencies Activated</div></div>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f'<span class="sev-badge {sev_css}">● {sev_label}</span>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:0.78rem;color:#2a5a8a;margin-bottom:12px;">{res["sev_rationale"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="verdict {v_css}">{v_icon}: {verdict}</div>', unsafe_allow_html=True)
            st.markdown("<br>**Priority Domains**", unsafe_allow_html=True)
            badges = "".join(f'<span class="dom-badge">{d}</span>' for d in res["priority_domains"])
            st.markdown(badges, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="panel">
                <div class="panel-title">Run Metadata</div>
                <div style="font-size:0.70rem;color:#2a5a8a;line-height:2.2;letter-spacing:0.06em;">
                OPERATOR &nbsp;&nbsp;&nbsp;{res['operator'].upper()}<br>
                TIMESTAMP &nbsp;&nbsp;{res['timestamp']}<br>
                SEVERITY &nbsp;&nbsp;&nbsp;{sev}<br>
                VERDICT &nbsp;&nbsp;&nbsp;&nbsp;{verdict}
                </div>
            </div>""", unsafe_allow_html=True)

        st.divider()

        _footnotes = ai_footnotes(res["executive_brief"], res["domain_analyses"])
        _bid = res.get("briefing_id", "PDSS-UNKNOWN")
        _wm_text = f"{res['operator'].upper()} // {sev.upper()} // {res['timestamp']}"
        _footnotes_html = ""
        for fn in _footnotes:
            _dom_color = "#4a9eff" if fn["priority"] else "#2a6080"
            _footnotes_html += f'''<div class="footnote-item">
                <span class="footnote-num">[{fn["num"]}]</span>
                <span><span class="footnote-domain" style="color:{_dom_color};">{fn["domain"]}</span>
                <span class="footnote-desc"> — {fn["desc"]}</span></span>
            </div>'''

        _subject = _html.escape(res['scenario_raw'][:120]) + ('...' if len(res['scenario_raw'])>120 else '')
        _verdict_color = '#3ddc6e' if verdict=='APPROVED' else '#ffb84d'
        _brief_body = _fmt_brief(res["executive_brief"])

        st.markdown(f"""<div class="panel brief-container" style="border-left:3px solid {sev_color};padding:22px 24px;">
          <div class="brief-watermark"><div class="brief-watermark-text">{_wm_text}</div></div>
          <div class="brief-content">
            <div class="brief-memo-header">
              <div class="brief-memo-row"><span class="brief-memo-key">TO:</span><span class="brief-memo-val">THE PRESIDENT OF THE UNITED STATES</span></div>
              <div class="brief-memo-row"><span class="brief-memo-key">FROM:</span><span class="brief-memo-val">NSC AI ANALYSIS SYSTEM — PDSS</span></div>
              <div class="brief-memo-row"><span class="brief-memo-key">DATE:</span><span class="brief-memo-val">{res['timestamp']}</span></div>
              <div class="brief-memo-row"><span class="brief-memo-key">CLASSIFICATION:</span><span class="brief-memo-val" style="color:{sev_color};">{sev.upper()} — EYES ONLY</span></div>
              <div class="brief-memo-row"><span class="brief-memo-key">BRIEFING ID:</span><span class="brief-memo-val" style="color:#4a9eff;">{_bid}</span></div>
              <div class="brief-memo-subject">SUBJECT: {_subject}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f'<div style="color:#a8c0dc;font-size:0.9rem;line-height:1.85;padding:0 0 16px 0;">{_brief_body}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="footnotes-block"><div class="footnotes-title">Analytical Sources</div>{_footnotes_html}</div>', unsafe_allow_html=True)

        st.markdown(f"""
          <div class="sig-block">
            <div class="sig-row">
              <div class="sig-col"><div class="sig-field-label">Prepared By</div><div class="sig-field-value signed">NSC AI ANALYSIS SYSTEM</div></div>
              <div class="sig-col"><div class="sig-field-label">Reviewed By</div><div class="sig-field-value signed">{res['operator'].upper()}</div></div>
              <div class="sig-col"><div class="sig-field-label">Critic Verdict</div><div class="sig-field-value signed" style="color:{_verdict_color};">{verdict}</div></div>
              <div class="sig-col"><div class="sig-field-label">Distribution</div><div class="sig-field-value">EYES ONLY — POTUS</div></div>
            </div>
            <hr class="sig-divider"/>
            <div class="sig-id-row">
              <span>BRIEFING ID: <span class="sig-id-val">{_bid}</span></span>
              <span>OPERATOR: <span class="sig-id-val">{res['operator'].upper()}</span></span>
              <span>SYSTEM: <span class="sig-id-val">PDSS v2 // NSC</span></span>
              <span>TIMESTAMP: <span class="sig-id-val">{res['timestamp']}</span></span>
            </div>
          </div></div></div>""", unsafe_allow_html=True)

        with st.expander("Critic Full Report"):
            st.markdown(res["critic_report"])

        report = (
            f"PRESIDENTIAL DECISION SUPPORT SYSTEM\n"
            f"Briefing ID: {res.get('briefing_id','N/A')} | Generated: {res['timestamp']} | Operator: {res['operator']}\n"
            f"{'='*60}\n\n"
            f"SCENARIO:\n{res['scenario_raw']}\n\n"
            f"AI-ASSESSED SEVERITY: {sev} — {res['sev_rationale']}\n"
            f"PRIORITY DOMAINS: {', '.join(res['priority_domains'])}\n"
            f"CRITIC VERDICT: {verdict}\n\n"
            f"EXECUTIVE BRIEF:\n{res['executive_brief']}\n\n"
            f"CRITIC REPORT:\n{res['critic_report']}\n\n"
            "DOMAIN ANALYSES:\n"
        )
        for e in res["domain_analyses"]:
            report += f"\n--- {e['domain']} {'[PRIORITY]' if e['priority'] else ''} ---\n{e['analysis']}\n"

        st.download_button("Download Full Report (.txt)", data=report,
                           file_name="pdss_report.txt", mime="text/plain")

        if user_role == "president":
            st.divider()
            st.markdown("#### Distribute This Brief")
            _chain_users = db.get_chain_users()
            _dist_options = {f"{u['display']} — {u['title']}": u["username"] for u in _chain_users}
            _already_sent = [d["to_user"] for d in db.get_distribution_list(res.get("briefing_id",""))]
            _col_sel, _col_note = st.columns([2,2])
            with _col_sel:
                _selected_labels = st.multiselect(
                    "Select Recipients",
                    options=list(_dist_options.keys()),
                    default=[k for k,v in _dist_options.items() if v in _already_sent],
                    key="dist_recipients"
                )
            with _col_note:
                _dist_note = st.text_input("Accompanying Note (optional)", key="dist_note",
                                           placeholder="e.g. For immediate review — POTUS")
            _dist_col, _ = st.columns([1,3])
            with _dist_col:
                if st.button("DISTRIBUTE BRIEF", use_container_width=True, key="dist_btn"):
                    _to_users = [_dist_options[l] for l in _selected_labels]
                    if _to_users:
                        db.distribute_brief(res["briefing_id"], user, _to_users, _dist_note)
                        for _ru in _to_users:
                            _ru_info = db.get_user(_ru)
                            db.send_message(
                                from_user=user,
                                to_user=_ru,
                                subject=f"New brief distributed: {res.get('briefing_id','N/A')}",
                                body=f"A new presidential brief has been distributed to you.\n\nBriefing ID: {res.get('briefing_id','N/A')}\nSeverity: {res['severity']}\nScenario: {res['scenario_raw'][:200]}\n\nNote: {_dist_note or 'No note provided.'}",
                                briefing_id=res.get("briefing_id")
                            )
                        st.success(f"Brief distributed to {len(_to_users)} recipient(s).")
                    else:
                        st.warning("Select at least one recipient.")

            _dlist = db.get_distribution_list(res.get("briefing_id",""))
            if _dlist:
                st.markdown('<div class="panel-title" style="margin-top:12px;">Distribution Record</div>', unsafe_allow_html=True)
                for _d in _dlist:
                    _duser = db.get_user(_d["to_user"])
                    _read_status = f"Read {_d['read_at'][:16]}" if _d["read_at"] else "Unread"
                    _rcolor = "#3ddc6e" if _d["read_at"] else "#ffb84d"
                    st.markdown(
                        f'<div style="font-size:0.72rem;color:#4a7a9a;padding:4px 0;border-bottom:1px solid #0a1a2a;">' +
                        f'<span style="color:#4a9eff;">{_duser["display"] if _duser else _d["to_user"].upper()}</span> — ' +
                        f'{_duser["title"] if _duser else ""} &nbsp; <span style="color:{_rcolor};">{_read_status}</span>' +
                        f'<span style="float:right;color:#2a5a8a;">{_d["sent_at"][:16]}</span></div>',
                        unsafe_allow_html=True
                    )

    with tabs[1]:
        intel = res.get("intel", {})
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="feed-header feed-news">Global News Feed</div>', unsafe_allow_html=True)
            for item in intel.get("news", []):
                st.markdown(f'<div class="intel-item news">{item}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="feed-header feed-health">Public Health Alerts</div>', unsafe_allow_html=True)
            for item in intel.get("health", []):
                st.markdown(f'<div class="intel-item health">{item}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="feed-header feed-cyber">Cyber Threat Intelligence</div>', unsafe_allow_html=True)
            for item in intel.get("cyber", []):
                st.markdown(f'<div class="intel-item cyber">{item}</div>', unsafe_allow_html=True)

    with tabs[2]:
        map_pts = res.get("map_pts", [])
        if map_pts:
            map_df = pd.DataFrame([{"lat": p["lat"], "lon": p["lon"]} for p in map_pts])
            st.map(map_df, size=18)
            st.markdown("#### Hotspot Analysis")
            cols = st.columns(2)
            for i, p in enumerate(map_pts):
                with cols[i % 2]:
                    st.markdown(
                        f'<div class="agency-card">'
                        f'<div class="agency-name">{p.get("label","Location")}</div>'
                        f'<div class="agency-desc">Coordinates: {p["lat"]:.4f}, {p["lon"]:.4f}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No map data available for this scenario.")

    with tabs[3]:
        sims = res.get("simulations", [])
        if sims:
            st.markdown("#### Policy Option Simulation Engine")
            st.dataframe(pd.DataFrame(sims), use_container_width=True, hide_index=True)
            chart_data = {}
            for s in sims:
                try:
                    prob = float(str(s.get("success_prob","50%")).replace("%",""))
                    chart_data[s.get("option","Option")] = prob
                except Exception:
                    pass
            if chart_data:
                st.markdown("#### Success Probability by Option")
                st.bar_chart(pd.DataFrame.from_dict(chart_data, orient="index", columns=["Success Probability (%)"]))
            st.markdown("#### Option Deep Dives")
            for s in sims:
                with st.expander(f"Option — {s.get('option','Option')}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Success Prob.", s.get("success_prob","—"))
                    c2.metric("Econ. Impact",  s.get("economic_impact","—"))
                    c3.metric("Public Trust",   s.get("public_trust","—"))
                    c4.metric("Time Horizon",   s.get("time_horizon","—"))
                    st.markdown(f"**Description:** {s.get('description','')}")
                    st.markdown(f"**Risk Level:** {s.get('risk_level','—')}")
        else:
            st.info("No policy simulations generated for this run.")

    with tabs[4]:
        col_ag, col_cc = st.columns([1, 1])
        with col_ag:
            st.markdown("#### Agency Activation Order")
            agencies = res.get("agencies", [])
            if agencies:
                for ag in agencies:
                    p_color = {"Immediate":"#ff5c5c","24hr":"#ffb84d","72hr":"#4a9eff"}.get(ag.get("priority",""),"#4a9eff")
                    st.markdown(
                        f'<div class="agency-card" style="border-left:3px solid {p_color};">'
                        f'<div class="agency-name">{ag.get("abbreviation","?")} — {ag.get("agency","")}'
                        f'<span style="float:right;font-size:0.62rem;color:{p_color};padding:2px 8px;'
                        f'background:rgba(0,0,0,0.3);border-radius:4px;">{ag.get("priority","")}</span></div>'
                        f'<div class="agency-desc">{ag.get("role","")}</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No agency data generated.")
        with col_cc:
            st.markdown("#### Chain of Command")
            chain = res.get("chain", [])
            if chain:
                st.dataframe(pd.DataFrame(chain), use_container_width=True, hide_index=True)
            else:
                st.info("No chain of command data generated.")

    with tabs[5]:
        st.markdown("#### All Domain Agent Reports")
        priority_entries   = [e for e in res["domain_analyses"] if e["priority"]]
        supporting_entries = [e for e in res["domain_analyses"] if not e["priority"]]
        st.markdown("**Priority Domains — Deep Analysis**")
        for e in priority_entries:
            with st.expander(f"[PRIORITY] {e['domain']}"):
                st.markdown(f'<div style="border-left:3px solid {sev_color};padding-left:12px;">{e["analysis"]}</div>', unsafe_allow_html=True)
        st.markdown("**Supporting Domains — Relevance Check**")
        for e in supporting_entries:
            with st.expander(e["domain"]):
                st.markdown(e["analysis"])

    with tabs[6]:
        st.markdown("#### Chief Strategic Advisor")
        st.caption("Ask any question about the current briefing.")
        context = (
            f"Scenario: {res['scenario_raw']}\n\n"
            f"Severity: {res['severity']} — {res['sev_rationale']}\n\n"
            f"Priority Domains: {', '.join(res['priority_domains'])}\n\n"
            f"Verdict: {res['verdict']}\n\n"
            f"Executive Brief:\n{res['executive_brief'][:2000]}"
        )
        for h in st.session_state.chat_history:
            st.markdown(f'<div class="chat-msg chat-user"><div class="chat-label chat-label-user">Operator</div>{h["q"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-msg chat-ai"><div class="chat-label chat-label-ai">Chief Advisor</div>{h["a"]}</div>', unsafe_allow_html=True)
        if "advisor_input_key" not in st.session_state:
            st.session_state.advisor_input_key = 0
        q_col, btn_col = st.columns([5, 1])
        with q_col:
            question = st.text_input(
                "Question",
                placeholder="What is the biggest risk? Which option is safest politically?",
                label_visibility="collapsed",
                key=f"advisor_q_{st.session_state.advisor_input_key}"
            )
        with btn_col:
            ask_btn = st.button("Ask", use_container_width=True)
        if ask_btn and question.strip():
            with st.spinner("Advisor responding..."):
                answer = ai_advisor_reply(question, context, st.session_state.chat_history)
            st.session_state.chat_history.append({"q": question, "a": answer})
            st.session_state.advisor_input_key += 1
            st.rerun()
        if st.session_state.chat_history:
            if st.button("Clear Conversation"):
                st.session_state.chat_history = []
                st.session_state.advisor_input_key = 0
                st.rerun()

else:
    with tabs[0]:
        if user_role == "president":
            st.markdown("""
            <div class="placeholder-panel">
                <div class="placeholder-seal">
                <svg width="60" height="60" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" opacity="0.3">
                  <circle cx="50" cy="50" r="48" fill="none" stroke="#2a6fdf" stroke-width="2"/>
                  <circle cx="50" cy="50" r="44" fill="#05111f"/>
                  <text x="50" y="62" text-anchor="middle" font-size="32" fill="#4a9eff">🦅</text>
                </svg>
                </div>
                <div class="placeholder-label">Awaiting Scenario Input — Clearance Required</div>
                <span class="redacted-line" style="width:60%;"></span>
                <span class="redacted-line" style="width:80%;"></span>
                <span class="redacted-line" style="width:45%;"></span>
                <span class="redacted-line" style="width:70%;"></span>
                <span class="redacted-line" style="width:55%;"></span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#070e1a;border:1px solid #0d1e36;border-left:3px solid #1a4fa0;
                        border-radius:10px;padding:20px 24px;margin-bottom:1rem;">
                <div style="font-size:0.62rem;color:#2a5a8a;letter-spacing:0.16em;text-transform:uppercase;
                            margin-bottom:6px;">Awaiting Brief — {user_title}</div>
                <div style="font-size:0.88rem;color:#4a7a9a;">
                    Briefs distributed to you will appear in your <strong style="color:#4a9eff;">Inbox</strong> tab.
                    Load a brief from there to view the full analysis.
                </div>
            </div>""", unsafe_allow_html=True)
            st.info("Check the Inbox tab to view and load briefs distributed to you.")
    for _ti in [1, 2, 3, 4, 5, 6]:
        with tabs[_ti]:
            st.info("Load a brief to view this section.")

# ── TAB 8: Inbox ─────────────────────────────────────────────
with tabs[7]:
    st.markdown("#### Intelligence Inbox — Distributed Briefs")
    _dist_briefs = db.list_distributed_briefs(user)
    if _dist_briefs:
        for _db_entry in _dist_briefs:
            _is_unread = not _db_entry.get("read_at")
            _sev_color_ib = SEVERITY_META.get(_db_entry["severity"], SEVERITY_META["Moderate"])[4]
            _sender_info  = db.get_user(_db_entry["operator"])
            _sender_disp  = _sender_info["display"] if _sender_info else _db_entry["operator"].upper()
            _unread_badge_ib = '<span style="font-size:0.60rem;background:#0a2448;color:#4a9eff;padding:2px 7px;border-radius:3px;margin-bottom:6px;display:inline-block;">UNREAD</span><br>' if _is_unread else ""
            _entry_id        = _db_entry["id"]
            _entry_scenario  = _db_entry["scenario"][:120]
            _entry_sev       = _db_entry["severity"].upper()
            _entry_sent      = _db_entry["sent_at"][:16]
            with st.container(border=True):
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#2a5a8a;letter-spacing:0.08em;margin-bottom:6px;">' +
                    (_unread_badge_ib if _is_unread else "") +
                    f'{_entry_id} &nbsp;·&nbsp; FROM: {_sender_disp} &nbsp;·&nbsp; {_entry_sent}</div>' +
                    f'<div style="font-size:0.95rem;color:#c8d8ec;margin-bottom:8px;font-weight:500;">{_entry_scenario}...</div>' +
                    (f'<div style="font-size:0.78rem;color:#4a7a9a;margin-bottom:4px;">Note: {_db_entry["note"]}</div>' if _db_entry.get("note") else "") +
                    f'<div style="font-size:0.70rem;color:{_sev_color_ib};text-align:right;font-weight:700;">{_entry_sev}</div>',
                    unsafe_allow_html=True
                )
                _ib_space, _ib_load, _ib_del = st.columns([8, 1, 1])
                with _ib_load:
                    st.markdown('<div class="small-btn">', unsafe_allow_html=True)
                    if st.button("Load", key=f"inbox_load_{_db_entry['dist_id']}", use_container_width=True):
                        _loaded = db.load_brief(_db_entry["id"])
                        if _loaded:
                            db.mark_brief_read(_db_entry["dist_id"])
                            st.session_state.current_result = _loaded
                            st.session_state.chat_history   = []
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with _ib_del:
                    st.markdown('<div class="small-btn">', unsafe_allow_html=True)
                    if st.button("Del", key=f"inbox_del_{_db_entry['dist_id']}", use_container_width=True):
                        with db.get_conn() as _conn:
                            _conn.execute("DELETE FROM distributions WHERE id = ?", (_db_entry["dist_id"],))
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No briefs have been distributed to you yet.")

# ── TAB 9: Messages ───────────────────────────────────────────
with tabs[8]:
    st.markdown("#### Secure Message Center")
    _msg_tab1, _msg_tab2, _msg_tab3 = st.tabs(["Inbox", "Sent", "Compose"])

    with _msg_tab1:
        _inbox = db.get_inbox(user)
        if _inbox:
            for _msg in _inbox:
                _is_unread_m = not _msg.get("read_at")
                _from_info   = db.get_user(_msg["from_user"])
                _from_disp   = _from_info["display"] if _from_info else _msg["from_user"].upper()
                with st.expander(f"{'🔵 ' if _is_unread_m else ''}{_from_disp} — {_msg['subject']} [{_msg['sent_at'][:16]}]"):
                    db.mark_message_read(_msg["id"])
                    st.markdown(f'<div style="font-size:0.72rem;color:#2a5a8a;margin-bottom:8px;">FROM: {_from_disp} &nbsp;|&nbsp; {_msg["sent_at"][:16]}</div>', unsafe_allow_html=True)
                    if _msg.get("briefing_id"):
                        st.markdown(f'<div style="font-size:0.68rem;color:#1a4fa0;margin-bottom:8px;">RE: Brief {_msg["briefing_id"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:0.86rem;color:#9ab8d4;white-space:pre-wrap;">{_msg["body"]}</div>', unsafe_allow_html=True)
                    _reply_key = f"reply_{_msg['id']}"
                    _reply_body = st.text_area("Reply", key=_reply_key, height=80, placeholder="Type reply...")
                    if st.button("Send Reply", key=f"reply_btn_{_msg['id']}"):
                        if _reply_body.strip():
                            db.send_message(user, _msg["from_user"], f"RE: {_msg['subject']}", _reply_body, _msg.get("briefing_id"))
                            st.success("Reply sent.")
                            st.rerun()
        else:
            st.info("Your inbox is empty.")

    with _msg_tab2:
        _sent = db.get_sent(user)
        if _sent:
            for _msg in _sent:
                _to_info  = db.get_user(_msg["to_user"])
                _to_disp  = _to_info["display"] if _to_info else _msg["to_user"].upper()
                _read_ind = "✓ Read" if _msg.get("read_at") else "Unread"
                _rcolor   = "#3ddc6e" if _msg.get("read_at") else "#ffb84d"
                with st.expander(f"TO: {_to_disp} — {_msg['subject']} [{_msg['sent_at'][:16]}]"):
                    st.markdown(f'<div style="font-size:0.72rem;color:#2a5a8a;margin-bottom:8px;">TO: {_to_disp} &nbsp;|&nbsp; {_msg["sent_at"][:16]} &nbsp;|&nbsp; <span style="color:{_rcolor};">{_read_ind}</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:0.86rem;color:#9ab8d4;white-space:pre-wrap;">{_msg["body"]}</div>', unsafe_allow_html=True)
        else:
            st.info("No sent messages.")

    with _msg_tab3:
        st.markdown("**New Secure Message**")
        _all_users = [u for u in db.get_all_users() if u["username"] != user]
        _user_options = {f"{u['display']} — {u['title']}": u["username"] for u in _all_users}
        _to_label  = st.selectbox("To", options=list(_user_options.keys()), key="compose_to_sel")
        _c_subject = st.text_input("Subject", key="compose_subject_inp", placeholder="RE: Brief PDSS-...")
        _c_body    = st.text_area("Message", key="compose_body_inp", height=120, placeholder="Secure message body...")
        _ref_brief = ""
        _cur_brief = st.session_state.get("current_result")
        if _cur_brief:
            if st.checkbox(f"Reference current brief ({_cur_brief.get('briefing_id','N/A')})", key="compose_ref"):
                _ref_brief = _cur_brief.get("briefing_id","")
        if st.button("SEND SECURE MESSAGE", use_container_width=False, key="compose_send"):
            if _c_subject.strip() and _c_body.strip():
                db.send_message(user, _user_options[_to_label], _c_subject, _c_body, _ref_brief or None)
                st.success(f"Message sent to {_to_label.split(' — ')[0]}.")
                st.rerun()
            else:
                st.warning("Subject and message body are required.")

# ── TAB 10: Archive ───────────────────────────────────────────
with tabs[9]:
    st.markdown("#### Decision Run Archive")
    _all_briefs = db.list_briefs(operator=user if user_role != "admin" else None, limit=100)
    if _all_briefs:
        st.dataframe(pd.DataFrame(_all_briefs), use_container_width=True, hide_index=True)
    else:
        st.info("No archived runs yet.")

    st.divider()
    _export_res = st.session_state.current_result
    if _export_res:
        st.markdown("#### Export Current Run")
        _export_data = {k: v for k, v in _export_res.items() if k != "map_pts"}
        st.download_button(
            "Download Run as JSON",
            data=json.dumps(_export_data, indent=2, default=str),
            file_name=f"pdss_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )