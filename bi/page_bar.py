"""The thin header bar of the panel's main pages (D-267), the one the Resumen has since D-264.

One rounded bar replaces the path row with «Volver», the page title, its subtitle and any
figure strip: Volver, «Section › Page», the title (cut with «…» when space runs out, its
explanation on hover), the page's key figures as chips (each says in full what it counts on
hover) and, at the end, the time of the latest load with a green dot, red when it failed.
The page below starts about 60 px higher, so it fits the window without scrolling.

Pure functions: no Streamlit. bi/dashboard.py lays the Streamlit buttons around this HTML.
"""

import html

from bi import buttons, charts


def esc(value):
    return html.escape(str(value), quote=True)


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, muted, card, border = palette["strong_text"], palette["reference"], palette["card"], palette["card_border"]
    soft = palette["grid"] if dark else "#f1f5f9"
    rise, fall = ("#ff8a96", "#83baff") if dark else ("#c81e3a", "#1d5fbf")
    return f"""<style>
.stApp .st-key-page_bar {{ background:{card}; border:1px solid {border}; border-radius:14px; padding:5px 14px 5px 6px !important;
  margin:4px 0 10px !important; gap:4px 10px !important; flex-wrap:wrap !important; align-items:center !important; min-height:44px; }}
.stApp .st-key-page_bar > * {{ flex:0 0 auto; min-width:0; width:auto !important; }}
/* The title and the chips keep at least 240 px: when the buttons, the terms or the time do not fit beside them,
   those go to a second line (pushed to the right) instead of covering the title. */
.stApp .st-key-page_bar > :has(.page-bar-main) {{ flex:1 1 0 !important; min-width:min(100%, 240px) !important; }}
.stApp .st-key-page_bar > :last-child {{ margin-left:auto; }}
.stApp .st-key-page_bar [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
.stApp .st-key-page_bar .st-key-return_to_previous button {{ border:0 !important; background:transparent !important;
  box-shadow:none !important; min-height:32px; width:32px; padding:0 !important; color:{ink}; }}
.stApp .st-key-page_bar .st-key-return_to_previous button:hover {{ background:{soft} !important; }}
.stApp .st-key-page_bar .st-key-return_to_previous button [data-testid="stMarkdownContainer"] {{ display:none; }}
.page-bar-main {{ display:flex; align-items:center; gap:8px; min-width:0; white-space:nowrap; font-size:13px; color:{ink}; }}
.page-bar-path {{ flex:none; color:{muted}; font-size:13.5px; padding-right:10px; border-right:1px solid {border}; }}
.page-bar-path:not(:has(b)) {{ padding-right:0; border-right:0; }}
.page-bar-title + .page-chip {{ margin-left:auto; }}
.page-bar-path b {{ color:{ink}; font-weight:600; }}
.page-bar-title {{ flex:0 1 auto; min-width:9em; margin:0 4px 0 2px; font-size:14.5px; font-weight:600; line-height:1.3;
  letter-spacing:-.01em; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; cursor:default; }}
.page-chip {{ flex:none; display:inline-flex; align-items:baseline; gap:6px; padding:3px 9px; border-radius:8px; background:{soft};
  color:{ink}; font-size:13.5px; line-height:1.35; font-variant-numeric:tabular-nums; cursor:default; }}
.page-chip b {{ font-weight:600; }}
.page-chip small {{ font-size:12px; color:{muted}; }}
.page-chip em {{ font-style:normal; font-size:10.5px; font-weight:500; letter-spacing:.06em; text-transform:uppercase; color:{muted}; }}
.page-chip b.rise {{ color:{rise}; }} .page-chip b.fall {{ color:{fall}; }}
.stApp .st-key-page_bar p {{ margin:0 !important; }}
.stApp .st-key-page_bar button {{ min-height:30px !important; padding:2px 12px !important; }}
.page-bar-updated {{ display:inline-flex; align-items:center; gap:6px; white-space:nowrap; font-size:12.5px; color:{muted}; }}
.page-bar-updated i {{ width:7px; height:7px; border-radius:50%; background:#529e57; flex:none; }}
.page-bar-updated i.failed {{ background:#e62035; }}
.page-bar-terms {{ display:grid; grid-template-columns:auto auto; gap:0 6px; align-items:baseline; padding-left:10px;
  border-left:1px solid {border}; font-size:11.5px; line-height:1.3; white-space:nowrap; color:{ink}; cursor:default; }}
.page-bar-terms em {{ font-style:normal; font-size:10px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{muted}; }}
/* Narrow windows (a tablet, a laptop with the menu open): the menu already shows where the page is, so the path
   leaves (it stays in the bar's aria-label); the title keeps its line and the chips that do not fit go to a second one. */
@media (max-width:1320px) {{ .page-bar-path {{ display:none; }}
  .page-bar-main {{ flex-wrap:wrap; row-gap:4px; }} .page-bar-title {{ flex:1 1 auto; }}
  .page-bar-title + .page-chip {{ margin-left:0; }} }}
</style>"""


def build_bar_html(path, title, description, chips=()):
    """Path, title and chips: (value as escaped HTML, what it counts in words, shown on hover). The title is a heading by role: Streamlit wraps a markdown <h1> in a block of its own,
    which would not shrink."""
    section, _, page = path.rpartition(" › ")
    # When the title is the page's own name, the path keeps only its section, so the name is not said twice.
    if page == title:
        route = f'<span class="page-bar-path">{esc(section)} ›</span>' if section else ""
    else:
        route = (
            f'<span class="page-bar-path">{esc(section)} › <b>{esc(page)}</b></span>'
            if section
            else f'<span class="page-bar-path"><b>{esc(page)}</b></span>'
        )
    return (
        f'<div class="page-bar-main" aria-label="Página actual: {esc(path)}">'
        + route
        + f'<span class="page-bar-title" role="heading" aria-level="1" title="{esc(description)}">{esc(title)}</span>'
        + "".join(f'<span class="page-chip" title="{esc(note)}">{value}</span>' for value, note in chips)
        + "</div>"
    )


def build_terms_html(terms):
    """«KPI · …» and «Métrica · …» in the right corner: what the page measures, with its definition on hover."""
    return (
        '<div class="page-bar-terms">'
        + "".join(
            f'<em>{esc(label)}</em><span title="{esc(definition)}">{esc(name)}</span>'
            for label, name, definition in terms
        )
        + "</div>"
    )


def build_link_html(text, address, note):
    """A link to another page, inside the bar: what it opens says itself on hover."""
    return buttons.build_link_html(text, address, icon="arrow", size="compact", note=note)


def build_updated_html(updated, loaded):
    """The time of the latest load, at the end of the bar: a green dot, or red when it failed."""
    state = "Carga correcta" if loaded else "Última carga con falla"
    return (
        f'<span class="page-bar-updated" title="Datos al {esc(updated)} · {state}">'
        f'<i class="{"loaded" if loaded else "failed"}"></i>{esc(updated)}</span>'
    )
