"""
PIM Play
by PIM team

A pre-presentation quiz to measure the room's PIM knowledge
before the main talk begins.

12 questions drawn from a pool of 15 per play.
Topics: what PIM is, Dan Murphy's, BWS, Langtons,
        data quality rules, inbound/outbound, workflows.

Same design as PIM Survivor. Different stakes.
No health — just points. No death — just scores.
Leaderboard at the end shows everyone's ranking.

Requires a Google Sheet tab named  "Quiz"
with row-1 headers:  Timestamp | Name | Score | Rank
"""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


# ─────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────
QUESTIONS_PER_PLAY = 12
POINTS_PER_CORRECT = 100

st.set_page_config(
    page_title="PIM Knowledge Check",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ═══════════════════════════════════════════════════════════════════
# STYLES — identical aurora + glassmorphism base, quiz-specific
#          accent colours (cyan/blue instead of coral/red)
# ═══════════════════════════════════════════════════════════════════
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-base:     #1a1d40;
    --bg-deep:     #13162e;
    --surface:     rgba(52, 62, 110, 0.55);
    --surface-2:   rgba(66, 78, 128, 0.70);
    --border:      rgba(255, 255, 255, 0.13);
    --border-hi:   rgba(255, 255, 255, 0.27);
    --text:        #fafaff;
    --text-mute:   #c5c6e2;
    --text-dim:    #8e90b5;
    --gold:        #ffd56b;
    --pink:        #ff6bc7;
    --cyan:        #6bdfff;
    --blue:        #7b9fff;
    --green:       #5ee29c;
    --danger:      #ff6680;
    --danger-soft: rgba(255, 102, 128, 0.16);
    --correct:     #5ee29c;
    --correct-soft:rgba(94, 226, 156, 0.15);
    --wrong:       #ff6680;
    --wrong-soft:  rgba(255, 102, 128, 0.15);
    --quiz-accent: #7b9fff;
    --quiz-soft:   rgba(123, 159, 255, 0.16);
}

.stApp { background: var(--bg-base); }

/* ── AURORA — same drifting blobs, slightly cooler blue-toned ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: -25%;
    background:
        radial-gradient(40% 40% at 25% 35%, rgba(123, 159, 255, 0.28) 0%, transparent 60%),
        radial-gradient(44% 44% at 78% 68%, rgba(255, 107, 199, 0.22) 0%, transparent 60%),
        radial-gradient(50% 50% at 55% 18%, rgba(107, 223, 255, 0.20) 0%, transparent 60%),
        radial-gradient(34% 34% at 32% 82%, rgba(94, 226, 156, 0.14) 0%, transparent 60%);
    filter: blur(70px);
    z-index: 0;
    pointer-events: none;
    animation: aurora 20s ease-in-out infinite alternate;
    will-change: transform;
}
@keyframes aurora {
    0%   { transform: translate(0,    0)    scale(1)    rotate(0deg);   }
    25%  { transform: translate(-4%,  3%)   scale(1.07) rotate(2deg);   }
    50%  { transform: translate(3%,  -4%)   scale(0.95) rotate(-2deg);  }
    75%  { transform: translate(-2%, -3%)   scale(1.09) rotate(1.5deg); }
    100% { transform: translate(2%,   2%)   scale(1.01) rotate(-1deg);  }
}
.main, .block-container { position: relative; z-index: 1; }

html, body, .main, [class*="css"], p, span, div, label, li {
    font-family: 'Inter', -apple-system, system-ui, sans-serif !important;
    color: var(--text);
}
code, .mono { font-family: 'JetBrains Mono', monospace !important; }

.main .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 780px; }

h1 { font-size: 2.2rem !important; font-weight: 800 !important; letter-spacing: -0.03em !important; line-height: 1.1 !important; margin-bottom: 0.5rem !important; }
h2 { font-size: 1.2rem !important; font-weight: 600 !important; }

/* ── KINETIC TITLE — cyan/blue/pink for the quiz ── */
.kinetic {
    background: linear-gradient(120deg, var(--cyan), var(--blue), var(--pink), var(--cyan));
    background-size: 300% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shift 5s ease-in-out infinite;
}
@keyframes shift { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }

.eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--cyan);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-weight: 600;
    margin-bottom: 0.5rem;
    animation: rise 0.6s ease-out;
}

@keyframes rise {
    0%   { opacity: 0; transform: translateY(24px) scale(0.96); }
    60%  { opacity: 1; transform: translateY(-4px) scale(1.01); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── GLASS CARDS ── */
.glass {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem 1.7rem;
    margin: 1rem 0;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    box-shadow: 0 1px 0 rgba(255,255,255,0.08) inset, 0 20px 50px -20px rgba(0,0,0,0.55);
    animation: rise 0.6s cubic-bezier(0.34, 1.4, 0.5, 1);
    transition: border-color 0.3s ease, transform 0.3s cubic-bezier(0.22,1,0.36,1), box-shadow 0.3s ease;
}
.glass:hover { border-color: var(--border-hi); transform: translateY(-4px); box-shadow: 0 1px 0 rgba(255,255,255,0.08) inset, 0 28px 60px -20px rgba(0,0,0,0.7); }

.card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--cyan);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    font-weight: 700;
}

