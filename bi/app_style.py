"""The global stylesheets of the panel (D-541): the theme, the app's own CSS, the code colors and the menu with its
activity bar. Streamlit has no stylesheet file of its own, so each function writes the CSS of the chosen theme and the
panel injects it; the page stylesheets stay with their pages.
"""

import base64

from bi import activity_bar, charts, zoom

# region Constants
# Code colors for the light themes: Streamlit's own steps fall under 3:1 on white,
# so each kind of token takes a darker step of its hue (4.5:1 or more).
LIGHT_CODE_COLORS = {
    "string": "#15803d",
    "boolean": "#15803d",
    "number": "#0f766e",
    "operator": "#c2410c",
    "keyword": "#1d4ed8",
    "function": "#1d4ed8",
    "comment": "#57606a",
    "punctuation": "#57606a",
}


# (text, heading, icon, hover fill, current fill, accent bar, hairline) for dark and light sidebars.
MENU_INK = {
    True: (
        "#cfd4dc",
        "#8b929c",
        "#aeb5bf",
        "rgba(255,255,255,.04)",
        "rgba(255,255,255,.07)",
        "#3b9eff",
        "rgba(255,255,255,.08)",
    ),
    False: (
        "#2b3340",
        "#596069",  # D-323: 4.5:1 on the lightest sidebar (Blue Light)
        "#4b5563",
        "rgba(15,23,42,.04)",
        "rgba(15,23,42,.07)",
        "#1d5fbf",
        "rgba(15,23,42,.09)",
    ),
}


ACTIVITY_BAR = 40  # D-539: the width of the column of icons on the menu's left edge, like VS Code's activity bar


# A dashboard in miniature: three figures over a bar chart and a line, in the colours of the charts.
DASHBOARD_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 46"><rect x="1" y="1" width="62" height="44" rx="6" '
    'fill="#1d3557" stroke="#5aa9ea" stroke-width="1.5"/><rect x="6" y="6" width="15" height="8" rx="2" fill="#5aa9ea"/>'
    '<rect x="24.5" y="6" width="15" height="8" rx="2" fill="#5fd39b"/><rect x="43" y="6" width="15" height="8" rx="2" '
    'fill="#f0b347"/><rect x="7" y="31" width="5" height="9" rx="1" fill="#8ac6f5"/><rect x="15" y="26" width="5" '
    'height="14" rx="1" fill="#8ac6f5"/><rect x="23" y="21" width="5" height="19" rx="1" fill="#8ac6f5"/>'
    '<path d="M34 37l7-8 6 4 11-12" fill="none" stroke="#5fd39b" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round"/></svg>'
)


# D-452: the same dashboard, split in two sources side by side, each with its own latest week.
CHANNELS_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 46"><rect x="1" y="1" width="62" height="44" rx="6" '
    'fill="#1d3557" stroke="#5aa9ea" stroke-width="1.5"/><path d="M32 6v34" stroke="#5aa9ea" stroke-width="1.2" '
    'stroke-dasharray="2 2"/><rect x="6" y="6" width="21" height="7" rx="2" fill="#5fd39b"/><rect x="37" y="6" '
    'width="21" height="7" rx="2" fill="#f0b347"/><rect x="8" y="27" width="5" height="13" rx="1" fill="#8ac6f5"/>'
    '<rect x="16" y="21" width="5" height="19" rx="1" fill="#8ac6f5"/><rect x="39" y="24" width="5" height="16" rx="1" '
    'fill="#8ac6f5"/><rect x="47" y="18" width="5" height="22" rx="1" fill="#8ac6f5"/></svg>'
)


# D-456: «Análisis»: a report with a line over bars and a magnifier, the history read closely.
BA_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 46"><rect x="1" y="1" width="62" height="44" rx="6" '
    'fill="#1d3557" stroke="#5aa9ea" stroke-width="1.5"/><rect x="7" y="27" width="5" height="12" rx="1" fill="#8ac6f5"/>'
    '<rect x="15" y="21" width="5" height="18" rx="1" fill="#8ac6f5"/><rect x="23" y="24" width="5" height="15" rx="1" '
    'fill="#8ac6f5"/><path d="M7 19l9-7 8 5 10-9" fill="none" stroke="#f0b347" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round"/><circle cx="46" cy="25" r="9" fill="#1d3557" stroke="#5fd39b" stroke-width="3"/>'
    '<path d="M52.5 31.5l6 6" stroke="#5fd39b" stroke-width="3.4" stroke-linecap="round"/></svg>'
)


SOURCES_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 50"><ellipse cx="28" cy="10" rx="20" ry="6" '
    'fill="#5fd39b"/><path d="M8 10v28c0 3.3 9 6 20 6s20-2.7 20-6V10c0 3.3-9 6-20 6S8 13.3 8 10z" '
    'fill="#2fb57a"/><path d="M8 24c0 3.3 9 6 20 6s20-2.7 20-6" fill="none" stroke="#5fd39b" stroke-width="2"/>'
    '<circle cx="50" cy="38" r="10" fill="#1f8f5f"/><path d="M46 42l8-8M49 34h5v5" fill="none" stroke="#fff" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


# A Finder-like folder, two blues, drawn once as an image the menu shows above «Documentos».
# D-533: the folder of the study of the source, in the green of its notebooks.
STUDY_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 50"><path d="M3 9a5 5 0 0 1 5-5h15.5'
    'a4 4 0 0 1 3 1.3L30 9h26a5 5 0 0 1 5 5v4H3z" fill="#22b35a"/><rect x="3" y="14" width="58" height="33" '
    'rx="5" fill="#5fd39b"/><rect x="3" y="14" width="58" height="3" fill="#8fe3b8"/></svg>'
)


FOLDER_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 50"><path d="M3 9a5 5 0 0 1 5-5h15.5'
    'a4 4 0 0 1 3 1.3L30 9h26a5 5 0 0 1 5 5v4H3z" fill="#5aa9ea"/><rect x="3" y="14" width="58" height="33" '
    'rx="5" fill="#8ac6f5"/><rect x="3" y="14" width="58" height="3" fill="#a9d6f8"/></svg>'
)
# endregion


