"""«Controles de auditoría» (D-196, D-220): the checks that make the published data trustworthy.

Eleven controls in four groups (sources, run and dbt, warehouse, results), each a small icon
with its status: green checked here, amber cannot be checked on this server or has a remark.
D-220 retired the single-price trace that came with them: it repeated the pipeline and asked
the reader to pick a product without saying why. The controls are global, so they need no
filter, and they now close the «Calidad» view. Pure functions, no Streamlit.
"""
import html

from bi import charts, quality_view

KINDS = {"ok": "ok", "pending": "pending", "fail": "fail"}


def build_controls_css(palette):
    """The CSS of the control icons, their status dot and hover tips."""
    dark = palette["base"] == charts.BASE_DARK
    muted, card, border, text = palette["reference"], palette["card"], palette["card_border"], palette["text"]
    shade = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    tip_shadow = "rgba(0,0,0,.5)" if dark else "rgba(0,0,0,.18)"
    colors = {"ok": "#22b35a", "pending": "#d97706", "fail": "#d03b3b"}
    states = "".join(f".ctl.s-{key}{{--c:{color};}}" for key, color in colors.items())
    return (states + f"""
.ctl .tip {{ position:absolute; z-index:60; width:290px; padding:12px 14px; border-radius:14px; text-align:left; background:{card};
  border:1px solid {border}; box-shadow:0 18px 40px {tip_shadow}; color:{text}; font-size:12.5px; line-height:1.45; display:none;
  pointer-events:none; transform:translateX(-50%); white-space:normal; }}
.ctl .tip i {{ display:block; margin:8px 0 2px; font:500 10px/1 sans-serif; font-style:normal; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.ctl .tip i:first-child {{ margin-top:0; }}
.controls {{ display:flex; gap:6px 22px; flex-wrap:wrap; justify-content:center; padding-top:8px; }}
.group h4 {{ margin:0 0 3px; text-align:center; font-size:10px; font-weight:500; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.group .row {{ display:flex; gap:10px; justify-content:center; }}
.ctl {{ position:relative; width:74px; text-align:center; outline:none; }}
.ctl .qa-icon {{ width:34px; height:34px; filter:drop-shadow(0 5px 5px {shade}); }}
.ctl .dot {{ position:absolute; top:0; left:calc(50% + 8px); width:10px; height:10px; border-radius:50%; background:var(--c);
  box-shadow:0 0 0 2px {palette['background']}; }}
.ctl small {{ display:block; font-size:10.5px; line-height:1.2; color:{muted}; margin-top:1px; display:-webkit-box; -webkit-line-clamp:2;
  -webkit-box-orient:vertical; overflow:hidden; }}
.ctl .tip {{ top:auto; bottom:calc(100% + 4px); left:50%; }}
.ctl:hover .tip, .ctl:focus .tip {{ display:block; }}
.ctl:hover, .ctl:focus {{ z-index:50; }}
""")


def build_controls_html(columns):
    """The controls as small icons with their status: [(group, [(icon, title, status, detail, why)])]."""
    groups = []
    for step, cards in columns:
        items = "".join(
            f'<div class="ctl s-{KINDS[quality_view.classify(status)]}" tabindex="0">{quality_view.build_icon_svg(icon)}'
            f'<span class="dot"></span><small>{html.escape(title)}</small><span class="tip" role="tooltip"><i>{html.escape(status)}</i>'
            f'{html.escape(detail)}<i>Qué comprueba</i>{html.escape(why)}</span></div>' for icon, title, status, detail, why in cards)
        groups.append(f'<div class="group"><h4>{html.escape(step)}</h4><div class="row">{items}</div></div>')
    return '<div class="controls">' + "".join(groups) + "</div>"
