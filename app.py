"""
═══════════════════════════════════════════════════════════════════
                       P I M   S U R V I V O R
═══════════════════════════════════════════════════════════════════

A small roguelike about catalog work, written for people who have
ever been on call at 4 AM with three tabs open and a feeling.

You start with 100 Catalog Integrity. Eight things go wrong in a row.
You pick how to handle each one. The HP cost is shown. The outcome
is not. Hit zero and the shift ends in a way that will be described
to you with a certain dryness.

— Ati from PIM
  catalog therapy by way of Streamlit

Design notes for the curious:
  · Aurora background (drifting gradient blobs, heavy blur)
  · Glassmorphism cards (backdrop-filter, layered translucency)
  · Kinetic gradient on the title (color cycles forever)
  · Shimmer animation on the HP bar (the sweep)
  · Confetti is pure CSS — 40 elements with random delays
  · One in twelve crises is replaced by something you weren't expecting
  · All copy is hand-written. No filler. Every line earns its place.

If you fork this and the writing makes you laugh once, that is
already more than I was hoping for. If it makes you laugh twice,
you owe me a coffee. Use the leaderboard as your IOU.
"""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ─────────────────────────────────────────────────────────────────
# THE ONE FACT THAT DEFINES THE WHOLE GAME
# Tweak with care. Larger = easier. Smaller = cruel.
# ─────────────────────────────────────────────────────────────────
START_HP = 100
ROUNDS = 8


# ─────────────────────────────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PIM Survivor — by Ati from PIM",
    page_icon="◉",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ═══════════════════════════════════════════════════════════════════
# THE STYLE
# ═══════════════════════════════════════════════════════════════════
# Aurora UI on the back. Glassmorphism on the cards.
# Everything has a transition because everything should.
# If you change one variable here, change the related ones too,
# or the colors will fight and you will lose.
# ═══════════════════════════════════════════════════════════════════
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg:           #07070a;
    --surface:      rgba(20, 20, 26, 0.6);
    --surface-2:    rgba(28, 28, 36, 0.7);
    --border:       rgba(255, 255, 255, 0.06);
    --border-soft:  rgba(255, 255, 255, 0.10);
    --border-hi:    rgba(255, 255, 255, 0.18);
    --text:         #f4f4f6;
    --text-mute:    #a1a1aa;
    --text-dim:     #6b6b76;
    --accent:       #00e5b8;
    --accent-2:     #00c4ff;
    --accent-3:     #a855f7;
    --accent-glow:  rgba(0, 229, 184, 0.35);
    --blood:        #ff5470;
    --blood-soft:   rgba(255, 84, 112, 0.14);
    --warn:         #f59e0b;
    --warn-soft:    rgba(245, 158, 11, 0.14);
}

/* ── BASE LAYER ─────────────────────────────────────────────── */
.stApp {
    background: var(--bg);
    color: var(--text);
}

/* ── THE AURORA ─────────────────────────────────────────────────
   Three drifting gradient blobs, heavily blurred. Each moves on a
   different timeline so the composition never repeats. The whole
   thing sits in a fixed pseudo-element behind everything else. */
.stApp::before {
    content: '';
    position: fixed;
    inset: -20% -20% -20% -20%;
    background:
        radial-gradient(35% 35% at 22% 30%, rgba(0, 229, 184, 0.18) 0%, transparent 60%),
        radial-gradient(40% 40% at 80% 70%, rgba(168, 85, 247, 0.16) 0%, transparent 60%),
        radial-gradient(45% 45% at 60% 20%, rgba(0, 196, 255, 0.12) 0%, transparent 60%),
        radial-gradient(30% 30% at 30% 85%, rgba(245, 158, 11, 0.08) 0%, transparent 60%);
    filter: blur(60px);
    z-index: 0;
    pointer-events: none;
    animation: aurora-drift 22s ease-in-out infinite alternate;
    will-change: transform;
}
@keyframes aurora-drift {
    0%   { transform: translate(0, 0)        scale(1); }
    33%  { transform: translate(-3%, 2%)     scale(1.05); }
    66%  { transform: translate(2%, -3%)     scale(0.97); }
    100% { transform: translate(-1%, 1%)     scale(1.02); }
}

/* keep content above the aurora */
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
    letter-spacing: -0.035em !important;
    line-height: 1.05 !important;
    margin-bottom: 0.5rem !important;
}
h2 { font-size: 1.2rem !important; font-weight: 600 !important; }

/* ── KINETIC GRADIENT TITLE ─────────────────────────────────────
   This is the one place I let the color do the talking. Two
   accent colors and a violet, cycling forever. Subtle. Hypnotic. */
.kinetic {
    background: linear-gradient(120deg, #00e5b8 0%, #00c4ff 35%, #a855f7 65%, #00e5b8 100%);
    background-size: 300% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: kinetic-shift 9s ease-in-out infinite;
}
@keyframes kinetic-shift {
    0%, 100% { background-position: 0% 50%; }
    50%      { background-position: 100% 50%; }
}

/* ── EYEBROW / micro-label ──────────────────────────────────── */
.eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-weight: 500;
    margin-bottom: 0.6rem;
}

/* ── GLASSMORPHISM CARDS ────────────────────────────────────────
   The whole point is the backdrop-filter. It makes the aurora
   show through, faintly. If you turn off blur, the cards look
   like flat rectangles and the magic dies. */
.glass {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    padding: 1.5rem 1.7rem;
    margin: 1rem 0;
    backdrop-filter: blur(20px) saturate(140%);
    -webkit-backdrop-filter: blur(20px) saturate(140%);
    box-shadow:
        0 1px 0 rgba(255, 255, 255, 0.04) inset,
        0 16px 40px -16px rgba(0, 0, 0, 0.5);
    animation: rise 0.55s cubic-bezier(0.22, 1, 0.36, 1);
    transition: border-color 0.25s ease, transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.glass:hover { border-color: var(--border-hi); }

@keyframes rise {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}

.card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-mute);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.85rem;
    font-weight: 600;
}

