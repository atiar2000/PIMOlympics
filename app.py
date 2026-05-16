"""
PIMOlympics — a small game about catalog work
by Ati from PIM

You start with 100 Health. Eight things go wrong in a row.
You pick how to handle each one. The cost is shown before you pick.
The outcome is not.

If your Health hits zero, the shift ends in a way I am told is funny.
Survive all eight and you get a rank on the leaderboard.

Built with Streamlit. Hosted on Streamlit Cloud. Leaderboard lives in
Google Sheets. The animations are pure CSS. The writing is mine.
"""

from __future__ import annotations

import random
import time
from collections.abc import Mapping
from datetime import datetime
from typing import Optional

import json
import pandas as pd
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ─────────────────────────────────────────────────────────────────
# CORE NUMBERS
# ─────────────────────────────────────────────────────────────────
START_HEALTH = 100
ROUNDS = 8
SPREADSHEET_KEY = "1Svd5GGaUl7OHz1vCLC86PMzVvxLkbcMo7z6sIiTf9MQ"
WORKSHEET_NAME = "Scores"


# ─────────────────────────────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PIM Survivor",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ═══════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════
# Lighter twilight palette with vivid accents.
# Animations are loud on purpose — you should see them moving.
# ═══════════════════════════════════════════════════════════════════
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-base:     #1d2147;
    --bg-deep:     #161937;
    --surface:     rgba(58, 68, 110, 0.55);
    --surface-2:   rgba(72, 82, 130, 0.7);
    --border:      rgba(255, 255, 255, 0.14);
    --border-hi:   rgba(255, 255, 255, 0.28);
    --text:        #fafaff;
    --text-mute:   #c8c9e5;
    --text-dim:    #9295b8;
    --gold:        #ffd56b;
    --pink:        #ff6bc7;
    --cyan:        #6bdfff;
    --coral:       #ff8c5a;
    --green:       #5ee29c;
    --danger:      #ff6680;
    --danger-soft: rgba(255, 102, 128, 0.18);
    --gold-soft:   rgba(255, 213, 107, 0.16);
    --pink-soft:   rgba(255, 107, 199, 0.16);
    --cyan-soft:   rgba(107, 223, 255, 0.16);
}

.stApp { background: var(--bg-base); }

/* ── THE AURORA ─────────────────────────────────────────────────
   Three vivid gradient blobs that drift visibly, with a bigger
   amplitude than before. You should be able to watch them move. */
.stApp::before {
    content: '';
    position: fixed;
    inset: -25%;
    background:
        radial-gradient(38% 38% at 20% 30%, rgba(255, 213, 107, 0.28) 0%, transparent 60%),
        radial-gradient(42% 42% at 80% 70%, rgba(255, 107, 199, 0.24) 0%, transparent 60%),
        radial-gradient(48% 48% at 60% 20%, rgba(107, 223, 255, 0.22) 0%, transparent 60%),
        radial-gradient(35% 35% at 30% 85%, rgba(94, 226, 156, 0.15) 0%, transparent 60%);
    filter: blur(70px);
    z-index: 0;
    pointer-events: none;
    animation: aurora 18s ease-in-out infinite alternate;
    will-change: transform;
}
@keyframes aurora {
    0%   { transform: translate(0,    0)    scale(1)    rotate(0deg);   }
    25%  { transform: translate(-5%,  3%)   scale(1.08) rotate(2deg);   }
    50%  { transform: translate(4%,  -4%)   scale(0.95) rotate(-2deg);  }
    75%  { transform: translate(-3%, -3%)   scale(1.1)  rotate(1.5deg); }
    100% { transform: translate(2%,   2%)   scale(1.02) rotate(-1deg);  }
}

.main, .block-container { position: relative; z-index: 1; }

/* ── TYPOGRAPHY ─────────────────────────────────────────────── */
html, body, .main, [class*="css"], p, span, div, label, li {
    font-family: 'Inter', -apple-system, system-ui, sans-serif !important;
    color: var(--text);
}
code, .mono, [data-testid="stCodeBlock"] * {
    font-family: 'JetBrains Mono', monospace !important;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 780px;
}

h1 {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    line-height: 1.1 !important;
    margin-bottom: 0.5rem !important;
}
h2 { font-size: 1.2rem !important; font-weight: 600 !important; }

/* ── KINETIC GRADIENT TITLE — faster cycle, three vivid colors ── */
.kinetic {
    background: linear-gradient(120deg, var(--gold), var(--pink), var(--cyan), var(--gold));
    background-size: 300% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shift 5s ease-in-out infinite;
}
@keyframes shift {
    0%, 100% { background-position: 0% 50%; }
    50%      { background-position: 100% 50%; }
}

/* ── EYEBROW ────────────────────────────────────────────────── */
.eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--gold);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-weight: 600;
    margin-bottom: 0.5rem;
    animation: rise 0.6s ease-out;
}

/* ── ENTRANCE ANIMATION ─ bigger, springier, more visible ── */
@keyframes rise {
    0%   { opacity: 0; transform: translateY(24px) scale(0.96); }
    60%  { opacity: 1; transform: translateY(-4px) scale(1.01); }
    100% { opacity: 1; transform: translateY(0)   scale(1);    }
}

/* ── GLASS CARDS ─ stronger surface, more visible borders ── */
.glass {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem 1.7rem;
    margin: 1rem 0;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    box-shadow:
        0 1px 0 rgba(255, 255, 255, 0.08) inset,
        0 20px 50px -20px rgba(0, 0, 0, 0.55);
    animation: rise 0.6s cubic-bezier(0.34, 1.4, 0.5, 1);
    transition: border-color 0.3s ease,
                transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.3s ease;
}
.glass:hover {
    border-color: var(--border-hi);
    transform: translateY(-5px);
    box-shadow:
        0 1px 0 rgba(255, 255, 255, 0.08) inset,
        0 28px 60px -20px rgba(0, 0, 0, 0.7);
}

.card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--gold);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    font-weight: 700;
}

/* ── HUD ────────────────────────────────────────────────────── */
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
.hud-cell {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    color: var(--text-mute);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.hud-cell .v {
    color: var(--text);
    font-weight: 700;
    font-size: 0.95rem;
    margin-left: 5px;
}
.hud-center { display: flex; align-items: center; gap: 0.8rem; }
.hud-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-mute);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    white-space: nowrap;
    font-weight: 600;
}

