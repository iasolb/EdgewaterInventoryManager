"""
Edgewater Farm — Brand Theme
=============================
Streamlit config.toml + CSS theming for the inventory management system.

The palette draws from the farm's visual identity:
- Deep sage green (#4A7C59) — greenhouses, growing things, primary actions
- Warm cream (#FDFBF7) — clean backgrounds like the farm's white-washed buildings
- Rich brown (#2C2417) — Connecticut River valley soil, text
- Soft lavender (#8B7BA5) — from the website's border, used as an accent
- Strawberry red (#C4453C) — PYO strawberries, alerts, destructive actions
- Harvest gold (#B8860B) — autumn crops, warnings, highlights
- River blue (#5B8BA0) — Connecticut River, informational elements

Usage:
    from edgewater_theme import apply_theme, COLORS

    # At the top of any page, after st.set_page_config():
    apply_theme()
"""

import streamlit as st

# ================================================================
# Brand Color Constants
# ================================================================

COLORS = {
    # Primary
    "sage": "#4A7C59",  # Primary green — actions, buttons, links
    "sage_light": "#6B9B7A",  # Lighter sage for hover states
    "sage_dark": "#3A6247",  # Darker sage for pressed/active
    "sage_bg": "#E8F0EB",  # Very light sage for success backgrounds
    # Neutrals
    "cream": "#FDFBF7",  # Page background
    "cream_dark": "#F3EDE4",  # Secondary background, cards, sidebar
    "cream_darker": "#E8DFD1",  # Borders, dividers
    "brown": "#2C2417",  # Primary text
    "brown_light": "#5C4F3D",  # Secondary text
    "brown_muted": "#8C7F6D",  # Muted text, captions, placeholders
    # Accents
    "lavender": "#8B7BA5",  # From website — subtle accent, tags
    "lavender_light": "#D4CCE0",  # Light lavender for backgrounds
    "strawberry": "#C4453C",  # Alerts, destructive actions
    "strawberry_light": "#F5E0DE",  # Error backgrounds
    "gold": "#B8860B",  # Warnings, highlights
    "gold_light": "#F5ECD4",  # Warning backgrounds
    "river": "#5B8BA0",  # Info elements
    "river_light": "#DDE8ED",  # Info backgrounds
}

# ================================================================
# CSS Theme
# ================================================================