/* ── HUD (score display instead of health bar) ── */
.hud {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 1.4rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.9rem 1.3rem;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    animation: rise 0.5s cubic-bezier(0.34, 1.4, 0.5, 1);
}
.hud-cell { font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: var(--text-mute); letter-spacing: 0.08em; text-transform: uppercase; }
.hud-cell .v { color: var(--text); font-weight: 700; font-size: 0.95rem; margin-left: 5px; }
.hud-center { display: flex; align-items: center; gap: 1rem; justify-content: center; }

/* ── PROGRESS BAR (question completion, not health) ── */
.prog-track {
    width: 220px;
    height: 10px;
    background: rgba(0,0,0,0.45);
    border: 1px solid var(--border);
    border-radius: 5px;
    overflow: hidden;
}
.prog-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, var(--cyan), var(--blue));
    transition: width 0.6s cubic-bezier(0.34, 1.3, 0.55, 1);
    position: relative;
}
.prog-fill::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,0.28) 50%, transparent 70%);
    animation: shimmer 2s linear infinite;
}
@keyframes shimmer { 0% { transform: translateX(-150%); } 100% { transform: translateX(150%); } }
.prog-label { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 700; color: var(--cyan); white-space: nowrap; }

/* ── SCORE BADGE ── */
.score-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: var(--gold);
    background: rgba(255,213,107,0.12);
    border: 1px solid rgba(255,213,107,0.35);
    border-radius: 8px;
    padding: 4px 14px;
    letter-spacing: 0.02em;
    animation: score-pop 0.4s cubic-bezier(0.34,1.5,0.55,1);
}
@keyframes score-pop {
    0% { transform: scale(0.85); opacity: 0.6; }
    100% { transform: scale(1); opacity: 1; }
}

/* ── QUESTION CARD — blue left border instead of coral ── */
.q-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--quiz-accent);
    border-radius: 16px;
    padding: 1.7rem 1.9rem;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    box-shadow: 0 20px 50px -20px rgba(0,0,0,0.6);
    animation: rise 0.65s cubic-bezier(0.34, 1.4, 0.5, 1);
    transition: transform 0.4s cubic-bezier(0.22,1,0.36,1), box-shadow 0.4s ease;
    transform-style: preserve-3d;
}
.q-card:hover {
    transform: perspective(900px) rotateX(-1deg) rotateY(0.5deg) translateY(-3px);
    box-shadow: 0 28px 65px -25px rgba(0,0,0,0.8);
}
.q-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 700;
    color: var(--quiz-accent);
    background: var(--quiz-soft);
    border: 1px solid rgba(123,159,255,0.42);
    border-radius: 6px;
    padding: 4px 11px;
    margin-bottom: 0.9rem;
    letter-spacing: 0.14em;
    animation: q-pulse 2.4s ease-out infinite;
}
@keyframes q-pulse {
    0%   { box-shadow: 0 0 0 0   rgba(123,159,255,0.55); }
    70%  { box-shadow: 0 0 0 9px rgba(123,159,255,0);    }
    100% { box-shadow: 0 0 0 0   rgba(123,159,255,0);    }
}
.q-card:hover .q-tag { animation: q-pulse 2.4s ease-out infinite, glitch 0.7s ease-in-out; }
@keyframes glitch {
    0%,100% { text-shadow: none; transform: translate(0); }
    20%     { text-shadow: -3px 0 var(--pink), 3px 0 var(--cyan); transform: translate(2px,0); }
    40%     { text-shadow:  3px 0 var(--pink),-3px 0 var(--cyan); transform: translate(-2px,0); }
    60%     { text-shadow: -2px 0 var(--gold), 2px 0 var(--pink); transform: translate(0,2px); }
    80%     { text-shadow:  2px 0 var(--gold),-2px 0 var(--pink); transform: translate(0,-2px); }
}
.q-title { font-size: 1.2rem; font-weight: 700; color: var(--text); margin-bottom: 0.5rem; line-height: 1.4; letter-spacing: -0.015em; }
.q-subtitle { color: var(--text-mute); font-size: 0.97rem; line-height: 1.65; }

/* ── OPTION BUTTONS ── */
.stButton { width: 100%; }
.stButton button {
    width: 100% !important;
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: 12px !important;
    text-align: left !important;
    padding: 1rem 1.25rem !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.97rem !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    white-space: normal !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    box-shadow: 0 4px 16px -8px rgba(0,0,0,0.3) !important;
    letter-spacing: -0.005em !important;
    transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s cubic-bezier(0.22,1,0.36,1), box-shadow 0.2s ease !important;
}
.stButton button:hover {
    border-color: var(--cyan) !important;
    background: rgba(107,223,255,0.07) !important;
    transform: translateY(-4px) scale(1.01) !important;
    box-shadow: 0 14px 36px -10px rgba(107,223,255,0.4) !important;
}
.stButton button:active { transform: translateY(-1px) scale(1) !important; transition-duration: 0.07s !important; }

