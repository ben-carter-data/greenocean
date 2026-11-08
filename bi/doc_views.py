"""The logos the project diagrams share (D-205, D-280: flat brand logos on a transparent background) and the six
captures of the panel the documents show (D-299). The context and container views of the SAD live in doc_figures (D-289).

build_mockups_html returns one HTML document for st.iframe.
"""

import base64
import html
from pathlib import Path

from bi import brand_icons, charts, database_map, i18n, static_files

# region Constants
# Disc colors (light top, dark bottom, glyph) of the brands the actors view needs, as in
# database_map.BRANDS.
DISCS = dict(
    database_map.BRANDS,
    git=("#ff9b7d", "#d6402a", "#ffffff"),
    streamlit=("#ff8f98", "#e0303f", "#ffffff"),
    pytest=("#7fc4ff", "#1f6fb5", "#ffffff"),
)
# D-382: the three views of the panel are three people: «visitor» is the Usuario, «professional» the Profesional.
PERSON_DISCS = {
    "visitor": ("#7ee2b0", "#14855a"),
    "professional": ("#8ec5ff", "#2563eb"),
    "author": ("#ffcf70", "#c98500"),
}
# D-280: brands whose own color is black or white take the text color of the theme, as GitHub asks for its mark.
INK_BRANDS = {"github"}
# (file, title, theme, view). D-392: the Dashboard twice, as the Usuario and as the Profesional see it.
MOCKUPS = [
    ("m1-dashboard-corporativo.jpg", "M-1 · Semanal", "Corporativo", "Usuario"),
    ("m2-resumen-vantablack.jpg", "M-2 · Semanal", "Vantablack", "Profesional"),
    ("m3-analisis-darkgrey.jpg", "M-3 · Análisis", "Dark Grey", "Profesional"),  # D-456
    ("m4-pipeline-bluelight.jpg", "M-4 · Pipeline y linaje", "Blue Light", "Profesional"),
    ("m5-sql-corporativo.jpg", "M-5 · Consultas SQL", "Corporativo", "Profesional"),
    ("m6-calidad-vantablack.jpg", "M-6 · Controles de datos", "Vantablack", "Profesional"),
]
# endregion

# region Variables
MOCKUP_DIR = Path(__file__).resolve().parent.parent / "docs" / "img"
# endregion


# region Logos
def esc(value):
    return html.escape(str(value))


def disc_logo(kind, name):
    """A brand, a person or a source as a 3D mark: lit disc, gloss and drop shadow (the panel views)."""
    if kind == "brand":
        if name in database_map.BRANDS:
            return database_map.brand_logo(name, "-actors")
        return _disc(name, *DISCS[name], brand_icons.logo_body(name))
    if kind == "source":
        return database_map.source_logo(name)
    top, bottom = PERSON_DISCS[name]
    person = '<circle cx="18" cy="12" r="6"/><path d="M6 31c1-8 6-12 12-12s11 4 12 12z"/>'
    return _disc(name, top, bottom, "#ffffff", person, scale=1.0)


def _disc(name, top, bottom, glyph, body, scale=1.58):
    gradient = f"disc-{name}-actors"
    offset = 17 if scale > 1.2 else 18
    return (
        f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>'
        f'<radialGradient id="{gradient}" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="{top}"/>'
        f'<stop offset="1" stop-color="{bottom}"/></radialGradient></defs>'
        f'<circle cx="36" cy="36" r="31" fill="url(#{gradient})"/>'
        f'<ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>'
        f'<g fill="{glyph}" transform="translate({offset} {offset}) scale({scale})">{body}</g></svg>'
    )


def flat_logo(kind, name):
    """A brand, a person or a source as its own mark in its own color, with no disc or background (D-280)."""
    if kind == "source":
        return database_map.source_logo(name)
    if kind == "brand":
        color = "currentColor" if name in INK_BRANDS else DISCS[name][1]
        return (
            f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true">'
            f'<g fill="{color}" transform="translate(9 9) scale(2.25)">{brand_icons.logo_body(name)}</g></svg>'
        )
    person = '<circle cx="18" cy="12" r="6"/><path d="M6 31c1-8 6-12 12-12s11 4 12 12z"/>'
    return (
        f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true">'
        f'<g fill="{PERSON_DISCS[name][1]}" transform="translate(9 9) scale(1.5)">{person}</g></svg>'
    )


# endregion


# region Text helpers
# D-455: the use cases of the PRD left with its invented profiles; the PRD shows the three views of the app.
def wrap(text, width):
    """The lines of a text no wider than width; translated whole first (D-284), so no line is a fragment to look up."""
    lines, line = [], ""
    for word in i18n.translate_text(text).split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


# endregion


# region The captures of the documents
def mockup_detail(theme, view):
    """«tema Corporativo · vista Usuario», or its English: the theme keeps its name, the view takes the panel's word."""
    if i18n.is_english():
        return f"{theme} theme · {i18n.lookup(view) or view} view"
    return f"tema {theme} · vista {view}"


def build_mockups_html(mode):
    """Six captures of the panel (D-299), every theme at least once, in a computer frame, two per row."""
    palette = charts.get_palette(mode)
    figures = []
    for file_name, title, theme, view in MOCKUPS:
        detail = mockup_detail(theme, view)
        # D-284: the English document shows the English captures, taken from the same pages.
        folder = MOCKUP_DIR / "en" if i18n.is_english() and (MOCKUP_DIR / "en" / file_name).exists() else MOCKUP_DIR
        data = base64.b64encode((folder / file_name).read_bytes()).decode()
        image = f'<img src="data:image/jpeg;base64,{data}" alt="{esc(title)}">'
        frame = f'<div class="screen">{image}</div><div class="base"></div>'
        figures.append(f'<figure>{frame}<figcaption><b>{esc(title)}</b> · {esc(detail)}</figcaption></figure>')
    css = static_files.style(
        "mockups.css",
        {
            'var(--go-text)': palette['text'],
            'var(--go-reference)': palette['reference'],
            'var(--go-strong-text)': palette['strong_text'],
        },
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        + css
        + '</head><body><div class="grid">'
        + "".join(figures)
        + "</div></body></html>"
    )


# endregion


# region The views of each marker
def views():
    """The document views by marker, with the height of their frame in the page. D-474: the context and container views
    are drawn by doc_figures (D-289); only the captures stay here."""
    return {
        "mockups": (build_mockups_html, 1080),
    }


# endregion
