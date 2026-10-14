"""Surfaces of the live dashboard: a plain background and light panels (D-068)."""
from bi import charts


def build_css(mode):
    """Scope every visual change to the dashboard, keeping native chart interaction."""
    palette = charts.get_palette(mode)
    dark = palette["base"] != charts.BASE_LIGHT

    def rgba(color, opacity):
        red, green, blue = (int(color[index:index + 2], 16) for index in (1, 3, 5))
        return f"rgba({red}, {green}, {blue}, {opacity})"

    # Use the established slate/cyan palette, rather than tinting panels green.
    surface = rgba(palette["card"], .94 if dark else .95)
    raised_surface = rgba(palette["field"], .96)
    border = rgba(palette["card_border"], .85)
    # Light panels: a thin border and almost no shadow, on a plain background.
    shadow = "0 1px 2px rgba(0, 0, 0, .12)"
    return f"""
    .stApp:has(.st-key-market_dashboard) {{
        background-color:{palette["background"]};
    }}
    .stApp:has(.st-key-market_dashboard) [data-testid="stHeader"] {{
        background:transparent;
    }}
    .stApp:has(.st-key-market_dashboard) [data-testid="stMainBlockContainer"] {{
        max-width:1600px; padding-inline:clamp(20px, 3.3vw, 64px);
    }}
    .st-key-market_dashboard {{ gap:18px; }}
    .st-key-market_intro {{ padding:4px 0 8px; max-width:780px; gap:4px; }}
    .st-key-market_intro h1 {{ font-size:clamp(1.8rem, 3vw, 2.6rem); letter-spacing:-.045em;
        padding-block:4px 10px; }}
    .market-eyebrow {{ font-size:.73rem; letter-spacing:.19em; font-weight:650;
        text-transform:uppercase; margin:0 0 4px; }}
    .st-key-market_intro .page-subtitle {{ font-size:1rem; max-width:560px; line-height:1.6; }}
    .st-key-market_dashboard .overview-metrics {{
        padding:0; margin:0 0 8px; background:transparent; border:0; gap:14px;
    }}
    .st-key-market_dashboard .overview-metrics > .overview-metric,
    .st-key-market_dashboard [class*="st-key-card_"],
    .st-key-market_dashboard [data-testid="stExpander"] details {{
        background:{surface}; border:1px solid {border}; border-radius:24px;
        box-shadow:{shadow}; backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
    }}
    .st-key-market_dashboard .overview-metrics > .overview-metric {{ padding:16px; position:relative;
        display:block; color:inherit !important; text-decoration:none; min-width:0;
        transition:transform .16s ease, border-color .16s ease, box-shadow .16s ease; }}
    .st-key-market_dashboard .overview-metrics > .overview-metric:hover,
    .st-key-market_dashboard .overview-metrics > .overview-metric:focus-visible {{
        transform:translateY(-2px); border-color:{rgba(palette["accent"], .72)};
        box-shadow:0 18px 48px rgba(0,0,0,.28), 0 0 0 2px {rgba(palette["accent"], .18)}; }}
    .st-key-market_dashboard .overview-metrics > .overview-metric:nth-child(even) {{
        background:{raised_surface};
        border-top-color:{rgba(palette["accent"], .45)};
    }}
    .metric-arrow {{ margin-left:auto; color:{palette["accent"]}; font-size:.9rem; }}
    .metric-value-row {{ display:flex; align-items:flex-end; justify-content:space-between;
        gap:12px; margin-top:5px; }}
    .metric-mini-chart {{ width:72px; height:34px; flex:0 0 72px; opacity:.78; }}
    .st-key-market_dashboard .overview-metrics .kpi-value {{
        font-size:clamp(1.4rem, 2.2vw, 2.1rem); font-variant-numeric:tabular-nums; letter-spacing:-.04em;
    }}
    .market-metric-heading {{ display:flex; align-items:center; gap:10px; min-height:32px; }}
    .market-metric-heading .component-symbol {{ width:24px; height:26px; margin:0; }}
    .market-metric-note {{ font-size:.73rem; margin-top:8px; opacity:.78; }}
    .st-key-market_dashboard [class*="st-key-card_"] {{ padding:18px 18px 12px; }}
    .st-key-market_dashboard [class*="st-key-card_"]:has(.component-symbol[data-kind="chart"]) {{
        border-radius:24px; border-bottom:1px solid {border};
    }}
    .st-key-market_dashboard .card-title {{ font-size:1.05rem; line-height:1.5; }}
    .st-key-market_dashboard .card-title .component-symbol {{ width:28px; height:30px; }}
    .st-key-market_dashboard [data-testid="stExpander"] summary {{ background:transparent; }}
    .st-key-market_dashboard [data-testid="stExpanderDetails"] {{ padding-top:4px; }}
    .stApp:has(.st-key-market_dashboard) .project-navigation {{
        background:{surface}; border:1px solid {border}; padding:12px 18px;
        border-radius:16px; backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
    }}
    @media (max-width:1000px) {{
        .st-key-market_dashboard [data-testid="stHorizontalBlock"]:has([class*="st-key-card_home_"]) {{
            flex-direction:column;
        }}
        .st-key-market_dashboard [data-testid="stColumn"]:has([class*="st-key-card_home_"]) {{
            width:100%; flex:1 1 100%;
        }}
    }}
    @media (max-width:640px) {{
        .stApp:has(.st-key-market_dashboard) {{ background-attachment:scroll; background-position:65% top; }}
        .st-key-market_intro {{ padding:8px 0 14px; }}
        .st-key-market_dashboard .overview-metrics {{ gap:10px; }}
        .st-key-market_dashboard .overview-metrics > .overview-metric {{ padding:15px; border-radius:18px; }}
        .market-metric-heading {{ align-items:flex-start; }}
        .market-metric-heading .kpi-label {{ font-size:.77rem; }}
        .st-key-market_dashboard [class*="st-key-card_"] {{ padding:18px 14px; }}
        .st-key-market_dashboard [data-testid="stHorizontalBlock"]:has([data-testid="stSlider"]) {{
            flex-direction:column;
        }}
        .st-key-market_dashboard [data-testid="stColumn"]:has([data-testid="stSlider"], [data-testid="stButtonGroup"]) {{
            width:100%; flex:1 1 100%;
        }}
    }}
    """