/* ── PRIMARY BUTTON ── */
.primary-action .stButton button {
    background: linear-gradient(135deg, var(--cyan) 0%, var(--blue) 55%, var(--pink) 100%) !important;
    color: #13162e !important;
    border-color: transparent !important;
    text-align: center !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    background-size: 200% 200% !important;
    animation: pulse-primary 4s ease-in-out infinite !important;
}
@keyframes pulse-primary { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
.primary-action .stButton button:hover {
    transform: translateY(-4px) scale(1.02) !important;
    box-shadow: 0 18px 44px -12px rgba(107,223,255,0.55) !important;
}

/* ── RESULT PANELS ── */
.result-panel {
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin: 1rem 0;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    animation: rise 0.55s cubic-bezier(0.34, 1.4, 0.5, 1);
}
.result-panel.correct {
    background: var(--surface);
    border: 1.5px solid rgba(94,226,156,0.45);
    box-shadow: 0 0 0 1px rgba(94,226,156,0.1) inset, 0 20px 50px -20px rgba(94,226,156,0.22);
}
.result-panel.wrong {
    background: var(--surface);
    border: 1.5px solid rgba(255,102,128,0.45);
    box-shadow: 0 0 0 1px rgba(255,102,128,0.1) inset, 0 20px 50px -20px rgba(255,102,128,0.18);
}
.result-verdict {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.84rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}
.result-verdict.correct { color: var(--correct); }
.result-verdict.wrong   { color: var(--wrong); }
.result-answer { font-size: 0.95rem; color: var(--text-mute); margin-bottom: 0.8rem; font-style: italic; padding-left: 1rem; border-left: 3px solid var(--border-hi); line-height: 1.5; }
.result-explain { color: var(--text); font-size: 1.02rem; line-height: 1.7; margin-bottom: 0.9rem; }
.result-points {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 7px;
}
.result-points.earned  { color: var(--correct); background: var(--correct-soft); border: 1px solid rgba(94,226,156,0.4); }
.result-points.nothing { color: var(--wrong);   background: var(--wrong-soft);   border: 1px solid rgba(255,102,128,0.4); }

/* ── BANNER (end screen) ── */
.banner {
    border-radius: 18px;
    padding: 2.4rem 1.8rem;
    text-align: center;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    animation: rise 0.8s cubic-bezier(0.34, 1.4, 0.5, 1);
}
.banner {
    border: 1.5px solid rgba(107,223,255,0.45);
    background: linear-gradient(160deg, rgba(123,159,255,0.18) 0%, rgba(107,223,255,0.1) 50%, var(--surface) 100%);
}
.banner .glyph  { font-size: 3.2rem; margin-bottom: 0.5rem; line-height: 1; }
.banner .name-line { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--gold); letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.5rem; font-weight: 700; }
.banner .title  { font-size: 1.85rem; font-weight: 800; color: var(--text); margin-bottom: 0.6rem; letter-spacing: -0.025em; line-height: 1.15; }
.banner .subtitle { color: var(--text-mute); font-size: 1rem; line-height: 1.65; max-width: 500px; margin: 0 auto; }

/* ── STAT TILES ── */
.stat { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.1rem 1.2rem; text-align: center; backdrop-filter: blur(24px) saturate(160%); -webkit-backdrop-filter: blur(24px) saturate(160%); transition: border-color 0.25s ease, transform 0.25s ease; animation: rise 0.5s cubic-bezier(0.34,1.4,0.5,1) backwards; }
.stat:hover { border-color: var(--border-hi); transform: translateY(-4px); }
.stat:nth-of-type(1) { animation-delay: 0.05s; }
.stat:nth-of-type(2) { animation-delay: 0.12s; }
.stat:nth-of-type(3) { animation-delay: 0.19s; }
.stat .stat-label { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--text-mute); letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.5rem; font-weight: 600; }
.stat .stat-value { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 800; color: var(--text); letter-spacing: -0.02em; }
.stat .stat-value.small { font-size: 1rem; line-height: 1.35; }

/* ── CONFETTI ── */
.confetti-container { position: fixed; inset: 0; pointer-events: none; z-index: 999; overflow: hidden; }
.confetti { position: absolute; top: -30px; border-radius: 2px; opacity: 0.95; animation: confetti-fall 5s linear forwards; }
@keyframes confetti-fall { 0% { transform: translateY(0) rotate(0deg); opacity: 1; } 100% { transform: translateY(110vh) rotate(900deg); opacity: 0; } }