# region Colors
def is_dark_surface(color):
    """Whether a hex surface needs the luminous brand colors."""
    rgb = tuple(int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return sum(rgb) / 3 < 0.5


# endregion


# region App styles
def build_theme_css(palette):
    """Page, sidebar and links in the colors of the active theme (T-44, D-052).

    Streamlit's own widgets keep the colors of its base mode; the theme only
    restyles what it can do without fighting them.
    """
    return f"""
    /* D-501: without this, a Mac thickens light text on a dark background. */
    html, body, .stApp {{ -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; }}
    .stApp {{ background: {palette["background"]}; color:{palette["text"]};
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    [data-testid="stMain"] p, [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] label, [data-testid="stMain"] input {{
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    [data-testid="stMain"] h1 {{font-weight:500 !important; letter-spacing:-.035em;}}
    [data-testid="stMain"] h2, [data-testid="stMain"] h3 {{font-weight:500 !important; letter-spacing:-.02em;}}
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{ color:{palette["text"]}; }}
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {{ color:{palette["text"]}; }}
    [data-testid="stHeading"] h1, [data-testid="stHeading"] h2,
    [data-testid="stHeading"] h3, [data-testid="stHeading"] h4 {{color:{palette["strong_text"]};}}
    [data-testid="stExpander"] details {{background:{palette["card"]}; border-color:{palette["card_border"]};}}
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p,
    [data-baseweb="tab"] p {{color:{palette["text"]};}}
    [data-testid="stPopoverBody"], [data-testid="stDialog"] [role="dialog"] {{
        background:{palette["card"]}; color:{palette["text"]};}}
    [data-testid="stRadio"] p {{color:{palette["text"]};}}
    [data-baseweb="select"] > div, [data-baseweb="input"],
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{
        background:{palette["field"]}; color:{palette["strong_text"]}; border-color:{palette["card_border"]};}}
    [data-baseweb="select"] input {{color:{palette["strong_text"]};}}
    [data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] [role="option"] {{
        background:{palette["field"]}; color:{palette["strong_text"]};}}
    [data-baseweb="popover"] [role="option"]:hover {{background:{palette["card"]};}}
    button[kind="secondary"], button[kind="secondaryFormSubmit"] {{
        background:{palette["card"]}; color:{palette["strong_text"]}; border-color:{palette["card_border"]};}}

    /* Desktop navigation stays in normal flow. On mobile the fixed logo bar
       needs an opaque surface so scrolling text never crosses the logo. */
    [data-testid="stHeader"] {{ background: transparent; }}
    @media(max-width:800px) {{
        [data-testid="stHeader"] {{background:{palette['background']};}}
    }}
    /* The app owns its four themes; hide Streamlit's duplicate theme/utility menu.
       Keep the header itself so the sidebar toggle and GreenOcean logo still work. */
    [data-testid="stMainMenu"] {{ display:none !important; }}
    /* D-328: Streamlit Cloud draws its owner actions (Share, star, edit) over the page bar's right end. */
    [data-testid="stToolbarActions"], [data-testid="stToolbarActionButton"] {{ display:none !important; }}
    [data-testid="stHeader"], [data-testid="stHeader"] * {{pointer-events:none !important;}}
    [data-testid="stHeader"] button, [data-testid="stHeader"] button *,
    [data-testid="stHeader"] a, [data-testid="stHeader"] a * {{pointer-events:auto !important;}}
    [data-testid="stSidebar"] {{ background: {palette["sidebar"]}; }}
    /* Streamlit's local file watcher is a floating developer control. It can
       cover report content when the viewport is narrow, so it is never part
       of the presentation UI. */
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: {palette["sidebar_text"]};
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stPageLink"] p,
    [data-testid="stSidebar"] [data-testid="stPageLink"] span {{ color:{palette["sidebar_text"]}; }}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a {{ background:transparent !important; }}
    [data-testid="stSidebarNavLink"][aria-current="page"] {{
        box-shadow: inset 2px 0 0 {palette["accent"]}, 0 0 14px {palette["glow"]};
    }}
    [data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{
        color: {palette["accent"]};
    }}
    [data-testid="stMain"] a {{ color: {palette["accent"]}; }}
    /* Text on the accent color (the chips of a multiple choice), always readable. */
    [data-testid="stToolbar"] button, [data-testid="stToolbar"] button p,
    [data-testid="stToolbar"] svg {{ color:{palette["strong_text"]}; fill:{palette["strong_text"]}; }}
    [data-testid="stCode"] pre, [data-testid="stCode"] code {{
        background:{palette["field"]} !important; color:{palette["strong_text"]};
    }}
    [data-baseweb="tag"] span, [data-baseweb="tag"] svg {{
        color: {palette["on_accent"]}; fill: {palette["on_accent"]};
    }}
    button[kind="primary"], button[kind="primaryFormSubmit"] {{
        background:{palette["accent"]}; color:{palette["on_accent"]};
    }}
    button[kind="primary"] p, button[kind="primaryFormSubmit"] p {{
        color:{palette["on_accent"]} !important;
    }}
    .hint {{ color: {palette["accent"]} !important; }}
    """


def build_code_colors_css(palette):
    """Darker code tokens on the light themes; Vantablack keeps Streamlit's colors."""
    if palette["base"] != charts.BASE_LIGHT:
        return ""
    return "".join(
        f'[data-testid="stCode"] .token.{token} {{ color: {color} !important; }}'
        for token, color in LIGHT_CODE_COLORS.items()
    )


def build_style_css(mode):
    """Cards, key figures, chips and tables, in the colors of the active theme."""
    palette = charts.get_palette(mode)
    return (
        build_theme_css(palette)
        + f"""
    [class*="st-key-card_"] {{
        background: {palette["card"]}; border: 1px solid {palette["card_border"]};
        border-radius: 18px; padding: 18px 20px 14px 20px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06), inset 0 1px 0 {palette["glow"]};
    }}
    [data-testid="stMainBlockContainer"] {{ padding-top:1.1rem; }}
    .devops-layers-title {{ font-size:.7rem; font-weight:600; letter-spacing:.08em;
        text-transform:uppercase; color:{palette["reference"]}; margin:0 0 6px; }}
    .st-key-devops_layers {{ margin-top:10px; }}
    .st-key-devops_layers button {{ justify-content:flex-start !important; min-height:52px;
        padding:10px 16px !important; border-radius:14px !important; background:{palette["card"]} !important;
        border:1px solid {palette["card_border"]} !important;
        box-shadow:0 10px 22px -16px rgba(0,0,0,.3); transition:transform .14s ease; }}
    .st-key-devops_layers button:hover {{ transform:translateY(-2px); border-color:{palette["accent"]} !important; }}
    .st-key-devops_layers button p {{ font-weight:600; font-size:.92rem; }}
    .st-key-devops_layers button [data-testid="stIconMaterial"] {{ color:{palette["accent"]}; }}
    /* Idle pause (D-131): set by IDLE_ANIMATION_SCRIPT after 20 s without activity. */
    .greenocean-idle *, .greenocean-idle *::before, .greenocean-idle *::after {{
        animation-play-state:paused !important; }}
    .page-freshness {{ color:{palette["text"]}; font-size:0.82rem; margin-bottom:8px; }}
    [data-testid="stMain"] h1 {{ font-size:clamp(1.7rem,3vw,2.35rem); line-height:1.15; }}
    @media(max-width:700px) {{
        [data-testid="stHorizontalBlock"]:has(.st-key-catalog_list) {{ flex-wrap:wrap; }}
        [data-testid="stColumn"]:has(.st-key-catalog_list) {{ min-width:100%; }}
    }}
    /* The report: title and analyzed week, actions at the right. */
    .report-title h1 {{ font-size:clamp(1.6rem,2.6vw,2.2rem) !important; margin:0 !important;
        padding:0 !important; line-height:1.15; }}
    .report-title p {{ margin:4px 0 0; color:{palette["text"]}; font-size:.92rem; }}
    .report-title strong {{ color:{palette["strong_text"]}; }}
    .report-divider {{ margin:0 10px; color:{palette["card_border"]}; }}
    .st-key-report_actions {{ gap:14px; align-items:center; flex-wrap:wrap; }}
    .st-key-report_actions [data-testid="stMarkdownContainer"] p {{ margin:0; }}
    /* The filter bar: one panel, each name written at the left of its field. */
    .st-key-report_filters {{ background:{palette["card"]}; border:1px solid {palette["card_border"]};
        border-radius:14px; padding:8px 14px; gap:6px 18px; flex-wrap:wrap !important; }}
    [class*="st-key-bar_"] {{ flex-wrap:nowrap !important; min-width:0; }}
    [class*="st-key-bar_"] [data-testid="stSelectbox"],
    [class*="st-key-bar_"] [data-testid="stSlider"] {{ flex:1 1 0; min-width:0; }}
    /* The width of each field lives on its wrapper, the item of the bar's row. */
    .st-key-report_filters > div:has(> [class*="st-key-bar_"]) {{ flex:1 1 170px; min-width:0; }}
    .st-key-report_filters > div:has(> .st-key-bar_product) {{ flex:2 1 240px; }}
    .st-key-report_filters > div:has(> .st-key-bar_top_n) {{ flex:1.4 1 190px; }}
    .st-key-report_filters > div:has(> .st-key-bar_order) {{ flex:1 1 150px; }}
    .bar-label {{ color:{palette["text"]}; font-size:.85rem; white-space:nowrap; }}
    /* The figures of the week: one line, no cards, thin dividers. */
    .kpi-strip {{ display:flex; flex-wrap:wrap; margin:6px 0 0;
        border-top:1px solid {palette["card_border"]}; border-bottom:1px solid {palette["card_border"]}; }}
    .kpi-strip-item {{ flex:1 1 170px; display:flex; flex-direction:column; gap:0;
        padding:6px 16px; min-width:0; text-decoration:none !important; color:inherit !important;
        border-left:1px solid {palette["card_border"]}; }}
    .kpi-strip-item:first-child {{ border-left:none; padding-left:4px; }}
    .kpi-strip-item:hover .kpi-strip-label {{ color:{palette["accent"]}; }}
    .kpi-strip-value {{ font-size:1.5rem; font-weight:600; line-height:1.15;
        color:{palette["strong_text"]}; white-space:nowrap; }}
    .kpi-strip-rise {{ color:{charts.get_status_text_color("critical", mode)}; }}
    .kpi-strip-accent {{ color:{palette["accent"]}; }}
    .kpi-strip-good {{ color:{charts.get_status_text_color("good", mode)}; font-size:1.2rem; }}
    .kpi-strip-label {{ color:{palette["strong_text"]}; font-size:.88rem; font-weight:600; }}
    .kpi-strip-note {{ color:{palette["text"]}; font-size:.75rem; white-space:normal; }}
    .kpi-strip-label {{ white-space:normal; }}
    .kpi-strip-meaning {{ justify-content:center; color:{palette["text"]}; font-size:.85rem; }}
    .filter-scope {{ color:{palette["text"]}; font-size:.78rem; margin:2px 0 0; }}
    .strip-note {{ color:{palette["text"]}; font-size:.8rem; margin:4px 0 0; }}
    .ring-legend {{ list-style:none; padding:0; margin:0; font-size:.84rem; }}
    .ring-legend span:nth-child(2) {{ min-width:0; white-space:normal; overflow-wrap:anywhere; }}
    .st-key-ranking_caption {{ flex-wrap:nowrap !important; justify-content:space-between; }}
    .st-key-ranking_caption [data-testid="stCaptionContainer"] {{ flex:1 1 auto; min-width:0; }}
    .st-key-ranking_order {{ flex:none; }}
    .ring-legend li {{ display:grid; grid-template-columns:8px minmax(0,1fr) auto; gap:8px; padding:3px 0; }}
    .ring-legend strong {{ color:{palette["strong_text"]}; }}
    .ring-note {{ color:{palette["text"]}; font-size:.78rem; margin:8px 0 0; }}
    /* Streamlit sizes markdown p and li itself: these win over it (D-072). */
    [data-testid="stMarkdownContainer"] ul.ring-legend li {{ font-size:.84rem; margin:0;
        white-space:nowrap; }}
    [data-testid="stMarkdownContainer"] p.ring-note,
    [data-testid="stMarkdownContainer"] p.filter-scope {{ font-size:.78rem; line-height:1.4; }}
    .report-footer {{ display:flex; flex-wrap:wrap; gap:6px 18px; align-items:center;
        color:{palette["text"]}; font-size:.85rem; padding:6px 0;
        border-top:1px solid {palette["card_border"]}; }}
    .report-footer a {{ font-weight:600; }}
    .project-navigation {{ display:grid; grid-template-columns:1fr auto 1fr; gap:12px;
        align-items:center; padding:12px 0; border-bottom:1px solid {palette["card_border"]};
        margin:4px 0 20px; font-size:0.85rem; }}
    .project-navigation > div:last-child {{ text-align:right; }}
    .journey-position {{ color:{palette["text"]}; font-size:0.75rem; }}
    .component-symbol {{ display:inline-flex; width:38px; height:42px; flex-shrink:0;
        vertical-align:middle; margin:0 10px 8px 0; color:{palette["accent"]}; }}
    .component-symbol svg {{ width:100%; height:100%; }}
    .info-card[data-component-kind="security"] {{ border-radius:18px 18px 42% 42% / 18px 18px 32px 32px;
        border-top:3px solid {palette["accent"]}; padding-bottom:36px; }}
    .info-card[data-component-kind="database"] {{ border-radius:50% / 18px;
        border-top:3px double {palette["accent"]}; border-bottom:3px double {palette["accent"]}; }}
    .info-card[data-component-kind="workflow"] {{ border-left:4px solid {palette["accent"]};
        border-radius:4px 24px 24px 4px; }}
    .info-card[data-component-kind="document"], .info-card[data-component-kind="code"] {{
        border-radius:3px 20px 3px 3px; border-top:3px solid {palette["accent"]}; }}
    .info-card[data-component-kind="chart"] {{ border-radius:8px; border-bottom:3px solid {palette["accent"]}; }}
    .info-card[data-component-kind="rule"] {{ border-radius:20px 4px 20px 4px;
        border-left:3px solid {palette["accent"]}; }}
    .info-card[data-component-kind="person"] {{ border-radius:28px 28px 8px 8px; }}
    .info-card[data-component-kind="mission"], .info-card[data-component-kind="vision"],
    .info-card[data-component-kind="scope"] {{ margin:14px 0; border-radius:0 16px 16px 0;
        border-left:4px solid {palette["accent"]}; display:flow-root; }}
    .info-card[data-component-kind="mission"] .component-symbol,
    .info-card[data-component-kind="vision"] .component-symbol,
    .info-card[data-component-kind="scope"] .component-symbol {{ width:64px; height:68px;
        float:left; margin:0 22px 6px 0; }}
    .info-card[data-component-kind="vision"] {{ border-radius:28px; border-left:1px solid {palette["card_border"]}; }}
    .info-card[data-component-kind="alert"] {{ border-left:4px solid {palette["rise"]}; border-radius:4px; }}
    [class*="st-key-card_"]:has(.component-symbol[data-kind="security"]) {{
        border-radius:18px 18px 40px 40px; border-top:3px solid {palette["accent"]}; }}
    [class*="st-key-card_"]:has(.component-symbol[data-kind="database"]) {{
        border-radius:30px / 16px; border-block:3px double {palette["card_border"]}; }}
    [class*="st-key-card_"]:has(.component-symbol[data-kind="workflow"]) {{
        border-left:4px solid {palette["accent"]}; border-radius:4px 20px 20px 4px; }}
    [class*="st-key-card_"]:has(.component-symbol[data-kind="chart"]) {{
        border-radius:8px; border-bottom:3px solid {palette["accent"]}; }}
    @media (max-width:640px) {{
        .project-navigation {{ grid-template-columns:1fr 1fr; gap:8px; }}
        .journey-position {{ grid-column:1/-1; grid-row:1; text-align:center; }}
        .component-symbol {{ width:30px; height:34px; }}
    }}
    .overview-metrics {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
        gap:16px; padding:20px; margin:12px 0 24px; border-radius:16px;
        background:{palette["card"]}; border:1px solid {palette["card_border"]}; }}
    .overview-metrics .kpi-value {{ font-size:1.75rem; margin-top:6px; overflow-wrap:anywhere; }}
    .mobile-rankings {{ display:none; list-style:none; padding:0; margin:12px 0; }}
    .mobile-rankings li {{ margin:0 0 16px; }}
    .mobile-ranking-label {{ display:flex; align-items:flex-start; gap:12px; margin-bottom:6px;
        font-size:0.85rem; line-height:1.4; color:{palette["strong_text"]}; }}
    .mobile-ranking-label span {{ min-width:0; overflow-wrap:anywhere; flex:1; }}
    .mobile-ranking-label strong {{ white-space:nowrap; }}
    .mobile-ranking-track {{ position:relative; height:8px; border-radius:4px;
        background:{palette["grid"]}; overflow:hidden; }}
    .mobile-ranking-track span {{ position:absolute; top:0; height:100%; border-radius:4px; }}
    .mobile-ranking-track i {{ position:absolute; left:50%; height:100%;
        border-left:1px solid {palette["text"]}; }}
    @media (max-width:640px) {{
        [class*="_ranking_desktop"] {{ display:none; }}
        /* The summary's clickable rankings too: on a phone the list replaces them and the
           Producto field does the filtering (D-072). */
        [class*="st-key-"][class*="_movements_chart_"],
        [class*="st-key-"][class*="_gaps_chart_"] {{ display:none; }}
        .mobile-rankings {{ display:block; }}
    }}
    .resource-tree {{ list-style:none; padding:0 0 0 18px; border-left:1px solid {palette["card_border"]}; }}
    /* A grid of floating cards, not a long list (D-122): the same elevated-card
       language as the KPI gallery and the GitHub page. */
    .technical-rows li {{ display:flex; align-items:flex-start; gap:12px; padding:16px;
        border-radius:14px; background:{palette["card"]}; border:1px solid {palette["card_border"]};
        box-shadow:0 12px 24px -14px rgba(0,0,0,.22), 0 2px 6px -1px rgba(0,0,0,.1);
        transition:transform .15s ease; }}
    .technical-rows li:hover {{ transform:translateY(-3px); }}
    .devops-logos {{ display:flex; gap:6px; flex-shrink:0; width:66px; }}
    .devops-logos svg {{ width:28px; height:28px; }}
    .technical-rows {{ list-style:none; padding:0; margin:8px 0 20px; display:grid;
        grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:14px; }}
    .technical-rows .component-symbol {{ width:28px; height:30px; margin:0; }}
    /* Layer cards (D-137): compact, floating, the real logo of each tool; auto-fit so
       two cards fill the dialog instead of leaving half of it empty. */
    .layer-cards {{ display:flex; flex-wrap:wrap; gap:16px;
        margin:6px 0 10px; --github-ink:{palette["strong_text"]}; }}
    .layer-card {{ flex:1 1 300px; display:flex; gap:14px; align-items:flex-start; padding:16px 18px;
        border-radius:18px; background:{palette["card"]}; border:1px solid {palette["card_border"]};
        box-shadow:0 14px 28px -16px color-mix(in srgb, var(--brand) 50%, #0004),
                   0 2px 7px -2px rgba(0,0,0,.14);
        transition:transform .16s ease, box-shadow .16s ease; }}
    .layer-card:hover {{ transform:translateY(-4px);
        box-shadow:0 22px 36px -16px color-mix(in srgb, var(--brand) 58%, #0004),
                   0 4px 10px -2px rgba(0,0,0,.16); }}
    .layer-logo {{ flex:none; display:flex; align-items:center; justify-content:center;
        width:44px; height:44px; border-radius:12px; color:var(--brand);
        background:color-mix(in srgb, var(--brand) 14%, transparent); }}
    .layer-logo svg {{ width:24px; height:24px; }}
    .layer-body {{ min-width:0; }}
    .layer-body strong {{ display:block; font-size:.95rem; font-weight:500; line-height:1.3;
        color:{palette["strong_text"]}; letter-spacing:-.01em; }}
    .layer-body p {{ margin:4px 0 6px; font-size:.86rem; line-height:1.45; color:{palette["text"]}; }}
    .layer-note {{ font-size:.75rem; color:{palette["reference"]}; }}
    .technical-rows li > div {{ min-width:0; }}
    .technical-rows p {{ margin:4px 0; font-size:.9rem; line-height:1.5; }}
    @media(max-width:640px) {{
    }}
    .resource-tree li {{ display:grid; grid-template-columns:minmax(160px,1fr) 2fr;
        gap:12px; margin:0; padding:14px 8px; border-bottom:1px solid {palette["card_border"]}; }}
    .resource-tree li span {{ color:{palette["text"]}; }}
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stWidgetLabel"],
    [data-testid="stMain"] [data-testid="stCaptionContainer"] {{ color:{palette["strong_text"]}; }}
    [data-testid="stExpander"] details {{ background:{palette["card"]};
        border:1px solid {palette["card_border"]}; border-radius:12px; }}
    [data-testid="stExpander"] summary {{ color:{palette["strong_text"]}; }}
    [data-testid="stDialog"] [data-testid="stWidgetLabel"],
    [data-testid="stDialog"] [data-testid="stMarkdownContainer"] {{ color:{palette["strong_text"]}; }}
    [data-testid="stDialog"] [role="dialog"] {{ background:{palette["card"]};
        color:{palette["strong_text"]}; border:1px solid {palette["card_border"]}; }}
    [data-testid="stSidebarNav"] [data-testid="stHeading"],
    [data-testid="stSidebarNav"] header, [data-testid="stSidebarNav"] p {{
        color:{palette["sidebar_text"]}; }}
    @media (max-width:640px) {{
        .overview-metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); padding:14px; }}
        .overview-metrics .kpi-value {{ font-size:1.3rem; }}
        .resource-tree li {{ grid-template-columns:1fr; gap:4px; }}
    }}
    .card-title {{ font-size: 1.05rem; font-weight: 600; color: {palette["strong_text"]}; }}
    .page-subtitle {{ color: {palette["text"]}; margin-top: 0; line-height:1.5; }}
    .kpi-label {{ color: {palette["text"]}; font-size: 0.9rem; }}
    .kpi-value {{ font-size: 2rem; font-weight: 600; color: {palette["strong_text"]};
                 line-height: 1.2; }}
    .kpi-note {{ color: {palette["text"]}; font-size: 0.8rem; }}
    .kpi-link {{ margin-left: 10px; font-size: 0.8rem; font-weight: 400; }}
    .card-title {{ display:flex; align-items:flex-start; gap:10px; flex-wrap:wrap; min-width:0; line-height:1.45; padding-bottom:6px; }}
    .card-title > *:not(.card-title-text) {{ flex: none; }}
    .card-title-text {{ min-width: 0; overflow: hidden; text-overflow: ellipsis;
                        white-space:normal; overflow-wrap:break-word; }}
    .card-title .kpi-link {{ margin-left: auto; white-space: nowrap; }}
    [class*="st-key-card_"] {{gap:12px;}}
    [class*="st-key-card_"] [data-testid="stCaptionContainer"] p {{line-height:1.55; margin:0; padding:2px 0 6px;}}
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p {{line-height:1.45; padding-bottom:4px;}}
    .regional-detail td, .regional-detail th, .chart-sample td, .chart-sample th {{line-height:1.5; vertical-align:top;}}
    .compact-header {{row-gap:10px;}}

    .chip {{ display: inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: 0.8rem; font-weight: 600; margin-left: 6px; }}
    .chip-ok {{ background: rgba(12, 163, 12, 0.16);
               color: {charts.get_status_text_color("good", mode)}; }}
    .chip-failed {{ background: rgba(208, 59, 59, 0.16);
                   color: {charts.get_status_text_color("critical", mode)}; }}
    .chip-running {{ background: rgba(57, 135, 229, 0.16);
                    color: {charts.get_status_text_color("running", mode)}; }}
    .chip-neutral {{ background: rgba(128, 128, 128, 0.16); color: {palette["text"]}; }}
    .chip-rise {{ background: rgba(227, 73, 72, 0.16); color: {palette["rise"]}; }}
    .chip-fall {{ background: rgba(57, 135, 229, 0.16); color: {palette["fall"]}; }}
    .hint {{ position: relative; display: inline-block; margin-left: 8px; cursor: help;
            color: {palette["text"]}; font-weight: 400; outline: none;
            padding: 0 4px; font-size: 1.1em; }}
    /* :focus makes the explanation open with a tap on phones, where there is no mouse. */
    .hint:hover::after, .hint:focus::after {{
        content: attr(data-hint); position: absolute; left: 0; top: 1.7em; z-index: 1000;
        width: min(340px, 75vw); padding: 10px 12px; border-radius: 10px; white-space: normal;
        background: {palette["card"]}; border: 1px solid {palette["card_border"]};
        color: {palette["strong_text"]}; font-size: 0.85rem; font-weight: 400;
        line-height: 1.45; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }}
    .hint-chip {{ position: relative; cursor: help; outline: none; }}
    /* On narrow screens the explanation opens as a panel at the bottom of the
       screen, so it never runs off the edge. On computers the chips use the
       browser's own tooltip (title), so only one explanation shows at a time. */
    @media (max-width: 640px) {{
        .hint:hover::after, .hint:focus::after {{
            position: fixed; left: 16px; right: 16px; bottom: 16px; top: auto;
            width: auto; font-size: 0.95rem;
        }}
        .hint-chip:focus::after {{
            content: attr(data-hint); position: fixed; left: 16px; right: 16px;
            bottom: 16px; z-index: 1000; padding: 10px 12px; border-radius: 10px;
            white-space: normal; background: {palette["card"]};
            border: 1px solid {palette["card_border"]}; color: {palette["strong_text"]};
            font-size: 0.95rem; font-weight: 400; line-height: 1.45;
        }}
    }}
    .figure-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
                    margin: 8px 0; }}
    .phone-only {{ display: none; }}
    .diagram-fit {{ width: 100%; min-width: 0; }}
    .diagram-fit img {{ display: block; width: 100%; max-width: 100%; height: auto; }}
    .pipeline-mini {{ width: 100%; overflow-x: auto; padding: 8px 0 2px; }}
    .pipeline-mini svg {{ display: block; width: 100%; min-width: 700px; height: auto; }}
    /* The whole diagram: wide from left to right; on narrow screens (phones,
       tablets, small windows) the wide one would shrink to unreadable text, so
       the vertical version takes its place. */
    .diagram-narrow {{ display: none; max-width: 440px; margin: 0 auto; }}
    @media (max-width: 1000px) {{
        .diagram-wide {{ display: none; }}
        .diagram-narrow {{ display: block; }}
    }}
    {zoom.build_zoom_css(palette)}
    .run-status {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
                   margin: 0 0 10px 0; font-size: 0.9rem; }}
    /* Phones: two figures per row and less empty room above the title, so
       «Empieza aquí» fits on one screen. */
    @media (max-width: 640px) {{
        .figure-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .phone-only {{ display: block; }}
        [data-testid="stMainBlockContainer"] {{ padding-top: 2.5rem; }}
        [class*="st-key-card_start_here"] li {{ font-size: 0.9rem; line-height: 1.4; }}
    }}
    /* Text sections (D-057): a title with one sentence, cards in a grid that stack
       by themselves on narrow screens, numbered steps and folded details. */
    .section-head {{ margin: 22px 0 10px 0; text-align: left; }}
    .section-title {{ font-size: 1.3rem; font-weight: 600; color: {palette["strong_text"]};
                      margin: 0; line-height: 1.3; }}
    .section-lead {{ font-size: 1rem; color: {palette["text"]}; margin: 4px 0 0 0;
                     max-width: 72ch; line-height: 1.5; }}
    .subsection-title {{ font-size: 1.08rem; font-weight: 500; color: {palette["strong_text"]};
                         margin: 0; }}
    .info-grid {{ display: grid; gap: 12px; margin: 6px 0 8px 0;
                  grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); }}
    .info-grid.is-compact {{ align-items: start; }}
    /* Business questions use an editorial layout: the symbol and the words float
       directly on the page, without six repetitive card backgrounds. */
    .question-showcase {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
        column-gap:clamp(28px,4vw,72px); row-gap:clamp(38px,6vw,82px);
        margin:20px 0 36px; align-items:start; }}
    .question-item {{ min-width:0; padding:8px 4px; }}
    .question-item .component-symbol {{ display:block; float:none; width:76px; height:86px;
        margin:0 0 20px; color:{palette["accent"]};
        filter:drop-shadow(0 12px 18px {palette["glow"]});
        transition:transform .28s ease, filter .28s ease; }}
    .question-item:hover .component-symbol {{ transform:translateY(-6px) scale(1.025);
        filter:drop-shadow(0 18px 24px {palette["glow"]}); }}
    .question-number {{ color:{palette["text"]}; font-size:.75rem; font-weight:500;
        letter-spacing:.055em; text-transform:uppercase; margin-bottom:10px; }}
    .question-title {{ color:{palette["strong_text"]}; font-size:clamp(1.15rem,1.45vw,1.48rem);
        font-weight:720; line-height:1.28; max-width:24ch; }}
    .question-scope {{ color:{palette["text"]}; font-size:.94rem; line-height:1.5;
        margin:12px 0 15px; max-width:34ch; }}
    .question-action a {{ color:{palette["accent"]}; font-weight:500;
        text-decoration:none; }}
    .question-action a:hover {{ text-decoration:underline; text-underline-offset:4px; }}
    @media(max-width:900px) {{ .question-showcase {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    @media(max-width:560px) {{
        .question-showcase {{ grid-template-columns:1fr; row-gap:42px; }}
        .question-item {{ padding:4px 2px; }}
        .question-item .component-symbol {{ width:66px; height:74px; margin-bottom:14px; }}
        .question-title {{ max-width:none; }}
    }}
    .info-card {{ display: flex; flex-direction: column; gap: 6px; min-width: 0;
                  padding: 16px 18px; border-radius: 16px; text-align: left;
                  background: {palette["card"]}; border: 1px solid {palette["card_border"]}; }}
    .info-card.is-warning {{ border-left: 3px solid {palette["rise"]}; }}
    .info-card.is-highlight {{ border: 1px solid {palette["accent"]};
                               box-shadow: 0 0 0 1px {palette["accent"]}33,
                                           0 0 18px {palette["accent"]}33; }}
    .info-label {{ font-size: 0.76rem; letter-spacing: 0.05em; text-transform: uppercase;
                   color: {palette["text"]}; }}
    .info-title {{ font-size: 1.02rem; font-weight: 600; color: {palette["strong_text"]};
                   line-height: 1.35; }}
    .info-text {{ font-size: 0.94rem; color: {palette["strong_text"]}; line-height: 1.5;
                  overflow-wrap: break-word; }}
    .info-note {{ font-size: 0.83rem; color: {palette["text"]}; line-height: 1.45; }}
    .info-link {{ margin-top: auto; padding-top: 4px; font-size: 0.9rem; }}
    .info-card code, .steps code {{ overflow-wrap: anywhere; }}
    .file-list {{ list-style: none; padding: 0 !important; margin: 4px 0 0 0 !important;
                  display: grid; gap: 6px; font-size: 0.9rem; }}
    .file-list li {{ margin: 0; line-height: 1.45; color: {palette["strong_text"]}; }}
    .file-list a {{ font-family: monospace; font-size: 0.86rem; }}
    /* !important: Streamlit indents every list of a Markdown block. */
    .steps {{ list-style: none; counter-reset: step; padding: 0 !important;
              margin: 6px 0 8px 0 !important; display: grid; gap: 10px; }}
    .steps li {{ counter-increment: step; position: relative; min-width: 0; margin: 0;
                 padding: 14px 16px 14px 58px; border-radius: 14px; line-height: 1.5;
                 background: {palette["card"]}; border: 1px solid {palette["card_border"]};
                 color: {palette["strong_text"]}; font-size: 0.94rem; }}
    .steps li::before {{ content: counter(step); position: absolute; left: 16px; top: 13px;
                         width: 28px; height: 28px; border-radius: 50%; font-weight: 600;
                         display: flex; align-items: center; justify-content: center;
                         background: {palette["accent"]}; color: {palette["background"]}; }}
    .stat-line {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 12px;
                  margin: 4px 0 6px 0; }}
    .stat-line strong {{ font-size: 1.35rem; color: {palette["strong_text"]}; }}
    /* Alertas: one row per alert; on phones the row wraps and the bar takes a line. */
    .alert-list {{ list-style: none; padding: 0 !important; margin: 4px 0 !important;
                   display: grid; gap: 8px; }}
    .alert-row {{ display: grid; align-items: center; gap: 4px 12px; margin: 0;
                  grid-template-columns: 7.5rem minmax(0, 1fr) 5.5rem minmax(90px, 160px) 4.5rem;
                  padding: 8px 10px; border-radius: 10px; border: 1px solid {palette["card_border"]};
                  font-size: 0.9rem; color: {palette["strong_text"]}; }}
    .alert-status {{ font-weight: 600; white-space: nowrap; }}
    .alert-product {{ min-width: 0; overflow-wrap: break-word; }}
    .alert-change {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
    .alert-meter {{ position: relative; height: 8px; border-radius: 4px;
                    background: {palette["grid"]}; }}
    .alert-bar {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 4px; }}
    .alert-limit {{ position: absolute; top: -4px; bottom: -4px; width: 2px;
                    background: {palette["strong_text"]}; }}
    .alert-distance {{ color: {palette["text"]}; font-size: 0.82rem; white-space: nowrap; }}
    @media (max-width: 640px) {{
        .alert-row {{ grid-template-columns: auto minmax(0, 1fr) auto; }}
        .alert-product {{ grid-column: 1 / -1; order: -1; }}
        .alert-meter {{ grid-column: 1 / -1; }}
    }}
    /* Datos y código (D-060): cards with a soft accent border, titles 14-16 px, text 13 px. */
    .query-meta {{ font-size: 13px; color: {palette["text"]}; margin: 2px 0 6px 0; }}
    .query-meta .chip {{ margin: 2px 4px 2px 0; }}
    /* Código y resultados (C03): the list of questions and the chosen one, sober. */
    .catalog-list-title {{ font-size: 17px; font-weight: 600; color: {palette["strong_text"]};
                           margin: 0 0 6px 0; }}
    .st-key-catalog_list [data-testid="stRadio"] [role="radiogroup"] {{ gap: 2px; }}
    .st-key-catalog_list [data-testid="stRadio"] label {{ width: 100%; padding: 7px 8px;
        border-radius: 6px; border-left: 3px solid transparent; }}
    .st-key-catalog_list [data-testid="stRadio"] label:has(input:checked) {{
        background: {palette["accent"]}14; border-left-color: {palette["accent"]}; }}
    .st-key-catalog_list [data-testid="stRadio"] label p {{ font-size: 14px;
        color: {palette["strong_text"]}; }}
    .catalog-head {{ display: flex; justify-content: space-between; gap: 16px;
                     align-items: flex-start; flex-wrap: wrap; margin-bottom: 8px; }}
    .catalog-question {{ font-size: 26px !important; margin: 0 !important; padding: 0 !important;
                         color: {palette["strong_text"]}; }}
    .catalog-compares {{ margin: 4px 0 2px 0; color: {palette["text"]}; font-size: 15px; }}
    .catalog-facts {{ margin: 0; color: {palette["strong_text"]}; font-size: 14px; }}
    .catalog-steps {{ display: flex; gap: 8px; align-items: center; font-size: 13px;
                      color: {palette["text"]}; flex-wrap: wrap; }}
    .catalog-step b {{ display: inline-flex; width: 22px; height: 22px; border-radius: 50%;
        align-items: center; justify-content: center; margin-right: 5px; font-size: 12px;
        border: 1px solid {palette["card_border"]}; color: {palette["strong_text"]}; }}
    .catalog-block-title {{ display: flex; justify-content: space-between; gap: 12px;
        flex-wrap: wrap; font-size: 16px; font-weight: 600; color: {palette["strong_text"]}; }}
    .catalog-block-title span {{ font-size: 13px; font-weight: 400; color: {palette["text"]}; }}
    .catalog-reading {{ font-size: 14px; color: {palette["text"]}; margin: 4px 0 6px 0; }}
    /* On a phone the list scrolls in its own box, so the result is a short scroll away. */
    @media (max-width: 640px) {{
        .st-key-catalog_list [data-testid="stRadio"] [role="radiogroup"] {{
            max-height: 230px; overflow-y: auto; flex-wrap: nowrap; }}
        .catalog-question {{ font-size: 22px !important; }}
    }}
    /* Consulta por clics (D-060). */
    [class*="st-key-card_search_"] {{ border-color: {palette["accent"]}40; }}
    [class*="st-key-card_search_"] .card-title {{ font-size: 16px; }}
    [class*="st-key-card_search_"] label p {{ font-size: 13px; }}
    [class*="st-key-search_chips"] {{ gap: 6px; margin: 4px 0 10px 0; flex-wrap: wrap; }}
    [class*="st-key-chip_"] button {{ border-radius: 999px; min-height: 30px; padding: 2px 12px;
                                      font-size: 13px; color: {palette["accent"]};
                                      border: 1px solid {palette["accent"]}66;
                                      background: {palette["accent"]}14; }}
    [class*="st-key-chip_"] button:hover {{ background: {palette["accent"]}2a;
                                            color: {palette["accent"]}; }}
    [class*="st-key-alert_card_"] {{ padding: 12px 14px; border-radius: 14px;
                                     background: {palette["background"]};
                                     border: 1px solid {palette["card_border"]}; }}
    .alert-card-label {{ font-size: 14px; font-weight: 600; }}
    [class*="st-key-alert_card_"] button p {{ font-size: 13px; }}
    [class*="st-key-group_breakdown"] button {{ min-height: 3.35rem; height: auto; }}
    [class*="st-key-group_breakdown"] button p {{
        white-space: normal !important; overflow: visible !important;
        text-overflow: clip !important; line-height: 1.25;
    }}
    [class*="st-key-card_search_form"] button[kind="primaryFormSubmit"] {{
        background: {palette["accent"]}; border-color: {palette["accent"]};
        color: {palette["on_accent"]}; }}
    /* Phones: the four state cards in a 2 x 2 grid instead of one column. */
    @media (max-width: 640px) {{
        [class*="st-key-search_kpis"] [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important; gap: 8px !important; }}
        [class*="st-key-search_kpis"] [data-testid="stColumn"] {{
            flex: 1 1 calc(50% - 8px) !important; min-width: calc(50% - 8px) !important; }}
        [class*="st-key-search_kpis"] .kpi-value {{ font-size: 1.5rem; }}
    }}
    .search-count {{ font-size: 13px; color: {palette["text"]}; padding-bottom: 10px; }}
    .page-lineage {{ margin: -4px 0 4px; }}
    .st-key-compact_footer {{ gap: 2px !important; margin-top: 6px; padding-top: 4px; border-top: 1px solid {palette["card_border"]}; }}
    .st-key-compact_footer [data-testid="stCaptionContainer"] {{ margin-top: 10px; }}
    .st-key-compact_footer [data-testid="stCaptionContainer"] p {{ font-size: .7rem; line-height: 1.35; }}
    /* D-267: on the pages that fit the window, the attribution shows its first line; the pointer opens it whole. */
    .st-key-compact_footer [data-testid="stCaptionContainer"] p {{ display: -webkit-box; -webkit-box-orient: vertical;
        -webkit-line-clamp: 1; overflow: hidden; cursor: default; }}
    .st-key-compact_footer [data-testid="stCaptionContainer"]:hover p {{ -webkit-line-clamp: unset; }}
    @media print {{ .st-key-compact_footer [data-testid="stCaptionContainer"] p {{ -webkit-line-clamp: unset; }} }}
    .st-key-compact_footer .page-lineage {{ margin: 0; }}
    .lineage-badge {{ display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 600;
        padding: 3px 10px; border-radius: 999px; border: 1px solid {palette["card_border"]};
        color: {palette["text"]}; background: {palette["card"]}; }}
    .lineage-badge::before {{ content: ""; width: 7px; height: 7px; border-radius: 50%; background: #9aa4b2; }}
    .lineage-badge.ok::before {{ background: #16a34a; }}
    .lineage-badge.failed::before {{ background: #dc2626; }}
    .lineage-frame {{ max-width: 1100px; margin: 0 auto; }}
    .detail-facts {{ display: grid; gap: 10px 18px; margin-bottom: 8px;
                     grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }}
    .detail-value {{ font-size: 15px; font-weight: 600; color: {palette["strong_text"]}; }}
    table.card-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    table.card-table th {{ text-align: left; color: {palette["text"]}; font-weight: 500;
                          padding: 6px 4px; border-bottom: 1px solid {palette["card_border"]}; }}
    table.card-table td {{ padding: 8px 4px; border-bottom: 1px solid {palette["card_border"]};
                          color: {palette["strong_text"]}; }}
    .link-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                  gap: 14px; margin: 10px 0; }}
    /* Floating, not flush (D-118): the same elevated-card language as the KPI
       gallery (D-114b), shared by this grid wherever it is used. */
    .link-card {{ display: flex; align-items: center; gap: 8px; min-height: 52px;
                  padding: 10px 12px; border-radius: 14px; background: {palette["card"]};
                  border: 1px solid {palette["card_border"]};
                  box-shadow: 0 12px 24px -14px rgba(0,0,0,.22), 0 2px 6px -1px rgba(0,0,0,.1);
                  transition: transform .16s ease, box-shadow .16s ease; }}
    .link-card:hover {{ transform: translateY(-3px);
                        box-shadow: 0 18px 32px -14px rgba(0,0,0,.26), 0 3px 8px -1px rgba(0,0,0,.12); }}
    .link-card a {{ flex: 1; display: flex; align-items: center; gap: 10px;
                    text-decoration: none; min-width: 0; }}
    .link-card .link-icon {{ font-family: "Material Symbols Rounded"; font-size: 22px;
                             color: {palette["accent"]}; }}
    .link-card .link-text {{ display: flex; flex-direction: column; min-width: 0; }}
    .link-card strong {{ color: {palette["strong_text"]}; font-size: 0.9rem; }}
    .link-card small {{ color: {palette["text"]}; font-size: 0.78rem; line-height: 1.3; }}
    .gh-repo-header {{ display: flex; align-items: center; gap: 12px; padding: 14px 18px;
                       margin: 10px 0 22px; border-radius: 14px; background: {palette["card"]};
                       border: 1px solid {palette["card_border"]}; text-decoration: none;
                       color: {palette["strong_text"]}; transition: border-color .12s ease; }}
    .gh-repo-header:hover {{ border-color: {palette["accent"]}; }}
    .gh-repo-slug {{ font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 0.95rem;
                     font-weight: 600; flex: 1; }}
    .gh-repo-open {{ font-size: 0.78rem; color: {palette["accent"]}; }}
    .copy-link {{ flex: none; min-height: 36px; padding: 4px 10px; border-radius: 8px;
                  cursor: pointer; font-size: 0.75rem; background: transparent;
                  color: {palette["text"]}; border: 1px solid {palette["card_border"]}; }}
    .copy-link:hover {{ color: {palette["accent"]}; border-color: {palette["accent"]}; }}
    .admin-locked {{ color: {palette["text"]}; font-size: 0.9rem; }}
    {build_code_colors_css(palette)}
    /* Report pages (Dashboard, D-067): one screen like Looker or Power BI. Title and
       freshness on one line, compact figures, tighter cards and gaps. */
    .compact-header {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 14px;
                       margin: 0 0 2px 0; }}
    .compact-header h1 {{ font-size: 1.0625rem !important; font-weight: 600 !important; margin: 0 !important; white-space: nowrap;
                          padding: 0 !important; line-height: 1.25; cursor: help; }}
    .compact-header .page-freshness {{ margin: 0; font-size: 0.8rem; }}
    /* Main navigation views open as a complete panorama. Long tables and
       methodology remain available in folded sections below that overview. */
    [data-testid="stElementContainer"]:has(.overview-viewport-marker) {{display:none;}}
    .stApp:has(.overview-viewport-marker) [data-testid="stMainBlockContainer"] {{
        padding-bottom:8px !important;}}
    .stApp:has(.overview-viewport-marker) .st-key-window_page,
    .stApp:has(.overview-viewport-marker) .st-key-window_page > [data-testid="stVerticalBlock"] {{
        gap:.45rem !important;}}
    .stApp:has(.overview-viewport-marker) [data-testid="stExpander"] summary {{
        min-height:34px; padding:5px 10px;}}
    .stApp:has(.overview-viewport-marker) [data-testid="stExpander"] summary p {{
        font-size:.82rem; line-height:1.2;}}
    .stApp:has(.overview-viewport-marker) hr {{margin:.25rem 0;}}
    /* Pipeline is a one-screen gallery: two detailed diagrams receive the
       available space, while the execution state stays in a compact strip. */
    .stApp:has(.overview-pipeline) [data-testid="stMainBlockContainer"] {{
        padding-bottom:4px!important;}}
    .stApp:has(.overview-pipeline) .pipeline-page-header {{
        display:block; margin:0 0 10px; padding:0;}}
    .stApp:has(.overview-pipeline) .pipeline-page-header h1 {{
        font-size:1.28rem!important; line-height:1.2;}}
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_"] {{
        padding:5px 8px; gap:4px; overflow:hidden;}}
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_"] .card-title {{
        font-size:.92rem; line-height:1.2; padding-bottom:0;}}
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_main"] {{
        min-height:0;}}
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_status"],
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_platform"] {{
        height:160px; min-height:160px; overflow:visible;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link {{
        position:relative; display:flex; align-items:center; justify-content:center;
        width:100%; overflow:hidden; border-radius:10px; text-decoration:none!important;
        cursor:zoom-in; outline:1px solid transparent; transition:background .18s ease,
        outline-color .18s ease;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link {{
        height:clamp(285px,calc(100vh - 420px),760px);}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-secondary-link {{
        height:105px;}}
    .stApp:has(.overview-pipeline) .pipeline-status-content {{
        display:flex; flex-direction:column; min-width:0;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-status-preview {{
        display:flex; align-items:center; justify-content:center; height:83px;
        width:100%; overflow:hidden;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-status-preview svg {{
        display:block; width:100%; height:100%;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link:hover,
    .stApp:has(.overview-pipeline) .pipeline-gallery-link:focus-visible {{
        background:{palette["accent"]}14; outline-color:{palette["accent"]};}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link svg {{
        display:block; width:100%; height:100%; max-width:100%; max-height:100%;
        transition:transform .18s ease;}}
    .stApp:has(.overview-pipeline) .pipeline-platform-detailed {{display:none;}}
    .stApp:has(.overview-pipeline) .pipeline-platform-compact {{display:block; width:100%; height:100%;}}
    .stApp:has(.overview-pipeline) .pipeline-platform-compact svg,
    .stApp:has(.overview-pipeline) .pipeline-platform-detailed svg {{
        display:block; width:100%; height:100%;}}
    /* The complete SVG has room between its nodes: use it for larger labels
       in the preview without changing the focused diagram or its geometry. */
    /* Pipeline labels a step larger (D-150): the 1560-unit drawing is shown at about
       930 px, which made 13-unit labels near 8 px on screen. */
    [class*="st-key-card_pipeline_main"] svg text[font-size="8"] {{font-size:9.5px;}}
    [class*="st-key-card_pipeline_main"] svg text[font-size="9.5"] {{font-size:11px;}}
    [class*="st-key-card_pipeline_main"] svg text[font-size="12"] {{font-size:13.5px;}}
    [class*="st-key-card_pipeline_main"] svg text[font-size="13"] {{font-size:14.5px;}}
    /* Project documents (D-151): a readable column, clean tables, spaced headings. */
    .doc-source {{font-size:.85rem; margin:-4px 0 14px;}}
    .st-key-doc_actions .doc-source {{margin:0;}}
    .st-key-doc_actions {{margin:0 0 10px;}}
    .doc-path {{font-size:.8rem; color:{palette['reference']}; margin:0 0 -6px;}}
    .doc-path a {{color:{palette['accent']} !important; text-decoration:none;}}
    .doc-path a:hover {{text-decoration:underline;}}
    .doc-path i {{font-style:normal; margin:0 6px;}}
    /* A sheet (step 6): centred, with margins on both sides, like a printed page. */
    .st-key-project_document {{max-width:900px; margin:6px auto 30px; padding:44px 60px 48px;
        background:{palette['card']}; border:1px solid {palette['card_border']}; border-radius:16px;
        box-shadow:0 18px 40px -24px rgba(0,0,0,.45), 0 2px 6px -2px rgba(0,0,0,.12);}}
    .st-key-project_document > div > div:first-child h2:first-child {{border-top:none; margin-top:0;}}
    .st-key-project_document .doc-diagram {{background:transparent;}}
    /* The document views use the whole card, padding included, so their text stays at full size (D-247). */
    .st-key-project_document [data-testid="stIFrame"] {{width:calc(100% + 80px) !important; margin:0 -40px;}}
    /* Evidence cells hold long file and test names: they wrap instead of widening the table. */
    .st-key-project_document table {{table-layout:auto; width:100%;}}
    .st-key-project_document td code {{white-space:normal; overflow-wrap:normal; word-break:normal; font-size:.78rem;}}
    /* D-297: sober inline code: the text color on a faint tint, never Streamlit's bright green. */
    .st-key-project_document code {{color:{palette['strong_text']} !important; background:color-mix(in srgb, {palette['card_border']} 45%, transparent) !important;
        border:0 !important; border-radius:4px; padding:1px 5px !important; font-size:.8em; font-weight:500;
        font-family:ui-monospace, SFMono-Regular, Menlo, monospace;}}
    /* In a table, a file or a test is a reference, not a highlight: plain muted text, no chip. */
    .st-key-project_document td code {{background:transparent !important; padding:0 !important; color:{palette['reference']} !important;
        font-size:.74rem !important; font-weight:400; line-height:1.45;}}
    /* D-290: a first cell may be a whole sentence; an identifier such as RF-01 never breaks at its hyphen anyway. */
    .st-key-project_document td:first-child, .st-key-project_document th:first-child {{white-space:normal; min-width:6.5em;}}
    @media (max-width:900px) {{ .st-key-project_document {{padding:22px 18px 26px;}} }}
    .st-key-project_document h2 {{font-size:1.35rem; font-weight:600; letter-spacing:-.02em;
        margin:34px 0 10px; padding-top:14px; border-top:1px solid {palette['card_border']};
        color:{palette['strong_text']};}}
    .st-key-project_document h3 {{font-size:1.05rem; font-weight:500; margin:22px 0 6px;
        color:{palette['strong_text']};}}
    .st-key-project_document p, .st-key-project_document li {{font-size:.95rem; line-height:1.68;
        color:{palette['text']};}}
    .st-key-project_document strong {{color:{palette['strong_text']};}}
    .st-key-project_document blockquote {{border-left:3px solid {palette['accent']}; margin:12px 0;
        padding:8px 16px; background:color-mix(in srgb,{palette['accent']} 6%,transparent);
        border-radius:0 10px 10px 0;}}
    /* D-288: tables like a pivot table: a solid header band, banded rows and a first column that names the row. */
    .st-key-project_document table {{width:100%; border-collapse:separate; border-spacing:0; margin:12px 0 20px;
        font-size:.86rem; border:1px solid {palette['card_border']}; border-radius:12px; overflow:hidden;}}
    .st-key-project_document th {{background:{palette['accent']}; color:#ffffff; font-weight:600; text-align:left;
        padding:9px 12px; font-size:.78rem; letter-spacing:.04em; text-transform:uppercase;}}
    .st-key-project_document td {{padding:8px 12px; border-top:1px solid color-mix(in srgb,{palette['card_border']} 70%,transparent);
        vertical-align:top; line-height:1.5;}}
    .st-key-project_document tbody tr:nth-child(even) td {{background:color-mix(in srgb,{palette['accent']} 5%,transparent);}}
    .st-key-project_document tbody tr:hover td {{background:color-mix(in srgb,{palette['accent']} 10%,transparent);}}
    .st-key-project_document td:first-child {{font-weight:600; color:{palette['strong_text']};}}
    .st-key-project_document hr {{display:none;}}
    .doc-diagram {{margin:12px 0 22px; padding:14px; border:1px solid {palette['card_border']};
        border-radius:14px; background:{palette['card']};}}
    .doc-diagram .zoom-content > svg {{display:block; width:100%; height:auto; max-height:640px; margin:0 auto;}}
    .st-key-card_pipeline_main {{margin-top:6px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="12"] {{font-size:13px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="13"] {{font-size:15px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="14"] {{font-size:15px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="15"] {{font-size:16px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="16"] {{font-size:17px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link:hover svg {{transform:scale(1.01);}}
    .stApp:has(.overview-pipeline) .pipeline-open-label {{
        position:absolute; right:8px; bottom:6px; padding:3px 8px; border-radius:999px;
        color:{palette["strong_text"]}; background:{palette["card"]};
        border:1px solid {palette["card_border"]}; font-size:.68rem; font-weight:500;
        box-shadow:0 2px 10px rgba(0,0,0,.18);}}
    .stApp:has(.overview-pipeline) .run-status {{margin-bottom:2px; font-size:.7rem;}}
    .stApp:has(.overview-pipeline) .pipeline-focus-toolbar {{
        display:flex; align-items:center; justify-content:center;
        margin:0 0 5px; min-height:34px;}}
    .stApp:has(.overview-pipeline) .pipeline-focus-toolbar strong {{
        color:{palette["strong_text"]}; font-size:1rem;}}
    .stApp:has(.overview-pipeline) [class*="st-key-pipeline_focus_"] {{
        position:relative; height:calc(100vh - 155px); min-height:0; padding:8px 10px;
        overflow:hidden;
        border:1px solid {palette["card_border"]}; border-radius:14px;
        background:{palette["card"]};}}
    .stApp:has(.overview-pipeline) .pipeline-focus-return {{
        display:flex; justify-content:flex-end; margin:4px 2px 0;}}
    .stApp:has(.overview-pipeline) .pipeline-focus-return a {{
        display:inline-flex; align-items:center; min-height:32px; padding:5px 11px;
        border-radius:999px; border:1px solid {palette["card_border"]};
        background:{palette["card"]}; color:{palette["accent"]};
        box-shadow:0 3px 12px rgba(0,0,0,.15); text-decoration:none; font-size:.76rem;
        font-weight:500;}}
    .stApp:has(.overview-pipeline) .pipeline-focus-return a:hover {{
        border-color:{palette["accent"]};}}
    .stApp:has(.overview-pipeline) [class*="st-key-pipeline_focus_"] .zoom-buttons {{
        position:absolute; left:14px; bottom:12px; z-index:3; margin:0;
        justify-content:flex-start;}}
    .stApp:has(.overview-pipeline) [class*="st-key-pipeline_focus_"] .zoom-viewport {{
        max-height:calc(100vh - 215px);}}
    .stApp:has(.overview-pipeline) [class*="st-key-pipeline_focus_"] .zoom-content svg {{
        max-height:calc(100vh - 215px);}}
    @media (max-height:800px) and (min-width:1001px) {{
        .stApp:has(.overview-pipeline) .pipeline-gallery-main-link {{
            height:clamp(240px,calc(100vh - 440px),320px);}}
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_status"],
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_platform"] {{
            height:175px; min-height:175px;}}
        .stApp:has(.overview-pipeline) .pipeline-gallery-secondary-link {{height:90px;}}
        .stApp:has(.overview-pipeline) .pipeline-gallery-status-preview {{height:68px;}}
    }}
    @media (min-height:1000px) and (min-width:1200px) {{
        .stApp:has(.overview-pipeline) .pipeline-gallery-main-link {{
            height:clamp(420px,42vh,600px);}}
        .stApp:has(.overview-pipeline) [data-testid="stHorizontalBlock"]:has(
            [class*="st-key-card_pipeline_gallery_status"]) {{
            display:flex; flex-direction:column; gap:6px;}}
        .stApp:has(.overview-pipeline) [data-testid="stColumn"]:has(
            [class*="st-key-card_pipeline_gallery_status"]),
        .stApp:has(.overview-pipeline) [data-testid="stColumn"]:has(
            [class*="st-key-card_pipeline_gallery_platform"]) {{
            width:100%!important; flex:0 0 auto!important;}}
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_status"] {{
            height:100px; min-height:100px;}}
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_platform"] {{
            height:clamp(290px,29vh,390px); min-height:0;}}
        .stApp:has(.overview-pipeline) .pipeline-status-content {{
            flex-direction:row; align-items:center; gap:12px; height:65px;}}
        .stApp:has(.overview-pipeline) .pipeline-status-content .run-status {{
            flex:1; min-width:0; margin:0; white-space:nowrap;}}
        .stApp:has(.overview-pipeline) .pipeline-gallery-status-preview {{
            flex:1; min-width:0; height:65px;}}
        .stApp:has(.overview-pipeline) .pipeline-gallery-secondary-link {{
            height:calc(clamp(290px,29vh,390px) - 50px);}}
        .stApp:has(.overview-pipeline) .pipeline-platform-compact {{display:none;}}
        .stApp:has(.overview-pipeline) .pipeline-platform-detailed {{
            display:block; width:100%; height:100%;}}
    }}
    @media (max-width:1000px) {{
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_status"],
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_platform"] {{
            height:auto; min-height:150px;}}
    }}
    .stApp:has(.overview-history) [data-testid="stVegaLiteChart"] {{max-height:52vh; overflow:hidden;}}
    .stApp:has(.overview-kpis) .kpi-register td,
    .stApp:has(.overview-kpis) .kpi-register th {{padding:5px 7px!important; line-height:1.2;}}
    /* The report starts right under the header: the invisible script frame between them
       keeps no band of its own. */
    [class*="st-key-report_page"] {{ gap:1rem; margin-top:0; }}
    [class*="st-key-report_page"] [data-testid="stVerticalBlock"] {{ gap:1rem; }}
    [class*="st-key-report_page"] [class*="st-key-card_"] {{ padding:16px 18px 18px 18px;
                                                              border-radius: 14px; }}
    [class*="st-key-report_page"] .card-title {{ font-size: 0.95rem; margin-bottom: 2px; }}
    [class*="st-key-report_page"] .card-title .component-symbol {{ width: 24px; height: 26px;
                                                                    margin: 0; }}
    [class*="st-key-report_page"] .kpi-link {{ font-size: 0.75rem; }}
    /* Three channels fit on one line in the pulse's field. */
    [class*="st-key-report_page"] [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        font-size: 0.72rem; height: 22px; margin: 1px 3px 1px 0; padding: 0 4px 0 6px; }}
    [class*="st-key-report_page"] .overview-metric .component-symbol {{ width: 22px; height: 22px;
                                                                        margin: 0 6px 0 0; }}
    [class*="st-key-report_page"] .overview-metric .kpi-label {{ font-size: 0.82rem; }}
    [class*="st-key-report_page"] .overview-metric .market-metric-note {{ font-size: 0.72rem;
                                                                          margin: 0; }}
    [class*="st-key-report_page"] .overview-metrics {{ gap: 8px !important;
                                                       margin: 0 0 4px 0 !important; }}
    /* Each figure on one line: its name left, its value right. */
    [class*="st-key-report_page"] .overview-metrics > .overview-metric {{ padding:6px 12px !important; }}
    [class*="st-key-report_page"] .overview-metrics .market-metric-heading {{ margin: 0 !important; }}
    [class*="st-key-report_page"] .overview-metrics .kpi-value {{ font-size: 1.25rem !important;
                                                                  line-height: 1.2 !important;
                                                                  white-space: nowrap; }}
    [class*="st-key-report_page"] .market-eyebrow {{ display: none; }}
    .summary-sentence {{ font-size: 0.95rem; font-weight: 600; color: {palette["strong_text"]};
                         margin: 0 0 6px 0; line-height: 1.35; }}
    .context-line {{ font-size: 0.75rem; color: {palette["text"]}; margin: 0; }}
    [class*="st-key-report_page"] [data-testid="stHorizontalBlock"] {{ gap:14px; }}
    .st-key-dashboard_filter_bar {{ padding:10px 14px 8px; margin:4px 0 2px;
        background:{palette["card"]}; border:1px solid {palette["card_border"]}; border-radius:14px; }}
    [class*="st-key-report_page"] [data-testid="stCaptionContainer"] {{ margin: 0; }}
    /* Bold text of the side menu takes the menu's own ink (navy menu in Corporativo). */
    [data-testid="stSidebar"] strong {{ color: {palette["sidebar_text"]}; }}
    /* Every list of the page stands out from what is behind it: its own fill and a
       visible border, the accent on hover and focus (D-060). */
    [data-testid="stMain"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"])
        .react-aria-ComboBox > div {{
        background: {palette["field"]} !important;
        border: 1px solid {palette["reference"]}99 !important; border-radius: 10px !important;
    }}
    [data-testid="stMain"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"])
        .react-aria-ComboBox > div:hover,
    [data-testid="stMain"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"])
        .react-aria-ComboBox > div:focus-within {{
        border-color: {palette["accent"]} !important;
    }}
    /* A text field inside a card stands out from the card around it. */
    [class*="st-key-card_"] [data-testid="stTextInputRootElement"] {{
        background: {palette["background"]} !important;
        border-color: {palette["reference"]} !important;
    }}
    /* Long file paths wrap inside their cell on phones; words do not break. */
    table.card-table td a {{ overflow-wrap: anywhere; }}
    /* The cover (C01): flat and quiet; thin rules separate its rows, no cards per line. */
    .st-key-cover_top {{ justify-content:space-between; flex-wrap:wrap !important; gap:8px 16px;
        margin-bottom:6px; }}
    .st-key-cover_top > div {{ width:auto !important; flex:0 1 auto; }}
    .st-key-cover_top [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
    .st-key-cover_top [data-testid="stMarkdownContainer"] p {{ margin:0; }}
    .cover-eyebrow {{ color:{palette["text"]}; font-size:.76rem; font-weight:600;
        letter-spacing:.14em; text-transform:uppercase; }}
    a.cover-github {{ display:inline-block; padding:7px 14px; border:1px solid {palette["card_border"]};
        border-radius:10px; color:{palette["strong_text"]} !important; font-size:.88rem;
        font-weight:600; text-decoration:none; white-space:nowrap; }}
    a.cover-github:hover, a.cover-github:focus-visible {{ border-color:{palette["accent"]}; }}
    [data-testid="stMain"] .st-key-cover_hero h1 {{ font-size:clamp(2.5rem,5vw,3.7rem);
        font-weight:600; letter-spacing:-.02em; line-height:1.05; padding:0; margin:0 0 10px;
        color:{palette["strong_text"]}; }}
    .cover-tagline {{ color:{palette["strong_text"]}; font-size:clamp(1.2rem,2.1vw,1.6rem);
        font-weight:600; line-height:1.25; margin:0 0 12px; }}
    .cover-tagline span {{ display:block; color:{palette["accent"]}; }}
    /* Links of the cover say where they go: the icon of the target window is noise. */
    [class*="st-key-cover_"] [data-testid="stPageLink"] a > span:has([data-testid="stIconMaterial"]) {{
        display:none; }}
    .cover-lead {{ color:{palette["text"]}; font-size:1.06rem; line-height:1.5; margin:0 0 6px;
        max-width:34em; }}
    .st-key-cover_actions {{ flex-wrap:wrap !important; gap:12px; margin-top:4px; }}
    .st-key-cover_actions > div {{ width:auto !important; flex:0 0 auto; }}
    :is(.st-key-cover_primary, .st-key-cover_secondary) [data-testid="stPageLink"] a,
    :is(.st-key-cover_primary, .st-key-cover_secondary) a {{ display:inline-flex;
        align-items:center; padding:9px 18px; border-radius:10px; text-decoration:none;
        border:1px solid {palette["card_border"]}; background:transparent; }}
    .st-key-cover_primary [data-testid="stPageLink"] a, .st-key-cover_primary a {{
        background:{palette["accent"]}; border-color:{palette["accent"]}; }}
    .st-key-cover_primary a, .st-key-cover_primary a * {{ color:{palette["on_accent"]} !important;
        font-weight:600; }}
    .st-key-cover_secondary a, .st-key-cover_secondary a * {{ color:{palette["strong_text"]} !important;
        font-weight:600; }}
    .st-key-cover_primary a:hover {{ filter:brightness(1.08); }}
    .st-key-cover_secondary a:hover {{ border-color:{palette["accent"]}; }}
    .cover-figures {{ border:1px solid {palette["card_border"]}; border-radius:14px;
        background:{palette["card"]}; padding:18px 22px 14px; }}
    .cover-figures-title {{ color:{palette["strong_text"]}; font-weight:600; font-size:.95rem;
        margin-bottom:10px; }}
    .cover-figures dl {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
        gap:16px 22px; margin:0; }}
    .cover-figures dt {{ color:{palette["text"]}; font-size:.8rem; font-weight:600; }}
    .cover-figures dd {{ color:{palette["strong_text"]}; font-size:1.75rem; font-weight:600;
        margin:2px 0 0; line-height:1.15; font-variant-numeric:tabular-nums; }}
    .cover-figures dl span {{ color:{palette["text"]}; font-size:.78rem; }}
    .cover-figures p {{ color:{palette["text"]}; font-size:.74rem; margin:14px 0 0;
        padding-top:10px; border-top:1px solid {palette["grid"]}; }}
    .cover-statements {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
        margin:26px 0 0; padding:20px 0; border-top:1px solid {palette["card_border"]};
        border-bottom:1px solid {palette["card_border"]}; }}
    .cover-statements .cover-statement {{ padding:0 22px; }}
    .cover-statements .cover-statement:first-child {{ padding-left:0; }}
    .cover-statements .cover-statement + .cover-statement {{
        border-left:1px solid {palette["card_border"]}; }}
    .cover-statement {{ display:flex; gap:14px; align-items:flex-start; }}
    .cover-statement .component-symbol {{ width:28px; height:32px; margin:2px 0 0; }}
    .cover-statement h3 {{ color:{palette["strong_text"]}; font-size:1.08rem; font-weight:600;
        margin:0 0 4px; padding:0; }}
    .cover-statement p {{ color:{palette["text"]}; margin:0; line-height:1.45; }}
    .cover-heading {{ color:{palette["strong_text"]}; font-size:1.5rem !important;
        font-weight:600; margin:22px 0 4px !important; padding:0 !important; }}
    .st-key-cover_evidence {{ gap:0 !important; flex-wrap:nowrap !important;
        padding-bottom:18px; border-bottom:1px solid {palette["card_border"]}; }}
    .st-key-cover_evidence > div {{ flex:1 1 0 !important; min-width:0; }}
    [class*="st-key-cover_evidence_"]:not([class*="_link_"]) {{ padding:0 22px; height:100%; }}
    .st-key-cover_evidence > div:first-child [class*="st-key-cover_evidence_"] {{ padding-left:0; }}
    .st-key-cover_evidence > div + div {{ border-left:1px solid {palette["card_border"]}; }}
    .cover-evidence-title {{ color:{palette["strong_text"]}; font-weight:600; font-size:1.05rem;
        margin-bottom:4px; }}
    .cover-evidence-title span {{ color:{palette["accent"]}; margin-right:10px;
        font-variant-numeric:tabular-nums; }}
    .cover-evidence p {{ color:{palette["text"]}; margin:0 0 6px; line-height:1.45; }}
    .cover-evidence p.cover-evidence-figure {{ color:{palette["strong_text"]}; font-size:.9rem;
        font-weight:600; }}
    :is([class*="st-key-cover_evidence_link_"], .st-key-cover_offer_link,
        .st-key-cover_limits_link) [data-testid="stPageLink"] a {{ padding:0; min-height:0;
        background:transparent !important; }}
    :is([class*="st-key-cover_evidence_link_"], .st-key-cover_offer_link,
        .st-key-cover_limits_link) a, :is([class*="st-key-cover_evidence_link_"],
        .st-key-cover_offer_link, .st-key-cover_limits_link) a * {{
        color:{palette["accent"]} !important; font-weight:600; }}
    .st-key-cover_closing {{ gap:0 !important; flex-wrap:nowrap !important; padding-top:18px; }}
    .st-key-cover_closing > div {{ flex:1 1 0 !important; min-width:0; }}
    .st-key-cover_closing > div + div {{ border-left:1px solid {palette["card_border"]}; }}
    .st-key-cover_offer {{ padding-right:22px; }}
    .st-key-cover_limits {{ padding-left:22px; }}
    :is(.st-key-cover_offer_link, .st-key-cover_limits_link) {{ padding-left:42px; }}
    /* D-295: the profile dialog: the brand, the question and two pills; the professional profiles under their pill. */
    div[data-testid="stDialog"] [role="dialog"] {{ border-radius:22px; padding-top:6px; }}
    /* D-316: with the title hidden, the content starts under the × of every dialog; the × stays on top and clickable. */
    div[data-testid="stDialog"] [role="dialog"] button[aria-label="Close"] {{ position:relative; z-index:20; }}
    div[data-testid="stDialog"] [role="dialog"] > div:first-child:has(> div > h2), div[data-testid="stDialog"] [role="dialog"] h2 {{
        display:none !important; }}
    .profile-brand {{ display:flex; align-items:center; justify-content:center; gap:10px; margin:6px 0 10px;
        color:{palette["strong_text"]}; font-size:1rem; font-weight:600; }}
    .profile-logo {{ display:inline-flex; align-items:center; justify-content:center; width:32px; height:32px; border-radius:9px;
        background:linear-gradient(135deg, #2dd4bf, #2563eb); color:#ffffff; font-family:"Material Symbols Rounded";
        font-size:20px; font-weight:400; line-height:1; font-feature-settings:"liga"; }}
    .profile-ask {{ text-align:center; color:{palette["strong_text"]} !important; font-size:1.65rem !important;
        font-weight:700 !important; letter-spacing:-.02em; margin:0 0 1.5rem !important; line-height:1.2 !important; }}
    .st-key-profile_choices {{ align-items:flex-start !important; }}
    .st-key-profile_choices > div {{ flex:1 1 0 !important; min-width:0; }}
    /* D-336, D-369: the two pills share one look, and their names never break in two lines, in either language. */
    [class*="st-key-profile_choose_"] button {{ min-height:52px; width:100%;
        border-radius:999px; border:1px solid {palette["card_border"]}; background:{palette["card"]}; padding:0 10px; }}
    [class*="st-key-profile_choose_"] button p {{ font-size:1rem; font-weight:600;
        color:{palette["strong_text"]}; white-space:nowrap; }}
    @media(max-width:480px) {{
        [class*="st-key-profile_choose_"] button p {{ font-size:.82rem; }}
        [class*="st-key-profile_choose_"] button [data-testid="stIconMaterial"] {{ display:none; }}
    }}
    /* D-369: the author's door, a small quiet link in the window's top corner; its key field opens on click. */
    div[data-testid="stDialog"] [role="dialog"]:has(.st-key-profile_author_corner) {{ position:relative; }}
    .st-key-profile_author_corner {{ position:absolute !important; top:12px; right:14px; width:auto !important;
        z-index:20; }}
    .st-key-profile_author_corner button {{ min-height:0 !important; padding:2px 4px !important; }}
    .st-key-profile_author_corner button p, .st-key-profile_author_corner button [data-testid="stIconMaterial"] {{
        font-size:.72rem !important; color:{palette["reference"]}; font-weight:400; }}
    .st-key-profile_author_corner button:hover p,
    .st-key-profile_author_corner button:hover [data-testid="stIconMaterial"] {{ color:{palette["accent"]}; }}
    /* D-369: while the window asks for the view, the app behind is covered: an opaque dark layer, nothing readable. */
    div[data-testid="stDialog"]:has(.st-key-profile_choices) {{ background:rgba(4, 8, 16, .97) !important;
        backdrop-filter:blur(24px); -webkit-backdrop-filter:blur(24px); }}
    .st-key-profile_choose_profesional button {{ background:color-mix(in srgb, {palette["accent"]} 12%, transparent);
        border-color:color-mix(in srgb, {palette["accent"]} 45%, transparent); }}
    .st-key-profile_choose_profesional button p, .st-key-profile_choose_profesional button [data-testid="stIconMaterial"] {{
        color:{palette["accent"]}; }}
    [class*="st-key-profile_choose_"] button:hover {{ border-color:{palette["accent"]}; }}
    /* D-336: the profiles line starts under its pill instead of being centered on it: with three pills a centered line
       ran out of the dialog on the left. */
    .st-key-profile_roles {{ justify-content:flex-start; flex-wrap:nowrap !important; width:max-content !important;
        max-width:none !important; margin:4px 0 0 4px !important; }}
    .st-key-profile_roles > div {{ flex:none !important; width:auto !important; }}
    .st-key-profile_roles button {{ padding:0 2px !important; min-height:0 !important; }}
    .st-key-profile_roles button p {{ font-size:.72rem; color:{palette["reference"]}; white-space:nowrap; }}
    .st-key-profile_roles > div + div button p::before {{ content:"·"; margin-right:4px; color:{palette["reference"]}; }}
    .st-key-profile_roles button:hover p {{ color:{palette["accent"]}; }}
    @media(max-width:900px) {{
        .cover-statements {{ grid-template-columns:1fr; padding:6px 0; }}
        .cover-statements .cover-statement {{ padding:14px 0; }}
        .cover-statements .cover-statement + .cover-statement {{ border-left:none;
            border-top:1px solid {palette["grid"]}; }}
        .st-key-cover_evidence, .st-key-cover_closing {{ flex-wrap:wrap !important; }}
        .st-key-cover_evidence > div, .st-key-cover_closing > div {{ flex:1 1 100% !important; }}
        .st-key-cover_evidence > div + div, .st-key-cover_closing > div + div {{ border-left:none;
            border-top:1px solid {palette["grid"]}; }}
        [class*="st-key-cover_evidence_"]:not([class*="_link_"]) {{ padding:12px 0; }}
        .st-key-cover_offer, .st-key-cover_limits {{ padding:12px 0; }}
    }}
    @media(max-width:640px) {{
        .app-brand span {{ display:inline; }}
        .kpi-strip-item {{ flex:1 1 45%; border-left:none; padding-left:4px; }}
        .kpi-strip-value {{ font-size:1.35rem; }}
        .st-key-report_filters > div:has(> [class*="st-key-bar_"]) {{ flex:1 1 100%; }}
    }}
    """
    )


# endregion


# region Menu styles
def build_section_colors_css(dark):
    """The flat menu (D-231): sections divided by a hairline, rows with a thin icon; the current page has a faint fill
    and a blue bar on its left. D-501: the sizes of a side panel like those of VS Code or Apple: rows of 13 px and thin,
    grey section headings of 11 px in plain case, and a menu of 232 px."""
    text, heading, icon, hover, current, accent, line = MENU_INK[dark]
    return f"""[class*="st-key-nav_block_"] {{margin:0 !important; padding:8px 0 !important; gap:2px !important;
        background:transparent !important; border:0; border-bottom:1px solid {line}; border-radius:0; box-shadow:none;}}
    .st-key-nav_block_documentos {{border-bottom:0;}}
    [class*="st-key-nav_block_"], [class*="st-key-nav_group_"], [class*="st-key-nav_group_"] > div,
    [class*="st-key-nav_group_"] button {{width:100% !important; box-sizing:border-box;}}
    [class*="st-key-nav_group_"] button {{justify-content:flex-start !important; padding:1px 8px !important;
        min-height:22px !important; background:transparent !important; border:0 !important; margin:0 0 4px;}}
    [class*="st-key-nav_group_"] button:hover:not(:disabled) {{background:transparent !important;}}
    [class*="st-key-nav_group_"] button > div {{justify-content:flex-start !important;}}
    [class*="st-key-nav_group_"] button p {{color:{heading} !important; -webkit-text-fill-color:{heading} !important;
        font-size:.6875rem !important; font-weight:500 !important; letter-spacing:0 !important; white-space:nowrap;
        text-align:left !important;}}
    [class*="st-key-nav_group_"] button:hover p {{color:{text} !important; -webkit-text-fill-color:{text} !important;}}
    [class*="st-key-nav_group_"] button p::after {{content:"⌄"; margin-left:8px; opacity:0; transition:opacity .12s ease;}}
    [class*="st-key-nav_group_"] button:hover p::after {{opacity:.8;}}
    [class*="st-key-nav_group_"][class*="_folded"] button p::after {{content:"›"; opacity:.8;}}
    /* D-459: «Dashboards», the title of the three tiles under «Negocio · BA y BI»: smaller than a section, set in. */
    /* Its block keeps the -1rem of a markdown block (D-173), so the paragraph keeps 1rem under it. */
    [data-testid="stSidebar"] p.nav-subtitle {{margin:0 0 calc(1rem + 3px) !important; padding:0 8px; color:{heading} !important;
        opacity:.8; font-size:.6875rem !important; font-weight:400; letter-spacing:0;}}
    /* D-512: rows of 28 px with 2 px between them, the air of VS Code's explorer, so a click never lands on the
       neighbour. */
    [class*="st-key-nav_block_"] [data-testid="stPageLink"] a {{position:relative; padding:3px 8px !important;
        min-height:28px !important; border-radius:6px !important; border:0 !important;
        background:transparent !important; box-shadow:none !important; gap:0 !important;}}
    [class*="st-key-nav_block_"] [data-testid="stPageLink"] a:hover {{background:{hover} !important;}}
    [class*="st-key-nav_block_"] [data-testid="stPageLink"] p {{color:{text} !important; -webkit-text-fill-color:{text} !important;
        font-size:.8125rem !important; font-weight:400 !important; padding-left:8px; text-shadow:none !important;
        white-space:normal; overflow:visible; text-overflow:clip; line-height:1.3;}}
    [class*="st-key-nav_block_"] [data-testid="stPageLink"] [data-testid="stIconMaterial"] {{color:{icon} !important;
        font-size:16px !important; width:16px; opacity:1; font-variation-settings:"wght" 300;}}
    [class*="st-key-nav_block_"] [class*="_nav_current"] [data-testid="stPageLink"] a {{background:{current} !important;}}
    [class*="st-key-nav_block_"] [class*="_nav_current"] [data-testid="stPageLink"] a::before {{content:""; position:absolute;
        left:0; top:7px; bottom:7px; width:3px; border-radius:3px; background:{accent};}}
    [class*="st-key-nav_block_"] [class*="_nav_current"] [data-testid="stPageLink"] p {{font-weight:500 !important;}}
    [class*="st-key-nav_block_"] [class*="_nav_current"] [data-testid="stIconMaterial"] {{color:{accent} !important;}}
    [data-testid="stSidebar"] a.nav-source-link {{display:flex; align-items:center; padding:5px 8px !important; margin:0 !important;
        font-size:.8125rem; color:{text} !important; -webkit-text-fill-color:{text} !important; text-decoration:none !important;
        border-radius:6px; line-height:1.3;}}
    [data-testid="stSidebar"] a.nav-source-link:hover {{background:{hover};}}
    [data-testid="stSidebar"] .nav-source-icon {{margin-right:8px; color:{icon}; flex:0 0 auto;}}    /* D-298: the alert of a failed load, under the menu, on every page. */
    .st-key-load_alert {{margin:0 0 6px; padding:8px 12px 6px; border-radius:10px; gap:2px !important;
        border:1px solid #e5484d; background:color-mix(in srgb, #e5484d 14%, transparent);}}
    .st-key-load_alert [data-testid="stMarkdownContainer"] {{margin-bottom:0 !important;}}
    .st-key-load_alert [data-testid="stElementContainer"] {{margin:0 !important;}}
    .st-key-load_alert p.load-alert-title {{margin:0 !important; font-size:.86rem !important; font-weight:600; line-height:1.3 !important;
        color:#ff8b8f !important;}}
    .st-key-load_alert p.load-alert-note {{margin:0 0 2px !important; font-size:.74rem !important; line-height:1.3 !important;
        color:{text} !important;}}
    .st-key-load_alert [data-testid="stPageLink"] a {{padding:0 !important; min-height:0 !important;}}
    .st-key-load_alert [data-testid="stPageLink"] p {{font-size:.76rem !important; color:{text} !important; text-decoration:underline;}}
"""


def build_bar_icons_css(quiet, bright):
    """D-540: the icon of each button of the activity bar, as a CSS mask in one tone, like VS Code's."""

    def mask(name):
        encoded = base64.b64encode(activity_bar.build_icon_svg(name).encode()).decode()
        return f'url("data:image/svg+xml;base64,{encoded}")'

    buttons = {
        '[class*="st-key-nav_folder_tile_0"] [data-testid="stPageLink"] a': "documents",
        '[class*="st-key-nav_folder_tile_1"] [data-testid="stPageLink"] a': "study",
        ".st-key-sources_tile button": "sources",
    } | {f".st-key-stack_tile_{key} button": icon for key, _, icon, _ in activity_bar.STACK_AREAS}
    rules = [
        f"{selector}::before {{content:\"\"; flex:none; width:22px !important; height:22px !important;"
        f" background:{quiet} !important; -webkit-mask:{mask(icon)} center / contain no-repeat;"
        f" mask:{mask(icon)} center / contain no-repeat; transition:background .15s ease;}}"
        for selector, icon in buttons.items()
    ]
    lit = ", ".join(f"{selector}:hover::before" for selector in buttons)
    current = '[class*="st-key-nav_folder_tile_"][class*="_nav_current"] [data-testid="stPageLink"] a::before'
    rules.append(f"{lit}, {current} {{background:{bright} !important; transform:none;}}")
    return "\n    ".join(rules)


def build_sidebar_css(mode):
    palette = charts.get_palette(mode)
    # The sidebar is flat (D-231): one plain surface, no gradient, border or shadow. Its text
    # follows that surface: Corporativo has a light page but a dark navy sidebar.
    dark = is_dark_surface(palette["sidebar"])
    text = MENU_INK[dark][0]
    hairline = MENU_INK[dark][6]
    quiet = "rgba(214, 218, 227, .68)" if dark else "rgba(31, 41, 55, .68)"
    # The price alert sits on the page, not in the sidebar (D-264): its red follows the page's surface.
    alert_text = "#ff9ca4" if is_dark_surface(palette["background"]) else "#9d1f2c"
    drop_text = "#6ee7a0" if is_dark_surface(palette["background"]) else "#15693a"
    view_ink = "#7dd3fc" if dark else palette["accent"]  # D-373: the view button reads on the sidebar's surface
    return f"""<style>
    [data-testid="stSidebar"] {{background:{palette['sidebar']}; border-right:0; box-shadow:none;}}
    [data-testid="stSidebar"][data-collapsed="false"] {{min-width:{232 + ACTIVITY_BAR}px !important;
        max-width:{232 + ACTIVITY_BAR}px !important;}}
    /* D-501: the menu keeps its width for its words: Streamlit's 20 px of margin leave. */
    [data-testid="stSidebarContent"] {{background:transparent; padding-left:0 !important; padding-right:0 !important;}}
    /* D-504: the logo and the fold button stay in sight, stuck to the top of the menu, when it scrolls. The header
       owns the 20 px of air under the logo (Streamlit's 16 px margin plus 4 px), so its surface paints that band. */
    [data-testid="stSidebarHeader"] {{height:72px; padding:12px 10px 26px 16px !important; margin-bottom:0 !important;
        border-bottom:0; position:sticky; top:0; z-index:6; background:{palette['sidebar']};}}
    [data-testid="stSidebarHeader"] img {{max-width:148px !important; height:28px !important;}}
    [data-testid="stSidebarCollapseButton"] button {{width:32px; height:32px; min-height:32px;
        border:0 !important; border-radius:8px !important; background:transparent !important; box-shadow:none;}}
    /* The menu is the only thing that scrolls when it does not fit; its bar shows on hover. */
    [data-testid="stSidebarContent"] {{overflow-y:auto; scrollbar-width:none;}}
    [data-testid="stSidebarContent"]:hover {{scrollbar-width:thin; scrollbar-color:{hairline} transparent;}}
    [data-testid="stSidebarContent"]::-webkit-scrollbar {{width:0;}}
    [data-testid="stSidebarContent"]:hover::-webkit-scrollbar {{width:6px;}}
    [data-testid="stSidebarContent"]:hover::-webkit-scrollbar-thumb {{background:{hairline}; border-radius:3px;}}
    [data-testid="stSidebarUserContent"] {{padding:0 8px !important;}}
    /* D-504: the menu's column is as tall as the window under the 72 px header, no more, so nothing scrolls towards
       a void when the menu fits. D-539: the footer is no longer at its end but a column of icons on its left edge. */
    [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {{gap:0 !important;
        min-height:calc(100vh - 72px); padding-bottom:0;}}
    [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"]
        > [data-testid="stLayoutWrapper"]:has(> .st-key-sidebar_footer) {{position:fixed !important; top:0 !important;
        bottom:0 !important; left:0 !important; width:{ACTIVITY_BAR}px !important; max-width:none; margin:0 !important;
        z-index:8;}}
    [data-testid="stSidebarNav"] {{display:none;}}
    {build_section_colors_css(dark)}
    /* GitHub's mark on a light pill in the footer (D-124): a near-black logo on a
       near-white background reads on every sidebar, where the blue mark almost vanished. */
    .st-key-sidebar_tools {{gap:3px !important; justify-content:flex-start !important;}}
    .st-key-sidebar_tools > div {{flex:0 0 auto !important; width:auto !important;}}
    .sidebar-github {{display:inline-flex; align-items:center; justify-content:center;
        width:28px; height:28px; border-radius:7px; background:#f6f8fa;
        border:1px solid rgba(255,255,255,.55); color:#1f2328 !important; transition:transform .12s ease;}}
    .sidebar-github svg {{fill:#1f2328; width:16px; height:16px;}}
    .sidebar-github:hover {{transform:translateY(-1px);}}
    .sidebar-github-current {{outline:2px solid {palette['accent']}; outline-offset:2px;}}
    /* D-373: the view button, under the logo, before the menu: visible, with its profile icon. */
    .st-key-profile_indicator_top {{ padding:0 0 10px; }}
    [data-testid="stSidebarLogo"], [data-testid="stHeaderLogo"] {{ cursor:pointer; }}
    [data-testid="stSidebar"] .st-key-profile_indicator_top button {{ min-height:28px; justify-content:flex-start;
        border-radius:10px !important; border:1px solid color-mix(in srgb, {view_ink} 55%, transparent) !important;
        background:color-mix(in srgb, {view_ink} 12%, transparent) !important; }}
    [data-testid="stSidebar"] .st-key-profile_indicator_top button p,
    [data-testid="stSidebar"] .st-key-profile_indicator_top button [data-testid="stIconMaterial"] {{
        color:{view_ink} !important; font-weight:400; font-size:.71875rem; }}
    [data-testid="stSidebar"] .st-key-profile_indicator_top button:hover {{ border-color:{view_ink} !important; }}
    /* D-539: the footer is the activity bar: folders and sources at the top, appearance and language at the bottom. */
    .st-key-sidebar_footer {{height:100%; padding:14px 0 12px !important; gap:4px !important; align-items:center;
        justify-content:space-between; border-right:1px solid {hairline};
        background:color-mix(in srgb, {palette['sidebar']} 92%, {text}) !important;}}
    /* The price alerts, a red chip in the Resumen's bar (D-169, D-264). */
    .st-key-home_alert_trigger button, .st-key-dialog_alert_trigger button {{border:0 !important; background:color-mix(in srgb,{alert_text} 14%,transparent) !important;
        color:{alert_text} !important; border-radius:8px; padding:3px 10px !important; min-height:28px; box-shadow:none !important;}}
    .st-key-home_alert_trigger button:hover, .st-key-dialog_alert_trigger button:hover {{background:color-mix(in srgb,{alert_text} 24%,transparent) !important;}}
    .st-key-home_alert_trigger button p, .st-key-dialog_alert_trigger button p {{color:{alert_text} !important; -webkit-text-fill-color:{alert_text} !important;
        font-weight:600; font-size:13.5px; letter-spacing:0; font-variant-numeric:tabular-nums;}}
    /* D-478: a chip's help never stays over the window it opened. */
    body:has([data-testid="stDialog"]) [data-baseweb="tooltip"] {{display:none !important;}}
    /* D-477: the sharp drops, a green chip beside it: good news for whoever buys. */
    .st-key-home_drop_trigger button, .st-key-dialog_drop_trigger button {{border:0 !important; background:color-mix(in srgb,{drop_text} 14%,transparent) !important;
        color:{drop_text} !important; border-radius:8px; padding:3px 10px !important; min-height:28px; box-shadow:none !important;}}
    .st-key-home_drop_trigger button:hover, .st-key-dialog_drop_trigger button:hover {{background:color-mix(in srgb,{drop_text} 24%,transparent) !important;}}
    .st-key-home_drop_trigger button p, .st-key-dialog_drop_trigger button p {{color:{drop_text} !important; -webkit-text-fill-color:{drop_text} !important;
        font-weight:600; font-size:13.5px; letter-spacing:0; font-variant-numeric:tabular-nums;}}
    /* D-491: the one shown in step 3 is outlined; both wait, faded, until a family is chosen. */
    .st-key-home_alert_trigger [data-testid="stBaseButton-primary"], .st-key-dialog_alert_trigger [data-testid="stBaseButton-primary"] {{box-shadow:inset 0 0 0 1.5px {alert_text} !important;}}
    .st-key-home_drop_trigger [data-testid="stBaseButton-primary"], .st-key-dialog_drop_trigger [data-testid="stBaseButton-primary"] {{box-shadow:inset 0 0 0 1.5px {drop_text} !important;}}
    .st-key-home_alert_trigger button:disabled, .st-key-home_drop_trigger button:disabled, .st-key-dialog_alert_trigger button:disabled, .st-key-dialog_drop_trigger button:disabled {{opacity:.45;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button {{background:transparent !important;
        box-shadow:none !important; color:{quiet} !important; padding:6px 8px !important;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button p {{color:{quiet} !important; font-size:.71875rem !important;}}
    [data-testid="stSidebar"] .st-key-language_switch button p {{color:{text} !important; -webkit-text-fill-color:{text} !important;}}
    .st-key-language_switch {{gap:3px !important;}}
    .st-key-profile_indicator_top button p {{white-space:nowrap !important;}}
    .st-key-sidebar_tools {{flex-wrap:nowrap !important; gap:3px !important;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button {{padding:4px 5px !important;}}
    .st-key-sidebar_tiles {{margin:0 0 6px !important;}}
    .st-key-sidebar_tiles > div {{flex:1 1 0 !important; min-width:0 !important;}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a, .st-key-sources_tile button {{
        display:flex !important; flex-direction:column; align-items:center; justify-content:center; gap:4px;
        width:34px !important; height:34px; min-height:34px !important; padding:0 !important; gap:0 !important;
        border-radius:6px; background:transparent !important;
        border:1px solid {MENU_INK[dark][6]} !important; box-shadow:none !important;}}
    .st-key-sources_tile, .st-key-sources_tile [data-testid="stLayoutWrapper"], .st-key-sources_tile [data-testid="stPopover"],
    .st-key-sources_tile [data-testid="stPopover"] > div {{width:100% !important;}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] {{margin:0 !important;}}
    .st-key-sources_tile button::before {{content:""; flex:none; width:22px; height:16px;
        background:url("data:image/svg+xml;base64,{base64.b64encode(SOURCES_TILE_SVG.encode()).decode()}") center / contain no-repeat;
        transition:transform .18s ease;}}
    .st-key-sources_tile button:hover {{background:{MENU_INK[dark][3]} !important;}}
    .st-key-sources_tile button:hover::before {{transform:translateY(-2px);}}
    .st-key-sources_tile button p {{color:{text} !important; -webkit-text-fill-color:{text} !important;
        font-size:.65rem !important; font-weight:400 !important; line-height:1.15 !important; white-space:nowrap; margin:0 !important;}}
    .st-key-sources_tile button [data-testid="stIconMaterial"], .st-key-sources_tile button svg {{display:none !important;}}
    .st-key-sources_tile button > div > div:has([data-testid="stIconMaterial"]) {{display:none !important;}}
    .st-key-sources_tile button > div {{display:contents;}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a::before {{content:""; flex:none; width:22px; height:16px;
        background:url("data:image/svg+xml;base64,{base64.b64encode(FOLDER_TILE_SVG.encode()).decode()}") center / contain no-repeat;
        transition:transform .18s ease;}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a:hover {{background:{MENU_INK[dark][3]} !important;}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a:hover::before {{transform:translateY(-2px);}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] p {{color:{text} !important; -webkit-text-fill-color:{text} !important;
        font-size:.65rem !important; font-weight:400 !important; line-height:1.12 !important; margin:0 !important;}}
    [class*="st-key-nav_folder_tile_"][class*="_nav_current"] [data-testid="stPageLink"] a {{background:{MENU_INK[dark][4]} !important;
        border-color:{MENU_INK[dark][5]};}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a > span:has([data-testid="stIconMaterial"]),
    [class*="st-key-nav_folder_tile"] [data-testid="stIconMaterial"] {{display:none !important;}}
    [class*="st-key-nav_folder_tile_1"] [data-testid="stPageLink"] a::before {{
        background-image:url("data:image/svg+xml;base64,{base64.b64encode(STUDY_TILE_SVG.encode()).decode()}") !important;}}
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] {{margin:2px 0 2px !important;}}
    [class*="st-key-nav_dashboard_tile_1"] [data-testid="stPageLink"] {{margin:0 0 2px !important;}}
    [class*="st-key-nav_dashboard_tile_1"] [data-testid="stPageLink"] a::before {{
        background-image:url("data:image/svg+xml;base64,{base64.b64encode(CHANNELS_TILE_SVG.encode()).decode()}") !important;}}
    [class*="st-key-nav_dashboard_tile_2"] [data-testid="stPageLink"] {{margin:0 0 10px !important;}}
    [class*="st-key-nav_dashboard_tile_2"] [data-testid="stPageLink"] a::before {{
        background-image:url("data:image/svg+xml;base64,{base64.b64encode(BA_TILE_SVG.encode()).decode()}") !important;}}
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] a {{display:flex !important; flex-direction:row;
        align-items:center; gap:8px !important; width:100% !important; min-height:36px !important; padding:4px 8px !important;
        border-radius:6px; background:{MENU_INK[dark][3]} !important; border:1px solid {MENU_INK[dark][6]} !important;
        box-shadow:none !important;}}
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] a::before {{content:""; flex:none; width:30px; height:22px;
        background:url("data:image/svg+xml;base64,{base64.b64encode(DASHBOARD_TILE_SVG.encode()).decode()}") center / contain no-repeat;
        transition:transform .18s ease;}}
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] a:hover {{background:{MENU_INK[dark][4]} !important;}}
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] a:hover::before {{transform:translateY(-2px);}}
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] p {{color:{text} !important; -webkit-text-fill-color:{text} !important;
        font-size:.8125rem !important; font-weight:400 !important; margin:0 !important;}}
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] a span:has(> div > p),
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] a span:has(> div > p) *,
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] p {{white-space:normal !important;
        overflow:visible !important; text-overflow:clip !important; line-height:1.2 !important;}}
    [class*="st-key-nav_dashboard_tile"][class*="_lit"] [data-testid="stPageLink"] a {{border-color:{MENU_INK[dark][5]} !important;
        background:{MENU_INK[dark][4]} !important;
        box-shadow:inset 3px 0 0 #5aa9ea !important;}}
    [class*="st-key-nav_dashboard_tile"] [data-testid="stPageLink"] a > span:has([data-testid="stIconMaterial"]),
    [class*="st-key-nav_dashboard_tile"] [data-testid="stIconMaterial"] {{display:none !important;}}
    .st-key-sidebar_footer [data-testid="stCaptionContainer"] p {{color:{text} !important; opacity:.75;
        font-size:.69rem; line-height:1.35; padding:0 3px;}}
    /* D-539: the footer is an activity bar, like VS Code's: a column of icons on the menu's left edge, the folders and
       the sources at the top, appearance and language at the bottom, each named on hover. The menu keeps its 232 px
       beside it and the whole height of the window, so «Calidad» is in sight when the app opens. */
    [data-testid="stSidebar"][data-collapsed="false"] [data-testid="stSidebarUserContent"] {{
        padding-left:{ACTIVITY_BAR + 8}px !important;}}
    [data-testid="stSidebar"][data-collapsed="false"] [data-testid="stSidebarHeader"] {{
        padding-left:{ACTIVITY_BAR + 16}px !important;}}
    [data-testid="stSidebar"][data-collapsed="true"] .st-key-sidebar_footer {{display:none !important;}}
    .st-key-sidebar_footer > div {{width:auto !important; flex:0 0 auto !important;}}
    .st-key-sidebar_tiles, .st-key-sidebar_tools, .st-key-language_switch {{flex-direction:column !important;
        align-items:center !important; gap:6px !important; margin:0 !important; width:auto !important;}}
    .st-key-sidebar_tiles > div, .st-key-sidebar_tools > div, .st-key-language_switch > div {{flex:0 0 auto !important;
        width:auto !important; min-width:0 !important;}}
    .st-key-sources_tile, .st-key-sources_tile [data-testid="stLayoutWrapper"], .st-key-sources_tile [data-testid="stPopover"],
    .st-key-sources_tile [data-testid="stPopover"] > div {{width:auto !important;}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a, .st-key-sources_tile button,
    .st-key-sidebar_appearance [data-testid="stPopover"] button {{width:34px !important; height:34px !important;
        min-height:34px !important; padding:0 !important; border:0 !important; border-radius:8px !important;
        justify-content:center !important; align-items:center !important; background:transparent !important;}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a::before, .st-key-sources_tile button::before {{
        width:22px !important; height:18px !important;}}
    /* The names stay for screen readers and on hover; the bar shows only the icons. */
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] p, .st-key-sources_tile button p,
    .st-key-sidebar_appearance [data-testid="stPopover"] button p {{position:absolute !important; width:1px !important;
        height:1px !important; overflow:hidden !important; clip:rect(0 0 0 0) !important; white-space:nowrap !important;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button div[aria-hidden="true"] {{display:none !important;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button [data-testid="stIconMaterial"] {{font-size:20px !important;
        margin:0 !important; color:{quiet} !important;}}
    [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a:hover, .st-key-sources_tile button:hover,
    .st-key-sidebar_appearance [data-testid="stPopover"] button:hover {{background:{MENU_INK[dark][3]} !important;}}
    [class*="st-key-nav_folder_tile_"][class*="_nav_current"] [data-testid="stPageLink"] a {{
        background:{MENU_INK[dark][4]} !important; box-shadow:inset 2px 0 0 {palette['accent']} !important;}}
    .st-key-language_switch button {{width:34px !important; min-width:34px !important; height:26px !important;
        min-height:26px !important; padding:0 !important;}}
    .st-key-language_switch button p {{font-size:.6875rem !important;}}
    /* D-540: line icons in one tone, like VS Code's: each shape is a mask painted in the menu's quiet ink, brighter on
       hover or while its page is open; the stack of each area opens in a window, names only. */
    {build_bar_icons_css(quiet, text)}
    [class*="st-key-stack_tile_"], [class*="st-key-stack_tile_"] [data-testid="stLayoutWrapper"],
    [class*="st-key-stack_tile_"] [data-testid="stPopover"], [class*="st-key-stack_tile_"] [data-testid="stPopover"] > div {{
        width:auto !important;}}
    [class*="st-key-nav_folder_tile"], [class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] {{height:34px; min-height:34px;}}
    [class*="st-key-stack_tile_"] button {{display:flex !important; flex-direction:column; align-items:center;
        justify-content:center; gap:0 !important;
        width:34px !important; height:34px !important; min-height:34px !important; padding:0 !important;
        border:0 !important; border-radius:8px !important; background:transparent !important; box-shadow:none !important;}}
    [class*="st-key-stack_tile_"] button:hover {{background:{MENU_INK[dark][3]} !important;}}
    [class*="st-key-stack_tile_"] button p {{position:absolute !important; width:1px !important; height:1px !important;
        overflow:hidden !important; clip:rect(0 0 0 0) !important; white-space:nowrap !important;}}
    [class*="st-key-stack_tile_"] button [data-testid="stIconMaterial"],
    [class*="st-key-stack_tile_"] button > div > div:has([data-testid="stIconMaterial"]) {{display:none !important;}}
    [class*="st-key-stack_tile_"] button > div {{display:contents;}}
    .stack-list .stack-title {{margin:0 0 6px !important; font-size:12px !important; font-weight:600; color:{text};}}
    .stack-list ol {{margin:0; padding-left:22px; font-size:12.5px; line-height:1.6;}}
    .stack-list li::marker {{color:{quiet}; font-variant-numeric:tabular-nums;}}
    </style>"""


# endregion