/* ── HEALTH BAR ─ visible shimmer, animated fill, pulse when low ── */
.bar-track {
    flex: 1;
    height: 18px;
    background: rgba(0, 0, 0, 0.45);
    border: 1px solid var(--border);
    border-radius: 9px;
    overflow: hidden;
    position: relative;
    box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.6);
}
.bar-fill {
    height: 100%;
    border-radius: 8px;
    position: relative;
    transition: width 0.8s cubic-bezier(0.34, 1.3, 0.55, 1),
                background 0.5s ease,
                box-shadow 0.5s ease;
    box-shadow: 0 0 16px currentColor;
}
.bar-fill::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(110deg,
        transparent 0%,
        transparent 30%,
        rgba(255, 255, 255, 0.30) 50%,
        transparent 70%,
        transparent 100%);
    animation: shimmer 1.8s linear infinite;
}
.bar-fill.low {
    animation: pulse-low 0.7s ease-in-out infinite alternate;
}
@keyframes shimmer {
    0%   { transform: translateX(-150%); }
    100% { transform: translateX(150%); }
}
@keyframes pulse-low {
    from { filter: brightness(1)   saturate(1); }
    to   { filter: brightness(1.3) saturate(1.4); }
}
.bar-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.96rem;
    font-weight: 700;
    color: var(--text);
    min-width: 75px;
    text-align: right;
    letter-spacing: -0.02em;
}

/* ── CRISIS CARD ─ left edge accent, 3D tilt on hover ── */
.crisis {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--coral);
    border-radius: 16px;
    padding: 1.7rem 1.9rem;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    box-shadow: 0 20px 50px -20px rgba(0, 0, 0, 0.6);
    animation: rise 0.65s cubic-bezier(0.34, 1.4, 0.5, 1);
    transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.4s ease;
    transform-style: preserve-3d;
}
.crisis:hover {
    transform: perspective(900px) rotateX(-1.5deg) rotateY(0.8deg) translateY(-4px);
    box-shadow: 0 30px 70px -25px rgba(0, 0, 0, 0.8);
}

.crisis-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 700;
    color: var(--coral);
    background: rgba(255, 140, 90, 0.18);
    border: 1px solid rgba(255, 140, 90, 0.4);
    border-radius: 6px;
    padding: 4px 11px;
    margin-bottom: 0.9rem;
    letter-spacing: 0.14em;
    position: relative;
    animation: tag-pulse 2s ease-out infinite;
}
@keyframes tag-pulse {
    0%   { box-shadow: 0 0 0 0  rgba(255, 140, 90, 0.55); }
    70%  { box-shadow: 0 0 0 9px rgba(255, 140, 90, 0);   }
    100% { box-shadow: 0 0 0 0  rgba(255, 140, 90, 0);    }
}
.crisis:hover .crisis-tag { animation: tag-pulse 2s ease-out infinite, glitch 0.7s ease-in-out; }
@keyframes glitch {
    0%, 100% { text-shadow: none; transform: translate(0); }
    20%      { text-shadow: -3px 0 var(--pink), 3px 0 var(--cyan); transform: translate(2px, 0); }
    40%      { text-shadow:  3px 0 var(--pink), -3px 0 var(--cyan); transform: translate(-2px, 0); }
    60%      { text-shadow: -2px 0 var(--gold), 2px 0 var(--pink); transform: translate(0, 2px); }
    80%      { text-shadow:  2px 0 var(--gold), -2px 0 var(--pink); transform: translate(0, -2px); }
}

.crisis-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.85rem;
    line-height: 1.25;
    letter-spacing: -0.02em;
}
.crisis-lead {
    color: var(--text-mute);
    font-size: 1.02rem;
    line-height: 1.7;
}

/* ── OPTION BUTTONS — visible lift on hover, glow ── */
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
    box-shadow: 0 4px 16px -8px rgba(0, 0, 0, 0.3) !important;
    letter-spacing: -0.005em !important;
    transition: border-color 0.25s ease,
                background 0.25s ease,
                transform 0.25s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.25s ease !important;
}
.stButton button:hover {
    border-color: var(--gold) !important;
    background: rgba(255, 213, 107, 0.08) !important;
    transform: translateY(-4px) scale(1.01) !important;
    box-shadow: 0 14px 36px -10px rgba(255, 213, 107, 0.45) !important;
}
.stButton button:active {
    transform: translateY(-1px) scale(1) !important;
    transition-duration: 0.08s !important;
}

/* ── PRIMARY BUTTON ─ gradient, big, centered ── */
.primary-action .stButton button {
    background: linear-gradient(135deg, var(--gold) 0%, var(--pink) 60%, var(--coral) 100%) !important;
    color: #14152a !important;
    border-color: transparent !important;
    text-align: center !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    letter-spacing: 0.02em !important;
    background-size: 200% 200% !important;
    animation: pulse-primary 4s ease-in-out infinite !important;
}
@keyframes pulse-primary {
    0%, 100% { background-position: 0% 50%; }
    50%      { background-position: 100% 50%; }
}
.primary-action .stButton button:hover {
    transform: translateY(-4px) scale(1.02) !important;
    box-shadow: 0 18px 44px -12px rgba(255, 107, 199, 0.6) !important;
}

/* ── OUTCOME ─ green accent, slides in ── */
.outcome {
    background: var(--surface);
    border: 1px solid rgba(94, 226, 156, 0.4);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin: 1rem 0;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    box-shadow:
        0 0 0 1px rgba(94, 226, 156, 0.1) inset,
        0 20px 50px -20px rgba(94, 226, 156, 0.2);
    animation: rise 0.6s cubic-bezier(0.34, 1.4, 0.5, 1);
}
.outcome-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--green);
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    font-weight: 700;
}
.outcome-choice {
    color: var(--text-mute);
    font-size: 0.94rem;
    margin-bottom: 0.9rem;
    font-style: italic;
    line-height: 1.55;
    padding-left: 1rem;
    border-left: 3px solid var(--border-hi);
}
.outcome-body {
    color: var(--text);
    font-size: 1.05rem;
    line-height: 1.75;
    margin-bottom: 1.1rem;
}
.outcome-hp {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
    padding: 7px 14px;
    border-radius: 7px;
    letter-spacing: 0.03em;
}
.outcome-hp.bad { color: var(--danger); background: var(--danger-soft); border: 1px solid rgba(255, 102, 128, 0.4); }
.outcome-hp.ok  { color: var(--green);  background: rgba(94, 226, 156, 0.15); border: 1px solid rgba(94, 226, 156, 0.4); }