/* ── HUD ────────────────────────────────────────────────────────
   The status bar that lives above every crisis. Round counter on
   the left, HP bar in the middle, name on the right. */
.hud {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 1.2rem;
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    padding: 0.85rem 1.2rem;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(20px) saturate(140%);
    -webkit-backdrop-filter: blur(20px) saturate(140%);
}
.hud-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--text-mute);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.hud-tag .v { color: var(--text); font-weight: 600; font-size: 0.88rem; margin-left: 4px; }
.hud-wrap { display: flex; align-items: center; gap: 0.75rem; }
.hud-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-mute);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    white-space: nowrap;
}

/* ── THE HP BAR ─────────────────────────────────────────────────
   Inset shadow on the track, gradient fill, animated shimmer that
   sweeps across the fill. The fill width transitions on a half-
   second curve so HP changes feel like something happened, not
   like a number got swapped. */
.hp-track {
    flex: 1;
    height: 16px;
    background: rgba(0, 0, 0, 0.5);
    border: 1px solid var(--border-soft);
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.6);
}
.hp-fill {
    height: 100%;
    border-radius: 7px;
    position: relative;
    transition: width 0.7s cubic-bezier(0.22, 1, 0.36, 1),
                background 0.5s ease,
                box-shadow 0.5s ease;
}
.hp-fill::after {
    /* the sweep — diagonal shimmer that travels across the fill */
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(110deg,
        transparent 0%,
        transparent 35%,
        rgba(255, 255, 255, 0.18) 50%,
        transparent 65%,
        transparent 100%);
    animation: shimmer 2.6s linear infinite;
}
@keyframes shimmer {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(100%);  }
}
.hp-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--text);
    min-width: 64px;
    text-align: right;
    letter-spacing: -0.01em;
}

/* ── CRISIS CARD ────────────────────────────────────────────────
   Like .glass but with a left-edge accent (red) and a slight
   3D tilt when you hover. */
.crisis {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-left: 3px solid var(--blood);
    border-radius: 14px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(20px) saturate(140%);
    -webkit-backdrop-filter: blur(20px) saturate(140%);
    box-shadow: 0 16px 40px -16px rgba(0, 0, 0, 0.5);
    animation: rise 0.55s cubic-bezier(0.22, 1, 0.36, 1);
    transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.4s ease;
    transform-style: preserve-3d;
}
.crisis:hover {
    transform: perspective(1000px) rotateX(-1deg) rotateY(0.5deg) translateY(-2px);
    box-shadow: 0 24px 60px -20px rgba(0, 0, 0, 0.6);
}

/* ── THE TAG WITH THE GLITCH ────────────────────────────────────
   On hover the tag splits into red and cyan ghosts that race past
   each other. Pure clip-path keyframes. Use sparingly: it's a
   little dramatic. */
.crisis-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--blood);
    background: var(--blood-soft);
    border: 1px solid rgba(255, 84, 112, 0.35);
    border-radius: 5px;
    padding: 3px 10px;
    margin-bottom: 0.85rem;
    letter-spacing: 0.12em;
    position: relative;
    animation: tag-pulse 2.4s ease-out infinite;
}
@keyframes tag-pulse {
    0%   { box-shadow: 0 0 0 0  rgba(255, 84, 112, 0.45); }
    70%  { box-shadow: 0 0 0 7px rgba(255, 84, 112, 0);   }
    100% { box-shadow: 0 0 0 0  rgba(255, 84, 112, 0);    }
}
.crisis:hover .crisis-tag {
    animation: tag-pulse 2.4s ease-out infinite, glitch 0.6s ease-in-out;
}
@keyframes glitch {
    0%, 100% { text-shadow: none; transform: translate(0); }
    20%      { text-shadow: -2px 0 #00e5b8, 2px 0 #ff5470; transform: translate(1px, 0); }
    40%      { text-shadow:  2px 0 #00e5b8, -2px 0 #ff5470; transform: translate(-1px, 0); }
    60%      { text-shadow: -1px 0 #00c4ff, 1px 0 #ff5470; transform: translate(0, 1px); }
    80%      { text-shadow:  1px 0 #00e5b8, -1px 0 #ff5470; transform: translate(0, -1px); }
}

.crisis-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.8rem;
    line-height: 1.25;
    letter-spacing: -0.02em;
}
.crisis-lead {
    color: var(--text-mute);
    font-size: 0.98rem;
    line-height: 1.65;
}

/* ── OPTION BUTTONS ─────────────────────────────────────────────
   These are real Streamlit buttons. Styled to look like option
   tiles. Left-aligned. Subtle border. They glow on hover. */
.stButton { width: 100%; }
.stButton button {
    width: 100% !important;
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-soft) !important;
    border-radius: 10px !important;
    text-align: left !important;
    padding: 0.95rem 1.2rem !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    line-height: 1.45 !important;
    white-space: normal !important;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: none !important;
    letter-spacing: -0.005em !important;
    transition: border-color 0.2s ease,
                background 0.2s ease,
                transform 0.18s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.2s ease !important;
}
.stButton button:hover {
    border-color: var(--accent) !important;
    background: rgba(0, 229, 184, 0.05) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px -10px var(--accent-glow) !important;
}
.stButton button:active {
    transform: translateY(0) !important;
    transition-duration: 0.06s !important;
}

/* ── PRIMARY BUTTON (start, continue, replay) ───────────────────
   When I want the button to feel like the answer, I wrap it
   in a .primary-action div and give it the accent treatment. */
.primary-action .stButton button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%) !important;
    color: #06120e !important;
    border-color: transparent !important;
    text-align: center !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em !important;
}
.primary-action .stButton button:hover {
    box-shadow: 0 12px 32px -10px var(--accent-glow) !important;
    transform: translateY(-2px) !important;
}

/* ── OUTCOME PANEL ──────────────────────────────────────────────
   Appears after a choice. Accent border. Quote-style choice line.
   The HP delta gets its own pill. */
