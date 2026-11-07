"""The thin header bar of the panel's pages (D-267), the one the Resumen has since D-264.

D-398: the bar only places the reader: «Volver», «Section › Page» (the page's description on hover) and, at the end,
the time of the data with a green dot, red when the load failed. Nothing else: no links to other pages (they live in
the menu), no figures and no buttons. What a page says (its question, its figures as chips, what it measures) and what
it does (a button, a switch) go in a row of the content right under the bar, which wraps instead of overlapping.

Pure functions: no Streamlit. bi/dashboard.py lays the Streamlit elements around this HTML.
"""

import html

from bi import charts, live_mark, static_files


# region The thin header bar of the panel's pages
def esc(value):
    return html.escape(str(value), quote=True)


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    live = live_mark.build_css(dark)  # D-510
    ink, muted, card, border = palette["strong_text"], palette["reference"], palette["card"], palette["card_border"]
    soft = palette["grid"] if dark else "#f1f5f9"
    rise, fall = ("#ff8a96", "#83baff") if dark else ("#c81e3a", "#1d5fbf")
    return static_files.style(
        "page_bar.css",
        {
            'var(--go-card)': card,
            'var(--go-border)': border,
            'var(--go-ink)': ink,
            'var(--go-soft)': soft,
            'var(--go-muted)': muted,
            'var(--go-live)': live,
            'var(--go-rise)': rise,
            'var(--go-fall)': fall,
        },
    )


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
