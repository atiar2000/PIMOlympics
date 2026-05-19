"""
PIM Play
by EDG PIM Team

Pre-presentation quiz. 12 questions .
Topics: product data, data quality, Dan Murphy's, BWS, Marketplace,
        and things that have gone spectacularly wrong in PIM catalogs.

No penalty for wrong answers. Just contribute and a leaderboard.

Requires: Google Sheet tab named for leaderboard "Quiz"
          Row 1 headers: Timestamp | Name | Score | Rank
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
QUESTIONS_PER_PLAY = 12
POINTS_PER_CORRECT = 100

st.set_page_config(
    page_title="PIM Knowledge Check",
    page_icon="🍔",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ═══════════════════════════════════════════════════════════════════
# STYLES — same aurora + glassmorphism, quiz blue/cyan accent
# ═══════════════════════════════════════════════════════════════════
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-base:     #1a1d40;
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
    --correct-soft:rgba(94, 226, 156, 0.15);
    --wrong-soft:  rgba(255, 102, 128, 0.15);
    --quiz-accent: #7b9fff;
    --quiz-soft:   rgba(123, 159, 255, 0.16);
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
    0%   { transform: translate(0,0) scale(1) rotate(0deg); }
    25%  { transform: translate(-4%,3%) scale(1.07) rotate(2deg); }
    50%  { transform: translate(3%,-4%) scale(0.95) rotate(-2deg); }
    75%  { transform: translate(-2%,-3%) scale(1.09) rotate(1.5deg); }
    100% { transform: translate(2%,2%) scale(1.01) rotate(-1deg); }
}
.main, .block-container { position: relative; z-index: 1; }

html, body, .main, [class*="css"], p, span, div, label, li {
    font-family: 'Inter', -apple-system, system-ui, sans-serif !important;
    color: var(--text);
}
code, .mono { font-family: 'JetBrains Mono', monospace !important; }
.main .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 780px; }
h1 { font-size: 2.2rem !important; font-weight: 800 !important; letter-spacing: -0.03em !important; line-height: 1.1 !important; margin-bottom: 0.5rem !important; }

.kinetic {
    background: linear-gradient(120deg, var(--cyan), var(--blue), var(--pink), var(--cyan));
    background-size: 300% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shift 5s ease-in-out infinite;
}
@keyframes shift { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }

.eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem; color: var(--cyan);
    text-transform: uppercase; letter-spacing: 0.18em;
    font-weight: 600; margin-bottom: 0.5rem;
    animation: rise 0.6s ease-out;
}
@keyframes rise {
    0%   { opacity:0; transform:translateY(24px) scale(0.96); }
    60%  { opacity:1; transform:translateY(-4px) scale(1.01); }
    100% { opacity:1; transform:translateY(0) scale(1); }
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

.hud {
    display: grid; grid-template-columns: auto 1fr auto;
    align-items: center; gap: 1.4rem;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 0.9rem 1.3rem; margin-bottom: 1.4rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    animation: rise 0.5s cubic-bezier(0.34,1.4,0.5,1);
}
.hud-cell { font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: var(--text-mute); letter-spacing: 0.08em; text-transform: uppercase; }
.hud-cell .v { color: var(--text); font-weight: 700; font-size: 0.95rem; margin-left: 5px; }
.hud-center { display: flex; align-items: center; gap: 1rem; justify-content: center; }

.prog-track { width: 200px; height: 10px; background: rgba(0,0,0,0.45); border: 1px solid var(--border); border-radius: 5px; overflow: hidden; }
.prog-fill {
    height: 100%; border-radius: 4px;
    background: linear-gradient(90deg, var(--cyan), var(--blue));
    transition: width 0.6s cubic-bezier(0.34,1.3,0.55,1);
    position: relative;
}
.prog-fill::after {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,0.28) 50%, transparent 70%);
    animation: shimmer 2s linear infinite;
}
@keyframes shimmer { 0% { transform:translateX(-150%); } 100% { transform:translateX(150%); } }
.prog-label { font-family:'JetBrains Mono',monospace; font-size:0.82rem; font-weight:700; color:var(--cyan); white-space:nowrap; }

.score-badge {
    font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:700;
    color:var(--gold); background:rgba(255,213,107,0.12);
    border:1px solid rgba(255,213,107,0.35); border-radius:8px;
    padding:4px 14px; letter-spacing:0.02em;
    animation: score-pop 0.4s cubic-bezier(0.34,1.5,0.55,1);
}
@keyframes score-pop { 0%{transform:scale(0.85);opacity:0.6;} 100%{transform:scale(1);opacity:1;} }

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
    display: inline-block; font-family:'JetBrains Mono',monospace;
    font-size:0.74rem; font-weight:700; color:var(--quiz-accent);
    background:var(--quiz-soft); border:1px solid rgba(123,159,255,0.42);
    border-radius:6px; padding:4px 11px; margin-bottom:0.9rem;
    letter-spacing:0.14em; animation:q-pulse 2.4s ease-out infinite;
}
@keyframes q-pulse {
    0%   {box-shadow:0 0 0 0   rgba(123,159,255,0.55);}
    70%  {box-shadow:0 0 0 9px rgba(123,159,255,0);}
    100% {box-shadow:0 0 0 0   rgba(123,159,255,0);}
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
.stButton button:active { transform:translateY(-1px) scale(1) !important; transition-duration:0.07s !important; }

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

.result-panel {
    border-radius:16px; padding:1.6rem 1.8rem; margin:1rem 0;
    backdrop-filter:blur(24px) saturate(160%);
    -webkit-backdrop-filter:blur(24px) saturate(160%);
    animation:rise 0.55s cubic-bezier(0.34,1.4,0.5,1);
}
.result-panel.correct {
    background:var(--surface);
    border:1.5px solid rgba(94,226,156,0.45);
    box-shadow:0 0 0 1px rgba(94,226,156,0.1) inset, 0 20px 50px -20px rgba(94,226,156,0.22);
}
.result-panel.wrong {
    background:var(--surface);
    border:1.5px solid rgba(255,102,128,0.45);
    box-shadow:0 0 0 1px rgba(255,102,128,0.1) inset, 0 20px 50px -20px rgba(255,102,128,0.18);
}
.result-verdict { font-family:'JetBrains Mono',monospace; font-size:0.84rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:0.75rem; }
.result-verdict.correct { color:var(--green); }
.result-verdict.wrong   { color:var(--danger); }
.result-answer { font-size:0.95rem; color:var(--text-mute); margin-bottom:0.8rem; font-style:italic; padding-left:1rem; border-left:3px solid var(--border-hi); line-height:1.5; }
.result-explain { color:var(--text); font-size:1.02rem; line-height:1.7; margin-bottom:0.9rem; }
.result-points { display:inline-block; font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:700; padding:6px 14px; border-radius:7px; }
.result-points.earned  { color:var(--green);  background:var(--correct-soft); border:1px solid rgba(94,226,156,0.4); }
.result-points.nothing { color:var(--danger); background:var(--wrong-soft);   border:1px solid rgba(255,102,128,0.4); }

.banner {
    border-radius:18px; padding:2.4rem 1.8rem; text-align:center; margin-bottom:1.4rem;
    backdrop-filter:blur(24px) saturate(160%);
    -webkit-backdrop-filter:blur(24px) saturate(160%);
    border:1.5px solid rgba(107,223,255,0.45);
    background:linear-gradient(160deg, rgba(123,159,255,0.18) 0%, rgba(107,223,255,0.1) 50%, var(--surface) 100%);
    animation:rise 0.8s cubic-bezier(0.34,1.4,0.5,1);
}
.banner .glyph { font-size:3.2rem; margin-bottom:0.5rem; line-height:1; }
.banner .name-line { font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:var(--gold); letter-spacing:0.14em; text-transform:uppercase; margin-bottom:0.5rem; font-weight:700; }
.banner .title  { font-size:1.85rem; font-weight:800; color:var(--text); margin-bottom:0.6rem; letter-spacing:-0.025em; line-height:1.15; }
.banner .subtitle { color:var(--text-mute); font-size:1rem; line-height:1.65; max-width:500px; margin:0 auto; }

.stat { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:1.1rem 1.2rem; text-align:center; backdrop-filter:blur(24px) saturate(160%); -webkit-backdrop-filter:blur(24px) saturate(160%); transition:border-color 0.25s ease, transform 0.25s ease; animation:rise 0.5s cubic-bezier(0.34,1.4,0.5,1) backwards; }
.stat:hover { border-color:var(--border-hi); transform:translateY(-4px); }
.stat:nth-of-type(1){animation-delay:0.05s;} .stat:nth-of-type(2){animation-delay:0.12s;} .stat:nth-of-type(3){animation-delay:0.19s;}
.stat .stat-label { font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:var(--text-mute); letter-spacing:0.14em; text-transform:uppercase; margin-bottom:0.5rem; font-weight:600; }
.stat .stat-value { font-family:'JetBrains Mono',monospace; font-size:1.8rem; font-weight:800; color:var(--text); letter-spacing:-0.02em; }
.stat .stat-value.small { font-size:1rem; line-height:1.35; }

.confetti-container { position:fixed; inset:0; pointer-events:none; z-index:999; overflow:hidden; }
.confetti { position:absolute; top:-30px; border-radius:2px; opacity:0.95; animation:confetti-fall 5s linear forwards; }
@keyframes confetti-fall { 0%{transform:translateY(0) rotate(0deg);opacity:1;} 100%{transform:translateY(110vh) rotate(900deg);opacity:0;} }

.stTextInput input { background:var(--surface-2) !important; color:var(--text) !important; border:1px solid var(--border-hi) !important; border-radius:10px !important; font-size:1rem !important; padding:0.8rem 1rem !important; backdrop-filter:blur(14px); transition:border-color 0.25s ease, box-shadow 0.25s ease !important; }
.stTextInput input:focus { border-color:var(--cyan) !important; box-shadow:0 0 0 5px rgba(107,223,255,0.15) !important; outline:none !important; }
.stTextInput input::placeholder { color:var(--text-dim) !important; }
.stTextInput label { color:var(--text-mute) !important; font-size:0.88rem !important; font-weight:600 !important; }

[data-testid="stDataFrame"] { background:var(--surface); border:1px solid var(--border); border-radius:14px; overflow:hidden; backdrop-filter:blur(20px); transition:border-color 0.25s ease; }
[data-testid="stDataFrame"]:hover { border-color:var(--border-hi); }

hr { border-color:var(--border) !important; margin:2rem 0 !important; }
#MainMenu, footer, header { visibility:hidden; }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:0.01ms !important; transition-duration:0.01ms !important; } }
</style>
"""


