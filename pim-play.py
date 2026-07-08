"""
PIM Play — 
by EDG PIM Team

"""

from __future__ import annotations

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
QUESTIONS_PER_PLAY = 5
POINTS_PER_CORRECT = 100
MAX_SCORE          = QUESTIONS_PER_PLAY * POINTS_PER_CORRECT   # 500

st.set_page_config(
    page_title  = "PIM Play",
    page_icon   = "🍔",
    layout      = "centered",
    initial_sidebar_state = "collapsed",
)


# ═══════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-base:      #1a1d40;
    --surface:      rgba(52, 62, 110, 0.55);
    --surface-2:    rgba(66, 78, 128, 0.70);
    --border:       rgba(255, 255, 255, 0.13);
    --border-hi:    rgba(255, 255, 255, 0.27);
    --text:         #fafaff;
    --text-mute:    #c5c6e2;
    --text-dim:     #8e90b5;
    --gold:         #ffd56b;
    --pink:         #ff6bc7;
    --cyan:         #6bdfff;
    --blue:         #7b9fff;
    --green:        #5ee29c;
    --danger:       #ff6680;
    --correct-soft: rgba(94, 226, 156, 0.15);
    --wrong-soft:   rgba(255, 102, 128, 0.15);
    --quiz-accent:  #7b9fff;
    --quiz-soft:    rgba(123, 159, 255, 0.16);
}

.stApp { background: var(--bg-base); }

.stApp::before {
    content: '';
    position: fixed;
    inset: -25%;
    background:
        radial-gradient(40% 40% at 25% 35%, rgba(123,159,255,0.28) 0%, transparent 60%),
        radial-gradient(44% 44% at 78% 68%, rgba(255,107,199,0.22) 0%, transparent 60%),
        radial-gradient(50% 50% at 55% 18%, rgba(107,223,255,0.20) 0%, transparent 60%),
        radial-gradient(34% 34% at 32% 82%, rgba(94,226,156,0.14) 0%, transparent 60%);
    filter: blur(70px);
    z-index: 0;
    pointer-events: none;
    animation: aurora 20s ease-in-out infinite alternate;
}
@keyframes aurora {
    0%   { transform: translate(0,0)    scale(1)    rotate(0deg);   }
    25%  { transform: translate(-4%,3%) scale(1.07) rotate(2deg);   }
    50%  { transform: translate(3%,-4%) scale(0.95) rotate(-2deg);  }
    75%  { transform: translate(-2%,-3%)scale(1.09) rotate(1.5deg); }
    100% { transform: translate(2%,2%)  scale(1.01) rotate(-1deg);  }
}
.main, .block-container { position: relative; z-index: 1; }

html, body, .main, [class*="css"], p, span, div, label, li {
    font-family: 'Inter', -apple-system, system-ui, sans-serif !important;
    color: var(--text);
}
code, .mono { font-family: 'JetBrains Mono', monospace !important; }
.main .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 780px; }
h1 { font-size: 2.1rem !important; font-weight: 800 !important; letter-spacing: -0.03em !important; line-height: 1.1 !important; margin-bottom: 0.5rem !important; }

.kinetic {
    background: linear-gradient(120deg, var(--cyan), var(--blue), var(--pink), var(--cyan));
    background-size: 300% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shift 5s ease-in-out infinite;
}
@keyframes shift { 0%,100%{background-position:0% 50%;} 50%{background-position:100% 50%;} }

.eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem; color: var(--cyan);
    text-transform: uppercase; letter-spacing: 0.18em;
    font-weight: 600; margin-bottom: 0.5rem;
    animation: rise 0.6s ease-out;
}
@keyframes rise {
    0%  { opacity:0; transform:translateY(24px) scale(0.96); }
    60% { opacity:1; transform:translateY(-4px)  scale(1.01); }
    100%{ opacity:1; transform:translateY(0)      scale(1);   }
}

.glass {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px; padding: 1.5rem 1.7rem; margin: 1rem 0;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    box-shadow: 0 1px 0 rgba(255,255,255,0.08) inset, 0 20px 50px -20px rgba(0,0,0,0.55);
    animation: rise 0.6s cubic-bezier(0.34,1.4,0.5,1);
    transition: border-color 0.3s ease, transform 0.3s cubic-bezier(0.22,1,0.36,1);
}
.glass:hover { border-color: var(--border-hi); transform: translateY(-4px); }

.card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem; color: var(--cyan);
    letter-spacing: 0.14em; text-transform: uppercase;
    margin-bottom: 0.8rem; font-weight: 700;
}

