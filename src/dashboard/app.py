import base64
import html
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots


# ============================================================
# CONFIG
# ============================================================

API_URL = os.getenv(
    "API_URL",
    "https://nz-transit-intelligence.onrender.com",
)

API_TIMEOUT = 90

st.set_page_config(
    page_title="NZ Transit Intelligence",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ASSETS
# ============================================================

def image_to_base64(path: Path) -> str:
    try:
        return base64.b64encode(
            path.read_bytes()
        ).decode("utf-8")
    except OSError:
        return ""


ASSET_DIR = (
    Path(__file__).resolve().parent
    / "assets"
)

HERO_IMAGE_PATH = (
    ASSET_DIR
    / "auckland_skyline.png"
)

HERO_IMAGE_BASE64 = image_to_base64(
    HERO_IMAGE_PATH
)

if HERO_IMAGE_BASE64:
    HERO_BACKGROUND = (
        f'url("data:image/png;base64,{HERO_IMAGE_BASE64}")'
    )
else:
    HERO_BACKGROUND = (
        "linear-gradient("
        "120deg,"
        "#0a2342,"
        "#154f82"
        ")"
    )


# ============================================================
# GLOBAL PREMIUM THEME
# ============================================================

st.html(
    f"""
    <style>
    :root {{
        --navy-950: #061426;
        --navy-900: #0a1b33;
        --navy-850: #0d2340;
        --navy-800: #102b4c;
        --blue-700: #1d4ed8;
        --blue-600: #2563eb;
        --blue-500: #3b82f6;
        --blue-400: #60a5fa;
        --cyan-400: #22d3ee;
        --green-600: #16a34a;
        --green-500: #22c55e;
        --amber-500: #f59e0b;
        --red-500: #ef4444;
        --red-400: #fb7185;
        --slate-950: #0f172a;
        --slate-800: #1e293b;
        --slate-700: #334155;
        --slate-600: #475569;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --slate-300: #cbd5e1;
        --slate-200: #e2e8f0;
        --slate-100: #f1f5f9;
        --canvas: #f4f7fb;
        --card: #ffffff;
        --border: #dde6f0;
        --shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
    }}

    html,
    body,
    [class*="css"] {{
        font-family:
            Inter,
            ui-sans-serif,
            system-ui,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
    }}

    .stApp {{
        background:
            radial-gradient(
                circle at 78% 0%,
                rgba(59,130,246,.08),
                transparent 30rem
            ),
            var(--canvas);
        color: var(--slate-950);
    }}

    /* ========================================================
       INTEGRATED TOP HEADER
       Native sidebar arrow + brand + native clickable nav + API
       ======================================================== */

    [data-testid="stHeader"] {{
        height: 78px !important;
        background: transparent !important;
        box-shadow: none !important;
        pointer-events: none;
    }}

    [data-testid="stToolbar"] {{
        display: flex !important;
        visibility: visible !important;
        pointer-events: auto !important;
    }}

    [data-testid="stDeployButton"],
    [data-testid="stMainMenu"] {{
        display: none !important;
    }}

    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    .block-container {{
        max-width: 1680px;
        padding-top: 6.3rem;
        padding-bottom: 1.5rem;
        padding-left: 1.35rem;
        padding-right: 1.35rem;
    }}

    .premium-topbar {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999990;
        height: 78px;

        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.2rem;

        padding: 0 1.45rem 0 4.85rem;

        background:
            radial-gradient(
                circle at 65% -80%,
                rgba(59,130,246,.28),
                transparent 26rem
            ),
            linear-gradient(
                90deg,
                #0a1a31 0%,
                #173f70 53%,
                #0a1a31 100%
            );

        border-bottom: 1px solid rgba(255,255,255,.08);
        box-shadow: 0 12px 30px rgba(3,12,24,.18);
    }}

    .premium-brand {{
        display: flex;
        align-items: center;
        gap: .72rem;
        min-width: 315px;
    }}

    .premium-brand-mark {{
        width: 48px;
        height: 48px;
        display: grid;
        place-items: center;
        border-radius: 14px;
        font-size: 1.58rem;
        background:
            linear-gradient(
                145deg,
                #48a3ff,
                #2469ee
            );
        box-shadow:
            0 10px 22px rgba(37,99,235,.30),
            inset 0 1px 0 rgba(255,255,255,.22);
    }}

    .premium-brand-title {{
        color: #ffffff;
        font-size: 1.23rem;
        font-weight: 850;
        letter-spacing: -.03em;
        line-height: 1.05;
    }}

    .premium-brand-sub {{
        color: #aebfd4;
        font-size: .69rem;
        margin-top: .26rem;
    }}

    .topbar-right {{
        min-width: 315px;
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: .8rem;
    }}

    .api-pill {{
        display: inline-flex;
        align-items: center;
        gap: .42rem;
        padding: .48rem .7rem;
        border-radius: 999px;
        border: 1px solid rgba(112,241,175,.22);
        background: rgba(16,185,129,.10);
        color: #6ee7b7 !important;
        font-size: .7rem;
        font-weight: 800;
        white-space: nowrap;
    }}

    .api-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4ade80;
        box-shadow: 0 0 0 4px rgba(74,222,128,.09);
    }}

    .api-pill.offline {{
        border-color: rgba(251,113,133,.25);
        background: rgba(239,68,68,.10);
        color: #fda4af !important;
    }}

    .api-pill.offline .api-dot {{
        background: #fb7185;
        box-shadow: 0 0 0 4px rgba(251,113,133,.09);
    }}

    .clock-wrap {{
        padding-left: .78rem;
        border-left: 1px solid rgba(255,255,255,.13);
        color: #e6edf6 !important;
        line-height: 1.25;
        text-align: left;
    }}

    .clock-date {{
        color: #aebfd4 !important;
        font-size: .63rem;
    }}

    .clock-time {{
        color: #ffffff !important;
        font-size: .78rem;
        font-weight: 800;
        margin-top: .12rem;
    }}

    /* Stable always-visible menu toggle beside the bus logo. */
    .st-key-sidebar_toggle_container {{
        position: fixed !important;
        top: 17px !important;
        left: 14px !important;
        z-index: 1000015 !important;

        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;

        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;

        margin: 0 !important;
        padding: 0 !important;
        overflow: visible !important;
    }}

    .st-key-sidebar_toggle_container > div,
    .st-key-sidebar_toggle_container [data-testid="stIFrame"],
    .st-key-sidebar_toggle_container iframe {{
        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;

        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;

        margin: 0 !important;
        padding: 0 !important;
        border: 0 !important;
        background: transparent !important;
        overflow: visible !important;
    }}

    /* Hide Streamlit's own hover-only collapse icon.
       The real button stays in the DOM and the proxy activates it. */
    [data-testid="stSidebarCollapseButton"] {{
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    .st-key-dashboard_nav {{
        position: fixed !important;
        top: 17px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;

        z-index: 1000004 !important;

        width: max-content !important;
        max-width: 46vw !important;

        margin: 0 !important;
        padding: 0 !important;

        overflow-x: auto !important;
        overflow-y: hidden !important;

        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }}

    .st-key-dashboard_nav::-webkit-scrollbar {{
        display: none !important;
    }}

    .st-key-dashboard_nav [data-testid="stSegmentedControl"] {{
        margin: 0 !important;
        width: max-content !important;
        min-width: max-content !important;
    }}

    .st-key-dashboard_nav [data-testid="stSegmentedControl"] > div {{
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;

        width: max-content !important;
        min-width: max-content !important;

        gap: .2rem !important;
        padding: 0 !important;

        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    .st-key-dashboard_nav [data-testid="stSegmentedControl"] button {{
        flex: 0 0 auto !important;

        min-height: 44px !important;
        height: 44px !important;

        padding: 0 .95rem !important;

        border: 1px solid transparent !important;
        border-radius: 13px !important;

        color: #f5f8fc !important;
        background: transparent !important;

        font-size: .74rem !important;
        font-weight: 780 !important;
        white-space: nowrap !important;
    }}

    .st-key-dashboard_nav [data-testid="stSegmentedControl"] button:hover {{
        color: #ffffff !important;
        background: rgba(255,255,255,.09) !important;
    }}

    .st-key-dashboard_nav [data-testid="stSegmentedControl"] button[aria-pressed="true"],
    .st-key-dashboard_nav [data-testid="stSegmentedControl"] button[data-selected="true"] {{
        color: #ffffff !important;
        background:
            linear-gradient(
                135deg,
                #3d96ff,
                #2874ed
            ) !important;
        border-color: rgba(255,255,255,.12) !important;
        box-shadow:
            0 8px 18px rgba(37,99,235,.30) !important;
    }}

    @media (max-width: 1050px) {{
        .premium-brand,
        .topbar-right {{
            min-width: auto;
        }}

        .premium-brand-sub {{
            display: none;
        }}

        .clock-wrap {{
            display: none;
        }}

        .st-key-dashboard_nav {{
            max-width: 42vw !important;
        }}

        .st-key-dashboard_nav [data-testid="stSegmentedControl"] button {{
            padding: 0 .68rem !important;
            font-size: .68rem !important;
        }}

        .hero-kpis {{
            grid-template-columns:
                repeat(2, minmax(0,1fr));
        }}

        .network-strip {{
            grid-template-columns:
                repeat(4, minmax(0,1fr));
            row-gap: .7rem;
        }}

        .model-grid {{
            grid-template-columns:
                repeat(3, minmax(0,1fr));
        }}
    }}

    @media (max-width: 760px) {{
        [data-testid="stHeader"] {{
            height: 118px !important;
        }}

        .premium-topbar {{
            height: 118px;
            align-items: flex-start;
            padding:
                .72rem .7rem
                3.35rem 4.25rem;
        }}

        .premium-brand-mark {{
            width: 42px;
            height: 42px;
            border-radius: 12px;
            font-size: 1.35rem;
        }}

        .premium-brand-title {{
            font-size: .98rem;
        }}

        .premium-brand-sub,
        .clock-wrap {{
            display: none;
        }}

        .topbar-right {{
            margin-left: auto;
        }}

        .api-pill {{
            padding: .42rem .58rem;
            font-size: .64rem;
        }}

        .st-key-sidebar_toggle_container {{
            top: 15px !important;
            left: 10px !important;

            width: 38px !important;
            min-width: 38px !important;
            max-width: 38px !important;

            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
        }}

        .st-key-sidebar_toggle_container > div,
        .st-key-sidebar_toggle_container [data-testid="stIFrame"],
        .st-key-sidebar_toggle_container iframe {{
            width: 38px !important;
            min-width: 38px !important;
            max-width: 38px !important;

            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
        }}

        .st-key-dashboard_nav {{
            top: 70px !important;
            left: .72rem !important;
            right: .72rem !important;
            transform: none !important;
            width: auto !important;
            max-width: none !important;
        }}

        .st-key-dashboard_nav [data-testid="stSegmentedControl"] button {{
            min-height: 36px !important;
            height: 36px !important;
            padding: 0 .66rem !important;
            font-size: .64rem !important;
        }}

        .block-container {{
            padding-top: 8.6rem;
            padding-left: .8rem;
            padding-right: .8rem;
        }}

        [data-testid="stSidebar"] > div {{
            padding-top: 1rem;
        }}

        .hero {{
            min-height: auto;
            padding: 1.25rem 1rem;
        }}

        .hero-kpis {{
            grid-template-columns:
                repeat(2, minmax(0,1fr));
        }}

        .network-strip {{
            grid-template-columns:
                repeat(2, minmax(0,1fr));
        }}
    }}

    /* --------------------------------------------------------
       SIDEBAR
       -------------------------------------------------------- */

    [data-testid="stSidebar"] {{
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        background:
            radial-gradient(
                circle at 0% 0%,
                rgba(67,145,255,.20),
                transparent 18rem
            ),
            linear-gradient(
                180deg,
                #0b1d37 0%,
                #102a4a 52%,
                #0a1a31 100%
            );
        border-right: 1px solid rgba(255,255,255,.07);
        box-shadow: 10px 0 32px rgba(6,20,38,.10);
    }}

    [data-testid="stSidebar"] > div {{
        padding-top: 1.15rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {{
        color: #eaf1f8 !important;
    }}

    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background: rgba(4,15,29,.48) !important;
        border: 1px solid rgba(139,172,210,.22) !important;
        border-radius: 12px !important;
        min-height: 42px;
    }}

    [data-testid="stSidebar"] [data-baseweb="select"] div,
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] input {{
        color: #ffffff !important;
    }}

    [data-testid="stSidebar"] [data-testid="stSlider"] {{
        padding-top: .08rem;
    }}

    [data-testid="stSidebar"] button[kind="primary"] {{
        min-height: 50px;
        border: none;
        border-radius: 15px;
        font-size: .88rem;
        font-weight: 820;
        color: white;
        background:
            linear-gradient(
                135deg,
                #3597ff,
                #2472f2
            );
        box-shadow:
            0 14px 28px rgba(37,99,235,.30);
    }}

    [data-testid="stSidebar"] button[kind="primary"]:hover {{
        transform: translateY(-1px);
        box-shadow:
            0 16px 31px rgba(37,99,235,.36);
    }}

    .side-cta {{
        display: flex;
        align-items: center;
        gap: .72rem;
        padding: .86rem .9rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        background:
            linear-gradient(
                135deg,
                #3297ff,
                #2470ed
            );
        box-shadow:
            0 14px 28px rgba(37,99,235,.24);
    }}

    .side-cta-icon {{
        width: 38px;
        height: 38px;
        display: grid;
        place-items: center;
        border-radius: 11px;
        color: white;
        font-size: 1.05rem;
        background: rgba(255,255,255,.12);
        border: 1px solid rgba(255,255,255,.14);
    }}

    .side-cta-title {{
        color: white;
        font-size: .92rem;
        font-weight: 850;
        line-height: 1.12;
    }}

    .side-cta-copy {{
        color: #dbeafe;
        font-size: .65rem;
        margin-top: .2rem;
    }}

    .side-section {{
        color: #91baf0;
        font-size: .62rem;
        font-weight: 850;
        text-transform: uppercase;
        letter-spacing: .12em;
        margin: .65rem 0 .38rem;
    }}

    .stop-meta {{
        margin: .28rem 0 .65rem;
        padding: .66rem .72rem;
        border-radius: 11px;
        background: rgba(255,255,255,.055);
        border: 1px solid rgba(255,255,255,.08);
        color: #b8c9dd;
        font-size: .68rem;
        line-height: 1.65;
    }}

    .side-location {{
        margin-top: 1rem;
        padding: .9rem .2rem .25rem;
        border-top: 1px solid rgba(255,255,255,.08);
        color: #99afc8;
        font-size: .68rem;
        line-height: 1.55;
    }}

    .side-location strong {{
        color: #ffffff;
        font-size: .74rem;
    }}

    /* --------------------------------------------------------
       HERO
       -------------------------------------------------------- */

    .hero {{
        position: relative;
        overflow: hidden;
        min-height: 260px;
        border-radius: 22px;
        padding: 1.65rem 1.75rem 1.35rem;
        color: white;
        background-image:
            linear-gradient(
                90deg,
                rgba(5,18,36,.96) 0%,
                rgba(7,30,56,.88) 34%,
                rgba(7,33,61,.60) 63%,
                rgba(7,27,52,.25) 100%
            ),
            {HERO_BACKGROUND};
        background-size: cover;
        background-position: center 48%;
        box-shadow:
            0 20px 46px rgba(9,30,54,.18);
    }}

    .hero:after {{
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        background:
            linear-gradient(
                180deg,
                rgba(255,255,255,.02),
                rgba(0,0,0,.04)
            );
    }}

    .hero-content {{
        position: relative;
        z-index: 2;
        max-width: 1040px;
    }}

    .hero-eyebrow {{
        color: #a9dcff;
        font-size: .68rem;
        font-weight: 850;
        text-transform: uppercase;
        letter-spacing: .12em;
        margin-bottom: .45rem;
    }}

    .hero-title {{
        color: #ffffff;
        font-size: clamp(1.6rem, 2.7vw, 2.3rem);
        font-weight: 880;
        letter-spacing: -.04em;
        line-height: 1.08;
        margin: 0;
        max-width: 760px;
    }}

    .hero-copy {{
        color: #d6e4f2;
        font-size: .82rem;
        line-height: 1.55;
        margin-top: .5rem;
        max-width: 650px;
    }}

    .hero-kpis {{
        display: grid;
        grid-template-columns:
            repeat(4, minmax(0,1fr));
        gap: .72rem;
        margin-top: 1.12rem;
        max-width: 900px;
    }}

    .hero-kpi {{
        display: flex;
        align-items: center;
        gap: .68rem;
        padding: .68rem .76rem;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,.25);
        background: rgba(7,25,46,.38);
        backdrop-filter: blur(12px);
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,.05);
    }}

    .hero-kpi-icon {{
        width: 36px;
        height: 36px;
        display: grid;
        place-items: center;
        border-radius: 11px;
        color: #8ddcff;
        background: rgba(63,150,255,.17);
        font-size: 1rem;
        flex-shrink: 0;
    }}

    .hero-kpi-value {{
        color: white;
        font-size: 1.15rem;
        font-weight: 860;
        line-height: 1.05;
    }}

    .hero-kpi-label {{
        color: #d4e4f4;
        font-size: .61rem;
        margin-top: .18rem;
        font-weight: 650;
    }}

    .wake-note {{
        margin-top: .72rem;
        padding: .6rem .75rem;
        border-radius: 12px;
        border: 1px solid #cfe1fb;
        background: #eef5ff;
        color: #365876;
        font-size: .7rem;
        line-height: 1.45;
    }}

    /* --------------------------------------------------------
       SECTIONS + CARDS
       -------------------------------------------------------- */

    .section-title-row {{
        margin: 1.25rem 0 .6rem;
    }}

    .section-kicker {{
        color: #2563eb;
        font-size: .62rem;
        font-weight: 870;
        text-transform: uppercase;
        letter-spacing: .10em;
        margin-bottom: .18rem;
    }}

    .section-title {{
        color: #0f172a;
        font-size: 1.25rem;
        font-weight: 870;
        letter-spacing: -.03em;
        line-height: 1.15;
    }}

    .section-copy {{
        color: #5c6d81;
        font-size: .72rem;
        margin-top: .22rem;
        line-height: 1.5;
    }}

    .premium-card {{
        background: rgba(255,255,255,.97);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: var(--shadow);
        padding: 1rem;
    }}

    .card-title {{
        color: #0f172a;
        font-size: .98rem;
        font-weight: 850;
        letter-spacing: -.02em;
    }}

    .card-copy {{
        color: #64748b;
        font-size: .68rem;
        margin-top: .12rem;
        line-height: 1.5;
    }}

    .result-box {{
        border-radius: 13px;
        padding: .7rem .76rem;
        border: 1px solid #e3eaf2;
        background: #fbfdff;
        margin-bottom: .5rem;
    }}

    .result-box.amber {{
        background:
            linear-gradient(
                180deg,
                #fffaf0,
                #fff6df
            );
        border-color: #f5deb0;
    }}

    .result-box.green {{
        background:
            linear-gradient(
                180deg,
                #effcf5,
                #e9f9f0
            );
        border-color: #ccebd9;
    }}

    .result-box.red {{
        background:
            linear-gradient(
                180deg,
                #fff4f3,
                #ffebea
            );
        border-color: #ffd0cc;
    }}

    .result-box.blue {{
        background:
            linear-gradient(
                180deg,
                #f1f7ff,
                #eaf3ff
            );
        border-color: #d4e5fb;
    }}

    .result-label {{
        color: #64748b;
        font-size: .62rem;
        font-weight: 780;
        text-transform: uppercase;
        letter-spacing: .05em;
    }}

    .result-value {{
        color: #0f172a;
        font-size: .92rem;
        font-weight: 850;
        margin-top: .14rem;
    }}

    .model-pill {{
        display: inline-flex;
        padding: .4rem .7rem;
        border-radius: 999px;
        background: #e7f0ff;
        color: #1765d4;
        font-size: .7rem;
        font-weight: 850;
    }}

    .model-grid {{
        display: grid;
        grid-template-columns:
            repeat(6, minmax(0,1fr));
        gap: 0;
        margin-top: .9rem;
        border-top: 1px solid #e5ebf3;
        border-bottom: 1px solid #e5ebf3;
    }}

    .model-stat {{
        padding: .72rem .42rem;
        text-align: center;
        border-right: 1px solid #e5ebf3;
    }}

    .model-stat:last-child {{
        border-right: none;
    }}

    .model-value {{
        color: #0f172a;
        font-size: .95rem;
        font-weight: 870;
    }}

    .model-label {{
        color: #64748b;
        font-size: .58rem;
        margin-top: .14rem;
    }}

    .model-note {{
        margin-top: .82rem;
        padding: .72rem .78rem;
        border-radius: 12px;
        border: 1px solid #d8e7fb;
        background: #f1f7ff;
        color: #4d6481;
        font-size: .67rem;
        line-height: 1.5;
    }}

    /* --------------------------------------------------------
       NETWORK STRIP
       -------------------------------------------------------- */

    .network-shell {{
        padding: .85rem .9rem .78rem;
        border-radius: 17px;
        border: 1px solid #dce5ef;
        background: #ffffff;
        box-shadow: var(--shadow);
    }}

    .network-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: .7rem;
    }}

    .network-title {{
        color: #0f172a;
        font-size: 1rem;
        font-weight: 850;
    }}

    .network-sub {{
        color: #64748b;
        font-size: .66rem;
        margin-top: .12rem;
    }}

    .data-badge {{
        color: #64748b;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        padding: .38rem .56rem;
        border-radius: 999px;
        font-size: .61rem;
        white-space: nowrap;
    }}

    .network-strip {{
        display: grid;
        grid-template-columns:
            repeat(8, minmax(0,1fr));
        gap: 0;
    }}

    .network-stat {{
        padding: .38rem .48rem;
        text-align: center;
        border-right: 1px solid #e7edf4;
    }}

    .network-stat:last-child {{
        border-right: none;
    }}

    .network-stat-icon {{
        font-size: .9rem;
        margin-bottom: .18rem;
    }}

    .network-stat-value {{
        color: #0f172a;
        font-size: .84rem;
        font-weight: 870;
        white-space: nowrap;
    }}

    .network-stat-label {{
        color: #64748b;
        font-size: .55rem;
        margin-top: .12rem;
        white-space: nowrap;
    }}

    /* --------------------------------------------------------
       PLOTLY + EXPANDERS
       -------------------------------------------------------- */

    div[data-testid="stPlotlyChart"] {{
        background: white;
        border: 1px solid #e0e8f1;
        border-radius: 16px;
        padding: .2rem .25rem .1rem;
        box-shadow:
            0 9px 26px rgba(15,23,42,.045);
        overflow: hidden;
    }}

    div[data-testid="stExpander"] {{
        border: 1px solid #dce4ee;
        border-radius: 13px;
        background: white;
        overflow: hidden;
        box-shadow:
            0 7px 20px rgba(15,23,42,.035);
    }}

    div[data-testid="stExpander"]
    details > summary {{
        background: #f8fafc !important;
        min-height: 42px;
    }}

    div[data-testid="stExpander"]
    details > summary p,
    div[data-testid="stExpander"]
    details > summary span,
    div[data-testid="stExpander"]
    details > summary div {{
        color: #334155 !important;
        font-weight: 760 !important;
    }}

    div[data-testid="stAlert"] {{
        border-radius: 13px;
    }}

    div[data-testid="stAlert"] p {{
        color: #294056 !important;
        font-weight: 640;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid #dfe6ef;
        border-radius: 12px;
        overflow: hidden;
    }}

    /* --------------------------------------------------------
       FOOTER
       -------------------------------------------------------- */

    .premium-footer {{
        margin-top: 1.15rem;
        padding: .8rem .95rem;
        border-radius: 14px;
        background:
            linear-gradient(
                90deg,
                #0b1c34,
                #102c4e
            );
        color: #c8d6e6;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
        font-size: .65rem;
    }}

    .premium-footer strong {{
        color: white;
    }}

    .premium-footer a {{
        color: #b9d7ff !important;
        text-decoration: none;
        margin-left: .75rem;
    }}

    @media (max-width: 1050px) {{
        .premium-brand,
        .topbar-right {{
            min-width: auto;
        }}

        .hero-kpis {{
            grid-template-columns:
                repeat(2, minmax(0,1fr));
        }}

        .network-strip {{
            grid-template-columns:
                repeat(4, minmax(0,1fr));
            row-gap: .7rem;
        }}

        .model-grid {{
            grid-template-columns:
                repeat(3, minmax(0,1fr));
        }}
    }}

    @media (max-width: 760px) {{
        .premium-topbar {{
            height: 118px;
            min-height: 118px;
            align-items: flex-start;
            padding:
                .72rem .7rem
                3.35rem 4.25rem;
        }}

        .premium-brand-title {{
            font-size: .98rem;
        }}

        .premium-brand-sub {{
            display: none;
        }}

        .clock-wrap {{
            display: none;
        }}

        .block-container {{
            padding-top: 8.6rem;
            padding-left: .8rem;
            padding-right: .8rem;
        }}

        [data-testid="stSidebar"] > div {{
            padding-top: 1rem;
        }}

        .hero {{
            min-height: auto;
            padding: 1.25rem 1rem;
        }}

        .hero-kpis {{
            grid-template-columns:
                repeat(2, minmax(0,1fr));
        }}

        .network-strip {{
            grid-template-columns:
                repeat(2, minmax(0,1fr));
        }}
    }}
    </style>
    """
)


# ============================================================
# API HELPERS
# ============================================================

@st.cache_data(ttl=300)
def get_routes():
    response = requests.get(
        f"{API_URL}/gtfs/routes",
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300)
def get_route_stops(
    route_id: str,
    direction_id: int,
):
    response = requests.get(
        f"{API_URL}/gtfs/routes/{route_id}/stops",
        params={
            "direction_id": direction_id,
        },
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()

    rows = response.json()
    unique_rows = []
    seen = set()

    for row in rows:
        key = (
            row["stop_id"],
            row["stop_sequence"],
        )

        if key not in seen:
            seen.add(key)
            unique_rows.append(row)

    return unique_rows


@st.cache_data(ttl=120)
def get_network_kpis():
    response = requests.get(
        f"{API_URL}/analytics/network-kpis",
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=120)
def get_time_period_performance():
    response = requests.get(
        f"{API_URL}/analytics/time-period-performance",
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=120)
def get_top_delayed_routes():
    response = requests.get(
        f"{API_URL}/analytics/top-delayed-routes",
        params={
            "limit": 10,
            "min_observations": 10,
        },
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=120)
def get_problem_stops():
    response = requests.get(
        f"{API_URL}/analytics/problem-stops",
        params={
            "limit": 50,
            "min_observations": 5,
        },
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=120)
def get_model_info():
    response = requests.get(
        f"{API_URL}/model-info",
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


# ============================================================
# DISPLAY HELPERS
# ============================================================

def safe(value):
    return html.escape(
        str(value)
    )


def route_label(route):
    short_name = (
        route.get("route_short_name")
        or ""
    ).strip()

    long_name = (
        route.get("route_long_name")
        or ""
    ).strip()

    route_id = route[
        "route_id"
    ]

    if (
        short_name
        and long_name
        and short_name.lower()
        == long_name.lower()
    ):
        return short_name

    if (
        short_name
        and long_name
    ):
        return (
            f"{short_name} — "
            f"{long_name}"
        )

    if short_name:
        return short_name

    if long_name:
        return long_name

    return route_id


def analytics_route_label(route):
    short_name = (
        route.get("route_short_name")
        or ""
    ).strip()

    long_name = (
        route.get("route_long_name")
        or ""
    ).strip()

    route_id = (
        route.get("route_id")
        or "Unknown"
    )

    if short_name:
        return short_name

    if long_name:
        return (
            long_name
            if len(long_name) <= 22
            else long_name[:21] + "…"
        )

    return route_id


def full_route_label(route):
    short_name = (
        route.get("route_short_name")
        or ""
    ).strip()

    long_name = (
        route.get("route_long_name")
        or ""
    ).strip()

    if (
        short_name
        and long_name
    ):
        return (
            f"{short_name} — "
            f"{long_name}"
        )

    return (
        short_name
        or long_name
        or route.get(
            "route_id",
            "Unknown",
        )
    )


def stop_label(stop):
    stop_name = (
        stop.get("stop_name")
        or stop["stop_id"]
    )

    return (
        f"{stop['stop_sequence']}. "
        f"{stop_name}"
    )


def sidebar_html(content):
    with st.sidebar:
        st.html(
            content
        )


def section_header(
    kicker,
    title,
    copy,
):
    st.html(
        f"""
        <div class="section-title-row">
            <div class="section-kicker">
                {safe(kicker)}
            </div>
            <div class="section-title">
                {safe(title)}
            </div>
            <div class="section-copy">
                {safe(copy)}
            </div>
        </div>
        """
    )


# ============================================================
# CHART HELPERS
# ============================================================

def create_probability_ring(
    probability: float,
):
    remaining = max(
        0.0,
        100.0 - probability,
    )

    figure = go.Figure(
        data=[
            go.Pie(
                values=[
                    probability,
                    remaining,
                ],
                hole=0.78,
                sort=False,
                direction="clockwise",
                rotation=90,
                marker=dict(
                    colors=[
                        "#2f80ed",
                        "#e5edf4",
                    ],
                    line=dict(
                        width=0,
                    ),
                ),
                textinfo="none",
                hoverinfo="skip",
            )
        ]
    )

    figure.add_annotation(
        x=0.5,
        y=0.55,
        text=(
            f"<b>{probability:.1f}%</b>"
        ),
        showarrow=False,
        font=dict(
            size=31,
            color="#0f172a",
        ),
    )

    figure.add_annotation(
        x=0.5,
        y=0.39,
        text=(
            "Delay<br>Probability"
        ),
        showarrow=False,
        font=dict(
            size=11,
            color="#475569",
        ),
        align="center",
    )

    figure.update_layout(
        height=250,
        margin=dict(
            l=5,
            r=5,
            t=6,
            b=6,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    return figure


def base_chart_layout(
    figure,
    height=330,
):
    figure.update_layout(
        height=height,
        margin=dict(
            l=12,
            r=16,
            t=18,
            b=28,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(
            family="Inter, Segoe UI, sans-serif",
            color="#475569",
            size=10,
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor="#0f172a",
            font_color="#ffffff",
        ),
        showlegend=False,
    )

    figure.update_xaxes(
        gridcolor="#e8eef5",
        linecolor="#dce5ef",
        tickfont=dict(
            color="#475569",
            size=9,
        ),
        title_font=dict(
            color="#334155",
            size=10,
        ),
        zerolinecolor="#dce5ef",
    )

    figure.update_yaxes(
        gridcolor="#e8eef5",
        linecolor="#dce5ef",
        tickfont=dict(
            color="#475569",
            size=9,
        ),
        title_font=dict(
            color="#334155",
            size=10,
        ),
        zerolinecolor="#dce5ef",
    )

    return figure


def create_top_routes_chart(
    routes,
):
    chart_rows = list(
        reversed(routes)
    )

    labels = [
        analytics_route_label(row)
        for row in chart_rows
    ]

    full_labels = [
        full_route_label(row)
        for row in chart_rows
    ]

    values = [
        float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    observations = [
        int(
            row.get(
                "observations",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    average_delays = [
        float(
            row.get(
                "average_delay_minutes",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    custom_data = [
        [
            observations[index],
            average_delays[index],
        ]
        for index in range(
            len(chart_rows)
        )
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            width=.58,
            marker=dict(
                color=values,
                colorscale=[
                    [0.0, "#fda4af"],
                    [0.48, "#fb7185"],
                    [1.0, "#ef4444"],
                ],
                line=dict(
                    width=0,
                ),
            ),
            text=[
                f"{value:.1f}%"
                for value in values
            ],
            textposition="outside",
            textfont=dict(
                color="#475569",
                size=9,
            ),
            customdata=custom_data,
            hovertext=full_labels,
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Delayed: %{x:.2f}%<br>"
                "Observations: "
                "%{customdata[0]:,}<br>"
                "Average delay: "
                "%{customdata[1]:.2f} min"
                "<extra></extra>"
            ),
        )
    )

    base_chart_layout(
        figure,
        height=330,
    )

    figure.update_layout(
        margin=dict(
            l=50,
            r=48,
            t=10,
            b=28,
        ),
        bargap=.28,
    )

    figure.update_xaxes(
        title="Delayed observations (%)",
        rangemode="tozero",
    )

    figure.update_yaxes(
        title=None,
        gridcolor="rgba(0,0,0,0)",
        automargin=True,
    )

    return figure


def create_time_performance_chart(
    rows,
):
    periods = [
        row.get(
            "time_period",
            "Unknown",
        )
        for row in rows
    ]

    delayed = [
        float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )
        for row in rows
    ]

    average_delay = [
        float(
            row.get(
                "average_delay_minutes",
                0,
            )
            or 0
        )
        for row in rows
    ]

    figure = make_subplots(
        specs=[
            [
                {
                    "secondary_y": True,
                }
            ]
        ]
    )

    figure.add_trace(
        go.Bar(
            x=periods,
            y=delayed,
            name="Delay Rate (%)",
            marker=dict(
                color="#fb7185",
            ),
            opacity=.93,
            text=[
                f"{value:.1f}%"
                for value in delayed
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Delay rate: %{y:.2f}%"
                "<extra></extra>"
            ),
        ),
        secondary_y=False,
    )

    figure.add_trace(
        go.Scatter(
            x=periods,
            y=average_delay,
            name="Average Delay (min)",
            mode="lines+markers",
            line=dict(
                color="#2563eb",
                width=3,
            ),
            marker=dict(
                size=7,
                color="#2563eb",
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Average delay: "
                "%{y:.2f} min"
                "<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    figure.update_layout(
        height=330,
        margin=dict(
            l=14,
            r=14,
            t=22,
            b=34,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(
            family="Inter, Segoe UI, sans-serif",
            color="#475569",
            size=9,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(
                size=8,
                color="#334155",
            ),
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_color="#ffffff",
            bordercolor="#0f172a",
        ),
    )

    figure.update_xaxes(
        gridcolor="#e8eef5",
        linecolor="#dce5ef",
        tickfont=dict(
            size=8,
            color="#475569",
        ),
    )

    figure.update_yaxes(
        title_text="Delay rate (%)",
        gridcolor="#e8eef5",
        linecolor="#dce5ef",
        tickfont=dict(
            size=8,
            color="#475569",
        ),
        title_font=dict(
            size=9,
            color="#334155",
        ),
        secondary_y=False,
    )

    figure.update_yaxes(
        title_text="Avg delay (min)",
        gridcolor="rgba(0,0,0,0)",
        tickfont=dict(
            size=8,
            color="#64748b",
        ),
        title_font=dict(
            size=9,
            color="#475569",
        ),
        secondary_y=True,
    )

    return figure


def create_problem_stops_chart(
    rows,
):
    chart_rows = list(
        reversed(
            rows[:10]
        )
    )

    stop_names = [
        row.get(
            "stop_name",
            row.get(
                "stop_id",
                "Unknown",
            ),
        )
        for row in chart_rows
    ]

    delayed = [
        float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    observations = [
        int(
            row.get(
                "observations",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=delayed,
            y=stop_names,
            orientation="h",
            width=.58,
            marker=dict(
                color=delayed,
                colorscale="YlOrRd",
                line=dict(
                    width=0,
                ),
            ),
            text=[
                f"{value:.1f}%"
                for value in delayed
            ],
            textposition="outside",
            customdata=observations,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Delayed: %{x:.2f}%<br>"
                "Observations: "
                "%{customdata:,}"
                "<extra></extra>"
            ),
        )
    )

    base_chart_layout(
        figure,
        height=370,
    )

    figure.update_layout(
        margin=dict(
            l=100,
            r=45,
            t=10,
            b=30,
        ),
    )

    figure.update_xaxes(
        title="Delayed observations (%)",
        rangemode="tozero",
    )

    figure.update_yaxes(
        title=None,
        gridcolor="rgba(0,0,0,0)",
        tickfont=dict(
            size=8,
            color="#334155",
        ),
        automargin=True,
    )

    return figure


def create_problem_stops_map(
    rows,
):
    valid_rows = []

    for row in rows:
        if (
            row.get("stop_lat")
            is not None
            and row.get("stop_lon")
            is not None
        ):
            valid_rows.append(
                row
            )

    if not valid_rows:
        return None

    latitudes = [
        float(
            row["stop_lat"]
        )
        for row in valid_rows
    ]

    longitudes = [
        float(
            row["stop_lon"]
        )
        for row in valid_rows
    ]

    delayed = [
        float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )
        for row in valid_rows
    ]

    marker_sizes = [
        min(
            25,
            max(
                8,
                8 + value * .28,
            ),
        )
        for value in delayed
    ]

    hover_text = []

    for row in valid_rows:
        stop_name = row.get(
            "stop_name",
            row.get(
                "stop_id",
                "Unknown",
            ),
        )

        observations = int(
            row.get(
                "observations",
                0,
            )
            or 0
        )

        delayed_pct = float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )

        avg_delay = float(
            row.get(
                "average_delay_minutes",
                0,
            )
            or 0
        )

        hover_text.append(
            (
                f"<b>{stop_name}</b><br>"
                f"Observations: "
                f"{observations:,}<br>"
                f"Delayed: "
                f"{delayed_pct:.2f}%<br>"
                f"Average delay: "
                f"{avg_delay:.2f} min"
            )
        )

    centre_lat = (
        sum(latitudes)
        / len(latitudes)
    )

    centre_lon = (
        sum(longitudes)
        / len(longitudes)
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scattermap(
            lat=latitudes,
            lon=longitudes,
            mode="markers",
            marker={
                "size":
                    marker_sizes,

                "color":
                    delayed,

                "colorscale":
                    "YlOrRd",

                "showscale":
                    True,

                "colorbar": {
                    "title": {
                        "text":
                            "Delay %"
                    },
                    "thickness":
                        10,
                },

                "opacity":
                    .85,
            },
            text=hover_text,
            hovertemplate=(
                "%{text}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        map={
            "style":
                "open-street-map",

            "center": {
                "lat":
                    centre_lat,

                "lon":
                    centre_lon,
            },

            "zoom":
                9,
        },
        height=370,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return figure


# ============================================================
# API HEALTH
# ============================================================

api_connected = False

try:
    health_response = requests.get(
        f"{API_URL}/health",
        timeout=API_TIMEOUT,
    )

    if (
        health_response.status_code
        == 200
    ):
        api_connected = True

except requests.RequestException:
    api_connected = False


# ============================================================
# CURRENT AUCKLAND TIME
# ============================================================

try:
    now_nz = datetime.now(
        ZoneInfo(
            "Pacific/Auckland"
        )
    )

    date_text = now_nz.strftime(
        "%a, %d %b %Y"
    )

    time_text = now_nz.strftime(
        "%I:%M %p"
    ).lstrip("0")

except Exception:
    date_text = (
        "Auckland, New Zealand"
    )

    time_text = ""


# ============================================================
# PREMIUM TOP BAR + REAL CLICKABLE NAVIGATION
# ============================================================

api_class = (
    "api-pill"
    if api_connected
    else "api-pill offline"
)

api_text = (
    "API Connected"
    if api_connected
    else "API Offline"
)

st.html(
    f"""
    <div class="premium-topbar">
        <div class="premium-brand">
            <div class="premium-brand-mark">
                🚌
            </div>

            <div>
                <div class="premium-brand-title">
                    NZ Transit Intelligence
                </div>

                <div class="premium-brand-sub">
                    Data. Insights. A More Connected Auckland.
                </div>
            </div>
        </div>

        <div class="topbar-right">
            <div class="{api_class}">
                <span class="api-dot"></span>
                {api_text}
            </div>

            <div class="clock-wrap">
                <div class="clock-date">
                    {safe(date_text)}
                </div>

                <div class="clock-time">
                    {safe(time_text)}
                </div>
            </div>
        </div>
    </div>
    """
)

nav_choice = st.segmented_control(
    "Dashboard navigation",
    options=[
        "Home",
        "Analytics",
        "Prediction",
        "Network",
        "About",
    ],
    default="Home",
    selection_mode="single",
    label_visibility="collapsed",
    key="dashboard_nav",
)

if nav_choice is None:
    nav_choice = "Home"


# ============================================================
# ALWAYS-VISIBLE SIDEBAR TOGGLE
# ============================================================

with st.container(key="sidebar_toggle_container"):
    components.html(
        """
        <!doctype html>
        <html>
        <head>
            <style>
                html,
                body {
                    margin: 0;
                    padding: 0;
                    width: 42px;
                    height: 42px;
                    overflow: hidden;
                    background: transparent;
                }
    
                #sidebar-toggle {
                    width: 42px;
                    height: 42px;
    
                    display: flex;
                    align-items: center;
                    justify-content: center;
    
                    padding: 0;
    
                    border: 1px solid rgba(255,255,255,.18);
                    border-radius: 11px;
    
                    background:
                        linear-gradient(
                            145deg,
                            #183b63,
                            #102b4d
                        );
    
                    color: #ffffff;
    
                    font-family:
                        Arial,
                        sans-serif;
    
                    font-size: 21px;
                    font-weight: 900;
                    letter-spacing: -5px;
                    line-height: 1;
    
                    cursor: pointer;
    
                    box-shadow:
                        0 7px 18px rgba(3,12,24,.28);
                }
    
                #sidebar-toggle:hover {
                    background:
                        linear-gradient(
                            145deg,
                            #215184,
                            #15375e
                        );
                }
    
                @media (max-width: 760px) {
                    html,
                    body,
                    #sidebar-toggle {
                        width: 38px;
                        height: 38px;
                    }
    
                    #sidebar-toggle {
                        font-size: 19px;
                    }
                }
            </style>
        </head>
    
        <body>
            <button
                id="sidebar-toggle"
                type="button"
                title="Open or close prediction menu"
                aria-label="Open or close prediction menu"
            >
                ❮❮
            </button>
    
            <script>
            (() => {
                const parentWindow = window.parent;
                const parentDoc = parentWindow.document;
                const button =
                    document.getElementById(
                        "sidebar-toggle"
                    );
    
                function getSidebar() {
                    return parentDoc.querySelector(
                        '[data-testid="stSidebar"]'
                    );
                }
    
                function getNativeToggle() {
                    const selectors = [
                        '[data-testid="stSidebarCollapseButton"] button',
                        '[data-testid="stSidebarCollapseButton"]',
                        '[data-testid="stSidebarCollapsedControl"] button',
                        '[data-testid="stSidebarCollapsedControl"]',
                        '[data-testid="collapsedControl"] button',
                        '[data-testid="collapsedControl"]',
                        'button[aria-label="Open sidebar"]',
                        'button[aria-label="Close sidebar"]',
                        'button[title="Open sidebar"]',
                        'button[title="Close sidebar"]'
                    ];

                    for (const selector of selectors) {
                        const element =
                            parentDoc.querySelector(
                                selector
                            );

                        if (element) {
                            return element;
                        }
                    }

                    return null;
                }

                function sidebarIsOpen() {
                    const sidebar =
                        getSidebar();

                    if (!sidebar) {
                        return false;
                    }

                    const ariaExpanded =
                        sidebar.getAttribute(
                            "aria-expanded"
                        );

                    if (ariaExpanded !== null) {
                        return ariaExpanded === "true";
                    }

                    const rect =
                        sidebar.getBoundingClientRect();

                    return (
                        rect.width > 80
                        && rect.right > 20
                    );
                }

                function updateArrow() {
                    const expanded =
                        sidebarIsOpen();

                    button.textContent =
                        expanded
                        ? "❮❮"
                        : "❯❯";

                    button.title =
                        expanded
                        ? "Close prediction menu"
                        : "Open prediction menu";
                }

                function openSidebarOnFirstMobileVisit() {
                    if (
                        parentWindow.innerWidth > 760
                    ) {
                        return;
                    }

                    const storageKey =
                        "nz_transit_mobile_sidebar_initialized_v2";

                    if (
                        parentWindow.sessionStorage.getItem(
                            storageKey
                        ) === "1"
                    ) {
                        return;
                    }

                    parentWindow.sessionStorage.setItem(
                        storageKey,
                        "1"
                    );

                    setTimeout(
                        () => {
                            if (!sidebarIsOpen()) {
                                const nativeToggle =
                                    getNativeToggle();

                                if (nativeToggle) {
                                    nativeToggle.click();

                                    setTimeout(
                                        updateArrow,
                                        180
                                    );
                                }
                            }
                        },
                        650
                    );
                }

                button.addEventListener(
                    "click",
                    () => {
                        const nativeToggle =
                            getNativeToggle();
    
                        if (nativeToggle) {
                            nativeToggle.click();
    
                            setTimeout(
                                updateArrow,
                                120
                            );
                        }
                    }
                );
    
                updateArrow();
                openSidebarOnFirstMobileVisit();
    
                const observer =
                    new MutationObserver(
                        updateArrow
                    );
    
                observer.observe(
                    parentDoc.body,
                    {
                        attributes: true,
                        childList: true,
                        subtree: true,
                        attributeFilter: [
                            "aria-expanded"
                        ]
                    }
                );
            })();
            </script>
        </body>
        </html>
        """,
        width=42,
        height=42,
        scrolling=False,
    )


# ============================================================
# SIDEBAR
# ============================================================

sidebar_html(
    """
    <div class="side-cta">
        <div class="side-cta-icon">
            ↗
        </div>

        <div>
            <div class="side-cta-title">
                Make a Prediction
            </div>

            <div class="side-cta-copy">
                Check the likelihood of a delay
            </div>
        </div>
    </div>

    <div class="side-section">
        Journey details
    </div>
    """
)


# ============================================================
# LOAD ROUTES
# ============================================================

routes = []

if api_connected:
    try:
        routes = (
            get_routes()
        )

    except requests.RequestException as error:
        st.sidebar.error(
            "Could not load GTFS routes."
        )

        st.sidebar.code(
            str(error)
        )


# ============================================================
# SIDEBAR INPUTS
# ============================================================

selected_route = None
selected_stop = None

route_id = None
stop_id = None
stop_sequence = None

direction_id = 0

stops = []


if routes:
    selected_route = (
        st.sidebar.selectbox(
            "Route",
            options=routes,
            format_func=route_label,
        )
    )

    route_id = selected_route[
        "route_id"
    ]

    direction_id = (
        st.sidebar.selectbox(
            "Direction",
            options=[
                0,
                1,
            ],
            format_func=lambda value: (
                f"Direction {value}"
            ),
        )
    )

    try:
        stops = get_route_stops(
            route_id,
            direction_id,
        )

    except requests.RequestException as error:
        stops = []

        st.sidebar.error(
            "Could not load stops."
        )

        st.sidebar.code(
            str(error)
        )

    if stops:
        selected_stop = (
            st.sidebar.selectbox(
                "Stop",
                options=stops,
                format_func=stop_label,
            )
        )

        stop_id = selected_stop[
            "stop_id"
        ]

        stop_sequence = int(
            selected_stop[
                "stop_sequence"
            ]
        )

        sidebar_html(
            f"""
            <div class="stop-meta">
                Stop ID:
                <strong>
                    {safe(stop_id)}
                </strong>
                <br>

                Stop sequence:
                <strong>
                    {safe(stop_sequence)}
                </strong>
            </div>
            """
        )

    else:
        st.sidebar.warning(
            "No stops found for this route and direction."
        )


local_hour = (
    st.sidebar.slider(
        "Hour of Day",
        min_value=0,
        max_value=23,
        value=17,
    )
)

day_number = (
    st.sidebar.selectbox(
        "Day",
        options=[
            1,
            2,
            3,
            4,
            5,
            6,
            7,
        ],
        format_func=lambda day: {
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday",
            7: "Sunday",
        }[day],
    )
)

predict_disabled = (
    not api_connected
    or selected_route is None
    or selected_stop is None
)

predict_clicked = (
    st.sidebar.button(
        "▶   Predict Delay",
        type="primary",
        width="stretch",
        disabled=predict_disabled,
    )
)

sidebar_html(
    """
    <div class="side-location">
        <strong>
            Auckland · New Zealand
        </strong>
        <br>
        Public transport for a brighter tomorrow.
    </div>
    """
)


# ============================================================
# SESSION STATE + PREDICTION
# ============================================================

if (
    "prediction_result"
    not in st.session_state
):
    st.session_state.prediction_result = None

if (
    "prediction_error"
    not in st.session_state
):
    st.session_state.prediction_error = None

if (
    "prediction_context"
    not in st.session_state
):
    st.session_state.prediction_context = None


if predict_clicked:
    payload = {
        "route_id":
            route_id,

        "stop_id":
            stop_id,

        "stop_sequence":
            stop_sequence,

        "direction_id":
            int(
                direction_id
            ),

        "local_hour":
            int(
                local_hour
            ),

        "day_number":
            int(
                day_number
            ),
    }

    try:
        with st.spinner(
            "Generating prediction..."
        ):
            response = requests.post(
                f"{API_URL}/predict-delay",
                json=payload,
                timeout=API_TIMEOUT,
            )

        if (
            response.status_code
            == 200
        ):
            st.session_state.prediction_result = (
                response.json()
            )

            st.session_state.prediction_error = (
                None
            )

            st.session_state.prediction_context = {
                "route":
                    route_label(
                        selected_route
                    ),

                "stop":
                    selected_stop.get(
                        "stop_name",
                        stop_id,
                    ),

                "stop_sequence":
                    stop_sequence,

                "direction":
                    direction_id,

                "hour":
                    local_hour,

                "day":
                    {
                        1: "Monday",
                        2: "Tuesday",
                        3: "Wednesday",
                        4: "Thursday",
                        5: "Friday",
                        6: "Saturday",
                        7: "Sunday",
                    }[day_number],
            }

        else:
            st.session_state.prediction_error = (
                response.text
            )

    except requests.RequestException as error:
        st.session_state.prediction_error = (
            str(error)
        )


# ============================================================
# LOAD ANALYTICS + MODEL INFO
# ============================================================

network_kpis = {}
time_rows = []
delayed_routes = []
problem_stops = []
model_info = {}


if api_connected:
    try:
        network_kpis = (
            get_network_kpis()
            or {}
        )
    except requests.RequestException:
        network_kpis = {}

    try:
        time_rows = (
            get_time_period_performance()
            or []
        )
    except requests.RequestException:
        time_rows = []

    try:
        delayed_routes = (
            get_top_delayed_routes()
            or []
        )
    except requests.RequestException:
        delayed_routes = []

    try:
        problem_stops = (
            get_problem_stops()
            or []
        )
    except requests.RequestException:
        problem_stops = []

    try:
        model_info = (
            get_model_info()
            or {}
        )
    except requests.RequestException:
        model_info = {}


if nav_choice == "Home":
    # ============================================================
    # HERO
    # ============================================================

    routes_value = int(
        network_kpis.get(
            "routes_observed",
            0,
        )
        or 0
    )

    stops_value = int(
        network_kpis.get(
            "stops_observed",
            0,
        )
        or 0
    )

    trips_value = int(
        network_kpis.get(
            "unique_trips",
            0,
        )
        or 0
    )

    observations_value = int(
        network_kpis.get(
            "total_observations",
            0,
        )
        or 0
    )


    st.html(
        f"""
        <div id="home"></div>

        <div class="hero">
            <div class="hero-content">
                <div class="hero-eyebrow">
                    Auckland public transport intelligence
                </div>

                <div class="hero-title">
                    Auckland Transport Analytics
                    &amp; Delay Prediction
                </div>

                <div class="hero-copy">
                    Real transport data, machine learning and
                    network analytics brought together in one
                    decision-support dashboard.
                </div>

                <div class="hero-kpis">
                    <div class="hero-kpi">
                        <div class="hero-kpi-icon">
                            🚌
                        </div>

                        <div>
                            <div class="hero-kpi-value">
                                {routes_value:,}
                            </div>

                            <div class="hero-kpi-label">
                                Routes Observed
                            </div>
                        </div>
                    </div>

                    <div class="hero-kpi">
                        <div class="hero-kpi-icon">
                            📍
                        </div>

                        <div>
                            <div class="hero-kpi-value">
                                {stops_value:,}
                            </div>

                            <div class="hero-kpi-label">
                                Stops Observed
                            </div>
                        </div>
                    </div>

                    <div class="hero-kpi">
                        <div class="hero-kpi-icon">
                            ↔
                        </div>

                        <div>
                            <div class="hero-kpi-value">
                                {trips_value:,}
                            </div>

                            <div class="hero-kpi-label">
                                Unique Trips
                            </div>
                        </div>
                    </div>

                    <div class="hero-kpi">
                        <div class="hero-kpi-icon">
                            ◉
                        </div>

                        <div>
                            <div class="hero-kpi-value">
                                {observations_value:,}
                            </div>

                            <div class="hero-kpi-label">
                                Total Observations
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="wake-note">
            ⏳ <strong>Free-tier hosting:</strong>
            the first visit after inactivity can take up to
            about one minute while the API wakes up.
        </div>
        """
    )



if nav_choice in ("Home", "Prediction"):
    # ============================================================
    # PREDICTION + MODEL
    # ============================================================

    st.html(
        '<div id="prediction"></div>'
    )

    prediction_column, model_column = (
        st.columns(
            [
                1.05,
                1,
            ],
            gap="medium",
        )
    )


    # ---------------- PREDICTION ----------------

    with prediction_column:
        st.html(
            """
            <div class="card-title">
                ✦ &nbsp;Prediction Result
            </div>

            <div class="card-copy">
                Machine-learning delay estimate for the
                selected journey.
            </div>
            """
        )

        result = (
            st.session_state.prediction_result
        )

        prediction_error = (
            st.session_state.prediction_error
        )

        context = (
            st.session_state.prediction_context
        )

        if prediction_error:
            st.error(
                "Prediction request failed."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(
                    prediction_error
                )

        elif result:
            probability = float(
                result.get(
                    "delay_probability_percent",
                    0,
                )
                or 0
            )

            risk = result.get(
                "risk_level",
                "Unknown",
            )

            delayed = bool(
                result.get(
                    "delayed",
                    False,
                )
            )

            time_period = result.get(
                "time_period",
                "Unknown",
            )

            is_weekend = bool(
                result.get(
                    "is_weekend",
                    False,
                )
            )

            gauge_column, result_column = (
                st.columns(
                    [
                        .78,
                        1.22,
                    ],
                    gap="small",
                )
            )

            with gauge_column:
                st.plotly_chart(
                    create_probability_ring(
                        probability
                    ),
                    width="stretch",
                    config={
                        "displayModeBar":
                            False,
                    },
                )

            with result_column:
                risk_class = (
                    "red"
                    if str(
                        risk
                    ).lower() in {
                        "high",
                        "very high",
                    }
                    else "amber"
                )

                prediction_class = (
                    "red"
                    if delayed
                    else "green"
                )

                selected_time = (
                    f"{int(context['hour']):02d}:00"
                    if context
                    else (
                        f"{int(local_hour):02d}:00"
                    )
                )

                st.html(
                    f"""
                    <div class="result-box {risk_class}">
                        <div class="result-label">
                            Risk Level
                        </div>

                        <div class="result-value">
                            {safe(risk)}
                        </div>
                    </div>

                    <div class="result-box {prediction_class}">
                        <div class="result-label">
                            Prediction
                        </div>

                        <div class="result-value">
                            {
                                "Delayed"
                                if delayed
                                else "Not Delayed"
                            }
                        </div>
                    </div>

                    <div class="result-box blue">
                        <div class="result-label">
                            Selected Time
                        </div>

                        <div class="result-value">
                            {safe(selected_time)}
                            ({safe(time_period)})
                        </div>
                    </div>
                    """
                )

            if delayed:
                st.error(
                    "⚠️ This journey is predicted to be delayed."
                )
            else:
                st.success(
                    "✓ This journey is currently predicted as not delayed."
                )

            if context:
                with st.expander(
                    "Journey summary"
                ):
                    summary_1, summary_2 = (
                        st.columns(2)
                    )

                    summary_1.write(
                        f"**Route:** "
                        f"{context['route']}"
                    )

                    summary_1.write(
                        f"**Stop:** "
                        f"{context['stop']}"
                    )

                    summary_1.write(
                        f"**Stop sequence:** "
                        f"{context['stop_sequence']}"
                    )

                    summary_2.write(
                        f"**Direction:** "
                        f"{context['direction']}"
                    )

                    summary_2.write(
                        f"**Journey time:** "
                        f"{context['hour']:02d}:00"
                    )

                    summary_2.write(
                        f"**Day:** "
                        f"{context['day']}"
                    )

                    summary_2.write(
                        f"**Weekend:** "
                        f"{'Yes' if is_weekend else 'No'}"
                    )

        else:
            st.html(
                """
                <div style="
                    min-height:250px;
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    justify-content:center;
                    text-align:center;
                    border:1px dashed #cbd5e1;
                    border-radius:15px;
                    background:#fbfdff;
                    padding:1.2rem;
                ">
                    <div style="
                        width:54px;
                        height:54px;
                        display:grid;
                        place-items:center;
                        border-radius:16px;
                        background:#eaf2ff;
                        font-size:1.35rem;
                        margin-bottom:.65rem;
                    ">
                        ✦
                    </div>

                    <div style="
                        color:#0f172a;
                        font-size:.96rem;
                        font-weight:850;
                    ">
                        Ready for a prediction
                    </div>

                    <div style="
                        color:#64748b;
                        font-size:.7rem;
                        line-height:1.5;
                        max-width:340px;
                        margin-top:.22rem;
                    ">
                        Choose route, direction, stop, hour
                        and day in the left panel, then click
                        Predict Delay.
                    </div>
                </div>
                """
            )


    # ---------------- MODEL INFO ----------------

    with model_column:
        st.html(
            '<div id="about"></div>'
        )

        if model_info:
            model_name = (
                model_info.get(
                    "model",
                    "Unknown",
                )
            )

            accuracy = float(
                model_info.get(
                    "accuracy",
                    0,
                )
                or 0
            )

            roc_auc = float(
                model_info.get(
                    "roc_auc",
                    0,
                )
                or 0
            )

            pr_auc = float(
                model_info.get(
                    "pr_auc",
                    0,
                )
                or 0
            )

            precision = float(
                model_info.get(
                    "precision",
                    0,
                )
                or 0
            )

            recall = float(
                model_info.get(
                    "recall",
                    0,
                )
                or 0
            )

            f1 = float(
                model_info.get(
                    "f1",
                    0,
                )
                or 0
            )

            st.html(
                f"""
                <div style="
                    display:flex;
                    align-items:center;
                    justify-content:space-between;
                    gap:.8rem;
                ">
                    <div>
                        <div class="card-title">
                            ⚙ &nbsp;Model Information
                        </div>

                        <div class="card-copy">
                            Transparent evaluation metrics for
                            the deployed classifier.
                        </div>
                    </div>

                    <div class="model-pill">
                        {safe(model_name)}
                    </div>
                </div>

                <div class="model-grid">
                    <div class="model-stat">
                        <div class="model-value">
                            {accuracy * 100:.2f}%
                        </div>

                        <div class="model-label">
                            Accuracy
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {roc_auc:.3f}
                        </div>

                        <div class="model-label">
                            ROC AUC
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {pr_auc:.3f}
                        </div>

                        <div class="model-label">
                            PR AUC
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {precision:.3f}
                        </div>

                        <div class="model-label">
                            Precision
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {recall:.3f}
                        </div>

                        <div class="model-label">
                            Recall
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {f1:.3f}
                        </div>

                        <div class="model-label">
                            F1 Score
                        </div>
                    </div>
                </div>

                <div class="model-note">
                    <strong>
                        How to read this
                    </strong>
                    <br>
                    The model estimates delay likelihood from
                    journey features. Accuracy is shown with
                    precision, recall, F1, ROC AUC and PR AUC
                    because delayed observations are an
                    imbalanced class.
                </div>
                """
            )

        else:
            st.info(
                "Model information is currently unavailable."
            )



if nav_choice in ("Home", "Network"):
    # ============================================================
    # NETWORK OVERVIEW — COMPACT STRIP
    # ============================================================

    st.html(
        '<div id="network"></div>'
    )

    section_header(
        "Network",
        "Network Overview",
        (
            "Key statistics from Auckland Transport "
            "realtime observations."
        ),
    )


    if network_kpis:
        average_delay = float(
            network_kpis.get(
                "average_delay_minutes",
                0,
            )
            or 0
        )

        median_delay = float(
            network_kpis.get(
                "median_delay_minutes",
                0,
            )
            or 0
        )

        delayed_percentage = float(
            network_kpis.get(
                "delayed_percentage",
                0,
            )
            or 0
        )

        on_time_percentage = float(
            network_kpis.get(
                "on_time_percentage",
                0,
            )
            or 0
        )

        st.html(
            f"""
            <div class="network-shell">
                <div class="network-head">
                    <div>
                        <div class="network-title">
                            Network Overview
                        </div>

                        <div class="network-sub">
                            Reliability snapshot from the
                            current analytics dataset.
                        </div>
                    </div>

                    <div class="data-badge">
                        ▣ Data period: recent collection
                    </div>
                </div>

                <div class="network-strip">
                    <div class="network-stat">
                        <div class="network-stat-icon">
                            ◉
                        </div>

                        <div class="network-stat-value">
                            {
                                int(
                                    network_kpis.get(
                                        "total_observations",
                                        0,
                                    )
                                    or 0
                                )
                            :,}
                        </div>

                        <div class="network-stat-label">
                            Observations
                        </div>
                    </div>

                    <div class="network-stat">
                        <div class="network-stat-icon">
                            ↔
                        </div>

                        <div class="network-stat-value">
                            {
                                int(
                                    network_kpis.get(
                                        "unique_trips",
                                        0,
                                    )
                                    or 0
                                )
                            :,}
                        </div>

                        <div class="network-stat-label">
                            Unique Trips
                        </div>
                    </div>

                    <div class="network-stat">
                        <div class="network-stat-icon">
                            🚌
                        </div>

                        <div class="network-stat-value">
                            {
                                int(
                                    network_kpis.get(
                                        "routes_observed",
                                        0,
                                    )
                                    or 0
                                )
                            :,}
                        </div>

                        <div class="network-stat-label">
                            Routes
                        </div>
                    </div>

                    <div class="network-stat">
                        <div class="network-stat-icon">
                            📍
                        </div>

                        <div class="network-stat-value">
                            {
                                int(
                                    network_kpis.get(
                                        "stops_observed",
                                        0,
                                    )
                                    or 0
                                )
                            :,}
                        </div>

                        <div class="network-stat-label">
                            Stops
                        </div>
                    </div>

                    <div class="network-stat">
                        <div class="network-stat-icon">
                            ◷
                        </div>

                        <div class="network-stat-value">
                            {average_delay:.2f} min
                        </div>

                        <div class="network-stat-label">
                            Average Delay
                        </div>
                    </div>

                    <div class="network-stat">
                        <div class="network-stat-icon">
                            ◴
                        </div>

                        <div class="network-stat-value">
                            {median_delay:.2f} min
                        </div>

                        <div class="network-stat-label">
                            Median Delay
                        </div>
                    </div>

                    <div class="network-stat">
                        <div class="network-stat-icon">
                            ▥
                        </div>

                        <div class="network-stat-value">
                            {delayed_percentage:.2f}%
                        </div>

                        <div class="network-stat-label">
                            Delayed
                        </div>
                    </div>

                    <div class="network-stat">
                        <div class="network-stat-icon">
                            ✓
                        </div>

                        <div class="network-stat-value">
                            {on_time_percentage:.2f}%
                        </div>

                        <div class="network-stat-label">
                            On Time
                        </div>
                    </div>
                </div>
            </div>
            """
        )

    else:
        st.warning(
            "Network analytics could not be loaded."
        )



if nav_choice in ("Home", "Analytics"):
    # ============================================================
    # ANALYTICS — ROUTES + TIME PERFORMANCE
    # ============================================================

    st.html(
        '<div id="analytics"></div>'
    )

    section_header(
        "Analytics",
        "Performance Intelligence",
        (
            "Compare route reliability and see how performance "
            "changes across different parts of the day."
        ),
    )

    routes_column, time_column = (
        st.columns(
            [
                1,
                1,
            ],
            gap="medium",
        )
    )


    with routes_column:
        st.html(
            """
            <div class="card-title">
                ▥ &nbsp;Routes with Highest Delay Rate
            </div>

            <div class="card-copy">
                Top routes ranked by delayed observations.
            </div>
            """
        )

        if delayed_routes:
            st.plotly_chart(
                create_top_routes_chart(
                    delayed_routes
                ),
                width="stretch",
                config={
                    "displayModeBar": False,
                },
            )
        else:
            st.info(
                "No route analytics available."
            )


    with time_column:
        st.html(
            """
            <div class="card-title">
                ◷ &nbsp;Performance by Time Period
            </div>

            <div class="card-copy">
                Delay rate and average delay by time of day.
            </div>
            """
        )

        if time_rows:
            st.plotly_chart(
                create_time_performance_chart(
                    time_rows
                ),
                width="stretch",
                config={
                    "displayModeBar": False,
                },
            )
        else:
            st.info(
                "No time-period analytics available."
            )


    # ------------------------------------------------------------
    # ROUTE + TIME DETAIL TABLES
    # ------------------------------------------------------------

    route_details_column, time_details_column = (
        st.columns(
            [
                1,
                1,
            ]
        )
    )


    with route_details_column:
        if delayed_routes:
            with st.expander(
                "View route performance data"
            ):
                route_table = []

                for row in delayed_routes:
                    route_table.append(
                        {
                            "Route":
                                full_route_label(
                                    row
                                ),

                            "Observations":
                                int(
                                    row.get(
                                        "observations",
                                        0,
                                    )
                                    or 0
                                ),

                            "Delay Observations":
                                int(
                                    row.get(
                                        "delay_observations",
                                        0,
                                    )
                                    or 0
                                ),

                            "Average Delay (min)":
                                round(
                                    float(
                                        row.get(
                                            "average_delay_minutes",
                                            0,
                                        )
                                        or 0
                                    ),
                                    2,
                                ),

                            "Delayed %":
                                round(
                                    float(
                                        row.get(
                                            "delayed_percentage",
                                            0,
                                        )
                                        or 0
                                    ),
                                    2,
                                ),

                            "On Time %":
                                round(
                                    float(
                                        row.get(
                                            "on_time_percentage",
                                            0,
                                        )
                                        or 0
                                    ),
                                    2,
                                ),
                        }
                    )

                st.dataframe(
                    route_table,
                    width="stretch",
                    hide_index=True,
                )


    with time_details_column:
        if time_rows:
            with st.expander(
                "View time-period data"
            ):
                time_table = []

                for row in time_rows:
                    time_table.append(
                        {
                            "Time Period":
                                row.get(
                                    "time_period"
                                ),

                            "Observations":
                                int(
                                    row.get(
                                        "observations",
                                        0,
                                    )
                                    or 0
                                ),

                            "Delay Observations":
                                int(
                                    row.get(
                                        "delay_observations",
                                        0,
                                    )
                                    or 0
                                ),

                            "Average Delay (min)":
                                round(
                                    float(
                                        row.get(
                                            "average_delay_minutes",
                                            0,
                                        )
                                        or 0
                                    ),
                                    2,
                                ),

                            "Delayed %":
                                round(
                                    float(
                                        row.get(
                                            "delayed_percentage",
                                            0,
                                        )
                                        or 0
                                    ),
                                    2,
                                ),
                        }
                    )

                st.dataframe(
                    time_table,
                    width="stretch",
                    hide_index=True,
                )


    # ============================================================
    # PROBLEM STOPS — GRAPH + MAP SIDE BY SIDE
    # ============================================================

    st.html(
        '<div id="stops"></div>'
    )

    section_header(
        "Hotspots",
        "Problem Stops",
        (
            "Identify stops with the highest observed delay rates "
            "and view their geographic distribution across Auckland."
        ),
    )

    problem_chart_column, problem_map_column = (
        st.columns(
            [
                1,
                1.15,
            ],
            gap="medium",
        )
    )


    with problem_chart_column:
        st.html(
            """
            <div class="card-title">
                ▥ &nbsp;Stops with Highest Delay Rate
            </div>

            <div class="card-copy">
                Top problem stops ranked by delayed observation percentage.
            </div>
            """
        )

        if problem_stops:
            st.plotly_chart(
                create_problem_stops_chart(
                    problem_stops
                ),
                width="stretch",
                config={
                    "displayModeBar": False,
                },
            )
        else:
            st.info(
                "No problem-stop analytics available."
            )


    with problem_map_column:
        st.html(
            """
            <div class="card-title">
                📍 &nbsp;Geographic Delay Hotspots
            </div>

            <div class="card-copy">
                Marker size and colour represent the observed delay rate.
            </div>
            """
        )

        if problem_stops:
            try:
                map_figure = (
                    create_problem_stops_map(
                        problem_stops
                    )
                )

                if (
                    map_figure
                    is not None
                ):
                    st.plotly_chart(
                        map_figure,
                        width="stretch",
                        config={
                            "displayModeBar": False,
                        },
                    )

                else:
                    st.info(
                        "No stop coordinates available."
                    )

            except Exception as error:
                st.warning(
                    "Problem stops map could not be displayed."
                )

                with st.expander(
                    "Technical details"
                ):
                    st.code(
                        str(error)
                    )

        else:
            st.info(
                "No problem-stop analytics available."
            )


    # ------------------------------------------------------------
    # PROBLEM STOP DATA TABLE — RESTORED
    # ------------------------------------------------------------

    if problem_stops:
        with st.expander(
            "View problem stop data"
        ):
            stop_table = []

            for row in problem_stops[:20]:
                stop_table.append(
                    {
                        "Stop":
                            row.get(
                                "stop_name"
                            ),

                        "Observations":
                            int(
                                row.get(
                                    "observations",
                                    0,
                                )
                                or 0
                            ),

                        "Delay Observations":
                            int(
                                row.get(
                                    "delay_observations",
                                    0,
                                )
                                or 0
                            ),

                        "Average Delay (min)":
                            round(
                                float(
                                    row.get(
                                        "average_delay_minutes",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),

                        "Maximum Delay (min)":
                            round(
                                float(
                                    row.get(
                                        "maximum_delay_minutes",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),

                        "Delayed %":
                            round(
                                float(
                                    row.get(
                                        "delayed_percentage",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),
                    }
                )

            st.dataframe(
                stop_table,
                width="stretch",
                hide_index=True,
            )




if nav_choice == "About":
    section_header(
        "About",
        "About NZ Transit Intelligence",
        (
            "An end-to-end Auckland public transport analytics "
            "and machine-learning decision-support project."
        ),
    )

    about_left, about_right = st.columns(
        [
            1.05,
            1,
        ],
        gap="medium",
    )

    with about_left:
        st.html(
            """
            <div class="premium-card">
                <div class="card-title">
                    Project Overview
                </div>

                <div class="card-copy" style="
                    font-size:.76rem;
                    line-height:1.72;
                    margin-top:.65rem;
                    color:#475569;
                ">
                    NZ Transit Intelligence combines Auckland Transport
                    GTFS and realtime observations with PostgreSQL analytics,
                    a deployed machine-learning model, FastAPI and Streamlit.
                    It supports network reliability analysis, delay-risk
                    prediction and geographic hotspot exploration.
                </div>
            </div>
            """
        )

    with about_right:
        st.html(
            """
            <div class="premium-card">
                <div class="card-title">
                    Technology Stack
                </div>

                <div class="card-copy" style="
                    font-size:.76rem;
                    line-height:1.82;
                    margin-top:.65rem;
                    color:#475569;
                ">
                    <strong>Data:</strong> Auckland Transport GTFS + realtime<br>
                    <strong>Database:</strong> PostgreSQL / Neon<br>
                    <strong>Backend:</strong> FastAPI / Render<br>
                    <strong>Machine Learning:</strong> Logistic Regression<br>
                    <strong>Frontend:</strong> Streamlit + Plotly<br>
                    <strong>Deployment:</strong> Streamlit Community Cloud
                </div>
            </div>
            """
        )

    if model_info:
        section_header(
            "Model",
            "Deployed Model Metrics",
            (
                "Evaluation metrics for the production "
                "delay classifier."
            ),
        )

        accuracy = float(
            model_info.get(
                "accuracy",
                0,
            )
            or 0
        )

        roc_auc = float(
            model_info.get(
                "roc_auc",
                0,
            )
            or 0
        )

        pr_auc = float(
            model_info.get(
                "pr_auc",
                0,
            )
            or 0
        )

        precision = float(
            model_info.get(
                "precision",
                0,
            )
            or 0
        )

        recall = float(
            model_info.get(
                "recall",
                0,
            )
            or 0
        )

        f1 = float(
            model_info.get(
                "f1",
                0,
            )
            or 0
        )

        st.html(
            f"""
            <div class="premium-card">
                <div class="model-grid">
                    <div class="model-stat">
                        <div class="model-value">
                            {accuracy * 100:.2f}%
                        </div>
                        <div class="model-label">
                            Accuracy
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {roc_auc:.3f}
                        </div>
                        <div class="model-label">
                            ROC AUC
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {pr_auc:.3f}
                        </div>
                        <div class="model-label">
                            PR AUC
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {precision:.3f}
                        </div>
                        <div class="model-label">
                            Precision
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {recall:.3f}
                        </div>
                        <div class="model-label">
                            Recall
                        </div>
                    </div>

                    <div class="model-stat">
                        <div class="model-value">
                            {f1:.3f}
                        </div>
                        <div class="model-label">
                            F1 Score
                        </div>
                    </div>
                </div>
            </div>
            """
        )



# ============================================================
# FOOTER
# ============================================================

st.html(
    f"""
    <div class="premium-footer">
        <div>
            <strong>
                🚌 NZ Transit Intelligence
            </strong>
            <br>
            Built with real Auckland Transport data,
            PostgreSQL, ML, FastAPI and Streamlit.
        </div>

        <div>
            Data for better cities

            <a
                href="https://github.com/adityabhati711-jpg/nz-transit-intelligence"
                target="_blank"
            >
                GitHub ↗
            </a>

            <a
                href="{safe(API_URL)}/docs"
                target="_blank"
            >
                API Docs ↗
            </a>
        </div>
    </div>
    """
)