# ═══════════════════════════════════════════════════════════════════
# QUESTION POOL — 12 Questions per play
# ═══════════════════════════════════════════════════════════════════
QUIZ_POOL = [

    # ── Q1 ───────────────────────────────────────────────────────
    {
        "tag": "PRODUCT DATA",
        "gif_id": "3zhxq2ttgN6rEw8SDx",
        "question": "A product on the Dan Murphy's website has no image. Just a grey box. A customer calls and asks what the bottle looks like. What was missing from the catalog?",
        "context": "Ana spotted fourteen of these during her morning audit. Ana has a very organised morning audit.",
        "options": [
            {"text": "A mandatory image DQ rule that blocks products from going live without a photo",
             "correct": True},
            {"text": "A customer willing to buy a grey rectangle for £45 — which, to be fair, three of them did",
             "correct": False},
            {"text": "A grey box is technically an image — the validator was satisfied",
             "correct": False},
            {"text": "Ana flagged this three weeks ago in Confluence — the report is still open",
             "correct": False},
        ],
        "explanation": "Blank listings frustrate customers who expect to see what they are buying. The PIM team sets mandatory image rules to block incomplete products from ever reaching live channels.",
    },

    # ── Q2 ───────────────────────────────────────────────────────
    {
        "tag": "PRODUCT DATA",
        "gif_id": "3jbR27OLT5YJv0ewvN",
        "question": "A product description reads: 'Lorem ipsum dolor sit amet consectetur adipiscing elit.' It has been live on the website for six weeks. Twelve people bought it. What happened?",
        "context": "The twelve customers have not complained. Two left five-star reviews. The reviews do not mention the description.",
        "options": [
            {"text": "A placeholder description was published without being replaced — the field was non-empty so it passed the mandatory check",
             "correct": True},
            {"text": "It is a premium Latin-language product for a very specific market segment",
             "correct": False},
            {"text": "ShiChang's translation pipeline mistakenly converted English into Lorem",
             "correct": False},
            {"text": "The copywriter submitted it ironically and the workflow approved it without reading",
             "correct": False},
        ],
        "explanation": "'Lorem ipsum' passes basic field checks but fails content quality. The PIM team applies strict language and placeholder validation to ensure real product data.",
    },

    # ── Q3 ───────────────────────────────────────────────────────
    {
        "tag": "ASSET VALIDATION",
        "gif_id": "YmszCwM1FV7zCI8sgL",
        "question": "A customer clicks on a premium whiskey product. The image shown is a bottle of dishwashing liquid. Both smell vaguely of lemon. The website sees no problem. What went wrong?",
        "context": "Vincy uploaded a batch of images in 2019. Vincy has been asked about this. Vincy is not saying.",
        "options": [
            {"text": "An image was mapped to the wrong product during a bulk upload — no image-content validation existed to catch the mismatch",
             "correct": True},
            {"text": "The whiskey and dishwashing liquid share the same SKU prefix, which confused the asset system",
             "correct": False},
            {"text": "The CDN cached the dishwashing liquid image and now believes it has always been correct",
             "correct": False},
            {"text": "Both products are technically liquids and both have a citrus note. The validator was thorough in its own way.",
             "correct": False},
        ],
        "explanation": "Image-to-product validation requires content analysis — checking that the image corresponds to the product's category. Without this, a wrong file selected during a bulk upload goes live and nobody catches it until a customer notices the lemon-scented whiskey. The PIM team ensures IDQ logic that media assts are verified and approved by human utilizing Vertex-AI and Tooljet.",
    },

    # ── Q4 ───────────────────────────────────────────────────────
    {
        "tag": "ENRICHMENT",
        "gif_id": "1UUZFXZteyHOrxaUeT",
        "question": "A wine description on the live website says: 'This wine pairs beautifully with [INSERT FOOD PAIRING HERE].' How did this happen?",
        "context": "Chien's enrichment workflow had a timeout at exactly the wrong moment. Chien does not know this yet.",
        "options": [
            {"text": "The product was published before enrichment was complete — the template placeholder was never replaced",
             "correct": True},
            {"text": "It is a very inclusive wine. The bracket is a feature. The bracket invites the customer into a collaborative content experience.",
             "correct": False},
            {"text": "The copywriter meant to write the pairing, got distracted, and the workflow approved the draft",
             "correct": False},
            {"text": "The supplier submitted this text and the ingest pipeline preserved it faithfully — well done, pipeline",
             "correct": False},
        ],
        "explanation": " Unfinished template placeholders can easily slip into live catalogs. The PIM team manages over 300 Data Quality rules and complex workflows to block publication until enrichment is complete.",
    },

    # ── Q5 ───────────────────────────────────────────────────────
    {
        "tag": "FRONTEND + PIM",
        "gif_id": "j6NxNqo8Cs8y9aZwco",
        "question": "The PIM API returns `null` for a product name field. The website displays the word 'null' as the product name on the homepage. Forty-seven people search for 'null.' Three add it to cart. What is the actual technical bug?",
        "context": "This is the sequel to a similar incident involving a product named NULL. Same genre. Different channel. Same energy.",
        "options": [
            {"text": "The frontend renders the API value literally instead of handling null gracefully with a fallback or placeholder",
             "correct": True},
            {"text": "'null' is a valid product name and those forty-seven customers have excellent and specific taste",
             "correct": False},
            {"text": "The PIM returned null correctly — this is entirely a frontend problem and has nothing to do with PIM",
             "correct": False},
            {"text": "The PIM team is responsible for this — the frontend rendered exactly what it received and should be congratulated for its literal accuracy",
             "correct": False},
        ],
        "explanation": "Downstream apps shouldn't render missing data as the literal text 'null'. The PIM team stops this at the source using completeness rules so channels only get fully populated payloads.",
    },

    # ── Q6 ───────────────────────────────────────────────────────
    {
        "tag": "REFERENCE DATA",
        "gif_id": "LO9E1dwHFgeipxKWn3",
        "question": "A product's category is set to 'Cleaning Products.' The product is a Grenache. A customer emails asking if it is safe to drink. The customer is joking. The catalog is not joking. What caused this?",
        "context": "Abhilash's pipeline moved the data faithfully from one system to another. The source system had an interesting data entry.",
        "options": [
            {"text": "The category field accepted free text instead of validating against a list of approved categories",
             "correct": True},
            {"text": "A robust Grenache can theoretically clean surfaces — an edge case the DQ team had not considered",
             "correct": False},
            {"text": "Abhilash's pipeline mapped the fields correctly — the error was upstream",
             "correct": False},
            {"text": "A developer who had never heard of Grenache made a reasonable assumption",
             "correct": False},
        ],
        "explanation": "Categories must match an approved master list to prevent mapping errors. The PIM team maintains strict reference taxonomies so bad categories get rejected on ingest.",
    },

    # ── Q7 ───────────────────────────────────────────────────────
    {
        "tag": "WORKFLOW",
        "gif_id": "xvaaWS9zCp1FxhypGD",
        "question": "A product has been in 'Coming Soon' status since 2019. Nobody updated it. Nobody questioned it. It appears in catalog searches. What failed?",
        "context": "The product is coming. It is just taking its time. It has been taking its time for six years.",
        "options": [
            {"text": "No lifecycle rule existed to flag or expire products stuck in a non-live state beyond a reasonable time",
             "correct": True},
            {"text": "The product is coming. It has been coming since 2019. It will continue coming. This is its journey now, and who are we to question a journey.",
             "correct": False},
            {"text": "The workflow has fourteen stages and nobody owns stage three, which is where it stopped",
             "correct": False},
            {"text": "Mark (DL) scheduled a review meeting for this product in 2021. The meeting was rescheduled. Twice.",
             "correct": False},
        ],
        "explanation": "Products stuck in 'Coming Soon' become ghost records without expiry rules. The PIM application's automated workflows help the team proactively escalate and fix stagnant statuses",
    },

    # ── Q8 ───────────────────────────────────────────────────────
    {
        "tag": "DATA QUALITY",
        "gif_id": "l4FGt5wmYS9z2GK6A",
        "question": "A product's ABV field says 'yes.' The legal team would like a word. What type of DQ rule was missing?",
        "context": "The supplier was asked to confirm the ABV. They confirmed. The pipeline faithfully recorded the confirmation.",
        "options": [
            {"text": "A numeric type validation rule — ABV must be a decimal number between 0 and 100",
             "correct": True},
            {"text": "A politeness filter — 'yes' is at least a positive and encouraging response",
             "correct": False},
            {"text": "A spell checker — 'yes' is spelled correctly and the validator had no further questions",
             "correct": False},
            {"text": "A follow-up to the supplier asking whether 'yes' refers to the alcohol percentage or their general enthusiasm for being a supplier",
             "correct": False},
        ],
        "explanation": "'Yes' isn't a valid decimal for alcohol by volume (ABV). The PIM team enforces strict data-typing rules to reject invalid manual entries from supplier feeds.",
    },

    # ── Q9 ───────────────────────────────────────────────────────
    {
        "tag": "DATA QUALITY",
        "gif_id": "ykSV717QxGYBA1nMvE",
        "question": "A wine's vintage year field says '2099.' Either the supplier invented time travel or someone mistyped. Which DQ rule catches this?",
        "context": "Yang spotted this in the monitoring dashboard and described it as 'interesting.' Yang's expressions cover a very wide range.",
        "options": [
            {"text": "A date range validation — vintage must fall between a reasonable historical year and the current year",
             "correct": True},
            {"text": "A spell checker — 2099 is a perfectly valid number and the validator saw nothing unusual",
             "correct": False},
            {"text": "Common sense — but common sense cannot be configured in a DQ rule builder",
             "correct": False},
            {"text": "Yang's weekly pipeline health check — Yang had not run it this week yet",
             "correct": False},
        ],
        "explanation": "Range validation prevents impossible data, like a vintage year from the future. The PIM system uses dynamic range rules to automatically block typos and time-traveling suppliers. (In-Progress Work)",
    },

    # ── Q10 ──────────────────────────────────────────────────────
    {
        "tag": "UNIT NORMALIZATION",
        "gif_id": "eqNSqDeR52QvxiGBGG",
        "question": "You order a '750ml' bottle of wine online. It arrives. The bottle says '75cl.' You call to report the wrong size was delivered. Were you sent the wrong size?",
        "context": "The customer is very confident they were wronged. The customer is also wrong about being wronged.",
        "options": [
            {"text": "No — 750ml and 75cl are identical. 1 centilitre equals 10 millilitres.",
             "correct": True},
            {"text": "Yes — the website said 750ml and the bottle clearly says 75cl. These are not the same number. The customer knows what the same number looks like.",
             "correct": False},
            {"text": "It depends on whether the website and the warehouse use the same unit system, which they probably do not",
             "correct": False},
            {"text": "This is a philosophical question about whether units define reality, and the answer is complicated",
             "correct": False},
        ],
        "explanation": "Suppliers submit mixed units (75cl vs 750ml) causing messy displays. The PIM team builds automated unit conversions so customer-facing volumes are always uniform.",
    },

    # ── Q11 ──────────────────────────────────────────────────────
    {
        "tag": "PRODUCT ATTRIBUTES",
        "gif_id": "b627RgxQUs5KspGD53",
        "question": "A product has been called 'Limited Edition' for five years. Two hundred thousand units have sold. The tag still says 'Limited Edition.' What field is lying?",
        "context": "Mara updated this once. The system reverted it. Mara does not talk about this.",
        "options": [
            {"text": "The 'Limited Edition' attribute — which needs either an expiry date or a maximum quantity threshold attached to it",
             "correct": True},
            {"text": "None — two hundred thousand is technically limited relative to infinity, so the tag is defensible",
             "correct": False},
            {"text": "The stock count — surely this product should be out of stock by now",
             "correct": False},
            {"text": "The product launch date — without it the system cannot calculate that five years have passed",
             "correct": False},
        ],
        "explanation": "'Limited Edition' tags shouldn't last forever. The PIM application uses dynamic expiry rules to automatically strip outdated marketing labels once stock thresholds are met. (Currently managed through Trader)",
    },

    # ── Q12 ──────────────────────────────────────────────────────
    {
        "tag": "ASSET CONTENT",
        "gif_id": "AlGHT3axauYhVPety0",
        "question": "A premium champagne product page shows a stock photo of a vineyard. The product is a gin. A beautifully photographed vineyard. For a gin. What validation was missing?",
        "context": "The image is genuinely gorgeous. The gin is genuinely a gin. These facts are unrelated and yet somehow the same listing.",
        "options": [
            {"text": "Image-category content validation — checking the image content matches the product's category before approval",
             "correct": True},
            {"text": "A rule preventing gins from using aspirational imagery — very niche, but arguably necessary",
             "correct": False},
            {"text": "Vincy ran a batch image upload. The vineyard was in the batch. Nobody asked questions.",
             "correct": False},
            {"text": "Nothing — the champagne might have sold better with this image, so it worked out",
             "correct": False},
        ],
        "explanation": "Image validation checks both file quality and whether the picture matches the product. The PIM team uses automated Vertex AI-based content checks and human approvals to stop mismatched images from going live.",
    },

    # ── Q13 ──────────────────────────────────────────────────────
    {
        "tag": "MANDATORY FIELDS",
        "gif_id": "ToMjGpNuOksUiclTp4c",
        "question": "A product review says: 'I don't know what this product is. The description is empty and the image is a question mark. Five stars because the price was right.' What TWO things were missing from the catalog?",
        "context": "The customer gave five stars. The catalog did not give the customer anything to work with. This is a balanced outcome.",
        "options": [
            {"text": "A mandatory description DQ rule AND a mandatory image DQ rule — both required before a product can go live",
             "correct": True},
            {"text": "A review moderation system — this review should not have been approved",
             "correct": False},
            {"text": "A product that makes sense — the customer cannot be held responsible for their confusion",
             "correct": False},
            {"text": "Ana's morning audit — Ana would have caught both within fifteen minutes of the product going live",
             "correct": False},
        ],
        "explanation": "Customers need more than just a price to make a purchase. The PIM team designs workflow completion gates to ensure every product has a real description and valid image.",
    },

    # ── Q14 ──────────────────────────────────────────────────────
    {
        "tag": "PRODUCT LIFECYCLE",
        "gif_id": "3ornjSZp9jUtEFlsL6",
        "question": "A product has eleven five-star reviews and has been on sale for three years. It is still tagged as 'New Arrival.' What field was never updated?",
        "context": "Yang runs a weekly tag audit. This product survives the audit every time. Yang finds this personally interesting.",
        "options": [
            {"text": "The product lifecycle tag — 'New Arrival' should auto-expire after a configured number of days",
             "correct": True},
            {"text": "The review count — clearly this is not new if it has eleven reviews",
             "correct": False},
            {"text": "The launch date — without it the system cannot calculate how long the product has existed",
             "correct": False},
            {"text": "Nothing — 'New Arrival' is a relative concept and this product is new to someone, somewhere",
             "correct": False},
        ],
        "explanation": "'New Arrival' badges become misleading if left up for years. The PIM team could manage that through an Attribute but currently Its managed by PDT team manually on Trader",
    },

    # ── Q15 ──────────────────────────────────────────────────────
    {
        "tag": "LOCALIZATION",
        "gif_id": "3o7TKxCX1CMPsUBE3e",
        "question": "A product description is entirely in German. It is on the English Dan Murphy's website. Fourteen people bought it. Nobody noticed for two weeks. What data rule was missing?",
        "context": "ShiChang's translation pipeline processed everything except this one product. ShiChang knows why. ShiChang has not been asked.",
        "options": [
            {"text": "A language detection validation — descriptions must match the target channel's configured locale",
             "correct": True},
            {"text": "A team member who speaks German and checks every product description personally",
             "correct": False},
            {"text": "Nothing — the fourteen buyers presumably speak German, so the listing served them correctly",
             "correct": False},
            {"text": "ShiChang's translation pipeline should have caught it — it catches everything else",
             "correct": False},
        ],
        "explanation": "Supplier feeds in the wrong language ruin the customer experience. The PIM application uses locale-specific validation to ensure content always matches the target region.",
    },

    # ═══════════════════════════════════════════════════════════════
    # TECHNICAL / DEVELOPER QUESTIONS
    # ═══════════════════════════════════════════════════════════════

    # ── T1 ───────────────────────────────────────────────────────
    {
        "tag": "DEVELOPER MOMENT",
        "gif_id": "Rf1J48VguE4wZpQi83",
        "question": "A developer hardcodes the product category as 'Wine' for all products to quickly fix a display bug. Beer, spirits, and RTD are now all categorised as Wine on the website. Filtering by 'Beer' returns zero results. What kind of fix is this?",
        "context": "Roshan has a document titled 'Things We Do Not Hardcode In Production.' It has twelve bullet points. This is now thirteen.",
        "options": [
            {"text": "A patch that fixed one thing by silently breaking three others — deployed without a staging test or code review",
             "correct": True},
            {"text": "A bold product strategy — everything is wine now, and that is a vision",
             "correct": False},
            {"text": "A temporary fix that will be removed later — it is always temporary, it is never removed",
             "correct": False},
            {"text": "Roshan's nightmare — Roshan has read about this exact scenario. Roshan wrote the document about it.",
             "correct": False},
        ],
        "explanation": "Hardcoded data causes silent failures and requires developer deploys to fix. The PIM acts as a dynamic source of truth, letting business users update categories instantly.",
    },

    # ── T2 ───────────────────────────────────────────────────────
    {
        "tag": "DEVELOPER MOMENT",
        "gif_id": "l0HlCV8U15grrbVaU",
        "question": "A webhook that sends product updates to the website fails silently. No errors are thrown. The website shows product data from three weeks ago. Sales keep coming in. How should this have been detected sooner?",
        "context": "Danish's Azure monitoring dashboard was configured. The alerts were set up. They went to a shared inbox that nobody opened since March.",
        "options": [
            {"text": "A monitoring alert that fires when no webhook events are received for more than 30 minutes",
             "correct": True},
            {"text": "A very attentive customer — they notice these things before the engineering team does, always",
             "correct": False},
            {"text": "Danish's Azure monitoring — it exists, it was configured, the inbox was not checked",
             "correct": False},
            {"text": "A morning standup question: 'did anything silently break overnight?' — not automated but not a bad idea",
             "correct": False},
        ],
        "explanation": "Silent failures (like stopped webhooks) are much worse than loud errors. The PIM team configures proactive health checks to monitor for missing events, not just error messages.",
    },

    # ── T3 ───────────────────────────────────────────────────────
    {
        "tag": "AI IN THE WILD",
        "gif_id": "pIRO4qpUFc2y9zRg2X",
        "question": "An AI-generated product description reads: 'As an AI language model, I cannot personally taste wine, but this Shiraz is reportedly excellent.' It is live on the Dan Murphy's homepage. What should have caught this?",
        "context": "Aparna has a proofreading checklist. The checklist exists. It was not consulted before this product went live.",
        "options": [
            {"text": "A human review step in the enrichment workflow before any AI-generated content is published",
             "correct": True},
            {"text": "An AI that can actually taste wine — it is coming, but it is not in the current sprint",
             "correct": False},
            {"text": "A text filter blocking the phrase 'As an AI language model' — this specific phrase has caused more incidents than people admit",
             "correct": False},
            {"text": "Aparna's proofreading checklist — it applies here, it was not consulted, Aparna is aware",
             "correct": False},
        ],
        "explanation": "AI-generated content can include rogue disclaimers or hallucinations. The PIM team enforces mandatory 'human-in-the-loop' workflow gates to review AI copy before publishing. (Work in-Progress)",
    },

    # ── T4 ───────────────────────────────────────────────────────
    {
        "tag": "MONITORING",
        "gif_id": "WCUJ1NOisNj3YxXhaE",
        "question": "The daily DQ report shows zero errors. Every product passes perfectly. A developer checks the logs — the DQ engine has not run in two weeks. It is reporting from a cached result set to never expire. What does this situation demonstrate?",
        "context": "Zero errors is the best possible outcome. Zero errors because the check is not running is a different kind of outcome.",
        "options": [
            {"text": "That you need to monitor your monitoring — the absence of errors should itself be alertable",
             "correct": True},
            {"text": "That zero errors means everything is fine — this is generally how zero errors works",
             "correct": False},
            {"text": "That the cache is working perfectly, which is technically a win in this situation",
             "correct": False},
            {"text": "That whoever set the cache TTL to 'never' should write a post-mortem addressed to themselves",
             "correct": False},
        ],
        "explanation": "A dashboard with zero errors is dangerous if the engine simply stopped running. The PIM team monitors system health to ensure data quality checks are actually executing daily.",
    },

    # ── T5 ───────────────────────────────────────────────────────
    {
        "tag": "WORKFLOW DESIGN",
        "gif_id": "7vAhGb4iAEMiBOROSQ",
        "question": "A Product 360 workflow has 14 steps. Step 8 requires approval from a team member who left 18 months ago. Two hundred products are stuck waiting for their ghost approval. What is the correct fix?",
        "context": "The former team member's account is still active in the system. The system misses them. The two hundred products miss them more.",
        "options": [
            {"text": "Reassign the workflow step to an active team member in the workflow configuration",
             "correct": True},
            {"text": "Email the former team member on their personal address and see what happens",
             "correct": False},
            {"text": "Skip step 8. It has been 18 months. Step 8 has not been missed. Step 8 does not know it is missed.",
             "correct": False},
            {"text": "Roshan uses admin access to clear the backlog, documents every action thoroughly, and calls it governance",
             "correct": False},
        ],
        "explanation": "Assigning workflows to individuals causes bottlenecks when people leave. The PIM team uses Role-Based Access Control (RBAC) so approvals seamlessly outlive individual team members.",
    },

    # ── T6 ───────────────────────────────────────────────────────
    {
        "tag": "PRODUCTION INCIDENT",
        "gif_id": "l41JS0g6UPOoKV7Z6",
        "question": "A developer writes a script to bulk-update 50,000 product descriptions to the word 'test'. They run it in production instead of staging. 50,000 products now say 'test'. What should have been in place?",
        "context": "Yang's review process exists for exactly this reason. This script was not reviewed by Yang. Yang was not consulted. Yang is aware.",
        "options": [
            {"text": "A staging environment, a dry-run mode that previews affected records, and a confirmation step before execution",
             "correct": True},
            {"text": "A developer with better habits — they are very aware of this now, personally and professionally",
             "correct": False},
            {"text": "A database backup from before the script ran — there is one, from last Tuesday, which is mostly helpful",
             "correct": False},
            {"text": "Yang's review — Yang reviews everything before it runs in production. Except this. This one time.",
             "correct": False},
        ],
        "explanation": "Blind bulk operations in production are a recipe for disaster. The PIM team uses sandbox environments and dry-runs to safely validate mass updates before committing them.",
    },

    # ── T7 ───────────────────────────────────────────────────────
    
    {
    "tag": "TAXONOMY & REFERENCE DATA",
        "gif_id": "3o7aD5eEm7qVu1mpYQ",
    "question": "A supplier's data feed maps a prestigious $300 bottle of vintage Champagne to the category 'Bathroom Cleaning Products.' The system happily accepts it, and now wealthy customers are very confused about how to scrub their toilets. What PIM feature was bypassed?",
    "context": "If you let external suppliers type whatever they want into a category column without checking it, they will eventually classify a keg of beer as a root vegetable.",
    "options": [
        {
            "text": "Validating inbound categories against a strict, predefined master reference list so unapproved values are rejected on ingest.",
            "correct": True
        },
        {
            "text": "A polite, automated webhook that emails the supplier to ask if they have recently tasted the Champagne.",
            "correct": False
        },
        {
            "text": "An AI enhancement tool that automatically updates the product's tasting notes to include 'vibrant hints of bleach and pine scrub'.",
            "correct": False
        },
        {
            "text": "Nothing is wrong. At that price point, the Champagne is probably an exceptionally good way to descale a showerhead.",
            "correct": False
        }
    ],
    "explanation": "Categories must match an approved master list to prevent mapping errors. The PIM team maintains strict reference taxonomies so bad categories get rejected on ingest."
},

]