.outcome {
    background: var(--surface);
    border: 1px solid rgba(0, 229, 184, 0.35);
    border-radius: 14px;
    padding: 1.5rem 1.7rem;
    margin: 1rem 0;
    backdrop-filter: blur(20px) saturate(140%);
    -webkit-backdrop-filter: blur(20px) saturate(140%);
    box-shadow:
        0 0 0 1px rgba(0, 229, 184, 0.08) inset,
        0 16px 40px -16px rgba(0, 229, 184, 0.15);
    animation: rise 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}
.outcome-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--accent);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
    font-weight: 600;
}
.outcome-choice {
    color: var(--text-mute);
    font-size: 0.92rem;
    margin-bottom: 0.85rem;
    font-style: italic;
    line-height: 1.5;
    padding-left: 0.85rem;
    border-left: 2px solid var(--border-hi);
}
.outcome-body {
    color: var(--text);
    font-size: 1.02rem;
    line-height: 1.7;
    margin-bottom: 1rem;
}
.outcome-hp {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    font-weight: 700;
    padding: 6px 12px;
    border-radius: 6px;
    letter-spacing: 0.02em;
}
.outcome-hp.bad { color: var(--blood); background: var(--blood-soft); border: 1px solid rgba(255, 84, 112, 0.35); }
.outcome-hp.ok  { color: var(--accent); background: rgba(0, 229, 184, 0.1); border: 1px solid rgba(0, 229, 184, 0.35); }

/* ── BANNERS (victory / death) ──────────────────────────────────
   Big dramatic moment at end-of-run. Heavy gradient, large glyph,
   centered. The death banner has a slow drift to feel haunted. */
.banner {
    border-radius: 16px;
    padding: 2.2rem 1.8rem;
    text-align: center;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(20px) saturate(140%);
    -webkit-backdrop-filter: blur(20px) saturate(140%);
    animation: rise 0.7s cubic-bezier(0.22, 1, 0.36, 1);
    position: relative;
    overflow: hidden;
}
.banner.alive {
    border: 1px solid rgba(0, 229, 184, 0.4);
    background: linear-gradient(160deg,
        rgba(0, 229, 184, 0.14) 0%,
        rgba(0, 196, 255, 0.08) 50%,
        var(--surface) 100%);
}
.banner.dead {
    border: 1px solid rgba(255, 84, 112, 0.35);
    background: linear-gradient(160deg,
        rgba(255, 84, 112, 0.14) 0%,
        rgba(168, 85, 247, 0.08) 60%,
        var(--surface) 100%);
    animation: rise 0.7s cubic-bezier(0.22, 1, 0.36, 1), drift 6s ease-in-out infinite;
}
@keyframes drift {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-3px); }
}
.banner .glyph {
    font-size: 2.8rem;
    margin-bottom: 0.5rem;
    font-weight: 200;
    line-height: 1;
}
.banner .title {
    font-size: 1.65rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.5rem;
    letter-spacing: -0.025em;
}
.banner .subtitle {
    color: var(--text-mute);
    font-size: 0.98rem;
    line-height: 1.65;
    max-width: 520px;
    margin: 0 auto;
}

/* ── STAT TILES ────────────────────────────────────────────────
   The three numbers on the end screen — final CI, rank, time. */
.stat {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
    backdrop-filter: blur(20px) saturate(140%);
    -webkit-backdrop-filter: blur(20px) saturate(140%);
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.stat:hover { border-color: var(--border-hi); transform: translateY(-2px); }
.stat .stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-mute);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}
.stat .stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
}
.stat .stat-value.small { font-size: 1.05rem; }

/* ── CONFETTI ──────────────────────────────────────────────────
   Pure CSS. Forty pieces fall from above with random colors,
   delays, and rotation speeds. Pointer-events are off so the
   user can still click through. */
.confetti-container {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 999;
    overflow: hidden;
}
.confetti {
    position: absolute;
    top: -20px;
    width: 8px;
    height: 14px;
    opacity: 0.9;
    animation: confetti-fall 4.5s linear forwards;
}
@keyframes confetti-fall {
    0%   { transform: translateY(0) rotate(0deg);   opacity: 1; }
    100% { transform: translateY(110vh) rotate(720deg); opacity: 0; }
}

/* ── INPUT FIELDS ──────────────────────────────────────────────── */
.stTextInput input {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    padding: 0.7rem 0.95rem !important;
    backdrop-filter: blur(10px);
    transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease !important;
}
.stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px rgba(0, 229, 184, 0.12) !important;
    outline: none !important;
}
.stTextInput input::placeholder { color: var(--text-dim) !important; }
.stTextInput label {
    color: var(--text-mute) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

/* ── DATAFRAME (leaderboard) ───────────────────────────────────── */
[data-testid="stDataFrame"] {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    overflow: hidden;
    backdrop-filter: blur(16px);
    transition: border-color 0.2s ease;
}
[data-testid="stDataFrame"]:hover { border-color: var(--border-hi); }

/* ── MISC ─────────────────────────────────────────────────────── */
hr { border-color: var(--border-soft) !important; margin: 2rem 0 !important; }
#MainMenu, footer, header { visibility: hidden; }
.stCaption { color: var(--text-mute) !important; }

.footer {
    color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    text-align: center;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-soft);
}
.footer .heart { color: var(--accent); }