/* ── BANNERS (victory / death) ──────────────────────────────── */
.banner {
    border-radius: 18px;
    padding: 2.4rem 1.8rem;
    text-align: center;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    animation: rise 0.8s cubic-bezier(0.34, 1.4, 0.5, 1);
    position: relative;
}
.banner.alive {
    border: 1.5px solid rgba(94, 226, 156, 0.5);
    background: linear-gradient(160deg,
        rgba(94, 226, 156, 0.18) 0%,
        rgba(107, 223, 255, 0.1) 50%,
        var(--surface) 100%);
}
.banner.dead {
    border: 1.5px solid rgba(255, 102, 128, 0.45);
    background: linear-gradient(160deg,
        rgba(255, 102, 128, 0.18) 0%,
        rgba(255, 107, 199, 0.1) 60%,
        var(--surface) 100%);
    animation: rise 0.8s cubic-bezier(0.34, 1.4, 0.5, 1), drift 5s ease-in-out infinite;
}
@keyframes drift {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-5px); }
}
.banner .glyph {
    font-size: 3.2rem;
    margin-bottom: 0.5rem;
    line-height: 1;
}
.banner .name-line {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--gold);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    font-weight: 700;
}
.banner .title {
    font-size: 1.85rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.6rem;
    letter-spacing: -0.025em;
    line-height: 1.15;
}
.banner .subtitle {
    color: var(--text-mute);
    font-size: 1rem;
    line-height: 1.65;
    max-width: 500px;
    margin: 0 auto;
}

/* ── STAT TILES ────────────────────────────────────────────── */
.stat {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
    text-align: center;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    transition: border-color 0.25s ease, transform 0.25s ease;
    animation: rise 0.5s cubic-bezier(0.34, 1.4, 0.5, 1) backwards;
}
.stat:hover { border-color: var(--border-hi); transform: translateY(-4px); }
.stat:nth-of-type(1) { animation-delay: 0.05s; }
.stat:nth-of-type(2) { animation-delay: 0.12s; }
.stat:nth-of-type(3) { animation-delay: 0.19s; }
.stat .stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-mute);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    font-weight: 600;
}
.stat .stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.02em;
}
.stat .stat-value.small { font-size: 1.05rem; line-height: 1.3; }

/* ── CONFETTI ─ more pieces, more colors, more visible ── */
.confetti-container {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 999;
    overflow: hidden;
}
.confetti {
    position: absolute;
    top: -30px;
    width: 10px;
    height: 16px;
    opacity: 0.95;
    border-radius: 2px;
    animation: confetti-fall 5s linear forwards;
}
@keyframes confetti-fall {
    0%   { transform: translateY(0)     rotate(0deg);    opacity: 1; }
    100% { transform: translateY(110vh) rotate(900deg);  opacity: 0; }
}

/* ── INPUTS ──────────────────────────────────────────────── */
.stTextInput input {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    padding: 0.8rem 1rem !important;
    backdrop-filter: blur(14px);
    transition: border-color 0.25s ease, box-shadow 0.25s ease, background 0.25s ease !important;
}
.stTextInput input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 5px rgba(255, 213, 107, 0.15) !important;
    outline: none !important;
}
.stTextInput input::placeholder { color: var(--text-dim) !important; }
.stTextInput label {
    color: var(--text-mute) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}

