"""Diagrams that only the documents need (PRD and SAD), drawn in the panel's own
visual language: the layer colors of architecture.LAYER_COLORS, the local brand
logos of brand_icons, the theme palette of charts.get_palette and a <title>
tooltip on every box.

The panel pages already draw the live journey, the dbt lineage, the platform
(DevOps) and the star model; a document reuses those only when one of them is
exactly the view it needs (the SAD's deployment view and data model). The views
here are the ones a PRD or a SAD normally has and the panel does not:

- actores: who uses GreenOcean, for what, and the external systems it relies on (PRD).
- pantalla: low-fidelity wireframe of the Resumen semanal, each zone with its
  functional requirements (PRD).
- contexto: C4 level 1, the system and its neighbours (SAD).
- contenedores: C4 level 2, every container with its technology (SAD).
- secuencia: the Tuesday run, step by step, as a sequence diagram (SAD).

Each function takes (mode, figures=None) and returns a standalone SVG string.
Pure functions: no Streamlit, no database. figures only overrides the few
counts printed on a diagram; the defaults are the delivered values.
"""
import html

from bi import architecture, brand_icons, charts, control

# region Constants
LAYER = architecture.LAYER_COLORS
MUTED = "#8a8984"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
# Counts of the last dbt build (dbt_node of datos.duckdb, D-157); a caller may pass
# the live ones in figures.
DEFAULT_FIGURES = {"dbt_models": 16, "dbt_tests": 31}
# endregion


# region Pieces
def esc(text):
    return html.escape(str(text))


def tip(part, explanation):
    """The same hover explanation the live diagrams use."""
    return architecture.add_tooltip(part, explanation)


def open_svg(width, height, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" role="img" aria-label="{esc(label)}" '
            f'font-family="{charts.CHART_FONT}">')


def text(x, y, content, palette, size=13, weight=None, color=None, anchor="start", mono=False,
         halo=False):
    """One line of text; halo paints the page color behind it where a line crosses."""
    attributes = [f'x="{x}"', f'y="{y}"', f'font-size="{size}"',
                  f'fill="{color or palette["text"]}"']
    if anchor != "start":
        attributes.append(f'text-anchor="{anchor}"')
    if weight:
        attributes.append(f'font-weight="{weight}"')
    if mono:
        attributes.append(f'font-family="{MONO}"')
    if halo:
        attributes.append(f'paint-order="stroke" stroke="{palette["background"]}" '
                          'stroke-width="5" stroke-linejoin="round"')
    return f'<text {" ".join(attributes)}>{esc(content)}</text>'


def icon_tile(cx, cy, layer, icon, size=40):
    """A tinted square with a brand logo (a slug) or one of architecture's icons."""
    color = LAYER[layer]
    half = size / 2
    tile = (f'<rect x="{cx - half}" y="{cy - half}" width="{size}" height="{size}" rx="11" '
            f'fill="{color}" fill-opacity=".08" stroke="{color}" stroke-opacity=".35" '
            f'stroke-width="1"/>')
    if isinstance(icon, str):
        logo = size * 0.6
        return tile + brand_icons.logo(icon, cx - logo / 2, cy - logo / 2, color, logo)
    scale = size / 52
    return (tile + f'<g transform="translate({cx} {cy}) scale({scale:.3f}) translate({-cx} {-cy})">'
            + icon(cx, cy, color) + '</g>')


def draw_person_icon(x, y, color):
    """A head and shoulders: a person, as C4 draws them."""
    return (f'<circle cx="{x}" cy="{y - 9}" r="8" fill="none" stroke="{color}" stroke-width="2.2"/>'
            f'<path d="M{x - 15} {y + 15} c0 -10 7 -15 15 -15 c8 0 15 5 15 15" fill="none" '
            f'stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>')


def box(x, y, width, height, layer, icon, title, lines, palette, tooltip, dashed=False):
    """A container or a system: frame in its layer color, icon tile on the left,
    a bold name and up to three lines (a line given as ("mono", text) is a path)."""
    color = LAYER[layer]
    left, top = x - width / 2, y - height / 2
    dash = ' stroke-dasharray="6 4"' if dashed else ""
    parts = [f'<rect x="{left}" y="{top}" width="{width}" height="{height}" rx="14" '
             f'fill="{palette["card"]}" stroke="{color}" stroke-width="1.5"{dash}/>',
             icon_tile(left + 30, y, layer, icon)]
    text_x = left + 60
    block = 17 + 15 * len(lines)
    baseline = y - block / 2 + 13
    parts.append(text(text_x, baseline, title, palette, 14, "700", palette["strong_text"]))
    for number, line in enumerate(lines):
        mono = isinstance(line, tuple)
        content = line[1] if mono else line
        parts.append(text(text_x, baseline + 17 + number * 15, content, palette,
                          11 if mono else 11.5, color=palette["text"] if mono else MUTED, mono=mono))
    return tip("".join(parts), tooltip)


def person(x, y, layer, title, subtitle, palette, tooltip):
    """A person centered on x: icon on top (y is the icon's center), name and role below."""
    color = LAYER[layer]
    parts = [f'<circle cx="{x}" cy="{y}" r="26" fill="{color}" fill-opacity=".08" '
             f'stroke="{color}" stroke-opacity=".45" stroke-width="1"/>',
             draw_person_icon(x, y + 3, color),
             text(x, y + 48, title, palette, 14, "700", palette["strong_text"], "middle"),
             text(x, y + 65, subtitle, palette, 11.5, color=MUTED, anchor="middle")]
    return tip("".join(parts), tooltip)