# ═══════════════════════════════════════════════════════════════════
# DATA LAYER
# ═══════════════════════════════════════════════════════════════════
SHEET_NAME     = "PIM_Odyssey_DB"
WORKSHEET_NAME = "Quiz"
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _get_worksheet():
    info   = dict(st.secrets["gcp_service_account"])
    creds  = Credentials.from_service_account_info(info, scopes=SCOPES)
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
        ws   = _get_worksheet()
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
# SCORING
# ═══════════════════════════════════════════════════════════════════
MAX_SCORE = QUESTIONS_PER_PLAY * POINTS_PER_CORRECT  # 1200


def rank_for(score: int) -> str:
    pct = score / MAX_SCORE
    if pct >= 0.92: return "PIM Expert — you should be presenting this yourself"
    if pct >= 0.75: return "Strong Foundation — you have definitely been paying attention"
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
        "score":         0,
        "correct_count": 0,
        "question_order": [],
        "question_idx":  0,
        "shuffled_opts": [],
        "last_result":   None,
        "started_at":    None,
        "saved":         False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def goto(stage: str):
    st.session_state.stage = stage
    st.rerun()


def _shuffle_opts(pool_idx: int) -> list[dict]:
    opts = QUIZ_POOL[pool_idx]["options"][:]
    random.shuffle(opts)
    return opts