/* ── INPUTS ── */
.stTextInput input { background: var(--surface-2) !important; color: var(--text) !important; border: 1px solid var(--border-hi) !important; border-radius: 10px !important; font-size: 1rem !important; padding: 0.8rem 1rem !important; backdrop-filter: blur(14px); transition: border-color 0.25s ease, box-shadow 0.25s ease !important; }
.stTextInput input:focus { border-color: var(--cyan) !important; box-shadow: 0 0 0 5px rgba(107,223,255,0.15) !important; outline: none !important; }
.stTextInput input::placeholder { color: var(--text-dim) !important; }
.stTextInput label { color: var(--text-mute) !important; font-size: 0.88rem !important; font-weight: 600 !important; }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; backdrop-filter: blur(20px); transition: border-color 0.25s ease; }
[data-testid="stDataFrame"]:hover { border-color: var(--border-hi); }

hr { border-color: var(--border) !important; margin: 2rem 0 !important; }
#MainMenu, footer, header { visibility: hidden; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }
</style>
"""


# ═══════════════════════════════════════════════════════════════════
# QUESTION POOL — 15 questions, 12 drawn per play
#
# Each question covers a real PIM concept, uses team member names
# where it lands naturally, and has exactly one correct option.
# Wrong options are plausible enough to be genuinely funny.
#
# Team: Harry, Mara, Yang, ShiChang, Roshan,
#       Aparna, Abhilash, Chien, Vincy, Danish, Ana, Ati
# ═══════════════════════════════════════════════════════════════════
QUIZ_POOL = [
    {
        "tag":      "WHAT IS PIM",
        "question": "What does PIM stand for?",
        "context":  "Harry Googled this before today's session. The results were confusing. Let's sort it out now.",
        "options": [
            {"text": "Product Information Management",                                "correct": True},
            {"text": "Product Integration Module",                                    "correct": False},
            {"text": "Priority Item Merchandising",                                   "correct": False},
            {"text": "Pretty Important Meetings — Mara's calendar is full of these",  "correct": False},
        ],
        "explanation": "PIM = Product Information Management. It's the central system for storing, managing, enriching, and distributing product data across every channel — websites, apps, marketplaces, and more.",
    },
    {
        "tag":      "WHAT IS PIM",
        "question": "What is a 'Golden Record' in product data management?",
        "context":  "Roshan uses this term constantly. It is worth knowing what it means.",
        "options": [
            {"text": "The single authoritative product version merged from all sources", "correct": True},
            {"text": "A product with zero data quality failures in its entire history",  "correct": False},
            {"text": "A vinyl record that passed catalog validation",                    "correct": False},
            {"text": "Roshan's name for a perfect pull request — he has many names",    "correct": False},
        ],
        "explanation": "A Golden Record is the single trusted version of a product, created by reconciling information from multiple source systems. When suppliers and internal systems disagree, the Golden Record is the tie-breaker.",
    },
    {
        "tag":      "WHAT IS PIM",
        "question": "What does 'data enrichment' mean in a PIM context?",
        "context":  "Aparna does this daily. She has feelings about what counts as enriched and what does not.",
        "options": [
            {"text": "Adding missing or enhanced information to existing product records",  "correct": True},
            {"text": "Encrypting sensitive product data before storage",                   "correct": False},
            {"text": "Charging suppliers a fee to appear in the catalog",                  "correct": False},
            {"text": "Aparna's morning routine before the data team standup",              "correct": False},
        ],
        "explanation": "Enrichment is the process of improving product records — filling in missing descriptions, adding high-quality images, writing marketing copy, tagging attributes. It happens after a record clears the DQ gate.",
    },
    {
        "tag":      "INBOUND / OUTBOUND",
        "question": "What is the difference between 'inbound' and 'outbound' in PIM?",
        "context":  "Yang built pipelines for both. Yang has strong opinions about which one is harder.",
        "options": [
            {"text": "Inbound = data coming FROM suppliers. Outbound = data going TO channels",  "correct": True},
            {"text": "Inbound = products shipped in physically. Outbound = products shipped out", "correct": False},
            {"text": "Inbound = approved records. Outbound = rejected records",                   "correct": False},
            {"text": "Inbound = Yang's morning. Outbound = Yang's evening",                       "correct": False},
        ],
        "explanation": "Inbound covers receiving and processing data from suppliers into the PIM. Outbound covers syndicating that data to channels — websites, apps, DoorDash, UberEats, and so on. Both require different validation rules.",
    },
    {
        "tag":      "DAN MURPHY'S",
        "question": "Dan Murphy's carries spirits, wine, beer, and RTD. Which set of fields makes a WINE product fully complete in the catalog?",
        "context":  "Ana checks product completeness every morning. Ana has a checklist. The checklist is laminated.",
        "options": [
            {"text": "Vintage year, ABV, volume (ml), grape variety, region",        "correct": True},
            {"text": "Barcode, weight (kg), fragrance, allergen rating",             "correct": False},
            {"text": "Delivery time, warehouse bin location, supplier code",          "correct": False},
            {"text": "Ana's approval — required, but technically not a catalog field","correct": False},
        ],
        "explanation": "Wine products need: vintage year (e.g. 2021), ABV percentage, volume in ml, grape variety (Shiraz, Riesling, etc.), and region (Barossa, Yarra Valley). Without these, the product can't be correctly filtered or found by customers.",
    },
    {
        "tag":      "DAN MURPHY'S",
        "question": "Yang notices that 2,000 Dan Murphy's products have no product image. What is the most likely catalog impact?",
        "context":  "Yang is looking at the monitoring dashboard. Yang's expression is difficult to read.",
        "options": [
            {"text": "Products won't display correctly and conversion drops significantly",  "correct": True},
            {"text": "Products still sell fine — customers do not look at images",           "correct": False},
            {"text": "The system automatically generates a placeholder from the brand logo", "correct": False},
            {"text": "Yang reports it to Abhilash who reports it to someone whose ownership is unclear", "correct": False},
        ],
        "explanation": "Images are one of the highest-impact fields in eCommerce. Products without images see significantly lower conversion rates. Most PIM systems include image validation as a mandatory DQ rule before a product can go live.",
    },
    {
        "tag":      "BWS",
        "question": "BWS focuses on convenience and speed. What type of product data matters MOST for BWS-specific channel requirements?",
        "context":  "ShiChang built the BWS outbound feed. ShiChang has many stories about it.",
        "options": [
            {"text": "Accurate stock levels, quick-purchase attributes, lightweight images",         "correct": True},
            {"text": "Long-form tasting notes and sommelier commentary",                             "correct": False},
            {"text": "Vintage provenance, auction history, and cellar maturity ratings",             "correct": False},
            {"text": "ShiChang's translation pipeline outputs — they work for everything apparently","correct": False},
        ],
        "explanation": "BWS serves convenience shoppers who want fast checkout. That means real-time stock accuracy, short punchy descriptions, and lightweight imagery optimised for mobile. Long tasting notes and provenance are for a different audience entirely.",
    },
    {
        "tag":      "LANGTONS",
        "question": "Langtons is very different from Dan Murphy's and BWS. What does Langtons specialise in?",
        "context":  "Chien had to look this up. Chien is not embarrassed about it.",
        "options": [
            {"text": "Fine wine, investment-grade bottles, and auction services",          "correct": True},
            {"text": "Ready-to-drink cocktail packs and premixed spirits",                 "correct": False},
            {"text": "Bulk spirits and kegs for the hospitality industry",                  "correct": False},
            {"text": "Chien's favourite Friday afternoon destination — important but separate","correct": False},
        ],
        "explanation": "Langtons is Australia's premier fine wine marketplace. It handles auction listings, cellar tracking, and investment-grade bottles. The product data requirements are completely different — provenance, drinkability windows, auction estimates — things a standard bottle shop never needs.",
    },
    {
        "tag":      "LANGTONS",
        "question": "Aparna is mapping product data for a Langtons listing. Which of these fields exists for Langtons but NOT for a Dan Murphy's listing?",
        "context":  "This one took Aparna a while to figure out when she first joined. She figured it out.",
        "options": [
            {"text": "Auction estimate, provenance history, cellar maturity rating",  "correct": True},
            {"text": "Barcode and SKU",                                                "correct": False},
            {"text": "ABV percentage",                                                 "correct": False},
            {"text": "Volume in millilitres",                                          "correct": False},
        ],
        "explanation": "Langtons needs fields that don't exist in a standard bottle shop catalog: auction estimates, provenance (where the bottle has been stored and by whom), and drinkability windows. ABV and volume are universal — they appear everywhere.",
    },
    {
        "tag":      "DATA QUALITY",
        "question": "Abhilash's ingest pipeline received 10,000 products but only 8,200 reached the catalog. What most likely happened?",
        "context":  "Abhilash has a dashboard for this. Abhilash always has a dashboard.",
        "options": [
            {"text": "1,800 records failed DQ rules and were quarantined for review",           "correct": True},
            {"text": "The pipeline ran during lunch and processed more slowly",                  "correct": False},
            {"text": "1,800 products were discontinued mid-import",                             "correct": False},
            {"text": "Abhilash deliberately set the batch cap to 8,200 for performance reasons","correct": False},
        ],
        "explanation": "A DQ gate validates every record against configured rules — mandatory fields, data types, reference data lookups, range checks. Records that fail are quarantined and don't go live until the issues are resolved. This is by design, not a bug.",
    },
    {
        "tag":      "DATA QUALITY",
        "question": "Which of these would FAIL a standard PIM data quality rule for an alcohol product?",
        "context":  "Vincy caught this exact issue in a supplier feed last month. Vincy was not impressed.",
        "options": [
            {"text": "ABV field contains the text 'strong enough'",    "correct": True},
            {"text": "ABV field contains the number 14.5",              "correct": False},
            {"text": "Volume field contains the number 750",            "correct": False},
            {"text": "Product name contains 'Penfolds Bin 389'",        "correct": False},
        ],
        "explanation": "ABV must be a numeric value (like 14.5). 'Strong enough' is free text in a numeric field — a type validation failure. This is one of the most common DQ issues in PIM ingest, especially from suppliers who fill fields manually.",
    },
    {
        "tag":      "DATA QUALITY",
        "question": "Ana finds that 300 products have the category field set to 'NULL'. Which DQ rule was missing?",
        "context":  "Ana found this during a routine catalog audit. Ana runs routine catalog audits because Ana cares.",
        "options": [
            {"text": "A mandatory field check with reference data lookup against valid categories",  "correct": True},
            {"text": "A duplicate detection rule",                                                    "correct": False},
            {"text": "An image file size validation rule",                                            "correct": False},
            {"text": "A price range check",                                                           "correct": False},
        ],
        "explanation": "Category is mandatory — but 'NULL' can technically pass a simple mandatory check if the rule only verifies the field isn't empty. A reference data lookup validates the value against a list of permitted categories. 'NULL' is not on that list.",
    },
    {
        "tag":      "WORKFLOW",
        "question": "Vincy notices a product has been in 'Pending Enrichment' state for 6 days. What does this mean in a PIM workflow?",
        "context":  "This is not unusual. The fact that Vincy noticed it is what is unusual.",
        "options": [
            {"text": "It passed DQ but hasn't received complete data yet — it's waiting in the enrichment queue",  "correct": True},
            {"text": "The product was rejected by the supplier and is awaiting resubmission",                       "correct": False},
            {"text": "The product is so good the system is withholding it for dramatic effect",                    "correct": False},
            {"text": "Danish's Azure service went down again and took enrichment with it",                          "correct": False},
        ],
        "explanation": "PIM workflow stages: Ingest → DQ Gate → Enrichment → Approval → Publish. 'Pending Enrichment' means the record cleared DQ validation but is waiting for descriptions, images, or attributes to be added. Six days is a long time to wait — that queue needs attention.",
    },
    {
        "tag":      "WORKFLOW",
        "question": "A product passes all DQ rules, gets enriched, and is approved. What happens next in the PIM outbound workflow?",
        "context":  "Roshan signed off on this product three times because Roshan signs off on things three times.",
        "options": [
            {"text": "It is syndicated — formatted and sent to each registered channel",           "correct": True},
            {"text": "It is sent to a warehouse for a physical quality inspection",                "correct": False},
            {"text": "It automatically becomes a bestseller by virtue of being approved",          "correct": False},
            {"text": "Roshan reviews it one more time — Roshan always reviews it one more time",   "correct": False},
        ],
        "explanation": "Syndication is the outbound stage. The product data is formatted to meet each channel's specific requirements and pushed out — to the Dan Murphy's website, BWS app, UberEats, DoorDash, Langtons, print, and wherever else it's registered.",
    },
    {
        "tag":      "DATA QUALITY",
        "question": "The same bottle of wine is listed differently on Dan Murphy's vs BWS. Which field is MOST likely to differ between channels?",
        "context":  "ShiChang manages both outbound feeds and has very specific thoughts about this question.",
        "options": [
            {"text": "Product description — each channel has its own tone and length requirements",  "correct": True},
            {"text": "ABV percentage — each channel measures alcohol differently",                   "correct": False},
            {"text": "Volume in millilitres — it depends on the bottle",                             "correct": False},
            {"text": "The wine itself — it is genuinely a different product per channel",            "correct": False},
        ],
        "explanation": "Core data — ABV, volume, vintage — stays consistent across channels. That's the Golden Record principle. Channel-specific fields like description length, image format, and marketing copy are customised per channel. This is exactly what outbound syndication handles.",
    },
]


# ═══════════════════════════════════════════════════════════════════
# DATA LAYER
# ═══════════════════════════════════════════════════════════════════
SHEET_NAME     = "PIM_Odyssey_DB"
WORKSHEET_NAME = "Quiz"   # Add a tab called "Quiz" with headers: Timestamp | Name | Score | Rank
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _get_worksheet():
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)


def save_score(name: str, score: int, rank: str) -> bool:
    try:
        ws = _get_worksheet()
        ws.append_row([datetime.now().isoformat(timespec="seconds"), name, score, rank])
        return True
    except Exception:
        return False


def fetch_leaderboard() -> pd.DataFrame:
    try:
        ws = _get_worksheet()
        rows = ws.get_all_values()
        if len(rows) < 2:
            return pd.DataFrame()
        headers = [h.strip() for h in rows[0]]
        df = pd.DataFrame(rows[1:], columns=headers)
        if "Score" not in df.columns or "Name" not in df.columns:
            return pd.DataFrame()
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0).astype(int)
        out = (df.groupby("Name", as_index=False)
                 .agg({"Score": "max", "Rank": "first"})
                 .sort_values("Score", ascending=False).head(15)
                 .reset_index(drop=True))
        out.index = out.index + 1
        out.index.name = "#"
        return out
    except Exception:
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════
# SCORING & RANKING
# ═══════════════════════════════════════════════════════════════════
MAX_SCORE = QUESTIONS_PER_PLAY * POINTS_PER_CORRECT   # 1200

def rank_for(score: int) -> str:
    pct = score / MAX_SCORE
    if pct >= 0.92: return "PIM Expert — you should be presenting this yourself"
    if pct >= 0.75: return "Strong Foundation — you have clearly been paying attention"
    if pct >= 0.58: return "Solid Awareness — this presentation will make a lot of sense"
    if pct >= 0.42: return "Getting There — you will leave knowing much more"
    if pct >= 0.25: return "Fresh Perspective — no assumptions, maximum learning"
    return "Blank Canvas — the best possible starting point"


# ═══════════════════════════════════════════════════════════════════
# STATE
# ═══════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "stage":           "intro",
        "name":            "",
        "score":           0,
        "correct_count":   0,
        "question_order":  [],         # shuffled indices into QUIZ_POOL
        "question_idx":    0,          # position in question_order
        "shuffled_opts":   [],         # shuffled options for current question
        "last_result":     None,       # set after answering
        "started_at":      None,
        "saved":           False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def goto(stage: str):
    st.session_state.stage = stage
    st.rerun()


def start_run(name: str):
    order = random.sample(range(len(QUIZ_POOL)), QUESTIONS_PER_PLAY)
    st.session_state.update({
        "name":          name,
        "score":         0,
        "correct_count": 0,
        "question_order": order,
        "question_idx":   0,
        "shuffled_opts":  _shuffle_opts(order[0]),
        "last_result":    None,
        "started_at":     time.time(),
        "saved":          False,
    })
    goto("question")


def _shuffle_opts(pool_idx: int) -> list[dict]:
    opts = QUIZ_POOL[pool_idx]["options"][:]
    random.shuffle(opts)
    return opts


def current_question() -> dict:
    idx = st.session_state.question_order[st.session_state.question_idx]
    return QUIZ_POOL[idx]


# ═══════════════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════════════
def render_hud():
    q_num  = st.session_state.question_idx + 1
    score  = st.session_state.score
    pct    = int((st.session_state.question_idx / QUESTIONS_PER_PLAY) * 100)

    st.markdown(
        f'<div class="hud">'
        f'  <div class="hud-cell">Question<span class="v">{q_num} of {QUESTIONS_PER_PLAY}</span></div>'
        f'  <div class="hud-center">'
        f'    <div class="prog-track"><div class="prog-fill" style="width:{pct}%;"></div></div>'
        f'    <span class="prog-label">{pct}%</span>'
        f'  </div>'
        f'  <div class="hud-cell"><span class="score-badge">✦ {score}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_confetti():
    colors = ["#ffd56b", "#ff6bc7", "#6bdfff", "#5ee29c", "#7b9fff", "#fafaff"]
    parts  = ['<div class="confetti-container">']
    for _ in range(55):
        parts.append(
            f'<div class="confetti" style="'
            f'left:{random.uniform(0,100)}vw; background:{random.choice(colors)}; '
            f'width:{random.choice([7,9,11])}px; height:{random.choice([11,15,19])}px; '
            f'animation-delay:{random.uniform(0,2.5)}s; animation-duration:{random.uniform(3.5,6.5)}s; '
            f'transform:rotate({random.uniform(-180,180)}deg);"></div>'
        )
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════
def screen_intro():
    st.markdown('<div class="eyebrow">Pre-presentation assessment</div>', unsafe_allow_html=True)
    st.markdown('<h1><span class="kinetic">How well do you know PIM?</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: var(--text-mute); font-size: 1.05rem; line-height: 1.7; margin-top: 0.3rem;">'
        '12 questions about product data, data quality rules, and how Dan Murphy\'s, BWS, and Langtons '
        'manage their catalog. Answer honestly — this tells us where to focus the presentation.'
        '</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="glass">'
        '<div class="card-label">How it works</div>'
        '<ul style="margin:0; padding-left:1.2rem; line-height:1.9; color:var(--text-mute); font-size:0.95rem;">'
        '<li>12 questions drawn from a pool of 15 — different every play</li>'
        '<li>4 options per question — one is correct</li>'
        '<li><strong style="color:var(--text);">+100 points</strong> for every correct answer</li>'
        '<li>No penalty for wrong answers — just be honest</li>'
        '<li>Leaderboard at the end shows how everyone scored</li>'
        '</ul>'
        '</div>',
        unsafe_allow_html=True,
    )

    name = st.text_input("Your name on the leaderboard", placeholder="how you'd like to appear", max_chars=32)

    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Start the quiz"):
        if name.strip():
            start_run(name.strip())
        else:
            st.warning("Please enter your name.")
    st.markdown('</div>', unsafe_allow_html=True)

    lb = fetch_leaderboard()
    if not lb.empty:
        st.markdown('<div class="card-label" style="margin-top:2.5rem;">Leaderboard</div>', unsafe_allow_html=True)
        st.dataframe(lb, use_container_width=True)


def screen_question():
    render_hud()
    q    = current_question()
    opts = st.session_state.shuffled_opts

    st.markdown(
        f'<div class="q-card">'
        f'<div class="q-tag">{q["tag"]}</div>'
        f'<div class="q-title">{q["question"]}</div>'
        f'<div class="q-subtitle">{q["context"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    q_key = st.session_state.question_idx
    for i, opt in enumerate(opts):
        if st.button(opt["text"], key=f"opt_{q_key}_{i}"):
            correct = opt["correct"]
            right_text = next(o["text"] for o in opts if o["correct"])

            if correct:
                st.session_state.score += POINTS_PER_CORRECT
                st.session_state.correct_count += 1

            st.session_state.last_result = {
                "correct":    correct,
                "chosen":     opt["text"],
                "right":      right_text,
                "explanation": q["explanation"],
                "points":     POINTS_PER_CORRECT if correct else 0,
            }
            goto("result")


def screen_result():
    r = st.session_state.last_result
    if r is None:
        goto("question")
        return

    render_hud()

    cls     = "correct" if r["correct"] else "wrong"
    verdict = "✓  Correct" if r["correct"] else "✗  Not quite"
    chosen_line = f'You chose: {r["chosen"]}' if r["correct"] else f'You chose: {r["chosen"]}<br>Correct answer: {r["right"]}'
    pts_cls = "earned" if r["correct"] else "nothing"
    pts_txt = f'+{r["points"]} points' if r["correct"] else 'No points this time'

    st.markdown(
        f'<div class="result-panel {cls}">'
        f'<div class="result-verdict {cls}">{verdict}</div>'
        f'<div class="result-answer">{chosen_line}</div>'
        f'<div class="result-explain">{r["explanation"]}</div>'
        f'<div class="result-points {pts_cls}">{pts_txt}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    is_last = st.session_state.question_idx >= QUESTIONS_PER_PLAY - 1

    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if is_last:
        if st.button("See your results"):
            st.session_state.last_result = None
            goto("end")
    else:
        nxt = st.session_state.question_idx + 2
        if st.button(f"Next question ({nxt} of {QUESTIONS_PER_PLAY})"):
            st.session_state.question_idx += 1
            idx = st.session_state.question_order[st.session_state.question_idx]
            st.session_state.shuffled_opts = _shuffle_opts(idx)
            st.session_state.last_result = None
            goto("question")
    st.markdown('</div>', unsafe_allow_html=True)


def screen_end():
    score   = st.session_state.score
    correct = st.session_state.correct_count
    name    = st.session_state.name or "anonymous"
    rank    = rank_for(score)
    elapsed = int(time.time() - st.session_state.started_at) if st.session_state.started_at else 0
    pct     = int(score / MAX_SCORE * 100)

    if pct >= 75:
        render_confetti()

    st.markdown(
        f'<div class="banner">'
        f'<div class="glyph">🧠</div>'
        f'<div class="name-line">{name}</div>'
        f'<div class="title">{correct} of {QUESTIONS_PER_PLAY} correct</div>'
        f'<div class="subtitle">{rank}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="stat"><div class="stat-label">Score</div>'
            f'<div class="stat-value" style="color: var(--cyan);">{score}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat"><div class="stat-label">Correct</div>'
            f'<div class="stat-value">{correct}/{QUESTIONS_PER_PLAY}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat"><div class="stat-label">Time</div>'
            f'<div class="stat-value">{elapsed // 60}m {elapsed % 60:02d}s</div></div>',
            unsafe_allow_html=True,
        )

    if not st.session_state.saved:
        save_score(name, score, rank)
        st.session_state.saved = True

    lb = fetch_leaderboard()
    if not lb.empty:
        st.markdown('<div class="card-label" style="margin-top:2rem;">Leaderboard</div>', unsafe_allow_html=True)
        st.dataframe(lb, use_container_width=True)

    st.markdown(
        '<p style="color: var(--text-mute); text-align: center; margin-top: 1.5rem; font-size: 0.95rem;">'
        "The presentation is about to begin. Your score is locked in. The leaderboard is live."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Play again"):
        kept = st.session_state.name
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        init_state()
        start_run(kept)
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════
def main():
    st.markdown(STYLE, unsafe_allow_html=True)
    init_state()

    stage = st.session_state.stage
    if   stage == "intro":    screen_intro()
    elif stage == "question": screen_question()
    elif stage == "result":   screen_result()
    elif stage == "end":      screen_end()
    else: goto("intro")


main()