def chip(x, y, content, color, palette, tooltip=None):
    """What travels through a link, in the live diagrams' chip style."""
    width = len(content) * 6.6 + 16
    return tip(f'<rect x="{x - width / 2:.1f}" y="{y - 11}" width="{width:.1f}" height="22" rx="6" '
               f'fill="{palette["card"]}" stroke="{color}" stroke-width="1"/>'
               + text(x, y + 4, content, palette, 11.5, "700", color, "middle", mono=True), tooltip)


def link(points, color, palette, label=None, label_at=None, tooltip=None, dashed=False,
         both=False, arrow=True):
    """Straight segments with an arrowhead (both ends when the flow goes both ways)."""
    path = "M" + " L".join(f"{x} {y}" for x, y in points)
    marker = architecture.arrow_marker_id(color)
    ends = (f' marker-end="url(#{marker})"' if arrow else "") + (
        f' marker-start="url(#{marker})"' if both else "")
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    part = (f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6" opacity="0.85"'
            f'{dash}{ends}/>')
    if label:
        part += chip(*label_at, label, color, palette)
    return tip(part, tooltip)


def boundary(x, y, width, height, title, subtitle, layer, palette):
    """The system boundary: a dashed frame with the system's name."""
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="18" fill="none" '
            f'stroke="{LAYER[layer]}" stroke-width="1.3" stroke-dasharray="6 5" opacity=".8"/>'
            f'<text x="{x + 18}" y="{y + 26}" font-size="14"><tspan font-weight="700" '
            f'letter-spacing="1" fill="{LAYER[layer]}">{esc(title)}</tspan><tspan dx="10" '
            f'fill="{MUTED}">{esc(subtitle)}</tspan></text>')


def arrow_defs():
    return architecture.build_arrow_defs(list(LAYER.values()) + [MUTED])


def read_figures(figures):
    return {**DEFAULT_FIGURES, **(figures or {})}
# endregion


# region PRD · actors and use cases
def build_actors_svg(mode, figures=None):
    """Who uses GreenOcean and for what, and the external systems it relies on."""
    palette = charts.get_palette(mode)
    width, height = 1340, 620
    visitor, author = LAYER["consumption"], LAYER["orchestration"]
    left, right = 410, 870
    center = (left + right) / 2
    visitor_cases = [
        ("Ver qué se movió esta semana y qué es inusual", "Resumen semanal · alertas K6",
         "Variación semanal por familia, región y producto sobre las mismas regiones, y "
         "alertas K6 (RF-12, RF-13)."),
        ("Saber si el precio de hoy es normal para la época", "Contexto de precios · nominal o real",
         "Rango habitual P25–P75 de la misma semana ISO ±1 en años anteriores, en pesos "
         "nominales o reales (RF-14, RF-16)."),
        ("Ver cuánto paga el consumidor sobre el mayorista", "Margen K1 por canal",
         "Margen K1 de cada canal frente a su propio rango habitual (RF-15)."),
        ("Revisar calidad, ejecuciones y documentos", "Ingeniería de datos · PRD, SAD y ADR",
         "Calidad de datos, linaje dbt, historial de ejecuciones y los documentos del "
         "proyecto, descargables en PDF (RF-17, RF-18, RF-20)."),
    ]
    author_cases = [
        ("Lanzar una ejecución manual", "Ejecuciones · clave de control",
         "El botón «Ejecutar pipeline ahora» pide la clave de control y lanza el mismo "
         "workflow semanal por la API de GitHub (RF-18, D-149)."),
        ("Mantener el código, los secretos y las decisiones", "git push · secretos del panel",
         "El autor escribe el código, lo sube al repositorio y administra el token de GitHub "
         "y la clave de control en los secretos de Streamlit."),
    ]
    visitor_ys = [130, 200, 270, 340]
    author_ys = [450, 520]
    parts = [open_svg(width, height, "Actores y casos de uso de GreenOcean"), arrow_defs(),
             boundary(left - 30, 62, right - left + 60, 516, "GREENOCEAN",
                      "panel de solo lectura y pipeline semanal", "processing", palette)]
    for cases, ys, color, person_y in ((visitor_cases, visitor_ys, visitor, 235),
                                       (author_cases, author_ys, author, 485)):
        for (title, subtitle, explanation), y in zip(cases, ys):
            parts.append(f'<path d="M190 {person_y} L{left} {y}" stroke="{color}" '
                         f'stroke-width="1.3" opacity=".6" fill="none"/>')
        for (title, subtitle, explanation), y in zip(cases, ys):
            parts.append(tip(
                f'<rect x="{left}" y="{y - 27}" width="{right - left}" height="54" rx="27" '
                f'fill="{color}" fill-opacity=".08" stroke="{color}" stroke-width="1.3"/>'
                + text(center, y - 3, title, palette, 14, "700", palette["strong_text"], "middle")
                + text(center, y + 15, subtitle, palette, 11.5, color=MUTED, anchor="middle"),
                explanation))
    parts.append(person(130, 220, "consumption", "Visitante", "analista, compras, gerencia",
                        palette, "Quien abre el enlace público del panel: analista de pricing, "
                        "comprador o gerencia. Solo lee; no hay inicio de sesión ni datos "
                        "personales."))
    parts.append(person(130, 470, "orchestration", "El autor", "operador del sistema", palette,
                        "Mantiene el código, administra los secretos, puede lanzar una "
                        "ejecución manual y recibe el correo de GitHub si algo falla."))
    systems = [
        (110, "sources", "file", "ODEPA", "precios mayorista y consumidor", "CSV", True,
         "Oficina de Estudios y Políticas Agrarias: un CSV por año y fuente, descargado por "
         "HTTPS cada martes."),
        (210, "sources", "file", "INE", "IPC de alimentos", "IPC", True,
         "Instituto Nacional de Estadísticas: IPC mensual de «Alimentos y bebidas no "
         "alcohólicas», para los precios reales (D-155)."),
        (310, "processing", "github", "GitHub Actions", "workflow semanal y de pruebas",
         "martes", True, "Ejecuta el workflow semanal cada martes a las 12:00 UTC y las "
         "pruebas en cada cambio."),
        (410, "orchestration", "git", "Repositorio GitHub", "código, base e informes", "commit",
         False, "Guarda el código, la base publicada datos.duckdb y el informe semanal como "
         "issue; avisa al autor por correo si el workflow falla."),
        (510, "consumption", "streamlit", "Streamlit Community Cloud", "publica el panel",
         "despliegue", True, "Publica el panel desde la rama main del repositorio."),
    ]
    system_x, system_width = 1160, 300
    for y, layer, icon, title, subtitle, label, inbound, explanation in systems:
        color = LAYER[layer]
        drawn_icon = architecture.draw_file_icon if icon == "file" else icon
        parts.append(box(system_x, y, system_width, 70, layer, drawn_icon, title, [subtitle],
                         palette, explanation))
        edge = system_x - system_width / 2
        points = [(edge, y), (right + 30, y)] if inbound else [(right + 30, y), (edge, y)]
        parts.append(link(points, color, palette, label, ((edge + right + 30) / 2, y),
                          both=not inbound))
    parts.append("</svg>")
    return "".join(parts)
