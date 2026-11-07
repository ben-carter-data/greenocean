"""The thin header bar of the panel's pages (D-267), the one the Resumen has since D-264.

D-398: the bar only places the reader: «Volver», «Section › Page» (the page's description on hover) and, at the end,
the time of the data with a green dot, red when the load failed. Nothing else: no links to other pages (they live in
the menu), no figures and no buttons. What a page says (its question, its figures as chips, what it measures) and what
it does (a button, a switch) go in a row of the content right under the bar, which wraps instead of overlapping.

Pure functions: no Streamlit. bi/dashboard.py lays the Streamlit elements around this HTML.
"""

import html

from bi import charts, live_mark


# region The thin header bar of the panel's pages
def esc(value):
    return html.escape(str(value), quote=True)


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    live = live_mark.build_css(dark)  # D-510
    ink, muted, card, border = palette["strong_text"], palette["reference"], palette["card"], palette["card_border"]
    soft = palette["grid"] if dark else "#f1f5f9"
    rise, fall = ("#ff8a96", "#83baff") if dark else ("#c81e3a", "#1d5fbf")
    return f"""<style>
/* D-513: the bar of a page with the measure of Apple's: 36 px, thin letters, the page's name only a step heavier. */
.stApp .st-key-page_bar {{ background:{card}; border:1px solid {border}; border-radius:10px; padding:2px 12px 2px 4px !important;
  margin:2px 0 6px !important; gap:4px 8px !important; flex-wrap:nowrap !important; align-items:center !important; min-height:36px; }}
.stApp .st-key-page_bar > * {{ flex:0 0 auto; min-width:0; width:auto !important; }}
/* D-398: the path takes the room left and is cut with «…» before anything can overlap; the time never moves. */
.stApp .st-key-page_bar > :has(.page-bar-main) {{ flex:1 1 0 !important; min-width:0 !important; }}
.stApp .st-key-page_bar [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
.stApp .st-key-page_bar .st-key-return_to_previous button {{ border:0 !important; background:transparent !important;
  box-shadow:none !important; min-height:28px; width:28px; padding:0 !important; color:{ink}; }}
.stApp .st-key-page_bar .st-key-return_to_previous button:hover {{ background:{soft} !important; }}
.stApp .st-key-page_bar .st-key-return_to_previous button [data-testid="stMarkdownContainer"] {{ position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap; }}
.stApp .st-key-page_bar p {{ margin:0 !important; }}
.page-bar-main {{ display:flex; align-items:center; min-width:0; white-space:nowrap; font-size:12.5px; color:{ink}; }}
.page-bar-path {{ min-width:0; overflow:hidden; text-overflow:ellipsis; color:{muted}; font-size:12.5px; font-weight:400;
  letter-spacing:-.005em; cursor:default; }}
.page-bar-path b {{ color:{ink}; font-weight:500; }}
.page-bar-updated {{ display:inline-flex; align-items:center; gap:6px; white-space:nowrap; font-size:11.5px; color:{muted}; }}
.page-bar-updated i {{ width:7px; height:7px; border-radius:50%; background:#529e57; flex:none; }}
.page-bar-updated i.failed {{ background:#e62035; }}
{live}
/* The row of the content under the bar: the page's question, its chips, its terms and its controls. It wraps. */
.stApp .st-key-page_info {{ gap:4px 8px !important; flex-wrap:wrap !important; align-items:center !important;
  margin:-2px 0 6px !important; }}
.stApp .st-key-page_info > * {{ min-width:0; width:auto !important; }}
.stApp .st-key-page_info > :has(.page-info) {{ flex:1 1 auto !important; }}
.stApp .st-key-page_info [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
.stApp .st-key-page_info p {{ margin:0 !important; }}
.stApp .st-key-page_info button {{ min-height:26px !important; padding:1px 10px !important; }}
.stApp .st-key-page_info button p {{ font-size:12px !important; }}
.page-info {{ display:flex; flex-wrap:wrap; align-items:center; gap:4px 6px; min-width:0; }}
.page-info-title {{ margin:0 6px 0 2px; font-size:13px; font-weight:500; line-height:1.3; letter-spacing:-.005em; color:{ink}; cursor:default; }}
/* D-513: a chip of 22 px, its figure a step heavier than its words, nothing bold. */
.page-chip {{ flex:none; display:inline-flex; align-items:baseline; gap:5px; padding:2px 8px; border-radius:7px; background:{soft};
  color:{ink}; font-size:12px; line-height:1.4; font-variant-numeric:tabular-nums; cursor:default; }}
.page-chip b {{ font-weight:500; }}
.page-chip small {{ font-size:11px; color:color-mix(in srgb, {muted} 45%, {ink}); }}
.page-chip em {{ font-style:normal; font-size:9.5px; font-weight:500; letter-spacing:.06em; text-transform:uppercase; color:color-mix(in srgb, {muted} 45%, {ink}); }}
.page-chip b.rise {{ color:{rise}; }} .page-chip b.fall {{ color:{fall}; }}
.page-bar-terms {{ display:grid; grid-template-columns:auto auto; gap:0 6px; align-items:baseline; padding-left:10px;
  border-left:1px solid {border}; font-size:11px; line-height:1.3; white-space:nowrap; color:{ink}; cursor:default; }}
.page-bar-terms em {{ font-style:normal; font-size:9.5px; font-weight:500; letter-spacing:.08em; text-transform:uppercase; color:{muted}; }}
</style>"""


def build_bar_html(path, description=""):
    """«Section › Page», the page's name in bold and as the heading (D-398): the bar says only where the reader is.
    The description of the page shows on hover."""
    section, _, page = path.rpartition(" › ")
    where = (f"{esc(section)} › " if section else "") + f'<b role="heading" aria-level="1">{esc(page)}</b>'
    return (
        f'<div class="page-bar-main" aria-label="Página actual: {esc(path)}">'
        f'<span class="page-bar-path" title="{esc(description)}">{where}</span></div>'
    )


def build_info_html(title, description, chips=(), show_title=True, live=None):
    """The row of the content under the bar (D-398): the page's question, when it is not just its name, and its figures
    as chips: (value as escaped HTML, what it counts in words, shown on hover). D-510: «live», what the figures were
    read from, adds the mark that beats beside them."""
    heading = (
        f'<span class="page-info-title" role="heading" aria-level="2" title="{esc(description)}">{esc(title)}</span>'
        if show_title
        else ""
    )
    return (
        '<div class="page-info">'
        + heading
        + "".join(f'<span class="page-chip" title="{esc(note)}">{value}</span>' for value, note in chips)
        + (live_mark.build_html(live) if live else "")
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


def build_updated_html(updated, loaded):
    """The time of the latest load, at the end of the bar: a green dot, or red when it failed."""
    state = "Carga correcta" if loaded else "Última carga con falla"
    return (
        f'<span class="page-bar-updated" title="Datos al {esc(updated)} · {state}">'
        f'<i class="{"loaded" if loaded else "failed"}"></i>{esc(updated)}</span>'
    )


# endregion