/* HUD */
.hud {
    display: grid; grid-template-columns: auto 1fr auto;
    align-items: center; gap: 1.4rem;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 0.9rem 1.3rem; margin-bottom: 1.4rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    animation: rise 0.5s cubic-bezier(0.34,1.4,0.5,1);
}
.hud-cell { font-family:'JetBrains Mono',monospace; font-size:0.76rem; color:var(--text-mute); letter-spacing:0.08em; text-transform:uppercase; }
.hud-cell .v { color:var(--text); font-weight:700; font-size:0.95rem; margin-left:5px; }
.hud-center { display:flex; align-items:center; gap:1rem; justify-content:center; }
.prog-track { width:200px; height:10px; background:rgba(0,0,0,0.45); border:1px solid var(--border); border-radius:5px; overflow:hidden; }
.prog-fill {
    height:100%; border-radius:4px;
    background:linear-gradient(90deg, var(--cyan), var(--blue));
    transition:width 0.6s cubic-bezier(0.34,1.3,0.55,1);
    position:relative;
}
.prog-fill::after {
    content:''; position:absolute; inset:0;
    background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,0.28) 50%,transparent 70%);
    animation:shimmer 2s linear infinite;
}
@keyframes shimmer { 0%{transform:translateX(-150%);} 100%{transform:translateX(150%);} }
.prog-label { font-family:'JetBrains Mono',monospace; font-size:0.82rem; font-weight:700; color:var(--cyan); white-space:nowrap; }
.score-badge {
    font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:700;
    color:var(--gold); background:rgba(255,213,107,0.12);
    border:1px solid rgba(255,213,107,0.35); border-radius:8px;
    padding:4px 14px; letter-spacing:0.02em;
    animation:score-pop 0.4s cubic-bezier(0.34,1.5,0.55,1);
}
@keyframes score-pop { 0%{transform:scale(0.85);opacity:0.6;} 100%{transform:scale(1);opacity:1;} }

/* Question card */
.q-card {
    background: var(--surface);
    border: 1px solid var(--border); border-left: 4px solid var(--quiz-accent);
    border-radius: 16px; padding: 1.7rem 1.9rem; margin-bottom: 1.4rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    box-shadow: 0 20px 50px -20px rgba(0,0,0,0.6);
    animation: rise 0.65s cubic-bezier(0.34,1.4,0.5,1);
    transition: transform 0.4s cubic-bezier(0.22,1,0.36,1), box-shadow 0.4s ease;
    transform-style: preserve-3d;
}
.q-card:hover {
    transform: perspective(900px) rotateX(-1deg) rotateY(0.5deg) translateY(-3px);
    box-shadow: 0 28px 65px -25px rgba(0,0,0,0.8);
}
.q-tag {
    display:inline-block; font-family:'JetBrains Mono',monospace;
    font-size:0.74rem; font-weight:700; color:var(--quiz-accent);
    background:var(--quiz-soft); border:1px solid rgba(123,159,255,0.42);
    border-radius:6px; padding:4px 11px; margin-bottom:0.9rem;
    letter-spacing:0.14em; animation:q-pulse 2.4s ease-out infinite;
}
@keyframes q-pulse {
    0%  {box-shadow:0 0 0 0   rgba(123,159,255,0.55);}
    70% {box-shadow:0 0 0 9px rgba(123,159,255,0);}
    100%{box-shadow:0 0 0 0   rgba(123,159,255,0);}
}
.q-card:hover .q-tag { animation: q-pulse 2.4s ease-out infinite, glitch 0.7s ease-in-out; }
@keyframes glitch {
    0%,100%{text-shadow:none;transform:translate(0);}
    20%{text-shadow:-3px 0 var(--pink),3px 0 var(--cyan);transform:translate(2px,0);}
    40%{text-shadow:3px 0 var(--pink),-3px 0 var(--cyan);transform:translate(-2px,0);}
    60%{text-shadow:-2px 0 var(--gold),2px 0 var(--pink);transform:translate(0,2px);}
    80%{text-shadow:2px 0 var(--gold),-2px 0 var(--pink);transform:translate(0,-2px);}
}
.q-title { font-size:1.2rem; font-weight:700; color:var(--text); margin-bottom:0.5rem; line-height:1.4; letter-spacing:-0.015em; }
.q-subtitle { color:var(--text-mute); font-size:0.97rem; line-height:1.65; }

