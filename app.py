import streamlit as st
from dotenv import load_dotenv

from f1_technical import show_f1_technical

load_dotenv()

st.set_page_config(
    page_title="KHEL | Sports Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    '''
    <style>
    .stApp {
        background:
            radial-gradient(circle at 10% 0%, rgba(103, 88, 255, .16), transparent 28%),
            radial-gradient(circle at 90% 0%, rgba(0, 214, 201, .10), transparent 24%),
            #080b12;
        color: #f5f7fb;
    }
    [data-testid="stHeader"] { background: rgba(8,11,18,.85); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#0b0f18,#070910);
        border-right: 1px solid rgba(255,255,255,.08);
    }
    [data-testid="stSidebar"] * { color: #e9edf5; }
    #MainMenu, footer { visibility: hidden; }
    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    .hero {
        padding: 38px;
        border-radius: 28px;
        border: 1px solid rgba(255,255,255,.10);
        background: linear-gradient(135deg,rgba(20,25,40,.97),rgba(12,16,27,.90));
        box-shadow: 0 24px 70px rgba(0,0,0,.34);
        margin-bottom: 24px;
    }
    .kicker {
        text-transform: uppercase;
        letter-spacing: .22em;
        font-size: .72rem;
        font-weight: 800;
        color: #8e9ab3;
        margin-bottom: 10px;
    }
    .title {
        font-size: clamp(2.3rem,5vw,4.7rem);
        line-height: .95;
        font-weight: 900;
        letter-spacing: -.055em;
        margin: 0;
        background: linear-gradient(90deg,#fff,#b8c5ff 55%,#83f1e7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        max-width: 760px;
        color: #aeb8ca;
        font-size: 1rem;
        line-height: 1.65;
        margin-top: 15px;
    }
    .live {
        display: inline-flex;
        gap: 8px;
        align-items: center;
        margin-top: 20px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(40,211,154,.09);
        border: 1px solid rgba(40,211,154,.22);
        color: #78e9c4;
        font-size: .78rem;
        font-weight: 750;
    }
    .dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #45e1ad;
        box-shadow: 0 0 14px rgba(69,225,173,.8);
    }
    .card {
        min-height: 145px;
        padding: 22px;
        border-radius: 22px;
        background: rgba(18,23,35,.82);
        border: 1px solid rgba(255,255,255,.08);
        box-shadow: 0 14px 40px rgba(0,0,0,.20);
    }
    .label {
        color: #8995ab;
        text-transform: uppercase;
        letter-spacing: .12em;
        font-size: .67rem;
        font-weight: 800;
    }
    .value {
        font-size: 1.4rem;
        font-weight: 850;
        margin-top: 10px;
    }
    .text {
        color: #9ea9bc;
        font-size: .86rem;
        line-height: 1.5;
        margin-top: 7px;
    }
    .section {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 30px 0 15px;
    }
    .bar {
        width: 5px; height: 30px; border-radius: 5px;
        background: linear-gradient(180deg,#8a78ff,#5be6d8);
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 850;
    }
    .brand {
        padding: 10px 4px 20px;
    }
    .brand-name {
        font-size: 2rem;
        font-weight: 950;
        letter-spacing: -.07em;
    }
    .brand-name span { color: #7e72ff; }
    .brand-sub {
        color: #7f8aa0;
        font-size: .76rem;
    }
    .footer {
        margin-top: 45px;
        padding-top: 18px;
        border-top: 1px solid rgba(255,255,255,.08);
        color: #69758a;
        font-size: .75rem;
        text-align: center;
    }
    div[data-testid="stMetric"] {
        background: rgba(18,23,35,.78);
        border: 1px solid rgba(255,255,255,.07);
        padding: 15px;
        border-radius: 17px;
    }
    
    /* KHEL UI motion */
    .khel-hero { animation: heroIn .7s ease-out both; }
    .khel-card {
        transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
        animation: cardIn .65s ease-out both;
    }
    .khel-card:hover {
        transform: translateY(-5px);
        border-color: rgba(126,114,255,.35);
        box-shadow: 0 18px 48px rgba(0,0,0,.30), 0 0 28px rgba(126,114,255,.08);
    }
    .khel-dot {
        animation: livePulse 1.7s ease-in-out infinite;
    }
    .khel-section-bar {
        animation: barGlow 2.2s ease-in-out infinite;
    }
    @keyframes heroIn {
        from { opacity: 0; transform: translateY(18px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes cardIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes livePulse {
        0%, 100% { transform: scale(.85); opacity: .65; }
        50% { transform: scale(1.25); opacity: 1; }
    }
    @keyframes barGlow {
        0%, 100% { filter: brightness(.85); }
        50% { filter: brightness(1.45); }
    }

    /* Animated Khel AI status */
    .khel-ai {
        position: relative;
        overflow: hidden;
        margin: 18px 0 24px;
        padding: 17px 20px;
        border-radius: 20px;
        background: linear-gradient(110deg, rgba(19,24,39,.96), rgba(15,20,33,.80));
        border: 1px solid rgba(126,114,255,.20);
    }
    .khel-ai:before {
        content: "";
        position: absolute;
        top: 0;
        left: -35%;
        width: 35%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #8a78ff, #5be6d8, transparent);
        animation: aiScan 2.8s linear infinite;
    }
    .khel-ai-row {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .khel-ai-orb {
        width: 42px;
        height: 42px;
        min-width: 42px;
        border-radius: 50%;
        background: radial-gradient(circle at 32% 28%, #fff 0 5%, #9a8cff 13%, #6557ff 45%, #211b62 78%);
        box-shadow: 0 0 20px rgba(126,114,255,.55);
        animation: aiPulse 2s ease-in-out infinite;
    }
    .khel-ai-title {
        font-weight: 850;
        font-size: .9rem;
    }
    .khel-ai-sub {
        color: #8995ab;
        font-size: .75rem;
        margin-top: 3px;
    }
    .khel-ai-bars {
        display: flex;
        gap: 4px;
        margin-left: auto;
        align-items: flex-end;
        height: 24px;
    }
    .khel-ai-bars span {
        width: 4px;
        height: 7px;
        border-radius: 4px;
        background: #7e72ff;
        animation: aiBars 1s ease-in-out infinite;
    }
    .khel-ai-bars span:nth-child(2) { animation-delay: .12s; }
    .khel-ai-bars span:nth-child(3) { animation-delay: .24s; }
    .khel-ai-bars span:nth-child(4) { animation-delay: .36s; }
    .khel-ai-bars span:nth-child(5) { animation-delay: .48s; }

    @keyframes aiPulse {
        0%, 100% { transform: scale(.94); box-shadow: 0 0 15px rgba(126,114,255,.35); }
        50% { transform: scale(1.06); box-shadow: 0 0 28px rgba(126,114,255,.72); }
    }
    @keyframes aiBars {
        0%, 100% { height: 7px; opacity: .45; }
        50% { height: 23px; opacity: 1; }
    }
    @keyframes aiScan {
        0% { left: -35%; }
        100% { left: 100%; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: .01ms !important;
        }
    }

    </style>
    ''',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-name">K<span>HEL</span></div>'
        '<div class="brand-sub">F1 SPORTS INTELLIGENCE LAB</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="padding:12px 10px;border-radius:14px;'
        'background:rgba(126,114,255,.10);border:1px solid rgba(126,114,255,.20);'
        'font-weight:800;">🏎️ Formula 1</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("KHEL turns Formula 1 race data into visual analysis and concise AI briefs.")

icon = "🏎️"
name = "Formula 1"

st.markdown(
    f'<div class="hero"><div class="kicker">KHEL / SPORTS INTELLIGENCE</div>'
    f'<div class="title">{icon} {name}</div>'
    f'<div class="subtitle">Explore performance, trends and technical metrics '
    f'through interactive visualisation, then let Khel AI turn the numbers '
    f'into a concise analyst brief.</div>'
    f'<div class="live"><span class="dot"></span> DATA-DRIVEN ANALYSIS</div></div>',
    unsafe_allow_html=True,
)

cards = [
    ("DATA ENGINE", "OpenF1", "Race sessions, laps and tyre stints"),
    ("VISUALS", "Race telemetry", "Compare pace and performance"),
    ("AI LAYER", "Khel AI", "Evidence-first race briefing"),
]

cols = st.columns(3)
for col, (label, value, text) in zip(cols, cards):
    with col:
        st.markdown(
            f'<div class="card"><div class="label">{label}</div>'
            f'<div class="value">{value}</div><div class="text">{text}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="khel-ai">'
    '<div class="khel-ai-row">'
    '<div class="khel-ai-orb"></div>'
    '<div><div class="khel-ai-title">Khel AI · Analysis engine</div>'
    '<div class="khel-ai-sub">Ready to turn F1 race data into an evidence-first brief</div></div>'
    '<div class="khel-ai-bars"><span></span><span></span><span></span><span></span><span></span></div>'
    '</div></div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section"><div class="bar"></div>'
    '<div class="section-title">Analysis workspace</div></div>',
    unsafe_allow_html=True,
)

show_f1_technical()

st.markdown(
    '<div class="footer">KHEL · SPORTS INTELLIGENCE · BUILT WITH STREAMLIT</div>',
    unsafe_allow_html=True,
)