# endregion


# region PRD · wireframe of the Resumen semanal
def rf_pill(x, y, content, palette):
    """A requirement tag (RF-xx) pinned on a zone of the wireframe."""
    width = len(content) * 6.6 + 14
    return (f'<rect x="{x}" y="{y - 10}" width="{width:.1f}" height="20" rx="10" '
            f'fill="{palette["accent"]}"/>'
            + text(x + width / 2, y + 4, content, palette, 11, "700", palette["on_accent"], "middle"))


def placeholder(x, y, width, palette, height=8):
    return (f'<rect x="{x}" y="{y - height / 2}" width="{width}" height="{height}" rx="{height / 2}" '
            f'fill="{palette["grid"]}"/>')


def panel_frame(x, y, width, height, title, palette):
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="12" '
            f'fill="{palette["card"]}" stroke="{palette["card_border"]}" stroke-width="1.2"/>'
            + text(x + 16, y + 26, title, palette, 14, "700", palette["strong_text"]))


def build_screen_svg(mode, figures=None):
    """Low-fidelity wireframe of the Resumen semanal: what each zone answers,
    tagged with its functional requirement. Placeholders, not data."""
    palette = charts.get_palette(mode)
    width, height = 1200, 720
    rise, fall, alert = palette["rise"], palette["fall"], LAYER["gold"]
    parts = [open_svg(width, height, "Boceto de la pantalla Resumen semanal"),
             f'<rect x="10" y="10" width="{width - 20}" height="{height - 20}" rx="18" '
             f'fill="{palette["field"]}" stroke="{palette["card_border"]}" stroke-width="1.2"/>']
    # Sidebar: the real menu of D-157.
    menu = [("DASHBOARD", None), ("Resumen semanal", True), ("Contexto de precios", False),
            ("INGENIERÍA DE DATOS", None), ("Pipeline y linaje", False), ("Modelo de datos", False),
            ("Calidad y auditoría", False), ("Ejecuciones y DevOps", False),
            ("FUENTES", None), ("ODEPA e INE", False),
            ("DOCUMENTACIÓN", None), ("PRD · SAD · ADR", False)]
    sidebar = [f'<rect x="10" y="10" width="190" height="{height - 20}" rx="18" '
               f'fill="{palette["card"]}" stroke="{palette["card_border"]}" stroke-width="1.2"/>',
               text(30, 46, "GreenOcean", palette, 16, "700", palette["strong_text"])]
    y = 84
    for label, active in menu:
        if active is None:
            y += 8
            sidebar.append(text(30, y, label, palette, 10.5, "700", MUTED))
        else:
            if active:
                sidebar.append(f'<rect x="22" y="{y - 15}" width="166" height="24" rx="8" '
                               f'fill="{palette["accent"]}" fill-opacity=".14"/>')
            sidebar.append(text(34, y + 2, label, palette, 12.5, "700" if active else None,
                                palette["strong_text"] if active else palette["text"]))
        y += 26
    parts.append(tip("".join(sidebar), "Menú del panel: Dashboard, Ingeniería de datos, Fuentes "
                     "y Documentación (D-157). Sin inicio de sesión."))
    main_x, main_right = 222, 1170
    # Header.
    parts.append(tip(
        text(main_x, 50, "¿Qué familias de alimentos subieron y bajaron?", palette, 18, "700",
             palette["strong_text"])
        + text(main_x, 72, "Variación típica (mediana) por familia frente a la semana anterior · "
               "semana y región elegidas", palette, 12, color=MUTED)
        + f'<rect x="{main_right - 150}" y="36" width="150" height="26" rx="13" '
          f'fill="{palette["card"]}" stroke="{palette["card_border"]}"/>'
          f'<circle cx="{main_right - 134}" cy="49" r="5" fill="{architecture.STATE_COLORS[control.RUN_OK]}"/>'
        + text(main_right - 122, 53, "Actualizado · fecha", palette, 11.5),
        "Título de la página y estado de la última carga."))
    # KPI tiles.
    tiles = [("Precios comparados", "con precio en ambas semanas"),
             ("Familias", "↑ · ↓ · sin cambio"), ("Regiones", "↑ · ↓ · sin dirección clara"),
             ("Alertas de precio", "inusuales y de al menos 10 %")]
    gap = 12
    tile_width = (main_right - main_x - 3 * gap) / 4
    for index, (label, note) in enumerate(tiles):
        x = main_x + index * (tile_width + gap)
        accent = alert if index == 3 else palette["card_border"]
        parts.append(tip(
            f'<rect x="{x:.1f}" y="92" width="{tile_width:.1f}" height="74" rx="12" '
            f'fill="{palette["card"]}" stroke="{accent}" stroke-width="1.2"/>'
            + text(x + 14, 114, label, palette, 12, "700", palette["text"])
            + placeholder(x + 14, 134, 70, palette, 12)
            + text(x + 14, 156, note, palette, 11, color=MUTED),
            "Cuatro cifras del mismo modelo semanal que los gráficos de abajo (D-150)."))
    parts.append(rf_pill(main_right - 118, 92, "RF-12 · RF-13", palette))
    # Map of regions.
    map_x, map_width, top, bottom = main_x, 300, 182, 640
    parts.append(tip(panel_frame(map_x, top, map_width, bottom - top, "Regiones", palette)
                     + text(map_x + 16, top + 46, "hacia dónde se movió cada región", palette, 11.5,
                            color=MUTED)
                     + build_map_sketch(map_x + 60, top + 70, palette, rise, fall),
                     "Mapa de Chile: la dirección de cada región, solo si pasa una prueba de "
                     "signos (D-146). ODEPA publica 9 de las 16 regiones."))
    parts.append(rf_pill(map_x + map_width - 66, top + 22, "RF-12", palette))
    # Movement by family.
    right_x = map_x + map_width + 16
    right_width = main_right - right_x
    family_bottom = 352
    family = [panel_frame(right_x, top, right_width, family_bottom - top, "Movimiento por familia",
                          palette)]
    axis = right_x + 330
    family.append(f'<path d="M{axis} {top + 42} V{family_bottom - 12}" stroke="{palette["card_border"]}"/>')
    for index, (length, direction) in enumerate([(70, 1), (46, 1), (22, 1), (14, -1), (38, -1),
                                                 (58, -1), (8, 1)]):
        y = top + 52 + index * 17
        parts_x = axis if direction > 0 else axis - length
        family.append(placeholder(right_x + 16, y, 150, palette, 7))
        family.append(f'<rect x="{parts_x}" y="{y - 5}" width="{length}" height="10" rx="3" '
                      f'fill="{rise if direction > 0 else fall}" fill-opacity=".75"/>')
        family.append(placeholder(axis + 150, y, 50, palette, 7))
    parts.append(tip("".join(family), "Una fila por familia: barra divergente desde cero con su "
                     "variación típica (mediana). Elegir una familia llena la tabla de abajo."))
    parts.append(rf_pill(right_x + right_width - 66, top + 22, "RF-12", palette))
    # Products of the chosen family.
    products_top = family_bottom + 14
    products = [panel_frame(right_x, products_top, right_width, bottom - products_top,
                            "Productos · familia elegida", palette)]
    controls = [("Buscar producto", 150), ("Canal ▾", 110), ("Orden ▾", 130)]
    cx = right_x + 16
    for label, control_width in controls:
        products.append(f'<rect x="{cx}" y="{products_top + 40}" width="{control_width}" height="26" '
                        f'rx="8" fill="{palette["field"]}" stroke="{palette["card_border"]}"/>'
                        + text(cx + 10, products_top + 57, label, palette, 11.5, color=MUTED))
        cx += control_width + 10
    context_x = cx
    products.append(f'<rect x="{context_x}" y="{products_top + 40}" width="110" height="26" rx="8" '
                    f'fill="{palette["accent"]}" fill-opacity=".14" stroke="{palette["accent"]}"/>'
                    + text(context_x + 55, products_top + 57, "Ver contexto", palette, 11.5, "700",
                           palette["accent"], "middle"))
    columns = [("Producto", 16), ("Canal", 190), ("Anterior", 300), ("Actual", 380),
               ("Variación", 450), ("Regiones ↑/↓", 530)]
    header_y = products_top + 92
    for label, offset in columns:
        products.append(text(right_x + offset, header_y, label, palette, 11.5, "700", MUTED))
    products.append(f'<path d="M{right_x + 12} {header_y + 8} H{right_x + right_width - 12}" '
                    f'stroke="{palette["card_border"]}"/>')
    for row in range(5):
        y = header_y + 28 + row * 26
        is_alert = row == 1
        if is_alert:
            products.append(f'<rect x="{right_x + 8}" y="{y - 12}" width="{right_width - 16}" '
                            f'height="24" rx="6" fill="{alert}" fill-opacity=".10"/>'
                            f'<circle cx="{right_x + right_width - 24}" cy="{y}" r="5" fill="{alert}"/>')
        for _, offset in columns:
            products.append(placeholder(right_x + offset, y, 120 if offset == 16 else 56, palette, 7))
    parts.append(tip("".join(products), "Los precios comparables de la familia elegida, con "
                     "búsqueda, canal y orden; una alerta K6 se marca en su fila. «Ver contexto» "
                     "abre Contexto de precios para el producto."))
    parts.append(rf_pill(context_x + 118, products_top + 53, "RF-14", palette))
    parts.append(rf_pill(right_x + right_width - 66, products_top + 22, "RF-13", palette))
    # Coverage note, full width (D-150).
    parts.append(tip(
        f'<rect x="{main_x}" y="654" width="{main_right - main_x}" height="40" rx="10" '
        f'fill="{palette["card"]}" stroke="{palette["card_border"]}"/>'
        + text(main_x + 16, 678, "Cobertura de la familia y de la semana · enlaces a Calidad y "
               "Metodología", palette, 12, color=MUTED),
        "Qué cubren las cifras: precios de la familia y de toda la semana, y cuántos no tienen "
        "comparación válida."))
    parts.append(rf_pill(main_right - 66, 674, "RF-17", palette))
    parts.append("</svg>")
    return "".join(parts)