/* ── DATAFRAME ──────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    backdrop-filter: blur(20px);
    transition: border-color 0.25s ease;
}
[data-testid="stDataFrame"]:hover { border-color: var(--border-hi); }

/* ── MISC ─────────────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 2rem 0 !important; }
#MainMenu, footer, header { visibility: hidden; }

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
"""


# ═══════════════════════════════════════════════════════════════════
# THE CRISES — 15, all rewritten, jokes wrapped around real data quality
# ═══════════════════════════════════════════════════════════════════
# Each crisis demonstrates a real data quality issue, told as a joke:
#   1.  Missing mandatory field   (the NULL wine)
#   2.  Range / type validation   (the four-dollar bottle)
#   3.  SQL injection / sanitize  (Bobby Tables)
#   4.  Localization / encoding   (the Klingon catalog)
#   5.  Single-language fields    (the polyglot bottle)
#   6.  False success messages    (silent save failure)
#   7.  Free text in numeric      (the honest supplier)
#   8.  Brand normalization       (47 variants)
#   9.  CSV delimiter handling    (the helpful comma)
#  10.  Asset / CDN validation    (bleach image on wine)
#  11.  Translation quality       (aggressive ending)
#  12.  Type vs semantic validation (MMXXI vintage)
#  13.  Workflow ownership        (the boomerang)
#  14.  Asset content matching    (the cat in the bow tie)
#  15.  Demand / inventory sync   (the viral moment)
# ═══════════════════════════════════════════════════════════════════
CRISIS_POOL = [
    {
        "title": "The Wine That Doesn't Exist",
        "tag":   "MISSING DATA",
        "lead":  "A wine has just appeared in the catalog with the product name 'NULL'. It is selling. The reviews are five stars. Most of them say 'Best NULL I've ever had.' One says 'tastes like absence.'",
        "options": [
            {"text": "Delete the NULL product",                                  "hp": -8,  "outcome": "Done. Customer support gets emails from people demanding the NULL back. They miss it. They have written poetry about it."},
            {"text": "Rename it to 'Mystery Wine' and double the price",         "hp": -3,  "outcome": "Sold out in fifteen minutes. You have invented a category. People are asking for a follow-up. There is now a roadmap item called 'Mystery Wine Phase Two'."},
            {"text": "Add a NOT NULL check to the validator going forward",       "hp": -2,  "outcome": "Boring. Effective. Three weeks later someone submits a product named 'undefined'. The validator accepts it. The validator was very specific."},
            {"text": "Leave it. It's thriving",                                   "hp": -25, "outcome": "It became the bestseller. Then someone wrote an article. The article asks how this is happening. You do not have a satisfying answer."},
        ],
    },
    {
        "title": "The Four-Dollar Bottle",
        "tag":   "PRICE INVALID",
        "lead":  "A bottle that should cost four hundred dollars is listed for four. The cart counter is climbing. It is climbing faster than the system can update. Three thousand people have just discovered fine wine.",
        "options": [
            {"text": "Hot-fix the price and purge the cache",                    "hp": -5,  "outcome": "Fixed in ninety seconds. Eight hundred bottles already shipped. The follow-up emails are very polite. The follow-up to those emails are less polite."},
            {"text": "Roll back this morning's deploy",                          "hp": -22, "outcome": "Price is correct. So is everything else from yesterday. Today's launches no longer exist. Tomorrow they will exist again. Nobody is excited about this."},
            {"text": "Honor the sales, fix forward",                              "hp": -3,  "outcome": "Small loss, large amount of trust earned. Nobody will remember this in your performance review. Trust does not show up in spreadsheets."},
            {"text": "Call it a flash sale",                                     "hp": -45, "outcome": "It worked for eleven thrilling minutes. The next two hours were not thrilling. The two hours after that involved finance, twice."},
        ],
    },
    {
        "title": "Little Bobby Tables Strikes Again",
        "tag":   "SECURITY",
        "lead":  "A new supplier's product description contains a SQL injection, an XSS payload, and what appears to be Morse code. Their preferred contact method is listed as 'carrier pigeon (trained)'.",
        "options": [
            {"text": "Sanitize, strip, escape, publish",                          "hp": -2,  "outcome": "Handled. You add the supplier to a personal watchlist that exists in a spreadsheet only you have. The spreadsheet has filters. You are proud of the filters."},
            {"text": "Reject the entire feed",                                    "hp": -12, "outcome": "Their eight thousand other products are also rejected. Someone is going to ask why. The answer is technical and accurate and unhelpful."},
            {"text": "Decode the Morse code first",                              "hp": -3,  "outcome": "It says: 'fix your validator'. A strange respect blooms in you. You will not act on it. You will think about it tonight."},
            {"text": "Forward it to the security team",                          "hp": -18, "outcome": "Ticket opened. The priority is 'below lunch'. You consider lunch. Lunch is over. Lunch was hours ago."},
        ],
    },
    {
        "title": "The Klingon Catalog",
        "tag":   "ENCODING",
        "lead":  "Every product description in tonight's feed arrived in tlhIngan Hol. The supplier insists this is per their reading of the contract. The contract is sixty pages. The relevant clause is somewhere between page seventeen and page fifty-eight.",
        "options": [
            {"text": "Auto-translate via AI",                                     "hp": -5,  "outcome": "Mostly works. Two gins are now described as 'honourable battle vessels'. The vodka is described as a poem. The poem is, honestly, not bad."},
            {"text": "Reject the feed politely",                                 "hp": -15, "outcome": "Reply received eleven days later. It is also in tlhIngan Hol. It is signed. It appears to be a longer reply than the original."},
            {"text": "Hold everything and pause tonight's catalog publish",       "hp": -22, "outcome": "Tomorrow's homepage is thin. People notice. They have always noticed. They will mention it neutrally, in a way that is not neutral."},
            {"text": "Publish it as a 'limited cultural experience'",            "hp": -32, "outcome": "Twelve customers loved it. Their feedback was extensive. You are now in charge of the cultural experience programme. There is no programme. There is now you."},
        ],
    },
    {
        "title": "The Polyglot Bottle",
        "tag":   "LOCALIZATION",
        "lead":  "A single gin's name field contains its name in seven languages, comma-separated. One of them is not a gin. It is a recipe for soup. The soup is, technically, branded.",
        "options": [
            {"text": "Split into seven properly-localized records",               "hp": -7,  "outcome": "Done correctly. One of the localized records is just the soup recipe. You delete the soup. The next morning, the soup is back. You don't know who is doing this."},
            {"text": "Keep the first language, drop the rest",                    "hp": -3,  "outcome": "Clean. Customers in six markets complain politely. You add it to the backlog. The backlog is, technically, also seven languages long."},
            {"text": "Forward to the localization team",                         "hp": -14, "outcome": "They scheduled a kick-off. The kick-off is in November. It is May."},
            {"text": "Publish it as 'an international tasting experience'",      "hp": -22, "outcome": "Seventy percent of customers in one specific market loved it. The market is the one that speaks the soup language. The soup is now a top product."},
        ],
    },
    {
        "title": "Saved Successfully (Citation Needed)",
        "tag":   "PHANTOM WRITES",
        "lead":  "The platform says 'Saved successfully' every time you click save. Nothing is actually saving. The success messages are confident. The data is not where you put it. You have been doing this for an hour. You are only now noticing.",
        "options": [
            {"text": "Bypass the interface and use the API directly",             "hp": -3,  "outcome": "Worked. You become the team's accidental expert on something nobody else uses. The expertise is yours forever. Forever is a long time."},
            {"text": "Restart everything and hope",                              "hp": -14, "outcome": "Two other services also restarted. They were not having problems. They are now."},
            {"text": "Open a critical support ticket",                           "hp": -20, "outcome": "Acknowledged. Estimated response: seven business days. The deadline is in six hours. Seven business days does not adjust."},
            {"text": "Wait, it usually fixes itself",                            "hp": -30, "outcome": "It did fix itself. It fixed itself wrong. Six hours later, somebody noticed. The wrongness had spread."},
        ],
    },
    {
        "title": "The Honest Supplier",
        "tag":   "INVALID TYPE",
        "lead":  "A new supplier feed has filled the ABV field with 'depends on the day'. The notes field says 'sometimes more, sometimes less'. The price field says 'we'll figure it out'. Their cover letter was four sentences. All four were apologies.",
        "options": [
            {"text": "Add type validation, reject malformed entries",             "hp": -3,  "outcome": "The validator caught all of it. Next week they send another feed. The new feed has numbers in it. The numbers are 'pretty close' and 'roughly accurate'."},
            {"text": "Manually correct what you can guess",                       "hp": -10, "outcome": "You guessed nine. You got six right. Three are dangerously wrong. One product is now legally a different category."},
            {"text": "Send the feed back with a stern note",                      "hp": -16, "outcome": "Reply received: 'fair enough'. The next feed is identical. The cover letter is shorter. The shorter cover letter is more confident."},
            {"text": "Publish it anyway, they're a small supplier",              "hp": -38, "outcome": "Customer service got creative emails. One person ordered 'the day-depends one'. The order went through. The order is being processed."},
        ],
    },
    {
        "title": "Brand Spelled Forty-Seven Ways",
        "tag":   "NORMALIZATION",
        "lead":  "A brand audit returns forty-seven different spellings of the same brand name in the active catalog. One is in Comic Sans. You did not think the catalog supported Comic Sans. The catalog has been hiding this.",
        "options": [
            {"text": "Run the brand normalization workflow",                      "hp": -4,  "outcome": "Cleaned. The brand sends a polite email correcting your canonical spelling. You explain. They correct you back. You stop responding. You do not stop thinking about it."},
            {"text": "Manually fix all forty-seven by hand",                      "hp": -25, "outcome": "Ninety minutes. You have learned nothing transferable. You feel a quiet peace that surprises you."},
            {"text": "Auto-merge via fuzzy matching",                            "hp": -8,  "outcome": "Forty-six correct. One merged with a different brand entirely. That brand is now gin. The market accepts this. The market is forgiving."},
            {"text": "Leave it, customers don't search exactly",                  "hp": -20, "outcome": "Customers do search exactly. Conversion drops twelve percent. The drop is small enough to blame on anything. It is not anything else."},
        ],
    },
    {
        "title": "The Helpful Comma",
        "tag":   "DELIMITER",
        "lead":  "A description read 'rich, smooth, oaky'. The CSV parser saw three products: 'rich', 'smooth', 'oaky'. Each is now its own SKU. Each is selling. Each has its own reviews section. The reviews are detailed.",
        "options": [
            {"text": "Switch the parser to tab-separated",                       "hp": -6,  "outcome": "Solved this case. Created a new one. Three suppliers use tabs in their product names. You discover this individually, painfully, on Tuesday."},
            {"text": "Merge the three back into one product",                    "hp": -4,  "outcome": "Customer reviews are preserved. The reviews contradict each other in interesting ways. 'rich' has different fans than 'smooth' has."},
            {"text": "Keep them. Three is more than one",                        "hp": -28, "outcome": "Inventory tracks them separately. Three SKUs all draw from the same bottle. The same bottle. The system thinks you have three. You have one."},
            {"text": "Properly quote the description and reimport",              "hp": -3,  "outcome": "Done. The next supplier sends descriptions wrapped in single quotes. Then the supplier after that uses smart quotes. The quotes are very smart."},
        ],
    },
    {
        "title": "The Cleaning Aisle Cabernet",
        "tag":   "ASSET DRIFT",
        "lead":  "A premium wine is showing the product image of a household cleaning chemical. The chemical is bleach. The CDN insists the image has always been like this. A customer has written a column. The column is well-written.",
        "options": [
            {"text": "Purge the CDN cache for that product",                      "hp": -2,  "outcome": "Fixed in six seconds. A few people saw it. They told their friends. Their friends made memes. The memes are pretty good actually."},
            {"text": "Wait twenty-four hours for the cache to expire",          "hp": -22, "outcome": "Twenty-four hours is enough time for someone to write a thing. They write a thing. The thing has photographs."},
            {"text": "Reupload the image with a fresh filename",                 "hp": -6,  "outcome": "Worked. There are now two copies of the image in storage. The old one is cached somewhere. It will come back. It always comes back."},
            {"text": "Post that it's a brave new pairing",                       "hp": -35, "outcome": "Some loved the joke. The wine brand did not. The wine brand has lawyers. The lawyers have schedules."},
        ],
    },
    {
        "title": "The Confident Translation",
        "tag":   "TRANSLATION",
        "lead":  "Auto-translation has been doing its job. Maybe too well. A tasting note 'crisp finish' has been translated to a key market as 'aggressive ending'. Sales there have collapsed in some categories. They have doubled in one specific category.",
        "options": [
            {"text": "Disable auto-translation entirely",                         "hp": -8,  "outcome": "Sensible. Slow. Expensive. The market recovers slowly, the way a person recovers from food poisoning."},
            {"text": "Build a glossary for tasting notes",                       "hp": -6,  "outcome": "Took an afternoon. Saves countless incidents. Nobody else will ever know about the glossary. The glossary is the only documentation. It lives in a spreadsheet."},
            {"text": "Issue a public correction",                                "hp": -13, "outcome": "Correction issued. It did some good. The reviews mentioning 'aggressive ending' remain searchable for the rest of time."},
            {"text": "Lean in. Aggressive Ending is the new brand voice",        "hp": -28, "outcome": "Surprising number of supportive comments. Less surprising number of unhappy emails. Three of the unhappy emails are from the wine producer."},
        ],
    },
    {
        "title": "MMXXI",
        "tag":   "TYPE VS MEANING",
        "lead":  "A wine vintage field contains the string 'MMXXI'. Investigation reveals it has been happening for six months. Roman numerals pass DQ because vintage is, somehow, free text. You suspect it has always been free text. You suspect this with a slow, settling dread.",
        "options": [
            {"text": "Build a Roman numeral parser into the validator",          "hp": -10, "outcome": "Took two hours. Next week, somebody submits a vintage in Mayan dates. You saw this coming. You did nothing about it. You are doing nothing about it now."},
            {"text": "Convert this batch, set stricter rules going forward",     "hp": -4,  "outcome": "Pragmatic. Documented. Sustainable. You feel like an engineer for the rest of the afternoon."},
            {"text": "Reject the records, bounce back to supplier",              "hp": -13, "outcome": "Supplier appeals via committee. The committee meets fortnightly. By the time it resolves, the wine is, technically, older."},
            {"text": "Document the field as 'intentionally permissive'",          "hp": -22, "outcome": "Six months later, a vintage comes through as 'before time itself'. You read it. You sit. You consider water."},
        ],
    },
    {
        "title": "The Boomerang",
        "tag":   "WORKFLOW CONFLICT",
        "lead":  "You fixed a product name yesterday. It changed back overnight. You fixed it again this morning. It changed back at lunch. You are now in a six-hour standoff with an automated job nobody can find. You are losing.",
        "options": [
            {"text": "Find and disable the job",                                  "hp": -7,  "outcome": "Found after an hour. The job is from 2019. Three other workflows depend on it. One of them is critical. The critical one cannot explain what it does."},
            {"text": "Override at a deeper layer the job can't touch",            "hp": -4,  "outcome": "Worked. The job now runs and quietly fails. The job will run and quietly fail for the next nine years. You will not investigate."},
            {"text": "Match the format the job expects",                          "hp": -10, "outcome": "The job is happy. The product name is correct. The name is also legally questionable. Legal will mention this eventually."},
            {"text": "Accept the change. It clearly wants something",            "hp": -25, "outcome": "The job got bolder. It started changing other products. Some of them are now also named what it likes. What it likes is hard to describe."},
        ],
    },
    {
        "title": "The Cat in the Bow Tie",
        "tag":   "ASSET CONTENT",
        "lead":  "A premium champagne's product image is a stock photo of a cat. The cat is wearing a small bow tie. The reviews mention the cat. The reviews do not mention the champagne. The cat has fans.",
        "options": [
            {"text": "Replace the image immediately",                             "hp": -3,  "outcome": "Done. The cat is gone. Three customers email asking where the cat went. One offers to buy the cat."},
            {"text": "Run an image-content audit across the catalog",             "hp": -11, "outcome": "Found four more animals. One is a goose. The goose is somehow on a single malt page. Nobody is taking responsibility for the goose."},
            {"text": "Keep the cat. It clearly works",                            "hp": -8,  "outcome": "The cat outsells the previous image. Marketing wants the cat in more places. The cat is now the campaign. You wonder if you have made a mistake."},
            {"text": "Add image validation to the ingest pipeline",               "hp": -5,  "outcome": "Built it that afternoon. Now scanning historical assets too. Within an hour you find seventeen more animals. There is a chart."},
        ],
    },
    {
        "title": "The Eight Million Views",
        "tag":   "DEMAND SYNC",
        "lead":  "A short video of someone using three of your products in a cocktail has done eight million views. All three are currently out of stock. Site traffic is two hundred times normal. The site is, somehow, still up.",
        "options": [
            {"text": "Hide the out-of-stock products immediately",                "hp": -3,  "outcome": "Smart. Conversion stays clean. The video creator notices their products vanished. They post about it. The new post does more views than the original."},
            {"text": "Show 'back soon' badges, capture wishlists",                "hp": -2,  "outcome": "Eight thousand wishlist additions. You will be asked about this moment in meetings for the next year. You will smile in those meetings."},
            {"text": "Mark all three as 'limited drops'",                         "hp": -6,  "outcome": "Sold four times the volume when restocked. You will be invited to talk about it at an off-site. The off-site has compulsory ice-breakers."},
            {"text": "Leave it, customers know what out-of-stock means",          "hp": -20, "outcome": "They did not. They wrote angry reviews. Several included photographs of empty shelves. One is from a person who is now your most engaged customer."},
        ],
    },
]


# ───────────────────────────────────────────────────────────────────
# THE GLITCH — one in twelve runs replaces a crisis with this
# ───────────────────────────────────────────────────────────────────
META_CRISIS = {
    "title": "—",
    "tag":   "?",
    "lead":  "The crisis card is empty. There is no description. The system appears to be waiting for you.",
    "options": [
        {"text": "Pretend nothing happened",                                       "hp":  0,  "outcome": "Wise. The shift continues. The system continues. You will think about this tonight."},
        {"text": "Make direct eye contact with the screen",                        "hp": -4,  "outcome": "The screen wins. The next crisis will be normal. You will not be normal."},
        {"text": "Refresh the browser and hope",                                   "hp": -6,  "outcome": "You lost a little progress. You gained a little peace. The peace is small but real."},
        {"text": "Get up and walk away for a moment",                              "hp": +8,  "outcome": "You needed that. Welcome back. The catalog missed you. The chair missed you too."},
    ],
}


# ═══════════════════════════════════════════════════════════════════
# DATA LAYER — Google Sheets leaderboard
# ═══════════════════════════════════════════════════════════════════
def get_db():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        key_data = st.secrets["gcp_service_account"]
        if isinstance(key_data, str):
            try:
                key_data = json.loads(key_data)
            except json.JSONDecodeError as e:
                raise ValueError(
                    "Leaderboard service account secret is a string but not valid JSON. "
                    "Check st.secrets configuration."
                ) from e
        if isinstance(key_data, Mapping) and not isinstance(key_data, dict):
            key_data = dict(key_data)
        if not isinstance(key_data, dict):
            raise ValueError("Leaderboard service account secret must be a JSON object/dict.")

        missing = [k for k in ("type", "project_id", "private_key_id", "private_key", "client_email", "client_id") if k not in key_data]
        if missing:
            raise ValueError(f"Leaderboard service account JSON is missing required keys: {missing}")

        private_key = key_data["private_key"]
        if not isinstance(private_key, str):
            raise ValueError("Leaderboard service account private_key must be a string.")
        if "-----BEGIN PRIVATE KEY-----" not in private_key or "-----END PRIVATE KEY-----" not in private_key:
            raise ValueError(
                "Leaderboard service account private_key does not contain a valid PEM block. "
                "Ensure the key is a full PEM string with BEGIN/END markers."
            )
        if "\\n" in private_key and "\n" not in private_key:
            key_data["private_key"] = private_key.replace("\\n", "\n")

        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_data, scope)
        db = gspread.authorize(creds).open_by_key(SPREADSHEET_KEY)
        st.session_state["leaderboard_source"] = f"{db.title} ({db.id})"
        return db
    except Exception as e:
        st.session_state["leaderboard_error"] = f"Leaderboard connection failed: {e}"
        raise


def get_scores_worksheet(db):
    try:
        return db.worksheet(WORKSHEET_NAME)
    except Exception as e:
        sheet_names = [ws.title for ws in db.worksheets()]
        st.session_state["leaderboard_error"] = (
            f'Leaderboard worksheet "{WORKSHEET_NAME}" was not found. '
            f'Available worksheet tabs: {sheet_names}. '
            'Create or rename a tab to Scores, then refresh.'
        )
        return None


def save_score(name: str, score: int, title: str) -> tuple[bool, Optional[str]]:
    try:
        try:
            db = get_db()
        except Exception as e:
            return False, str(e)
        worksheet = get_scores_worksheet(db)
        if worksheet is None:
            return False, st.session_state.get("leaderboard_error")
        worksheet.append_row([
            datetime.now().isoformat(timespec="seconds"), name, score, title
        ])
        return True, None
    except Exception as e:
        st.session_state["leaderboard_error"] = f"Leaderboard save failed: {e}"
        return False, str(e)


def fetch_leaderboard() -> pd.DataFrame:
    try:
        try:
            db = get_db()
        except Exception:
            return pd.DataFrame()
        worksheet = get_scores_worksheet(db)
        if worksheet is None:
            return pd.DataFrame()
        rows = worksheet.get_all_values()
        if len(rows) == 0:
            st.session_state["leaderboard_error"] = (
                f"Leaderboard worksheet is empty. Source: {st.session_state.get('leaderboard_source', 'unknown')}"
            )
            return pd.DataFrame()
        if len(rows) == 1:
            headers = [h.strip() for h in rows[0]]
            st.session_state["leaderboard_error"] = (
                f"Leaderboard worksheet has only a header row. Found headers: {headers}. "
                f"Source: {st.session_state.get('leaderboard_source', 'unknown')}"
            )
            return pd.DataFrame()
        headers = [h.strip() for h in rows[0]]
        df = pd.DataFrame(rows[1:], columns=headers)
        # tolerate the old schema names too
        df = df.rename(columns={"Architect": "Name", "CI": "Score", "Phase": "Title"})
        if "Score" not in df.columns or "Name" not in df.columns:
            st.session_state["leaderboard_error"] = (
                f"Leaderboard worksheet is missing required columns. Found: {list(df.columns)}. "
                f"Source: {st.session_state.get('leaderboard_source', 'unknown')}"
            )
            return pd.DataFrame()
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0).astype(int)
        out = (df.groupby("Name", as_index=False)
                 .agg({"Score": "max", "Title": "first"})
                 .sort_values("Score", ascending=False).head(12)
                 .reset_index(drop=True))
        out.index = out.index + 1
        out.index.name = "#"
        st.session_state["leaderboard_error"] = None
        return out
    except Exception as e:
        st.session_state["leaderboard_error"] = f"Leaderboard fetch failed: {e}"
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════
# GAME STATE & LOGIC
# ═══════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "stage":       "intro",
        "name":        "",
        "health":      START_HEALTH,
        "round_pool":  [],
        "round_idx":   0,
        "last_choice": None,
        "started_at":  None,
        "survived":    False,
        "saved":       False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def goto(stage: str):
    st.session_state.stage = stage
    st.rerun()


def start_run(name: str):
    # draw 8 random crises from the pool; 1-in-12 chance one is replaced
    # with the hidden meta crisis (sentinel value -1)
    pool = random.sample(range(len(CRISIS_POOL)), ROUNDS)
    if random.random() < (1 / 12):
        pool[random.randint(0, ROUNDS - 1)] = -1
    st.session_state.update({
        "name":        name,
        "health":      START_HEALTH,
        "round_pool":  pool,
        "round_idx":   0,
        "last_choice": None,
        "started_at":  time.time(),
        "survived":    False,
        "saved":       False,
    })
    goto("crisis")


def current_crisis() -> dict:
    idx = st.session_state.round_pool[st.session_state.round_idx]
    return META_CRISIS if idx == -1 else CRISIS_POOL[idx]


def rank_for(health: int, survived: bool) -> str:
    if not survived:
        return "Did not survive"
    if health >= 90: return "Catalog Whisperer"
    if health >= 75: return "Made it look easy"
    if health >= 55: return "Capable on a bad day"
    if health >= 35: return "Survived the shift"
    if health >= 15: return "Barely"
    return "Technically alive"


def death_message() -> tuple[str, str]:
    options = [
        ("You have been moved to special projects.",
         "There are no special projects. There is a desk. The desk is near the elevators."),
        ("The catalog has new leadership.",
         "It is not you. There was no announcement. There was a quiet swap and a series of permission changes you cannot see."),
        ("Your access has been reviewed.",
         "The review is complete. You are not told the result. You are told the review is complete. The distinction is doing a lot of work."),
        ("Your callsign has been retired.",
         "Quietly. A plaque exists somewhere. It is engraved correctly. It is in a hallway that nobody walks down."),
    ]
    return random.choice(options)


# ═══════════════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════════════
def health_gradient(health: int) -> str:
    """Cycle from green-cyan to gold to red as health drops."""
    if health >= 65:
        return "linear-gradient(90deg, #5ee29c, #6bdfff)"
    if health >= 35:
        return "linear-gradient(90deg, #ffd56b, #ff8c5a)"
    return "linear-gradient(90deg, #ff6680, #ff6bc7)"


def health_color_word(health: int) -> str:
    if health >= 65: return "var(--green)"
    if health >= 35: return "var(--gold)"
    return "var(--danger)"


def render_hud():
    health = max(0, st.session_state.health)
    round_num = st.session_state.round_idx + 1
    pct = max(0, min(100, health))
    fill = health_gradient(health)
    low_class = " low" if health < 30 else ""

    st.markdown(
        f'<div class="hud">'
        f'  <div class="hud-cell">Crisis<span class="v">{round_num} of {ROUNDS}</span></div>'
        f'  <div class="hud-center">'
        f'    <span class="hud-label">Health</span>'
        f'    <div class="bar-track"><div class="bar-fill{low_class}" style="width:{pct}%; background:{fill};"></div></div>'
        f'    <span class="bar-num">{health} / 100</span>'
        f'  </div>'
        f'  <div class="hud-cell">Player<span class="v">{st.session_state.name or "—"}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_confetti(pieces: int = 60):
    """Pure-CSS confetti — 60 colorful pieces with randomized everything."""
    colors = ["#ffd56b", "#ff6bc7", "#6bdfff", "#5ee29c", "#ff8c5a", "#fafaff"]
    parts = ['<div class="confetti-container">']
    for _ in range(pieces):
        left   = random.uniform(0, 100)
        delay  = random.uniform(0, 2.5)
        dur    = random.uniform(3.5, 6.5)
        rot    = random.uniform(-180, 180)
        color  = random.choice(colors)
        width  = random.choice([8, 10, 12])
        height = random.choice([12, 16, 20])
        parts.append(
            f'<div class="confetti" style="'
            f'left:{left}vw; background:{color}; '
            f'width:{width}px; height:{height}px; '
            f'animation-delay:{delay}s; animation-duration:{dur}s; '
            f'transform:rotate({rot}deg);"></div>'
        )
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════
def screen_intro():
    st.markdown('<div class="eyebrow">A small game about PIM data quality</div>', unsafe_allow_html=True)
    st.markdown('<h1><span class="kinetic">Don\'t let the catalog die.</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: var(--text-mute); font-size: 1.05rem; line-height: 1.7; margin-top: 0.3rem;">'
        'Eight things go wrong. You handle each one. The cost is shown before you pick. '
        'Survive all eight to get on the leaderboard.'
        '</p>',
        unsafe_allow_html=True,
    )

    name = st.text_input(
        "Your name on the leaderboard",
        placeholder="anything you'd like to see",
        max_chars=32,
    )

    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Start"):
        if name.strip():
            start_run(name.strip())
        else:
            st.warning("Please enter a name.")
    st.markdown('</div>', unsafe_allow_html=True)

    lb = fetch_leaderboard()
    error = st.session_state.get("leaderboard_error")
    if error:
        st.error(error)
    elif not lb.empty:
        st.markdown('<div class="card-label" style="margin-top: 2.5rem;">Leaderboard</div>', unsafe_allow_html=True)
        st.dataframe(lb, use_container_width=True)
    else:
        st.info("Leaderboard is empty. Play once to add a score.")


def screen_crisis():
    render_hud()
    c = current_crisis()

    st.markdown(
        f'<div class="crisis">'
        f'<div class="crisis-tag">{c["tag"]}</div>'
        f'<div class="crisis-title">{c["title"]}</div>'
        f'<div class="crisis-lead">{c["lead"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # render each option as a clickable button
    for i, opt in enumerate(c["options"]):
        hp_label = f"{opt['hp']:+d}" if opt["hp"] != 0 else "0"
        label = f"{opt['text']}   ({hp_label})"
        if st.button(label, key=f"option_{st.session_state.round_idx}_{i}"):
            st.session_state.last_choice = {
                "crisis":  c["title"],
                "text":    opt["text"],
                "hp":      opt["hp"],
                "outcome": opt["outcome"],
            }
            st.session_state.health += opt["hp"]
            goto("outcome")


def screen_outcome():
    """
    FIXED LOGIC: round_idx is ONLY advanced when the user clicks "Next".
    Previously it was advancing on every render of this screen, which
    caused the same outcome to keep showing and the game to end early.
    """
    c = st.session_state.last_choice
    if c is None:
        # safety net — shouldn't happen, but if it does, recover gracefully
        goto("crisis")
        return

    render_hud()

    hp_cls = "bad" if c["hp"] < 0 else "ok"
    hp_text = f"{c['hp']:+d}" if c["hp"] != 0 else "0"

    st.markdown(
        f'<div class="outcome">'
        f'<div class="outcome-label">What happened</div>'
        f'<div class="outcome-choice">You chose: {c["text"]}</div>'
        f'<div class="outcome-body">{c["outcome"]}</div>'
        f'<div class="outcome-hp {hp_cls}">{hp_text} health</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # decide what to show next, WITHOUT mutating round_idx yet
    is_dead = st.session_state.health <= 0
    is_last_round = st.session_state.round_idx >= ROUNDS - 1

    st.markdown('<div class="primary-action">', unsafe_allow_html=True)

    if is_dead:
        if st.button("See how this ended"):
            st.session_state.survived = False
            goto("end")
    elif is_last_round:
        if st.button("See the final result"):
            st.session_state.survived = True
            goto("end")
    else:
        next_round = st.session_state.round_idx + 2  # human-numbered next
        if st.button(f"Next crisis ({next_round} of {ROUNDS})"):
            # advance round_idx ONLY when actually moving on
            st.session_state.round_idx += 1
            st.session_state.last_choice = None
            goto("crisis")

    st.markdown('</div>', unsafe_allow_html=True)


def screen_end():
    health = max(0, st.session_state.health)
    survived = st.session_state.survived
    title = rank_for(health, survived)
    elapsed = int(time.time() - st.session_state.started_at) if st.session_state.started_at else 0
    name = st.session_state.name or "anonymous"

    if survived:
        render_confetti(60)
        st.markdown(
            f'<div class="banner alive">'
            f'<div class="glyph">🏆</div>'
            f'<div class="name-line">{name}</div>'
            f'<div class="title">You survived the shift.</div>'
            f'<div class="subtitle">Eight crises down. The catalog is still standing.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        dt_title, dt_sub = death_message()
        st.markdown(
            f'<div class="banner dead">'
            f'<div class="glyph">💀</div>'
            f'<div class="name-line">{name}</div>'
            f'<div class="title">{dt_title}</div>'
            f'<div class="subtitle">{dt_sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # three stat tiles
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="stat">'
            f'<div class="stat-label">Final Health</div>'
            f'<div class="stat-value" style="color: {health_color_word(health)};">{health}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat">'
            f'<div class="stat-label">Rank</div>'
            f'<div class="stat-value small">{title}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat">'
            f'<div class="stat-label">Time</div>'
            f'<div class="stat-value">{elapsed // 60}m {elapsed % 60:02d}s</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # save once
    if not st.session_state.saved:
        ok, save_error = save_score(name, health, title)
        st.session_state.saved = True
        if ok:
            st.success("Score saved to the leaderboard.")
        else:
            st.error(save_error or "Failed to save score to the leaderboard.")

    # leaderboard
    st.markdown('<div class="card-label" style="margin-top: 2rem;">Leaderboard</div>', unsafe_allow_html=True)
    lb = fetch_leaderboard()
    error = st.session_state.get("leaderboard_error")
    if error:
        st.error(error)
    elif not lb.empty:
        st.dataframe(lb, use_container_width=True)
    else:
        st.info("Leaderboard is empty. Play once to add a score.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Play again"):
        kept_name = st.session_state.name
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        init_state()
        start_run(kept_name)
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════
def main():
    st.markdown(STYLE, unsafe_allow_html=True)
    init_state()

    stage = st.session_state.stage
    if   stage == "intro":   screen_intro()
    elif stage == "crisis":  screen_crisis()
    elif stage == "outcome": screen_outcome()
    elif stage == "end":     screen_end()
    else: goto("intro")


main()