def start_run(name: str):
    order = random.sample(range(len(QUIZ_POOL)), QUESTIONS_PER_PLAY)
    st.session_state.update({
        "name":           name,
        "score":          0,
        "correct_count":  0,
        "question_order": order,
        "question_idx":   0,
        "shuffled_opts":  _shuffle_opts(order[0]),
        "last_result":    None,
        "started_at":     time.time(),
        "saved":          False,
    })
    goto("question")


def current_question() -> dict:
    idx = st.session_state.question_order[st.session_state.question_idx]
    return QUIZ_POOL[idx]


# ═══════════════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════════════
def render_hud():
    q_num = st.session_state.question_idx + 1
    score = st.session_state.score
    pct   = int((st.session_state.question_idx / QUESTIONS_PER_PLAY) * 100)
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
    st.markdown('<div class="eyebrow">Hello, Full Stack Fury Team !!</div>', unsafe_allow_html=True)
    st.markdown('<h1><span class="kinetic">How well do you know PIM?</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:var(--text-mute); font-size:1.05rem; line-height:1.7; margin-top:0.3rem;">'
        '12 questions about product data, data quality, and things that have gone spectacularly wrong '
        'in online catalogs. No penalty for wrong answers. Please participate for a fun game of PIM.'
        '</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="glass"><div class="card-label">How it works</div>'
        '<ul style="margin:0; padding-left:1.2rem; line-height:1.9; color:var(--text-mute); font-size:0.95rem;">'
        '<li>12 questions from a Question pool of 22 — different combination every play</li>'
        '<li>4 options per question — one is correct, three are wrong in interesting ways</li>'
        '<li><strong style="color:var(--text);">+100 points</strong> per correct answer &nbsp;·&nbsp; Maximum possible: 1,200</li>'
        '<li>No penalty for guessing — be playful, some of our names are applied in this game !</li>'
        '<li>Leaderboard shows rankings after everyone plays</li>'
        '<li>Are you ready ?? :) </li>'
        '</ul></div>',
        unsafe_allow_html=True,
    )

    name = st.text_input(
        "Your name on the leaderboard",
        placeholder="how you'd like to appear",
        max_chars=32,
    )
    st.markdown('<div class="primary-action">', unsafe_allow_html=True)
    if st.button("Lets Go!"):
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

    # GIF display — centered, rounded, above the question card
    gif_id = q.get("gif_id", "")
    if gif_id:
        gif_url = f"https://media.giphy.com/media/{gif_id}/giphy.gif"
        st.markdown(
            f'<div style="text-align:center; margin-bottom:0.8rem;">'
            f'<img src="{gif_url}" style="height:180px; max-width:100%; border-radius:12px; object-fit:cover; border:1px solid rgba(255,255,255,0.12);"/>'
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
                   f'You chose: {r["chosen"]}<br>Correct: {r["right"]}')
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
            st.session_state.last_result   = None
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
        st.markdown(f'<div class="stat"><div class="stat-label">Score</div><div class="stat-value" style="color:var(--cyan);">{score}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat"><div class="stat-label">Correct</div><div class="stat-value">{correct}/{QUESTIONS_PER_PLAY}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat"><div class="stat-label">Time</div><div class="stat-value">{elapsed//60}m {elapsed%60:02d}s</div></div>', unsafe_allow_html=True)

    if not st.session_state.saved:
        save_score(name, score, rank)
        st.session_state.saved = True

    lb = fetch_leaderboard()
    if not lb.empty:
        st.markdown('<div class="card-label" style="margin-top:2rem;">Leaderboard</div>', unsafe_allow_html=True)
        st.dataframe(lb, use_container_width=True)

    st.markdown(
        '<p style="color:var(--text-mute); text-align:center; margin-top:1.5rem; font-size:0.95rem;">'
        "The presentation is about to begin. Your score is locked in."
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