/* Buttons */
.stButton { width:100%; }
.stButton button {
    width:100% !important; background:var(--surface-2) !important;
    color:var(--text) !important; border:1px solid var(--border-hi) !important;
    border-radius:12px !important; text-align:left !important;
    padding:1rem 1.25rem !important; font-family:'Inter',sans-serif !important;
    font-size:0.97rem !important; font-weight:500 !important;
    line-height:1.5 !important; white-space:normal !important;
    backdrop-filter:blur(20px) !important;
    box-shadow:0 4px 16px -8px rgba(0,0,0,0.3) !important;
    transition: border-color 0.2s ease, background 0.2s ease,
                transform 0.2s cubic-bezier(0.22,1,0.36,1), box-shadow 0.2s ease !important;
}
.stButton button:hover {
    border-color:var(--cyan) !important;
    background:rgba(107,223,255,0.07) !important;
    transform:translateY(-4px) scale(1.01) !important;
    box-shadow:0 14px 36px -10px rgba(107,223,255,0.4) !important;
}
.stButton button:active { transform:translateY(-1px) scale(1) !important; }

.primary-action .stButton button {
    background:linear-gradient(135deg, var(--cyan) 0%, var(--blue) 55%, var(--pink) 100%) !important;
    color:#13162e !important; border-color:transparent !important;
    text-align:center !important; font-weight:800 !important; font-size:1rem !important;
    background-size:200% 200% !important;
    animation:pulse-primary 4s ease-in-out infinite !important;
}
@keyframes pulse-primary { 0%,100%{background-position:0% 50%;} 50%{background-position:100% 50%;} }
.primary-action .stButton button:hover {
    transform:translateY(-4px) scale(1.02) !important;
    box-shadow:0 18px 44px -12px rgba(107,223,255,0.55) !important;
}

/* Result panel */
.result-panel {
    border-radius:16px; padding:1.6rem 1.8rem; margin:1rem 0;
    backdrop-filter:blur(24px) saturate(160%);
    animation:rise 0.55s cubic-bezier(0.34,1.4,0.5,1);
}
.result-panel.correct { background:var(--surface); border:1.5px solid rgba(94,226,156,0.45); box-shadow:0 0 0 1px rgba(94,226,156,0.1) inset,0 20px 50px -20px rgba(94,226,156,0.22); }
.result-panel.wrong   { background:var(--surface); border:1.5px solid rgba(255,102,128,0.45); box-shadow:0 0 0 1px rgba(255,102,128,0.1) inset,0 20px 50px -20px rgba(255,102,128,0.18); }
.result-verdict { font-family:'JetBrains Mono',monospace; font-size:0.84rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:0.75rem; }
.result-verdict.correct { color:var(--green); }
.result-verdict.wrong   { color:var(--danger); }
.result-answer  { font-size:0.95rem; color:var(--text-mute); margin-bottom:0.8rem; font-style:italic; padding-left:1rem; border-left:3px solid var(--border-hi); line-height:1.5; }
.result-explain { color:var(--text); font-size:1.02rem; line-height:1.7; margin-bottom:0.9rem; }
.result-points  { display:inline-block; font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:700; padding:6px 14px; border-radius:7px; }
.result-points.earned  { color:var(--green);  background:var(--correct-soft); border:1px solid rgba(94,226,156,0.4); }
.result-points.nothing { color:var(--danger); background:var(--wrong-soft);   border:1px solid rgba(255,102,128,0.4); }

/* Banner */
.banner {
    border-radius:18px; padding:2.4rem 1.8rem; text-align:center; margin-bottom:1.4rem;
    backdrop-filter:blur(24px) saturate(160%);
    border:1.5px solid rgba(107,223,255,0.45);
    background:linear-gradient(160deg,rgba(123,159,255,0.18) 0%,rgba(107,223,255,0.1) 50%,var(--surface) 100%);
    animation:rise 0.8s cubic-bezier(0.34,1.4,0.5,1);
}
.banner .glyph     { font-size:3.2rem; margin-bottom:0.5rem; line-height:1; }
.banner .name-line { font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:var(--gold); letter-spacing:0.14em; text-transform:uppercase; margin-bottom:0.5rem; font-weight:700; }
.banner .title     { font-size:1.85rem; font-weight:800; color:var(--text); margin-bottom:0.6rem; letter-spacing:-0.025em; line-height:1.15; }
.banner .subtitle  { color:var(--text-mute); font-size:1rem; line-height:1.65; max-width:500px; margin:0 auto; }

