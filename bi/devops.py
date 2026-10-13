"""Compact DevOps lifecycle, with locally bundled logos of the tools actually used."""
import html
from bi import architecture, charts
from bi.brand_icons import logo, logo_body


STAGES = [
    ("Código", "Git · GitHub", "Versionado y revisión", ("git", "github"), "ingestion", 290, 65),
    ("Pruebas", "pytest", "Pruebas en cada push", ("pytest",), "quality", 100, 245),
    ("Carga", "Python · SQLite", "ETL y base validada", ("python", "sqlite"), "gold", 290, 430),
    ("Publicación", "Streamlit", "Panel desde main", ("streamlit",), "consumption", 710, 65),
    ("Operación", "GitHub Actions", "Job semanal y caché", ("github",), "processing", 900, 245),
    ("Monitoreo", "GitHub Issues", "Informe, alertas y logs", ("github",), "orchestration", 710, 430),
]
SEGMENTS = [
    ("M500 245 C420 120 300 110 240 170", 345, 167),
    ("M240 170 C155 250 210 345 300 345", 225, 267),
    ("M300 345 C390 345 440 300 500 245", 360, 328),
    ("M500 245 C580 120 700 110 760 170", 655, 167),
    ("M760 170 C845 250 790 345 700 345", 775, 267),
    ("M700 345 C610 345 560 300 500 245", 640, 328),
]


def build_svg(states, mode, animate_flow=False):
    palette = charts.get_palette(mode)
    pieces = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 490" '
              'role="img" aria-label="Ciclo DevOps del proyecto: código, pruebas, carga, '
              f'publicación, operación y monitoreo" font-family="{charts.CHART_FONT}">',
              '<style>@media(prefers-reduced-motion:reduce){.devops-flow{display:none}}</style>']
    for stage, (path, tx, ty) in zip(STAGES, SEGMENTS):
        color = architecture.LAYER_COLORS[stage[4]]
        pieces.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-opacity=".60" '
                      'stroke-width="22" stroke-linecap="round"/>')
        pieces.append(f'<text x="{tx}" y="{ty}" text-anchor="middle" font-size="14" '
                      f'font-weight="600" fill="{palette["strong_text"]}">{stage[0]}</text>')
    if animate_flow:
        cycle = ("M500 245 C420 120 300 110 240 170 C155 250 210 345 300 345 "
                 "C390 345 440 300 500 245 C580 120 700 110 760 170 "
                 "C845 250 790 345 700 345 C610 345 560 300 500 245")
        pieces.append(f'<circle class="devops-flow" r="4" fill="{palette["strong_text"]}">'
                      f'<animateMotion dur="14s" repeatCount="indefinite" path="{cycle}"/></circle>')
    for index, (phase, title, note, slugs, layer, x, y) in enumerate(STAGES):
        color = architecture.LAYER_COLORS[layer]
        pieces.append(f'<g><title>{html.escape(phase + ": " + title + ". " + note)}</title>')
        for offset, slug in enumerate(slugs):
            pieces.append(logo(slug, x - len(slugs) * 18 + offset * 36, y - 29, color))
        pieces.append(f'<text x="{x}" y="{y + 17}" text-anchor="middle" font-size="14" '
                      f'font-weight="600" fill="{palette["strong_text"]}">{html.escape(title)}</text>'
                      f'<text x="{x}" y="{y + 37}" text-anchor="middle" font-size="12" '
                      f'fill="{palette["text"]}">{html.escape(note)}</text>')
        state = {3: states.get("panel"), 4: states.get("workflow"), 5: states.get("report")}.get(index)
        if architecture.has_real_state(state):
            pieces.append(f'<circle cx="{x + 46}" cy="{y - 17}" r="4" '
                          f'fill="{architecture.STATE_COLORS[state]}">'
                          f'<title>{architecture.STATE_LABELS[state]}</title></circle>')
        pieces.append('</g>')
    pieces.append('</svg>')
    return "".join(pieces)


def build_html(states, mode, animate_flow=False):
    """Desktop diagram and exclusive mobile list, with the same six stages."""
    rows = []
    for phase, title, note, slugs, layer, _, _ in STAGES:
        color = architecture.LAYER_COLORS[layer]
        icons = ''.join(f'<svg viewBox="0 0 24 24" aria-hidden="true" fill="{color}">'
                        f'{logo_body(slug)}</svg>' for slug in slugs)
        rows.append(f'<li><div class="devops-logos">{icons}</div><div>'
                    f'<strong>{phase} · {html.escape(title)}</strong>'
                    f'<span>{html.escape(note)}</span></div></li>')
    return ('<div class="devops-cycle">' + build_svg(states, mode, animate_flow) + '</div>'
            '<ol class="devops-cycle-mobile">' + ''.join(rows) + '</ol>')