def build_map_sketch(x, y, palette, rise, fall):
    """A long, narrow country and nine region rows: a sketch, not the real map."""
    outline = (f'<path d="M{x + 22} {y} c8 40 2 90 6 140 c3 50 -4 100 2 150 c3 40 -10 70 -18 100 '
               f'l-8 -6 c6 -30 10 -60 6 -95 c-4 -50 2 -100 -2 -150 c-3 -50 2 -100 6 -139 z" '
               f'fill="{palette["field"]}" stroke="{palette["card_border"]}" stroke-width="1.4"/>')
    rows = []
    colors = [rise, rise, fall, rise, MUTED, fall, rise, fall, MUTED]
    for index, color in enumerate(colors):
        dot_y = y + 50 + index * 36
        dot_x = x + 24 if index < 8 else x + 18
        rows.append(f'<circle cx="{dot_x}" cy="{dot_y}" r="4.5" fill="{color}"/>'
                    f'<path d="M{dot_x + 6} {dot_y} H{x + 90}" stroke="{palette["card_border"]}"/>'
                    + placeholder(x + 96, dot_y, 90, palette, 7)
                    + f'<rect x="{x + 194}" y="{dot_y - 7}" width="26" height="14" rx="7" '
                      f'fill="{color}" fill-opacity=".25"/>')
    return outline + "".join(rows)