_THEME_CSS = """
<style>
    /* ========== GLOBAL ========== */
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Source+Sans+3:wght@300;400;500;600&display=swap');

    /* Base typography */
    html, body, [class*="css"] {
        font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #2C2417;
    }

    /* Headings — Lora serif for warmth and heritage feel */
    h1, h2, h3 {
        font-family: 'Lora', Georgia, 'Times New Roman', serif !important;
        color: #2C2417 !important;
        font-weight: 600 !important;
    }

    h1 { letter-spacing: -0.01em; }

    /* ========== MAIN CONTAINER ========== */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #FDFBF7;
    }

    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] {
        background-color: #F3EDE4;
        border-right: 1px solid #E8DFD1;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #2C2417 !important;
    }

    /* ========== BUTTONS ========== */
    /* Primary buttons */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background-color: #4A7C59 !important;
        border-color: #4A7C59 !important;
        color: white !important;
        font-weight: 500;
        border-radius: 6px;
        transition: all 0.15s ease;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background-color: #3A6247 !important;
        border-color: #3A6247 !important;
    }

    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        border-color: #E8DFD1 !important;
        color: #5C4F3D !important;
        background-color: #FDFBF7 !important;
        border-radius: 6px;
        transition: all 0.15s ease;
    }

    .stButton > button[kind="secondary"]:hover {
        border-color: #4A7C59 !important;
        color: #4A7C59 !important;
        background-color: #E8F0EB !important;
    }

    /* ========== INPUTS ========== */
    .stTextInput > div > div,
    .stTextArea > div > div,
    .stNumberInput > div > div,
    .stSelectbox > div > div,
    .stMultiselect > div > div {
        border-color: #E8DFD1 !important;
        border-radius: 6px !important;
    }

    .stTextInput > div > div:focus-within,
    .stTextArea > div > div:focus-within,
    .stNumberInput > div > div:focus-within,
    .stSelectbox > div > div:focus-within,
    .stMultiselect > div > div:focus-within {
        border-color: #4A7C59 !important;
        box-shadow: 0 0 0 1px #4A7C59 !important;
    }

    /* ========== DATAFRAMES & TABLES ========== */
    [data-testid="stDataFrame"] {
        border: 1px solid #E8DFD1;
        border-radius: 8px;
        overflow: hidden;
    }

    /* ========== EXPANDERS ========== */
    .streamlit-expanderHeader {
        font-family: 'Source Sans 3', sans-serif;
        font-weight: 500;
        color: #2C2417;
        background-color: #F3EDE4;
        border-radius: 6px;
    }

    /* ========== TABS ========== */
    .stTabs [data-baseweb="tab"] {
        font-family: 'Source Sans 3', sans-serif;
        font-weight: 500;
        color: #5C4F3D;
    }

    .stTabs [aria-selected="true"] {
        color: #4A7C59 !important;
        border-bottom-color: #4A7C59 !important;
    }

    /* ========== METRICS ========== */
    [data-testid="stMetricValue"] {
        font-family: 'Lora', Georgia, serif;
        color: #2C2417;
    }

    [data-testid="stMetricLabel"] {
        color: #5C4F3D;
    }

    /* ========== ALERTS ========== */
    .stAlert [data-testid="stNotificationContentInfo"] {
        background-color: #DDE8ED;
        color: #2C2417;
    }

    .stAlert [data-testid="stNotificationContentSuccess"] {
        background-color: #E8F0EB;
        color: #2C2417;
    }

    .stAlert [data-testid="stNotificationContentWarning"] {
        background-color: #F5ECD4;
        color: #2C2417;
    }

    .stAlert [data-testid="stNotificationContentError"] {
        background-color: #F5E0DE;
        color: #2C2417;
    }

    /* ========== DIVIDERS ========== */
    hr {
        border-color: #E8DFD1 !important;
    }

    /* ========== LINKS ========== */
    a {
        color: #4A7C59 !important;
    }
    a:hover {
        color: #3A6247 !important;
    }

    /* ========== CAPTIONS & SMALL TEXT ========== */
    .stCaption, small {
        color: #8C7F6D !important;
    }

    /* ========== CHECKBOXES ========== */
    .stCheckbox label span[data-testid="stCheckbox"] {
        color: #2C2417;
    }

    /* ========== DOWNLOAD BUTTON ========== */
    .stDownloadButton > button {
        border-color: #E8DFD1 !important;
        color: #5C4F3D !important;
        border-radius: 6px;
    }

    .stDownloadButton > button:hover {
        border-color: #4A7C59 !important;
        color: #4A7C59 !important;
    }

    /* ========== CUSTOM STATUS BADGES (for order tracking) ========== */
    .status-received {
        background: #E8F0EB;
        color: #3A6247;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .status-pending {
        background: #F5ECD4;
        color: #8B6914;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .status-overdue {
        background: #F5E0DE;
        color: #9E3A33;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .supplier-badge {
        background: #4A7C59;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }

    .cost-badge {
        background: #B8860B;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }

    .count-badge {
        background: #8B7BA5;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
        display: inline-block;
    }
</style>
"""


def apply_theme():
    """
    Apply the Edgewater Farm brand theme.
    Call once per page, right after st.set_page_config().
    """
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


def brand_header(title: str, icon: str = "🌿"):
    """Render a branded page header with the farm's style."""
    st.markdown(
        f"""
        <div style="
            padding: 1rem 0 0.5rem;
            border-bottom: 2px solid #E8DFD1;
            margin-bottom: 1rem;
        ">
            <h1 style="
                font-family: 'Lora', Georgia, serif;
                color: #2C2417;
                margin: 0;
                font-size: 1.8rem;
            ">{icon} {title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
