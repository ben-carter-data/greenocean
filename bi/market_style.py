"""A compact report grid: a summary band above three aligned analytical panels."""
from bi import charts


def build_css(mode):
    """Keep the reference layout independent from its business-specific chart choices."""
    p = charts.get_palette(mode)
    return f"""
    .stApp:has(.st-key-market_dashboard) {{ background:{p['background']}; }}
    .stApp:has(.st-key-market_dashboard) [data-testid="stMainBlockContainer"] {{
        max-width:1680px; padding:16px clamp(18px,2.2vw,40px) 24px; }}
    .st-key-market_dashboard, .st-key-report_page {{ gap:16px; }}
    .st-key-market_dashboard [class*="st-key-card_"] {{
        background:{p['card']}; border:1px solid {p['card_border']};
        border-radius:4px; box-shadow:none; padding:16px; gap:12px; min-width:0; }}
    .st-key-market_dashboard .card-title {{ font-size:.95rem; line-height:1.45; gap:10px;
        align-items:flex-start; flex-wrap:wrap; }}
    .st-key-market_dashboard .card-title-text {{ white-space:normal; overflow:visible;
        flex:1 1 130px; }}
    .st-key-market_dashboard .card-title .component-symbol {{ display:none; }}
    .st-key-market_dashboard .card-title .kpi-link {{ display:none; }}
    .st-key-market_dashboard [data-testid="stCaptionContainer"] {{ font-size:.76rem; line-height:1.55; }}
    .st-key-dashboard_summary_band {{margin-bottom:18px;}}
    .st-key-dashboard_summary_band .kpi-strip {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
        margin:0; border:1px solid {p['card_border']}; background:{p['card']}; min-height:268px; }}
    .st-key-dashboard_summary_band .kpi-strip-item {{ justify-content:flex-start; padding:18px; gap:12px; }}
    .st-key-dashboard_summary_band .kpi-strip-value {{ font-size:clamp(1.45rem,2.5vw,2.1rem); }}
    .st-key-dashboard_summary_band .kpi-strip-good {{ font-size:1.2rem; white-space:normal; }}
    .st-key-dashboard_summary_band .kpi-strip-label {{ font-size:.88rem; line-height:1.3; white-space:normal; }}
    .st-key-dashboard_summary_band .kpi-strip-note {{ font-size:.76rem; line-height:1.35; white-space:normal; }}
    .st-key-dashboard_summary_band .st-key-card_usable_data {{ min-height:268px; }}
    .st-key-dashboard_summary_band [data-testid="stMarkdownContainer"]:has(> .ring-legend) {{margin-bottom:0;}}
    .metric-symbol {{font-family:"Material Symbols Rounded"; font-size:22px; font-weight:400; color:{p['accent']};}}
    .st-key-dashboard_summary_band .kpi-strip-label {{display:flex; gap:8px; align-items:center; min-height:46px;}}
    .metric-explanation {{font-size:.78rem; line-height:1.5; color:{p['text']};}}
    .metric-action {{font-size:.78rem; margin-top:auto; padding-top:6px; color:{p['accent']};}}
    .quality-summary {{display:flex; flex-direction:column; gap:12px; font-size:.8rem; line-height:1.5;}}
    .quality-value {{font-size:1.9rem; line-height:1.15; color:{p['accent']};}}
    .quality-meter {{height:8px; width:100%; border-radius:5px; background:{p['grid']}; overflow:hidden;}}
    .quality-meter span {{display:block; height:100%; border-radius:5px;}}
    .quality-counts {{font-size:.76rem; line-height:1.5;}}
    .st-key-dashboard_summary_band .ring-legend {{ font-size:.72rem; }}
    .st-key-dashboard_summary_band .ring-note {{ margin:4px 0 0; font-size:.72rem; }}
    .st-key-dashboard_summary_band ul.ring-legend li {{ font-size:.72rem; gap:5px; white-space:normal; }}
    .st-key-dashboard_analysis_grid [class*="st-key-card_"] {{ min-height:300px; }}
    .st-key-dashboard_analysis_grid .st-key-ranking_caption {{ flex-wrap:wrap !important; gap:4px; }}
    .st-key-dashboard_analysis_grid .st-key-ranking_order {{ margin-left:auto; }}
    .st-key-market_dashboard [data-testid="stExpander"] details {{
        border-radius:4px; border:1px solid {p['card_border']}; background:{p['card']}; }}
    .st-key-market_dashboard [data-testid="stExpander"] summary p {{ font-size:.76rem; }}
    .st-key-market_dashboard [data-testid="stMarkdownContainer"]:has(> .filter-scope) {{margin-bottom:0;}}
    .st-key-market_dashboard .filter-scope {{ margin:0; font-size:.72rem; }}
    .st-key-market_dashboard .report-footer {{ font-size:.75rem; gap:4px 12px; }}
    @media(max-width:1100px) {{
        .st-key-dashboard_analysis_grid > [data-testid="stHorizontalBlock"],
        .st-key-dashboard_analysis_grid [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] > div > [class*="st-key-card_"]) {{
            flex-wrap:wrap; }}
        .st-key-dashboard_analysis_grid [data-testid="stColumn"] {{ min-width:min(100%,310px); }}
    }}
    @media(max-width:700px) {{
        .st-key-dashboard_summary_band .kpi-strip {{ grid-template-columns:1fr; min-height:0; }}
        .st-key-dashboard_summary_band .kpi-strip-item {{ padding:14px; border-left:0;
            border-bottom:1px solid {p['card_border']}; }}
        .st-key-dashboard_summary_band .kpi-strip-item:last-child {{ border-bottom:0; }}
        .st-key-dashboard_analysis_grid [class*="st-key-card_"] {{ min-height:0; }}
        .st-key-dashboard_analysis_grid [data-testid="stColumn"] {{ min-width:100%; }}
    }}
    """