# endregion


# region SAD · C4 level 1, context
def build_context_svg(mode, figures=None):
    """C4 level 1: GreenOcean as one box, the people who use it and the systems around it."""
    palette = charts.get_palette(mode)
    width, height = 1320, 470
    system_x, system_y, system_width, system_height = 660, 340, 380, 200
    system_left, system_right = system_x - system_width / 2, system_x + system_width / 2
    system_top = system_y - system_height / 2
    accent = LAYER["processing"]
    parts = [open_svg(width, height, "Contexto del sistema (C4, nivel 1)"), arrow_defs()]
    parts.append(tip(
        f'<rect x="{system_left}" y="{system_top}" width="{system_width}" height="{system_height}" '
        f'rx="20" fill="{accent}" fill-opacity=".10" stroke="{accent}" stroke-width="2"/>'
        + icon_tile(system_x, system_top + 44, "processing", architecture.draw_chart_icon, 48)
        + text(system_x, system_top + 100, "GreenOcean", palette, 20, "700", palette["strong_text"],
               "middle")
        + text(system_x, system_top + 120, "[sistema de software]", palette, 12, color=MUTED,
               anchor="middle")
        + text(system_x, system_top + 148, "Pipeline semanal de precios de alimentos", palette, 13,
               anchor="middle")
        + text(system_x, system_top + 166, "y panel de BI de solo lectura", palette, 13,
               anchor="middle"),
        "El sistema completo: ingesta, capa bronce, dbt, data warehouse DuckDB y panel "
        "Streamlit. Su interior es la vista de contenedores (C4, nivel 2)."))
    parts.append(person(560, 68, "consumption", "Visitante", "analista, compras, gerencia",
                        palette, "Lee el panel desde un enlace público; no escribe nada."))
    parts.append(person(760, 68, "orchestration", "El autor", "operador", palette,
                        "Mantiene el código y los secretos, lanza ejecuciones manuales y recibe "
                        "el correo de GitHub si algo falla."))
    parts.append(link([(560, 150), (560, system_top)], LAYER["consumption"], palette,
                      "consulta · HTTPS", (560, 192), "Navegador del visitante al panel publicado."))
    parts.append(link([(760, 150), (760, system_top)], LAYER["orchestration"], palette,
                      "ejecución manual", (760, 192),
                      "Clave de control y botón «Ejecutar pipeline ahora» (D-149)."))
    externals = [
        ("left", 290, "sources", architecture.draw_file_icon, "ODEPA", ["datos abiertos de precios"],
         "CSV · HTTPS", True,
         "Proveedor: un CSV por año y fuente, mayorista diario y consumidor semanal."),
        ("left", 390, "sources", architecture.draw_file_icon, "INE", ["IPC de alimentos"],
         "IPC · HTTPS", True,
         "Proveedor: la serie del IPC base 2023 y la serie empalmada de divisiones."),
        ("right", 290, "processing", "github", "GitHub", ["Actions · repositorio · issues"],
         "workflow · commit", False,
         "Plataforma: guarda el código y la base publicada, ejecuta los workflows, publica el "
         "informe semanal y avisa por correo."),
        ("right", 390, "consumption", "streamlit", "Streamlit Community Cloud", ["publica el panel"],
         "despliegue", False, "Plataforma: publica el panel desde la rama main."),
    ]
    external_width = 270
    for side, y, layer, icon, title, lines, label, inbound, explanation in externals:
        color = LAYER[layer]
        x = 155 if side == "left" else width - 155
        parts.append(box(x, y, external_width, 80, layer, icon, title, lines, palette, explanation))
        if side == "left":
            start, end = (x + external_width / 2, y), (system_left, y)
        else:
            start, end = (x - external_width / 2, y), (system_right, y)
        middle = ((start[0] + end[0]) / 2, y)
        parts.append(link([start, end], color, palette, label, middle, both=not inbound))
    # The author pushes code to GitHub and GitHub mails the author when a run fails.
    github_x = width - 155
    parts.append(link([(830, 68), (github_x, 68), (github_x, 250)], LAYER["orchestration"], palette,
                      "git push · correo", (1000, 68),
                      "El autor sube el código con git push; GitHub le avisa por correo si el "
                      "workflow semanal falla.", both=True))
    parts.append("</svg>")
    return "".join(parts)