/* Stat tiles */
.stat { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:1.1rem 1.2rem; text-align:center; backdrop-filter:blur(24px) saturate(160%); transition:border-color 0.25s ease, transform 0.25s ease; animation:rise 0.5s cubic-bezier(0.34,1.4,0.5,1) backwards; }
.stat:hover { border-color:var(--border-hi); transform:translateY(-4px); }
.stat:nth-of-type(1){animation-delay:0.05s;} .stat:nth-of-type(2){animation-delay:0.12s;} .stat:nth-of-type(3){animation-delay:0.19s;}
.stat .stat-label { font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:var(--text-mute); letter-spacing:0.14em; text-transform:uppercase; margin-bottom:0.5rem; font-weight:600; }
.stat .stat-value { font-family:'JetBrains Mono',monospace; font-size:1.8rem; font-weight:800; color:var(--text); letter-spacing:-0.02em; }
.stat .stat-value.small { font-size:1rem; line-height:1.35; }

/* Confetti */
.confetti-container { position:fixed; inset:0; pointer-events:none; z-index:999; overflow:hidden; }
.confetti { position:absolute; top:-30px; border-radius:2px; opacity:0.95; animation:confetti-fall 5s linear forwards; }
@keyframes confetti-fall { 0%{transform:translateY(0) rotate(0deg);opacity:1;} 100%{transform:translateY(110vh) rotate(900deg);opacity:0;} }