/* respect motion preferences — quietly turn off everything ambient */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
"""


# ═══════════════════════════════════════════════════════════════════
# THE CRISES
# ═══════════════════════════════════════════════════════════════════
# Fifteen of these. Eight get drawn per run. The writing is the
# game — if a line doesn't earn its place, it goes. Every outcome
# is the truth told slightly sideways.
#
# Constraints I held myself to:
#   · no proper names (no Daves, no Mikes, no Karens)
#   · no specific job titles (no CEOs, no merchandisers, no QA)
#   · just situations and the consequences of them
#   · funny when it can be funny, quiet when it shouldn't
# ═══════════════════════════════════════════════════════════════════
CRISIS_POOL = [
    {
        "title": "Brand Registry Mutiny",
        "tag":   "INCIDENT",
        "lead":  "Overnight, every product from a major distillery decided it was named something else. Not slight variations. Creative ones. The registry is calm about this. Nothing else is.",
        "options": [
            {"text": "Restore yesterday's snapshot",                              "hp": -10, "outcome": "Done. Four hours of legitimate edits are now in the past tense. The people responsible for those edits have feelings. You will not be at the retro."},
            {"text": "Hot-patch the registry in production",                     "hp":  -5, "outcome": "Risky, fast, worked. An automated ticket gets created to document the incident. The ticket has your name on it. The ticket is already getting comments."},
            {"text": "Tell everyone it's an intentional rebrand activation",     "hp": -40, "outcome": "It was believed for six minutes. The forty minutes that followed were difficult to live through and impossible to forget."},
            {"text": "Use the break-glass escalation channel",                    "hp":  -2, "outcome": "Fixed in four minutes. You will be invited to talk about it. Slides will need to exist. There will be follow-up slides. There will be a follow-up to the follow-up."},
        ],
    },
    {
        "title": "The Ghost in the Catalog",
        "tag":   "CATALOG_HYGIENE",
        "lead":  "A product called 'DELETE_PLEASE_TESTING' has been live on a major homepage for four years. Someone with 800K followers just found it. The screenshot is trending. The replies are creative.",
        "options": [
            {"text": "Quietly delete it and move on",                             "hp":  -3, "outcome": "Gone. Forty-seven other test SKUs are still in production. You will not look for them today, and you will spend the rest of the week not looking for them either."},
            {"text": "Run a full catalog audit for test data",                    "hp": -12, "outcome": "Audit took six hours. It found two hundred more. Some are still selling. One is on a billboard somewhere in a regional capital."},
            {"text": "Rebrand it as a limited mystery edition, double the price", "hp": -40, "outcome": "Three people bought it before someone with authority intervened. The intervention was thorough. Documentation was generated. You feature in the documentation."},
            {"text": "Post a self-deprecating reply on the same platform",        "hp":  -8, "outcome": "Got two thousand likes. Generated some goodwill. Consumed one nerve. You are now considered 'the funny one' at work, which is its own kind of trap."},
        ],
    },
    {
        "title": "The Decimal Point Incident",
        "tag":   "P1",
        "lead":  "A four-hundred-dollar bottle is currently listed for four dollars. The cart count for it is climbing in real time. It is climbing faster than the system can update. The site is, somehow, still up.",
        "options": [
            {"text": "Hot-fix the price and purge the cache",                     "hp":  -8, "outcome": "Fixed in ninety seconds. Eight hundred and forty bottles already shipped at the wrong price. The follow-up emails are polite. The replies to the follow-up emails are less polite."},
            {"text": "Roll back this morning's deploy entirely",                  "hp": -25, "outcome": "Price is correct. So is everything else from yesterday. Today's launches no longer exist. They will need to launch again. They will not love this."},
            {"text": "Honor the prices that already sold, fix forward",           "hp":  -5, "outcome": "Quietly done. Small loss, large amount of trust earned. None of this will be remembered when you ask for a raise. Trust does not appear in spreadsheets."},
            {"text": "Declare it a flash sale and ride the wave",                 "hp": -50, "outcome": "It worked for eleven thrilling minutes. The next two hours were not thrilling. The two hours after that involved a meeting with the word 'urgent' in the title twice."},
        ],
    },
    {
        "title": "Little Bobby Tables Returns",
        "tag":   "SECURITY",
        "lead":  "A new supplier's product description contains a SQL injection pattern, an XSS payload, and what appears to be Morse code. Their preferred contact method is listed as 'pigeons (carrier, trained)'.",
        "options": [
            {"text": "Sanitize, strip, escape, ship",                             "hp":  -3, "outcome": "Handled. You add the supplier to a personal watchlist that lives in a spreadsheet. The spreadsheet is colour-coded. Nobody else will ever see it."},
            {"text": "Reject the entire feed",                                    "hp": -15, "outcome": "Their eight thousand other products are also rejected. Someone is going to ask why. The answer is complicated and accurate and unhelpful."},
            {"text": "Forward to the security team and let them decide",          "hp": -20, "outcome": "A ticket is opened. The ticket has a priority. The priority is below 'lunch'. You consider lunch. Lunch is over."},
            {"text": "Decode the Morse code first",                               "hp":  -5, "outcome": "It says: 'fix your validator'. A strange respect blooms in you for the person on the other end. You will not act on it."},
        ],
    },
    {
        "title": "The Klingon Catalog",
        "tag":   "INBOUND",
        "lead":  "Every description in tonight's feed has arrived in tlhIngan Hol. The supplier insists this is per their reading of the contract. The contract is sixty pages. The relevant clause is somewhere in those sixty pages.",
        "options": [
            {"text": "Run it through AI auto-translation",                        "hp":  -6, "outcome": "Mostly works. Two gins are now described as 'honourable battle vessels'. The vodka is described as a poem. The poem is not bad, actually."},
            {"text": "Reject the feed with a politely-worded reply",              "hp": -18, "outcome": "Reply received eleven days later. It is also in tlhIngan Hol. It is signed."},
            {"text": "Hold the feed, publish nothing tonight",                    "hp": -25, "outcome": "Tomorrow's catalog is thin. The people whose launches were on the schedule will notice. They have always noticed. They will mention it in a way that sounds neutral but isn't."},
            {"text": "Ship it as a limited cultural experience",                  "hp": -32, "outcome": "Twelve customers loved it. Their feedback was 'finally, a brand that takes us seriously'. You are now responsible for the cultural experience programme. There is no cultural experience programme. You are responsible for it anyway."},
        ],
    },
    {
        "title": "Saved Successfully (Citation Needed)",
        "tag":   "PLATFORM",
        "lead":  "The platform says 'Saved successfully' every time you click save. Nothing is actually saving. The success messages are confident. The data is not where you put it. This has been going on for an hour. You are only now noticing.",
        "options": [
            {"text": "Bypass the UI and use the API directly",                    "hp":  -4, "outcome": "Worked. You are now the team's accidental expert on something nobody else uses. Nobody else will use it now either. The expertise is yours forever."},
            {"text": "Restart everything",                                        "hp": -15, "outcome": "Two other services also restarted. They were not having any problems. They are now."},
            {"text": "Open a critical support ticket",                            "hp": -22, "outcome": "Acknowledged. Estimated response time is seven business days. The deadline is in six hours. The seven days does not adjust to fit the six hours."},
            {"text": "Wait, it usually fixes itself",                             "hp": -32, "outcome": "It did fix itself. It fixed itself wrong. Six hours later, somebody noticed. By then, the wrongness had spread."},
        ],
    },
    {
        "title": "The Inheritance",
        "tag":   "DQ",
        "lead":  "A wine vintage field contains the string 'MMXXI'. Investigation reveals this has been happening for at least six months. Roman numerals are passing DQ because the field type is — somehow — free text. You suspect it has always been free text. You suspect this with a slow, settling dread.",
        "options": [
            {"text": "Build a Roman numeral parser into the DQ pipeline",         "hp": -12, "outcome": "Took two hours. It works. Next week, a vintage arrives in Mayan dates. You saw this coming. You did nothing about it. You are doing nothing about it now."},
            {"text": "Convert just this batch and set stricter rules going forward","hp": -5, "outcome": "Pragmatic. Documented. Sustainable. You feel like an actual engineer for the rest of the afternoon."},
            {"text": "Reject the records and bounce them back",                   "hp": -15, "outcome": "Supplier appeals through a committee. The committee meets fortnightly. By the time it resolves, the wine in question is, technically, older."},
            {"text": "Mark the field 'intentionally permissive' and move on",     "hp": -25, "outcome": "Six months later, a vintage comes through as 'twenty-twenty-six but in a fun way'. You read it. You sit. You drink some water. You do not finish the water."},
        ],
    },
    {
        "title": "The Beach Approver",
        "tag":   "WORKFLOW",
        "lead":  "Twelve thousand products are stuck pending approval. The one person with approval rights for this category is on holiday somewhere without signal. They are happy. They have been very clear that they do not want to be reached.",
        "options": [
            {"text": "Implement a 24-hour auto-approve fallback rule",            "hp":  -8, "outcome": "Sensible, boring, effective. Two of the auto-approved products turn out to be regulated in ways nobody flagged. They are not regulated for long."},
            {"text": "Force-approve all twelve thousand",                         "hp": -25, "outcome": "Done. Forty-seven should not have been approved. One is illegal in one specific state. That state notices. That state always notices."},
            {"text": "Reassign approvals to someone less senior",                 "hp": -15, "outcome": "Approved everything in eleven minutes. The next morning they are also unreachable. The pattern is not lost on you."},
            {"text": "Wait for the approver to come back",                        "hp": -42, "outcome": "They came back, well-rested. The launches they were supposed to approve had been delayed. One of the delayed launches was for their favourite category. They had things to say."},
        ],
    },
    {
        "title": "The 4 AM Image Swap",
        "tag":   "INFRA",
        "lead":  "A premium wine is currently showing the product image of a household cleaning chemical. The chemical is bleach. The CDN says the image has always been like this. The CDN is wrong but the CDN is confident.",
        "options": [
            {"text": "Purge the CDN cache for that product",                       "hp":  -3, "outcome": "Fixed in six seconds. A small number of customers had a confusing moment. They will write about it on the internet for free."},
            {"text": "Wait for the 24-hour TTL to expire",                        "hp": -25, "outcome": "Twenty-four hours is enough time for someone to write a thing. They write a thing. The thing is well-written."},
            {"text": "Upload the image again under a new filename",               "hp":  -8, "outcome": "Worked. Now there are two of the image in storage. The wrong one is still cached somewhere. It will surface again later. It always surfaces again later."},
            {"text": "Post that it's an experimental new pairing",                "hp": -38, "outcome": "Some people enjoyed the joke. The brand whose product was misrepresented enjoyed it less. They have lawyers. The lawyers have schedules."},
        ],
    },
    {
        "title": "The Variant Explosion",
        "tag":   "DQ",
        "lead":  "A brand normalization audit reveals forty-seven different spellings of the same brand name in the active catalog. One of them is in Comic Sans. You did not think that was possible. It is.",
        "options": [
            {"text": "Run the normalization workflow",                            "hp":  -6, "outcome": "Cleaned. The brand sends a friendly email correcting your canonical spelling. You explain politely. They correct you back. You stop responding. You do not stop thinking about it."},
            {"text": "Manually fix all forty-seven variants by hand",             "hp": -28, "outcome": "Done in ninety minutes. You have learned nothing transferable. You feel a strange and complicated peace."},
            {"text": "Auto-merge using fuzzy matching",                           "hp": -10, "outcome": "Forty-six merged correctly. One was accidentally merged with a completely different brand. That brand is now also gin. The market is, somehow, fine with this."},
            {"text": "Leave it, customers won't notice",                          "hp": -22, "outcome": "Customers did notice. Conversion drops by twelve percent. The drop is small enough that it could be anything else. It is not anything else."},
        ],
    },
    {
        "title": "The Viral Moment",
        "tag":   "DEMAND",
        "lead":  "A short video of someone making a cocktail with three of your products has done eight million views. All three products are currently out of stock. Site traffic is two hundred times normal. The site is holding. The site is the only thing holding.",
        "options": [
            {"text": "Hide the out-of-stock products immediately",                "hp":  -4, "outcome": "Smart. Conversion stays clean. The creator notices their featured products vanished. They post about it. The new post does more views than the original."},
            {"text": "Show 'back soon' badges and capture wishlists",             "hp":  -2, "outcome": "Eight thousand four hundred wishlist additions. The data is gorgeous. You will spend the next year being asked about this exact moment in meetings."},
            {"text": "Switch all three to a 'limited drop' campaign",             "hp":  -8, "outcome": "Sold four times the volume when restocked. You will be invited to give a talk you do not want to give. The talk will be at an off-site. The off-site has compulsory ice-breakers."},
            {"text": "Leave it, customers know what OOS means",                   "hp": -22, "outcome": "They did not know what OOS means. They wrote angry reviews. Some included photographs of empty shelves. Six were from the same person, who is now your most engaged customer."},
        ],
    },
    {
        "title": "The Compliance Knock",
        "tag":   "AUDIT",
        "lead":  "There is an audit in two hours. You need to prove every product in the catalog has a correct ABV value. You realise, just now, that some of them are blank. You realise, also just now, that some of them say 'TBC'.",
        "options": [
            {"text": "Run a pre-audit script to find and patch",                  "hp": -10, "outcome": "Found two thousand issues. Patched most. Some are now wrong in different ways. Different is not better, but it is different."},
            {"text": "Bulk-update from supplier data and hope",                   "hp": -22, "outcome": "Updated. A hundred and forty products now have ABVs the suppliers never specified. The auditor finds three of them within the first half hour."},
            {"text": "Hide the worst offenders from the audit query",             "hp": -45, "outcome": "The audit was passed. Two months later, somebody runs a different query. They find what you did. They find what you did with timestamps."},
            {"text": "Pre-audit the audit and fix only what they'll check",       "hp":  -5, "outcome": "Surgical. Effective. Some products are still wrong, but the right ones are right. You feel a small, complicated pride. You should not feel proud. You feel proud anyway."},
        ],
    },
    {
        "title": "The Recursive Bug",
        "tag":   "WORKFLOW",
        "lead":  "A workflow is creating tickets faster than they can be resolved. Each ticket spawns two more. The queue is doubling every fifteen minutes. The queue is now larger than the catalog itself. The queue is, technically, the new catalog.",
        "options": [
            {"text": "Disable the offending workflow trigger",                    "hp":  -5, "outcome": "Stopped. The existing queue remains. The existing queue is the same size as the catalog. Resolving it will take approximately one calendar year of human attention."},
            {"text": "Bulk-resolve every duplicate ticket",                       "hp": -12, "outcome": "Resolved. Eight legitimate tickets were also resolved by accident. Those eight tickets re-emerge as customer complaints, individually, over the next month, in increasingly dramatic ways."},
            {"text": "Roll back the deploy that introduced it",                   "hp": -18, "outcome": "Rolled back. Six other features rolled back with it. People are asking where their features went. Their features are not gone, just deferred. The distinction does not help anyone."},
            {"text": "Let it run, it'll crash the queue eventually",              "hp": -45, "outcome": "It crashed the queue. It crashed several other things, too. One of them is now famous. The thing being famous is good for the system in some abstract way nobody can articulate."},
        ],
    },
    {
        "title": "The Unexpected Translation",
        "tag":   "OUTBOUND",
        "lead":  "Auto-translation has been on. A wine described as 'notes of leather and earth' has been translated to a key market as 'tastes like shoes and dirt'. Sales in that market have collapsed. Customer reviews are extensive. They are detailed. Several include photographs.",
        "options": [
            {"text": "Disable auto-translation, translate manually going forward","hp": -10, "outcome": "Sensible. Slow. Expensive. The market recovers over the next month, slowly, the way a person recovers from food poisoning."},
            {"text": "Curate a translation glossary for tasting notes",           "hp":  -8, "outcome": "Took an afternoon. Saves countless future incidents. Nobody else will know the glossary exists. The glossary is the only documentation. The glossary lives in a spreadsheet."},
            {"text": "Issue a public correction",                                 "hp": -15, "outcome": "Correction issued. It does some good. The reviews mentioning shoes remain searchable in perpetuity."},
            {"text": "Lean in. 'Shoes and dirt' is now the brand voice",          "hp": -35, "outcome": "A surprising number of supportive comments. A less surprising number of unsupportive emails. Three of the unsupportive emails are from the wine producer themselves."},
        ],
    },
    {
        "title": "The Macro From The Past",
        "tag":   "INBOUND",
        "lead":  "The supplier feed has been processed for nine years by an Excel macro. The macro was written by someone who has since started a successful YouTube channel about woodworking. The macro broke last night. The macro is password-protected. Nobody has the password. The YouTube channel does not reply to inquiries.",
        "options": [
            {"text": "Build a clean Python replacement today",                    "hp": -15, "outcome": "Took most of the day. Works correctly. Two edge cases the macro handled silently are now breaking loudly. You will discover them one at a time over the next month."},
            {"text": "Pay someone online to crack the password",                  "hp": -25, "outcome": "It took an hour. The macro is, internally, beautiful. There are comments. The comments are in Old English. You consider going back to the woodworking channel."},
            {"text": "Keep using the broken macro and patch the output manually", "hp": -30, "outcome": "It works. You become deeply familiar with the macro's quirks. You become the only person who understands it. You realise this is a trap. You are already inside it."},
            {"text": "Email the woodworking channel and ask nicely",              "hp":  -3, "outcome": "Replied within an hour. The password was 'butter1985'. The password works. You spend ten minutes trying to imagine why."},
        ],
    },
]


# ───────────────────────────────────────────────────────────────────
# THE GLITCH
# One in twelve crises is silently replaced with this. The fourth
# wall flexes for a moment. It is the only crisis where the options
# are not really about catalog work. It is about you.
# ───────────────────────────────────────────────────────────────────
META_CRISIS = {
    "title": "—",
    "tag":   "?",
    "lead":  "The crisis card is empty. There is no description. The system appears to be waiting for you to do something.",
    "options": [
        {"text": "Pretend nothing happened and continue",                          "hp":  0, "outcome": "Wise. The shift continues. The system continues. Nobody mentions the gap. You will think about it tonight."},
        {"text": "Make direct eye contact with the screen",                        "hp": -5, "outcome": "The screen wins. The next crisis will be normal. You will not be normal."},
        {"text": "Refresh and hope this didn't happen",                            "hp": -8, "outcome": "Brave. You lost some progress, gained some peace. The peace is not large but it is real."},
        {"text": "Stand up and walk away from the desk for a minute",              "hp": +8, "outcome": "You needed that. We won't tell anyone. Welcome back. The catalog missed you. So did the chair."},
    ],
}


# ═══════════════════════════════════════════════════════════════════
# DATA LAYER — Google Sheets leaderboard, kept compatible
# ═══════════════════════════════════════════════════════════════════
@st.cache_resource
def get_db():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), scope
    )
    return gspread.authorize(creds).open("PIM_Odyssey_DB")


def save_score(name: str, score: int, title: str) -> tuple[bool, Optional[str]]:
    # quiet save; failure is non-fatal
    try:
        get_db().worksheet("Scores").append_row(
            [datetime.now().isoformat(timespec="seconds"), name, score, title]
        )
        return True, None
    except Exception as e:
        return False, str(e)


def fetch_leaderboard() -> pd.DataFrame:
    # tolerate either the old schema or the new one
    try:
        rows = get_db().worksheet("Scores").get_all_values()
        if len(rows) < 2:
            return pd.DataFrame()
        headers = [h.strip() for h in rows[0]]
        df = pd.DataFrame(rows[1:], columns=headers)
        df = df.rename(columns={"Architect": "Name", "Score": "CI", "Phase": "Title"})
        if "CI" not in df.columns or "Name" not in df.columns:
            return pd.DataFrame()
        df["CI"] = pd.to_numeric(df["CI"], errors="coerce").fillna(0).astype(int)
        out = (df.groupby("Name", as_index=False)
                 .agg({"CI": "max", "Title": "first"})
                 .sort_values("CI", ascending=False).head(12)
                 .reset_index(drop=True))
        out.index = out.index + 1
        out.index.name = "#"
        return out
    except Exception:
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════
# GAME LOGIC
# ═══════════════════════════════════════════════════════════════════
def init_state():
    # everything I need to remember across reruns
    defaults = {
        "stage":       "intro",     # intro | crisis | outcome | end
        "name":        "",
        "hp":          START_HP,
        "round_pool":  [],          # list of crisis indices (or -1 for meta)
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
    # draw the pool: 8 random crises, plus a 1-in-12 chance of replacing
    # one of them with the meta crisis. always picks a different position.
    pool = random.sample(range(len(CRISIS_POOL)), ROUNDS)
    if random.random() < (1 / 12):
        # replace one slot with the glitch
        slot = random.randint(0, ROUNDS - 1)
        pool[slot] = -1  # sentinel for the meta crisis
    st.session_state.update({
        "name":        name,
        "hp":          START_HP,
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


# Survival rank — used on the leaderboard and the end screen.
# Names are descriptive, not titular. No promotions implied.
def rank_for(hp: int, survived: bool) -> str:
    if not survived:
        return "Did not survive"
    if hp >= 95: return "Catalog Whisperer"
    if hp >= 80: return "Made It Look Easy"
    if hp >= 60: return "Capable On A Bad Day"
    if hp >= 40: return "Survived The Shift"
    if hp >= 20: return "Barely"
    return "Technically Alive"


# Death messages — randomized so the third run is different from the first.
# Each is the same shape: a quiet sentence and a slightly quieter one.
def death_message() -> tuple[str, str]:
    options = [
        ("You have been moved to special projects",
         "There are no special projects. There is a desk. The desk is near the elevators. The elevators are loud."),
        ("The catalog has chosen new leadership",
         "It is not you. There was no vote. There was no announcement. There was a quiet swap and a series of permission changes you do not have visibility into."),
        ("Your access to production has been reviewed",
         "The review concluded. You are not informed of the conclusion. You are informed of the conclusion of the review. The distinction matters less than you'd hope."),
        ("Your callsign has been retired with regret",
         "A plaque exists somewhere. The plaque is engraved correctly. The plaque is in a hallway that nobody walks down. That is something. It is not much."),
    ]
    return random.choice(options)


# ═══════════════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════════════
def hp_gradient(hp: int) -> str:
    # smooth transitions between green → amber → red
    if hp >= 60:
        return "linear-gradient(90deg, #00e5b8, #00c4ff)"
    if hp >= 30:
        return "linear-gradient(90deg, #f59e0b, #ff9d4d)"
    return "linear-gradient(90deg, #ff5470, #ff8aa0)"


def render_hud():
    hp = max(0, st.session_state.hp)
    idx = st.session_state.round_idx + 1
    pct = max(0, min(100, hp))
    fill = hp_gradient(hp)

    st.markdown(
        f'<div class="hud">'
        f'  <div class="hud-tag">CRISIS<span class="v">{idx} / {ROUNDS}</span></div>'
        f'  <div class="hud-wrap">'
        f'    <span class="hud-label">CATALOG INTEGRITY</span>'
        f'    <div class="hp-track"><div class="hp-fill" style="width:{pct}%; background:{fill};"></div></div>'
        f'    <span class="hp-num">{hp} / 100</span>'
        f'  </div>'
        f'  <div class="hud-tag">OPS<span class="v">{st.session_state.name or "—"}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_confetti(pieces: int = 42):
    """Sprinkle. Pure CSS. Random colors, positions, delays.
    Generated server-side so there's no flicker on first paint."""
    colors = ["#00e5b8", "#00c4ff", "#a855f7", "#f59e0b", "#ff5470", "#f4f4f6"]
    parts = ['<div class="confetti-container">']
    for _ in range(pieces):
        left   = random.uniform(0, 100)
        delay  = random.uniform(0, 3.0)
        dur    = random.uniform(3.0, 6.5)
        rot    = random.uniform(-180, 180)
        color  = random.choice(colors)
        width  = random.choice([6, 8, 10])
        height = random.choice([10, 14, 18])
        parts.append(
            f'<div class="confetti" style="'
            f'left:{left}vw; background:{color}; '
            f'width:{width}px; height:{height}px; '
            f'animation-delay:{delay}s; animation-duration:{dur}s; '
            f'transform:rotate({rot}deg);"></div>'
        )
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def footer():
    st.markdown(
        '<div class="footer">'
        'built with too much care by <span class="heart">Ati from PIM</span> · '
        'streamlit + a leaderboard + fifteen problems'
        '</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════
def screen_intro():
    st.markdown('<div class="eyebrow">A small roguelike about catalog work</div>', unsafe_allow_html=True)
    st.markdown('<h1><span class="kinetic">Don\'t let the catalog die.</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: var(--text-mute); font-size: 1.05rem; line-height: 1.7; margin-top: 0.2rem; max-width: 620px;">'
        'You are on a chaotic shift. Eight things are about to go wrong, drawn at random from a pool of fifteen. '
        'Every choice costs you some <strong style="color: var(--text);">Catalog Integrity</strong>. '
        'Hit zero and the shift ends. Survive all eight and you get a rank, a leaderboard spot, '
        'and a quiet feeling of accomplishment that you can take into the rest of your day.'
        '</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="glass">'
        '<div class="card-label">HOW IT WORKS</div>'
        '<ul style="margin: 0; padding-left: 1.2rem; line-height: 1.9; color: var(--text-mute); font-size: 0.95rem;">'
        '<li>You start at <strong style="color: var(--text);">100 CI</strong>. There is no healing. There is only damage of varying quality.</li>'
        '<li>The HP cost is shown <em>before</em> you commit. The consequences are not.</li>'
        '<li>HP at zero ends the shift early. Make it to crisis eight and you are ranked by remaining CI.</li>'
        '<li>Every run draws a different combination. One run in twelve does something I am not going to spoil.</li>'
        '<li>Your highest score is what makes the leaderboard.</li>'
        '</ul>'
        '</div>',
        unsafe_allow_html=True,
    )

    name = st.text_input(
        "What should we call you?",
        placeholder="anything you'd like to see on the leaderboard",
        max_chars=32,
        label_visibility="visible",
    )

    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Begin shift"):
        if name.strip():
            start_run(name.strip())
        else:
            st.warning("A name, even a pseudonym, is required.")
    st.markdown('</div>', unsafe_allow_html=True)

    # leaderboard preview, if there's something to show
    lb = fetch_leaderboard()
    if not lb.empty:
        st.markdown(
            '<div class="card-label" style="margin-top: 2rem;">CURRENT LEADERBOARD</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(lb, use_container_width=True)

    footer()


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

    for i, opt in enumerate(c["options"]):
        hp_label = f"{opt['hp']:+d} CI" if opt["hp"] != 0 else "0 CI"
        label = f"{opt['text']}  ·  {hp_label}"
        if st.button(label, key=f"opt_{st.session_state.round_idx}_{i}"):
            st.session_state.last_choice = {
                "crisis": c["title"],
                "text":   opt["text"],
                "hp":     opt["hp"],
                "outcome": opt["outcome"],
            }
            st.session_state.hp += opt["hp"]
            goto("outcome")

    footer()


def screen_outcome():
    render_hud()
    c = st.session_state.last_choice
    hp_cls = "bad" if c["hp"] < 0 else "ok"
    hp_text = f"{c['hp']:+d} CI" if c["hp"] != 0 else "±0 CI"

    st.markdown(
        f'<div class="outcome">'
        f'<div class="outcome-label">OUTCOME · {c["crisis"]}</div>'
        f'<div class="outcome-choice">{c["text"]}</div>'
        f'<div class="outcome-body">{c["outcome"]}</div>'
        f'<div class="outcome-hp {hp_cls}">{hp_text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # death check happens before incrementing round
    if st.session_state.hp <= 0:
        st.session_state.survived = False
        st.markdown('<div class="primary-action">', unsafe_allow_html=True)
        if st.button("See how this ended"):
            goto("end")
        st.markdown('</div>', unsafe_allow_html=True)
        footer()
        return

    # advance the counter so the next crisis is the next one
    st.session_state.round_idx += 1

    if st.session_state.round_idx >= ROUNDS:
        st.session_state.survived = True
        st.markdown('<div class="primary-action">', unsafe_allow_html=True)
        if st.button("See the summary"):
            goto("end")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="primary-action">', unsafe_allow_html=True)
        next_n = st.session_state.round_idx + 1
        if st.button(f"Next  ({next_n} of {ROUNDS})"):
            st.session_state.last_choice = None
            goto("crisis")
        st.markdown('</div>', unsafe_allow_html=True)

    footer()


def screen_end():
    hp = max(0, st.session_state.hp)
    survived = st.session_state.survived
    title = rank_for(hp, survived)
    elapsed = int(time.time() - st.session_state.started_at) if st.session_state.started_at else 0

    if survived:
        render_confetti()
        st.markdown(
            f'<div class="banner alive">'
            f'<div class="glyph">◉</div>'
            f'<div class="title">You survived the shift.</div>'
            f'<div class="subtitle">Eight crises down. The catalog is still on its feet. '
            f'The launches launched, more or less. Tomorrow will bring its own problems. '
            f'They will not be these problems.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        dt_title, dt_sub = death_message()
        st.markdown(
            f'<div class="banner dead">'
            f'<div class="glyph">⌀</div>'
            f'<div class="title">{dt_title}</div>'
            f'<div class="subtitle">{dt_sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # three numbers, equal weight, no decoration
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="stat">'
            f'<div class="stat-label">FINAL CI</div>'
            f'<div class="stat-value" style="color: {("var(--accent)" if hp >= 60 else "var(--warn)" if hp >= 30 else "var(--blood)")};">{hp}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat">'
            f'<div class="stat-label">RANK</div>'
            f'<div class="stat-value small">{title}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat">'
            f'<div class="stat-label">SHIFT TIME</div>'
            f'<div class="stat-value">{elapsed // 60}m {elapsed % 60:02d}s</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # save once, quietly
    if not st.session_state.saved:
        ok, err = save_score(st.session_state.name, hp, title)
        st.session_state.saved = True
        if not ok:
            st.caption(f"(Leaderboard write failed: {err})")

    st.markdown('<div class="card-label" style="margin-top: 2rem;">LEADERBOARD</div>', unsafe_allow_html=True)
    lb = fetch_leaderboard()
    if lb.empty:
        st.caption("No entries yet. You could be the first.")
    else:
        st.dataframe(lb, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Another run"):
        name = st.session_state.name
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        init_state()
        start_run(name)
    st.markdown('</div>', unsafe_allow_html=True)

    footer()


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


# go
main()