# endregion


# region SAD · C4 level 2, containers
def build_containers_svg(mode, figures=None):
    """C4 level 2: every container of GreenOcean with its technology and how they talk."""
    palette = charts.get_palette(mode)
    width, height = 1740, 790
    ext, col_a, col_b, col_c, col_d, col_e = 110, 400, 700, 1000, 1300, 1600
    row_1, row_2, row_3, row_4 = 270, 410, 550, 690
    box_width, box_height, half = 214, 78, 39
    parts = [open_svg(width, height, "Contenedores del sistema (C4, nivel 2)"), arrow_defs(),
             boundary(270, 200, 1450, 560, "GREENOCEAN", "contenedores", "processing", palette)]

    def container(x, y, layer, icon, title, path, tech, explanation, dashed=False, box_w=box_width):
        return box(x, y, box_w, box_height, layer, icon, title, [("mono", path), tech], palette,
                   explanation, dashed)

    # Outside the boundary.
    parts.append(person(col_e, 92, "consumption", "Visitante", "navegador", palette,
                        "Quien abre el enlace público del panel."))
    for y, layer, icon, title, line, explanation in [
            (row_1, "orchestration", "git", "Repositorio", "GitHub · rama main",
             "Guarda el código, datos.duckdb, el respaldo datos.db y el registro de descargas; "
             "recibe el informe semanal como issue."),
            (row_2, "sources", architecture.draw_file_icon, "ODEPA", "CSV por año",
             "Portal de datos abiertos de ODEPA: mayorista diario y consumidor semanal."),
            (row_3, "sources", architecture.draw_file_icon, "INE", "IPC de alimentos",
             "Las dos series del IPC del INE, en CSV.")]:
        parts.append(box(ext, y, 170, box_height, layer, icon, title, [line], palette, explanation))
    # Inside: workflows on top, then processes and stores.
    parts.append(container(550, row_1, "orchestration", "github", "Workflow semanal",
                           ".github/workflows/semanal.yml", "GitHub Actions · martes 12:00 UTC",
                           "Orquesta la carga completa cada martes: descarga, respaldo SQLite, "
                           "pipeline.py, pytest, commit e informe.", box_w=500))
    parts.append(container(col_d, row_1, "orchestration", "pytest", "Workflow de pruebas",
                           ".github/workflows/pruebas.yml", "GitHub Actions · pytest",
                           "En cada cambio compila el proyecto dbt (dbt parse) y corre la suite "
                           "de pruebas.", box_w=290))
    containers = [
        (col_a, row_2, "ingestion", "python", "Agente de ingesta", "agent/agent.py",
         "Python · requests", "Descarga los CSV de ODEPA, valida tamaño y encabezado, calcula su "
         "huella y registra cada resultado."),
        (col_b, row_2, "ingestion", architecture.draw_database_icon, "Zona de aterrizaje",
         "etl/raw.db", "SQLite · no se sube", "Las filas de los CSV tal como llegan; se "
         "reconstruye en cada ejecución."),
        (col_c, row_2, "processing", "python", "Orquestador", "etl/pipeline.py", "Python",
         "Encadena bronce, IPC, dbt build y el control de volumen; escribe la base de servicio y "
         "registra la carga en etl_run."),
        (col_d, row_2, "gold", "duckdb", "Base de servicio", "etl/datos.duckdb",
         "DuckDB · se sube", "Las tablas que lee el panel, el registro etl_run y el "
         "linaje dbt (dbt_node, dbt_result)."),
        (col_e, row_2, "consumption", "streamlit", "Panel", "bi/", "Streamlit · Plotly",
         "Dashboard, ingeniería de datos y documentación; abre datos.duckdb en solo lectura."),
        (col_a, row_3, "ingestion", "python", "Ingesta del IPC", "etl/ine.py", "Python · requests",
         "La llama pipeline.py: descarga las dos series del INE y guarda la división de alimentos "
         "en bronce, como texto."),
        (col_b, row_3, "bronze", "apacheparquet", "Capa bronce", "etl/bronze/", "Parquet · pyarrow",
         "Copia literal por fuente y año, más las series del INE; no se sube."),
        (col_c, row_3, "processing", "dbt", "Proyecto dbt", "dbt/", "dbt Core · dbt-duckdb",
         "Staging, intermedio y marts, con sus pruebas de datos."),
        (col_c, row_4, "quality", "duckdb", "Almacén de trabajo", "warehouse_build.duckdb",
         "DuckDB · no se sube", "Donde dbt construye y prueba cada modelo antes de publicar."),
    ]
    for x, y, layer, icon, title, path, tech, explanation in containers:
        parts.append(container(x, y, layer, icon, title, path, tech, explanation))
    parts.append(container(col_d, row_3, "gold", architecture.draw_database_icon, "Respaldo",
                           "etl/datos.db", "SQLite · etl/etl.py",
                           "El data warehouse anterior, construido en paralelo y comparado con "
                           "DuckDB por una prueba de paridad (D-154).", dashed=True))
    blue, green, bronze = LAYER["ingestion"], LAYER["sources"], LAYER["bronze"]
    purple, gold, teal, orange = LAYER["processing"], LAYER["gold"], LAYER["consumption"], LAYER["orchestration"]
    edge = box_width / 2
    links = [
        ([(300, row_1), (ext + 85, row_1)], orange, "commit", "Commit de datos.duckdb, datos.db y "
         "el registro de descargas; luego el issue «Informe semanal»."),
        ([(ext + 85, row_2), (col_a - edge, row_2)], green, "HTTPS", "Descarga de los CSV de ODEPA."),
        ([(ext + 85, row_3), (col_a - edge, row_3)], green, "HTTPS", "Descarga de los CSV del INE."),
        ([(col_a + edge, row_2), (col_b - edge, row_2)], blue, "CSV", "Los archivos descargados "
         "se cargan tal como llegan."),
        ([(col_b, row_2 + half), (col_b, row_3 - half)], bronze, "Parquet", "pipeline.py copia "
         "las tablas crudas a Parquet, como texto."),
        ([(col_a + edge, row_3), (col_b - edge, row_3)], blue, "texto", "Las filas del IPC, "
         "como texto, en bronze/ine_ipc."),
        ([(col_b + edge, row_3), (col_c - edge, row_3)], bronze, "sources", "dbt lee los Parquet "
         "de bronce como fuentes."),
        ([(col_c, row_2 + half), (col_c, row_3 - half)], purple, "dbt build", "Modelos y pruebas, "
         "en el almacén de trabajo."),
        ([(col_c, row_3 + half), (col_c, row_4 - half)], purple, "construye", "dbt materializa y "
         "prueba cada modelo."),
        ([(col_c + edge, row_2), (col_d - edge, row_2)], gold, "reemplaza", "Copia solo las tablas "
         "del panel a un archivo temporal y reemplaza la base publicada de una vez (ADR-34)."),
        ([(col_d + edge, row_2), (col_e - edge, row_2)], teal, "SQL", "Consultas con nombre, en "
         "solo lectura (bi/queries.sql)."),
        ([(col_a, row_1 + half), (col_a, row_2 - half)], orange, "ejecuta", "El workflow lanza "
         "agent/agent.py."),
        ([(800, row_1), (col_c, row_1), (col_c, row_2 - half)], orange, "ejecuta",
         "El workflow lanza etl/pipeline.py."),
        ([(col_d, row_1 + half), (col_d, row_2 - half)], orange, "pytest", "La suite corre "
         "contra la base nueva."),
        ([(col_e, 160), (col_e, row_2 - half)], teal, "HTTPS", "El navegador del visitante abre "
         "el panel publicado en Streamlit Community Cloud."),
    ]
    for points, color, label, explanation in links:
        (x1, y1), (x2, y2) = points[-2], points[-1]
        if len(points) == 3:
            label_at = ((points[0][0] + points[1][0]) / 2, points[0][1])
        else:
            label_at = ((x1 + x2) / 2, (y1 + y2) / 2)
        parts.append(link(points, color, palette, label, label_at, explanation))
    parts.append(link([(col_d, row_2 + half), (col_d, row_3 - half)], gold, palette, "paridad",
                      (col_d, (row_2 + row_3) / 2), "Una prueba compara DuckDB y SQLite fila a "
                      "fila cada semana.", dashed=True, both=True))
    parts.append("</svg>")
    return "".join(parts)