/* Inputs */
.stTextInput input {
    background:var(--surface-2) !important; color:var(--text) !important;
    border:1px solid var(--border-hi) !important; border-radius:10px !important;
    font-size:1rem !important; padding:0.8rem 1rem !important;
    transition:border-color 0.25s ease, box-shadow 0.25s ease !important;
}
.stTextInput input:focus { border-color:var(--cyan) !important; box-shadow:0 0 0 5px rgba(107,223,255,0.15) !important; outline:none !important; }
.stTextInput input::placeholder { color:var(--text-dim) !important; }
.stTextInput label { color:var(--text-mute) !important; font-size:0.88rem !important; font-weight:600 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { background:var(--surface); border:1px solid var(--border); border-radius:14px; overflow:hidden; backdrop-filter:blur(20px); transition:border-color 0.25s ease; }
[data-testid="stDataFrame"]:hover { border-color:var(--border-hi); }

/* Email status */
.email-sent {
    background:rgba(94,226,156,0.12); border:1px solid rgba(94,226,156,0.4);
    border-radius:10px; padding:0.85rem 1.2rem; margin-top:1rem;
    font-family:'JetBrains Mono',monospace; font-size:0.85rem; color:var(--green);
    animation:rise 0.5s cubic-bezier(0.34,1.4,0.5,1);
}
.email-fail {
    background:rgba(255,102,128,0.1); border:1px solid rgba(255,102,128,0.35);
    border-radius:10px; padding:0.85rem 1.2rem; margin-top:1rem;
    font-family:'JetBrains Mono',monospace; font-size:0.85rem; color:var(--danger);
}

/* All players table */
.all-players {
    background:var(--surface); border:1px solid var(--border);
    border-radius:14px; overflow:hidden; margin-top:0.5rem;
}

hr { border-color:var(--border) !important; margin:2rem 0 !important; }
#MainMenu, footer, header { visibility:hidden; }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:0.01ms !important; transition-duration:0.01ms !important; } }
</style>
"""


# ═══════════════════════════════════════════════════════════════════
# THE 5 FIXED QUESTIONS — same for every player, every time
# Wrong answers are funny. Correct answers are real.
# ═══════════════════════════════════════════════════════════════════
QUIZ_POOL = [

    {
        "tag":      "ASSET VALIDATION",
        "gif_id":   "YmszCwM1FV7zCI8sgL",
        "question": "A customer clicks on a premium whiskey. The product image is a bottle of dishwashing liquid. Both smell faintly of lemon. The website sees absolutely no problem. What went wrong?",
        "context":  "Vincy uploaded a batch of images in 2019. Vincy has been asked about this. Vincy is not saying.",
        "options": [
            {"text": "An image was mapped to the wrong product during bulk upload — no content validation existed to catch the mismatch",
             "correct": True},
            {"text": "The dishwashing liquid is extremely premium. Both products belong in the same tax bracket now.",
             "correct": False},
            {"text": "The CDN has been caching the dishwashing liquid since 2019 and at this point considers it canon",
             "correct": False},
            {"text": "Both are technically liquids. The system made a brave, liquid-forward categorisation decision.",
             "correct": False},
        ],
        "explanation": "Image-to-product validation checks that an uploaded image matches the product category. Without it, a wrong file from a bulk upload goes live and stays live until a customer notices the lemon-scented whiskey. The PIM team uses Vertex AI and human approval to validate all media assets.",
    },

    {
        "tag":      "DATA QUALITY",
        "gif_id":   "l4FGt5wmYS9z2GK6A",
        "question": "A product's ABV field says 'yes.' The legal team would very much like a word. What data quality rule was missing?",
        "context":  "The supplier was asked to confirm the ABV. They confirmed. The pipeline faithfully recorded the confirmation and felt good about itself.",
        "options": [
            {"text": "A numeric type validation rule — ABV must be a decimal number between 0 and 100",
             "correct": True},
            {"text": "A positivity filter — 'yes' is at least enthusiastic and the catalog deserves some optimism",
             "correct": False},
            {"text": "A spell checker — 'yes' is spelled correctly and the system had absolutely no further notes",
             "correct": False},
            {"text": "A follow-up email asking the supplier whether 'yes' refers to the percentage, their job satisfaction, or both",
             "correct": False},
        ],
        "explanation": "ABV is a decimal number. 'Yes' is not a decimal number. A type validation rule rejects it before it enters the catalog. This is one of the most common DQ failures — suppliers filling numeric fields as if they were customer satisfaction surveys.",
    },

    {
        "tag":      "ENRICHMENT",
        "gif_id":   "1UUZFXZteyHOrxaUeT",
        "question": "A wine description on the live Dan Murphy's website reads: 'This wine pairs beautifully with [INSERT FOOD PAIRING HERE].' How did this happen?",
        "context":  "Chien's enrichment workflow had a timeout at exactly the wrong moment. Chien does not know this yet. Chien will know very soon.",
        "options": [
            {"text": "The product was published before enrichment completed — the template placeholder was never replaced",
             "correct": True},
            {"text": "It is a genuinely open-minded wine. The bracket is an invitation. The customer is the co-author.",
             "correct": False},
            {"text": "The copywriter wrote it ironically and the workflow approved the irony without reading the subtext",
             "correct": False},
            {"text": "The supplier submitted this exact text and the ingest pipeline preserved it faithfully. Well done, pipeline.",
             "correct": False},
        ],
        "explanation": "Template placeholders go live when the publication workflow doesn't enforce enrichment completion. The PIM team manages over 300 DQ rules and workflow gates specifically to block products from publishing until every field is properly filled.",
    },

    {
        "tag":      "WORKFLOW",
        "gif_id":   "xvaaWS9zCp1FxhypGD",
        "question": "A product has been in 'Coming Soon' status since 2019. Nobody updated it. Nobody questioned it. It still appears in catalog searches. What failed?",
        "context":  "The product is coming. It has always been coming. It will continue to be coming. This is its journey now.",
        "options": [
            {"text": "No lifecycle rule existed to flag or expire products stuck in a non-live state beyond a set time",
             "correct": True},
            {"text": "The product is simply taking its time. Some products are on a different clock. We should respect that.",
             "correct": False},
            {"text": "The workflow has fourteen stages. Nobody owns stage three. Stage three is where products go to become philosophers.",
             "correct": False},
            {"text": "A review meeting was scheduled in 2021. The meeting was rescheduled. The rescheduled meeting was also rescheduled.",
             "correct": False},
        ],
        "explanation": "Without expiry rules or lifecycle governance, products get stuck in intermediate states indefinitely and become ghost records. The PIM team uses automated workflow escalations to surface and resolve stagnant statuses before they haunt the catalog for six years.",
    },

    {
        "tag":      "TAXONOMY & REFERENCE DATA",
        "gif_id":   "3o7aD5eEm7qVu1mpYQ",
        "question": "A supplier maps a $300 bottle of vintage Champagne to the category 'Bathroom Cleaning Products.' Wealthy customers are now deeply confused. What PIM feature was bypassed?",
        "context":  "If you let suppliers type whatever they want into a category field without validating it, they will eventually classify a keg of beer as a root vegetable. This is not a hypothetical.",
        "options": [
            {"text": "Inbound category validation against a strict master reference list — unapproved values must be rejected on ingest",
             "correct": True},
            {"text": "An automated webhook that emails the supplier to check whether they have personally tasted the Champagne",
             "correct": False},
            {"text": "An AI enrichment tool that updates the tasting notes to include 'vibrant hints of pine and bleach'",
             "correct": False},
            {"text": "Nothing is wrong. At $300, this Champagne is probably exceptional at descaling a showerhead.",
             "correct": False},
        ],
        "explanation": "Category fields must validate against a master reference taxonomy. Free-text category entry allows any value — including 'Bathroom Cleaning Products' — to slip past ingest and reach the website. Reference data validation is one of the foundational DQ rules in any PIM implementation.",
    },

]



# ═══════════════════════════════════════════════════════════════════
# DATA LAYER
# ═══════════════════════════════════════════════════════════════════
# ── UPDATE THIS to match your Google Sheet file name exactly ──────
SHEET_NAME     = "PIM_Odyssey_DB"   # ← exact file name in Google Drive
WORKSHEET_NAME = "Quiz"             # ← exact tab name inside the file
# ─────────────────────────────────────────────────────────────────

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _get_worksheet():
    creds  = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)


def db_test() -> tuple[bool, str]:
    """
    Run on the intro screen to surface the real error message.
    Returns (ok, message).
    """
    try:
        ws      = _get_worksheet()
        headers = ws.row_values(1)
        return True, f"Connected · tab '{WORKSHEET_NAME}' · headers: {headers}"
    except gspread.exceptions.SpreadsheetNotFound:
        return False, (
            f"Sheet not found: '{SHEET_NAME}'. "
            "Check the name matches exactly in Google Drive (case-sensitive)."
        )
    except gspread.exceptions.WorksheetNotFound:
        return False, (
            f"Tab not found: '{WORKSHEET_NAME}'. "
            f"Make sure a tab called exactly '{WORKSHEET_NAME}' exists inside '{SHEET_NAME}'."
        )
    except gspread.exceptions.APIError as e:
        return False, (
            f"Google API error: {e}. "
            "Most likely the service account hasn't been given Editor access to the sheet."
        )
    except KeyError:
        return False, (
            "Missing 'gcp_service_account' in Streamlit secrets. "
            "Go to App Settings → Secrets and check the block name is [gcp_service_account]."
        )
    except Exception as e:
        return False, f"Unexpected error: {type(e).__name__}: {e}"


def save_score(name: str, email: str, score: int, rank: str) -> tuple[bool, str]:
    try:
        _get_worksheet().append_row(
            [datetime.now().isoformat(timespec="seconds"), name, email, score, rank]
        )
        return True, ""
    except Exception as e:
        return False, str(e)


def fetch_all_players() -> tuple[pd.DataFrame, str]:
    """Return (dataframe, error_message). Error is empty string on success."""
    try:
        rows = _get_worksheet().get_all_values()
        if len(rows) < 2:
            return pd.DataFrame(), ""
        headers = [h.strip() for h in rows[0]]
        df      = pd.DataFrame(rows[1:], columns=headers)
        df      = df.rename(columns={"Rank": "Title"})
        if "Score" not in df.columns or "Name" not in df.columns:
            return pd.DataFrame(), (
                f"Column mismatch. Found: {list(df.columns)}. "
                "Expected: Timestamp, Name, Email, Score, Rank"
            )
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0).astype(int)
        out = (
            df.groupby("Name", as_index=False)
              .agg({"Score": "max", "Title": "first"})
              .sort_values("Score", ascending=False)
              .reset_index(drop=True)
        )
        out.index      = out.index + 1
        out.index.name = "#"
        return out, ""
    except Exception as e:
        return pd.DataFrame(), str(e)


# ═══════════════════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════════════════
def rank_for(score: int) -> str:
    pct = score / MAX_SCORE
    if pct >= 0.92: return "PIM Expert — teach this session yourself next time"
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
        "stage":         "intro",
        "name":          "",
        "email":         "",
        "score":         0,
        "correct_count": 0,
        "question_idx":  0,
        "shuffled_opts": _shuffle_opts(0),
        "last_result":   None,
        "started_at":    None,
        "saved":         False,
        "email_sent":    False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def goto(stage: str):
    st.session_state.stage = stage
    st.rerun()


def _shuffle_opts(pool_idx: int) -> list[dict]:
    """Return options in random order — correct answer position changes each run."""
    import random as _random
    opts = QUIZ_POOL[pool_idx]["options"][:]
    _random.shuffle(opts)
    return opts


def start_run(name: str, email: str):
    st.session_state.update({
        "name":          name,
        "email":         email,
        "score":         0,
        "correct_count": 0,
        "question_idx":  0,
        "shuffled_opts": _shuffle_opts(0),
        "last_result":   None,
        "started_at":    time.time(),
        "saved":         False,
        "email_sent":    False,
    })
    goto("question")


def current_question() -> dict:
    return QUIZ_POOL[st.session_state.question_idx]


# ═══════════════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════════════
def render_hud():
    q_num = st.session_state.question_idx + 1
    score = st.session_state.score
    pct   = int(((q_num - 1) / QUESTIONS_PER_PLAY) * 100)
    name  = st.session_state.name or "—"
    st.markdown(
        f'<div class="hud">'
        f'<div class="hud-cell">Question<span class="v">{q_num} / {QUESTIONS_PER_PLAY}</span></div>'
        f'<div class="hud-center">'
        f'<div class="prog-track"><div class="prog-fill" style="width:{pct}%;"></div></div>'
        f'<span class="prog-label">{pct}%</span>'
        f'</div>'
        f'<div class="hud-cell"><span class="score-badge">✦ {score}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_confetti():
    import random as _r
    colors = ["#ffd56b","#ff6bc7","#6bdfff","#5ee29c","#7b9fff","#fafaff"]
    parts  = ['<div class="confetti-container">']
    for _ in range(55):
        parts.append(
            f'<div class="confetti" style="'
            f'left:{_r.uniform(0,100)}vw;background:{_r.choice(colors)};'
            f'width:{_r.choice([7,9,11])}px;height:{_r.choice([11,15,19])}px;'
            f'animation-delay:{_r.uniform(0,2.5)}s;animation-duration:{_r.uniform(3.5,6.5)}s;'
            f'transform:rotate({_r.uniform(-180,180)}deg);"></div>'
        )
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════
def screen_intro():
    st.markdown('<div class="eyebrow">Hello, Full Stack Fury !! &nbsp;·&nbsp; EDG PIM Team</div>', unsafe_allow_html=True)
    st.markdown('<h1><span class="kinetic">How well do you know PIM?</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:var(--text-mute);font-size:1.05rem;line-height:1.7;margin-top:0.3rem;">'
        '5 questions. Same questions for everyone. Funny wrong answers, real correct ones. '
        'A recognition email lands in your inbox the moment you finish.'
        '</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="glass"><div class="card-label">How it works</div>'
        '<ul style="margin:0;padding-left:1.2rem;line-height:1.9;color:var(--text-mute);font-size:0.95rem;">'
        '<li>5 questions — identical for every player</li>'
        '<li>4 choices — one correct, three increasingly confident wrong answers</li>'
        '<li><strong style="color:var(--text);">+100 points</strong> per correct · Max: 500</li>'
        '<li>No penalty for guessing — this is a game, not a performance review</li>'
        '<li>Everyone sees everyone\'s scores at the end</li>'
        '<li>A personalised email from the PIM team lands in your inbox when you finish</li>'
        '</ul></div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(
            "Your name on the leaderboard",
            placeholder="e.g. Roshan, Mara, chaos-agent",
            max_chars=32,
            key="intro_name",
        )
    with col2:
        email = st.text_input(
            "Your work email (for the recognition certificate)",
            placeholder="name@company.com",
            max_chars=64,
            key="intro_email",
        )

    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Let's Go! 🚀"):
        if not name.strip():
            st.warning("Please enter your name.")
        elif not email.strip() or "@" not in email:
            st.warning("Please enter a valid email address.")
        else:
            start_run(name.strip(), email.strip())
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Database connection diagnostic ──────────────────────────
    with st.expander("Database connection check", expanded=False):
        ok, msg = db_test()
        if ok:
            st.success(f"Connected: {msg}")
        else:
            st.error(f"Connection failed: {msg}")
            st.caption(
                "Common fixes:\n"
                f"1. SHEET_NAME in code must match exactly: {SHEET_NAME}\n"
                f"2. Tab name must be: {WORKSHEET_NAME}\n"
                "3. Share the sheet with the service account email (Editor)\n"
                "4. Check [gcp_service_account] block in Streamlit secrets"
            )

    # ── Leaderboard preview ───────────────────────────────────────
    lb, lb_err = fetch_all_players()
    if lb_err:
        st.caption(f"Leaderboard unavailable: {lb_err}")
    elif not lb.empty:
        st.markdown('<div class="card-label" style="margin-top:2.5rem;">Current standings</div>', unsafe_allow_html=True)
        st.dataframe(lb, use_container_width=True)


def screen_question():
    render_hud()
    q    = current_question()
    opts = st.session_state.shuffled_opts

    # GIF above question
    gif_id = q.get("gif_id", "")
    if gif_id:
        gif_url = f"https://media.giphy.com/media/{gif_id}/giphy.gif"
        st.markdown(
            f'<div style="text-align:center;margin-bottom:0.8rem;">'
            f'<img src="{gif_url}" style="height:180px;max-width:100%;border-radius:12px;'
            f'object-fit:cover;border:1px solid rgba(255,255,255,0.12);"/>'
            f'</div>',
            unsafe_allow_html=True,
        )

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
            correct    = opt["correct"]
            right_text = next(o["text"] for o in opts if o["correct"])
            if correct:
                st.session_state.score         += POINTS_PER_CORRECT
                st.session_state.correct_count += 1
            st.session_state.last_result = {
                "correct":     correct,
                "chosen":      opt["text"],
                "right":       right_text,
                "explanation": q["explanation"],
                "points":      POINTS_PER_CORRECT if correct else 0,
            }
            goto("result")


def screen_result():
    r = st.session_state.last_result
    if r is None:
        goto("question")
        return

    render_hud()

    cls         = "correct" if r["correct"] else "wrong"
    verdict     = "✓  Correct" if r["correct"] else "✗  Not quite"
    chosen_line = (f'You chose: {r["chosen"]}'
                   if r["correct"] else
                   f'You chose: {r["chosen"]}<br>Correct answer: {r["right"]}')
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
        if st.button("See the final results"):
            st.session_state.last_result = None
            goto("end")
    else:
        nxt = st.session_state.question_idx + 2
        if st.button(f"Next question  ({nxt} of {QUESTIONS_PER_PLAY})"):
            st.session_state.question_idx += 1
            st.session_state.shuffled_opts = _shuffle_opts(st.session_state.question_idx)
            st.session_state.last_result   = None
            goto("question")
    st.markdown('</div>', unsafe_allow_html=True)


def screen_end():
    score   = st.session_state.score
    correct = st.session_state.correct_count
    name    = st.session_state.name  or "anonymous"
    email   = st.session_state.email or ""
    rank    = rank_for(score)
    elapsed = int(time.time() - st.session_state.started_at) if st.session_state.started_at else 0
    pct     = int(score / MAX_SCORE * 100)

    if pct >= 60:
        render_confetti()

    # Personal banner
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
    with c1: st.markdown(f'<div class="stat"><div class="stat-label">Score</div><div class="stat-value" style="color:var(--cyan);">{score}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat"><div class="stat-label">Correct</div><div class="stat-value">{correct}/{QUESTIONS_PER_PLAY}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat"><div class="stat-label">Time</div><div class="stat-value">{elapsed//60}m {elapsed%60:02d}s</div></div>', unsafe_allow_html=True)

    # Save score once — show error if it fails
    if not st.session_state.saved:
        save_ok, save_err = save_score(name, email, score, rank)
        st.session_state.saved = True
        if not save_ok:
            st.warning(
                f"Score could not be saved to leaderboard: {save_err}  \n"
                "Check the database connection expander on the intro screen."
            )

    # Email is handled by Google Apps Script watching the sheet.
    # Show a friendly notice once per session.
    if not st.session_state.email_sent and email:
        st.session_state.email_sent = True
        st.markdown(
            f'<div class="email-sent">'
            f'✉ A recognition email will be on its way to {email} shortly — sent automatically by the PIM team.' 
            f'</div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.email_sent and email:
        st.markdown(
            f'<div class="email-sent">✉ Recognition email on its way to {email}</div>',
            unsafe_allow_html=True,
        )

    # ── ALL PLAYERS RESULTS ──────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="card-label">Everyone\'s results</div>', unsafe_allow_html=True)
    st.caption("This table shows all players — refresh to see new completions as your teammates finish.")

    lb, lb_err = fetch_all_players()
    if lb_err:
        st.warning(f"Could not load leaderboard: {lb_err}")
    elif lb.empty:
        st.caption("No scores yet — you are the first!")
    else:
        st.dataframe(lb, use_container_width=True)

    # Play again — resets everything, returns to intro
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Play again"):
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════
def main():
    import random  # noqa — needed here for reproducible shuffle seeding
    st.markdown(STYLE, unsafe_allow_html=True)
    init_state()
    stage = st.session_state.stage
    if   stage == "intro":    screen_intro()
    elif stage == "question": screen_question()
    elif stage == "result":   screen_result()
    elif stage == "end":      screen_end()
    else: goto("intro")


main()