# endregion


# region SAD · runtime view of the weekly run
def build_sequence_svg(mode, figures=None):
    """The Tuesday run as a sequence diagram, from the schedule to the weekly issue."""
    palette = charts.get_palette(mode)
    counts = read_figures(figures)
    lanes = [
        ("actions", "GitHub Actions", "semanal.yml", "orchestration", "github",
         "Ejecuta el workflow semanal cada martes a las 12:00 UTC."),
        ("agent", "Agente", "agent/agent.py", "ingestion", "python",
         "Descarga los CSV de ODEPA y valida su encabezado."),
        ("sources", "ODEPA · INE", "CSV · HTTPS", "sources", architecture.draw_file_icon,
         "Las fuentes oficiales: los CSV de ODEPA y del IPC del INE."),
        ("ine", "Ingesta IPC", "etl/ine.py", "ingestion", "python",
         "Descarga las dos series del IPC y guarda la división de alimentos en bronce."),
        ("pipeline", "Orquestador", "etl/pipeline.py", "processing", "python",
         "Bronce, IPC, dbt build, control de volumen y base de servicio."),
        ("dbt", "dbt build", "dbt Core · DuckDB", "processing", "dbt",
         f"{counts['dbt_models']} modelos y {counts['dbt_tests']} pruebas de datos, en el "
         "almacén de trabajo."),
        ("serving", "Base de servicio", "datos.duckdb", "gold", "duckdb",
         "La base que lee el panel; se reemplaza de una sola vez."),
        ("pytest", "Pruebas", "pytest -q", "quality", "pytest",
         "La suite de Python contra la base nueva, con la paridad SQLite y DuckDB."),
        ("repo", "Repositorio", "GitHub · main", "consumption", "git",
         "Recibe el commit de la base y el issue «Informe semanal»."),
    ]
    first_x, spacing = 110, 165
    x_of = {lane[0]: first_x + index * spacing for index, lane in enumerate(lanes)}
    width = first_x * 2 + spacing * (len(lanes) - 1)
    steps = [
        ("actions", "actions", "cron · martes 12:00 UTC", "call",
         "El horario del workflow; restaura de la caché los CSV de años cerrados (D-047)."),
        ("actions", "agent", "python agent/agent.py", "call", "Primer paso de datos."),
        ("agent", "sources", "descarga CSV de ODEPA", "call",
         "El año en curso y lo que falte en la caché."),
        ("sources", "agent", "encabezado validado", "return",
         "Un encabezado distinto detiene el workflow."),
        ("actions", "actions", "etl/etl.py · respaldo SQLite", "call",
         "Reconstruye raw.db y el respaldo datos.db."),
        ("actions", "pipeline", "python etl/pipeline.py", "call", "La carga con dbt (D-154)."),
        ("pipeline", "pipeline", "raw.db → bronce Parquet", "call",
         "Copia literal por fuente y año, como texto."),
        ("pipeline", "ine", "actualiza el IPC", "call", "prepare_ipc: llama a etl/ine.py."),
        ("ine", "sources", "descarga CSV del IPC", "call", "Las dos series oficiales del INE."),
        ("sources", "ine", "alimentos → bronce", "return",
         "Si el INE no responde, se usa el bronce previo o el IPC ya publicado."),
        ("pipeline", "dbt", "dbt build", "call",
         f"{counts['dbt_models']} modelos y {counts['dbt_tests']} pruebas, en "
         "warehouse_build.duckdb."),
        ("dbt", "pipeline", "todo en verde", "return",
         "Si un modelo o una prueba falla, la falla queda en etl_run y la base no cambia."),
        ("pipeline", "pipeline", "control de volumen ≥ 90 %", "call",
         "Menos del 90 % de las filas de la última carga correcta detiene la carga."),
        ("pipeline", "serving", "archivo temporal → reemplazo", "call",
         "Copia solo las tablas del panel y reemplaza la base publicada de una vez (ADR-34)."),
        ("actions", "pytest", "pytest -q", "call", "La suite completa contra la base nueva."),
        ("pytest", "serving", "lee la base · paridad", "call",
         "Incluye la paridad fila a fila entre DuckDB y el respaldo SQLite."),
        ("actions", "repo", "git commit · push", "call",
         "datos.duckdb, datos.db y el registro de descargas."),
        ("actions", "repo", "gh issue create", "call", "Publica el issue «Informe semanal»."),
    ]
    header_top, header_height = 24, 92
    first_step_y, step = header_top + header_height + 40, 36
    last_y = first_step_y + step * (len(steps) - 1)
    note_y = last_y + 44
    height = note_y + 58
    parts = [open_svg(width, height, "Vista de ejecución: el martes automático"), arrow_defs()]
    for key, title, subtitle, layer, icon, explanation in lanes:
        x = x_of[key]
        color = LAYER[layer]
        parts.append(f'<path d="M{x} {header_top + header_height} V{last_y + 18}" stroke="{color}" '
                     f'stroke-width="1.2" stroke-dasharray="4 5" opacity=".55"/>')
        parts.append(tip(
            f'<rect x="{x - 72}" y="{header_top}" width="144" height="{header_height}" rx="14" '
            f'fill="{palette["card"]}" stroke="{color}" stroke-width="1.5"/>'
            + icon_tile(x, header_top + 26, layer, icon, 36)
            + text(x, header_top + 62, title, palette, 13.5, "700", palette["strong_text"], "middle")
            + text(x, header_top + 79, subtitle, palette, 10.5, color=palette["text"], anchor="middle",
                   mono=True),
            explanation))
    for number, (source, target, label, kind, explanation) in enumerate(steps, 1):
        y = first_step_y + (number - 1) * step
        x1, x2 = x_of[source], x_of[target]
        color = LAYER[dict((lane[0], lane[3]) for lane in lanes)[source]]
        marker = architecture.arrow_marker_id(color)
        dash = ' stroke-dasharray="5 4"' if kind == "return" else ""
        badge = (f'<circle cx="26" cy="{y}" r="10" fill="{color}"/>'
                 f'<text x="26" y="{y + 4}" font-size="11" font-weight="700" text-anchor="middle" '
                 f'fill="#fff">{number}</text>')
        if x1 == x2:
            path = f"M{x1} {y - 8} h28 v16 h-26"
            label_part = text(x1 + 36, y + 4, label, palette, 12, halo=True)
        else:
            offset = 4 if x2 > x1 else -4
            path = f"M{x1 + offset} {y} H{x2 - offset}"
            label_part = text((x1 + x2) / 2, y - 7, label, palette, 12, anchor="middle", halo=True)
        parts.append(tip(badge + f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6"'
                         f'{dash} marker-end="url(#{marker})"/>' + label_part, explanation))
    failure = LAYER["quarantine"]
    parts.append(tip(
        f'<rect x="{first_x - 72}" y="{note_y - 20}" width="{width - 2 * (first_x - 72)}" height="40" '
        f'rx="12" fill="{failure}" fill-opacity=".08" stroke="{failure}" stroke-opacity=".6"/>'
        + text(width / 2, note_y + 5, "Si cualquier paso falla, el workflow se detiene: no hay "
               "commit, la base publicada no cambia y GitHub avisa al autor por correo.", palette,
               13, "700", failure, "middle"),
        "Integridad ante fallas (ADR-15, RNF-06)."))
    parts.append("</svg>")
    return "".join(parts)
# endregion


DOC_DIAGRAMS = {
    "actores": build_actors_svg,
    "pantalla": build_screen_svg,
    "contexto": build_context_svg,
    "contenedores": build_containers_svg,
    "secuencia": build_sequence_svg,
}
# Markers that reuse a live panel diagram (drawn by the dashboard, not here).
LIVE_DIAGRAMS = ("plataforma", "pipeline", "modelo")
