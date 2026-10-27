"""«Plan de pruebas y seguridad» (D-258, D-260, D-290): the ten test cases and the procedure that runs them, as two clickable diagrams.

The cases S-01 to S-10 live here and only here (the document used to hold them in a long table): each is a node around the
lock of the plan, with the logo of the technology it attacks, and a click opens its attack, its expected result, its OWASP Top 10 (2021) category, the threat it
belongs to and the test that verifies it. The procedure is a cycle of five steps, as in a software life cycle, with the
way back when a case fails. The pop-ups are CSS sheets opened with :target, with no script; the document anchors itself
(<base href="about:srcdoc">) because in an srcdoc frame a #link would otherwise resolve against the page around it.
"""

import html

from bi import charts, doc_views, i18n, quality_view, security_map

# (id, short name, attack, expected result, OWASP code or «—», the tests that verify it)
CASES = [
    (
        "S-01",
        "SQL que lee secretos",
        "19 consultas SQL para leer secretos o escribir archivos",
        "Rechazada; el secreto nunca aparece",
        "A03",
        ["tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files"],
    ),
    (
        "S-02",
        "Órdenes directas al motor",
        "9 órdenes directas al motor",
        "Error de permiso",
        "A05",
        ["tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed"],
    ),
    (
        "S-03",
        "Consultas sin fin",
        "Consultas sin fin o de millones de filas",
        "Cortada a los 10 segundos; como máximo 5.000 filas",
        "A04",
        [
            "tests/test_sql_explorer.py::test_slow_query_is_interrupted",
            "tests/test_sql_explorer.py::test_result_is_limited_and_flagged",
        ],
    ),
    (
        "S-04",
        "Clave con ñ o emojis",
        "Clave con ñ, tildes o emojis",
        "«Clave incorrecta.», sin error",
        "A07",
        ["tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe"],
    ),
    (
        "S-05",
        "Probar claves sin parar",
        "Probar claves sin parar",
        "«Clave incorrecta.» cada vez, sin bloqueo: riesgo aceptado por el autor (ver el resumen)",
        "A07",
        ["tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time"],
    ),
    (
        "S-06",
        "Tokens en el repositorio",
        "Buscar tokens en el repositorio",
        "Ninguno",
        "A02",
        ["tests/test_security.py::test_no_secret_is_tracked_by_git"],
    ),
    (
        "S-07",
        "Error de GitHub",
        "Provocar un error de GitHub",
        "El mensaje nunca muestra el token",
        "A09",
        ["tests/test_control.py::test_github_error_never_shows_the_token"],
    ),
    (
        "S-08",
        "Permisos del workflow",
        "Abusar de los permisos del workflow",
        "Solo contenido e issues",
        "A01",
        ["tests/test_security.py::test_the_weekly_job_has_least_privilege"],
    ),
    (
        "S-09",
        "Control sin prueba",
        "Afirmar un control sin prueba",
        "Cada control de la arquitectura de seguridad apunta a una prueba que existe",
        "—",
        ["tests/test_security.py::test_every_control_of_the_map_points_to_a_test_that_exists"],
    ),
    (
        "S-10",
        "Pipeline sin la clave",
        "Lanzar el pipeline sin la clave",
        "El botón no existe antes de la clave",
        "A01",
        ["tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code"],
    ),
]
# The technology each case attacks (D-260), drawn as its logo inside the node: the SQL engine, the comparison of the code in
# Python, the repository, GitHub and its workflow, the tests themselves and the panel.
TECH = {
    "S-01": "duckdb",
    "S-02": "duckdb",
    "S-03": "duckdb",
    "S-04": "python",
    "S-05": "python",
    "S-06": "git",
    "S-07": "github",
    "S-08": "github",
    "S-09": "pytest",
    "S-10": "streamlit",
}
TECH_NAMES = {
    "duckdb": "DuckDB",
    "python": "Python",
    "git": "Git",
    "github": "GitHub",
    "pytest": "pytest",
    "streamlit": "Streamlit",
}
# Where each case sits around the lock (x, y); the lines run on a horizontal trunk and turn at right angles, as in the
# entity-relationship diagram.
CASE_PLACES = {
    "S-01": (500, 115),
    "S-02": (715, 135),
    "S-03": (885, 215),
    "S-04": (885, 365),
    "S-05": (715, 445),
    "S-06": (500, 465),
    "S-07": (285, 445),
    "S-08": (115, 365),
    "S-09": (115, 215),
    "S-10": (285, 135),
}


def esc(value):
    return html.escape(str(value))


def threat_of(case_id):
    """The threat (T1 to T6) whose cases include this one, and the names of its controls, or None."""
    for tid, title, owasp, numbers, cases, asset in security_map.THREATS:
        if case_id in cases:
            return tid, title, [security_map.CONTROLS[n - 1][1] for n in numbers]
    return None


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:400 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
svg.plan {{ display:block; width:100%; height:auto; }}
svg.plan a {{ cursor:pointer; outline:none; }}
svg.plan a:hover .node, svg.plan a:focus .node {{ stroke-width:3.4; }}
svg.plan a:hover .core, svg.plan a:focus .core {{ filter:brightness(1.12); }}
.note {{ margin:4px 4px 0; font-size:12.5px; color:{muted}; }}
.modal {{ display:none; position:fixed; inset:0; z-index:50; align-items:center; justify-content:center; padding:10px; background:rgba(0,0,0,.55); }}
.modal:target {{ display:flex; }}
.modal .back {{ position:absolute; inset:0; cursor:default; }}
.sheet {{ position:relative; z-index:1; width:100%; max-width:680px; max-height:100%; overflow:auto; padding:18px 22px 14px; border-radius:18px;
  background:{card}; border:1px solid {border}; box-shadow:0 24px 60px rgba(0,0,0,{'.6' if dark else '.25'}); }}
.sheet h3 {{ margin:0 36px 2px 0; font-size:19px; font-weight:600; color:{ink}; }}
.sheet .q {{ margin:0 0 6px; color:{accent}; font-size:14px; font-weight:500; }}
.sheet .close {{ position:absolute; top:12px; right:14px; width:30px; height:30px; display:grid; place-items:center; border-radius:50%;
  border:1px solid {border}; color:{ink}; text-decoration:none; font-size:15px; }}
.sheet .close:hover {{ border-color:{accent}; }}
.sheet h4 {{ margin:12px 0 2px; font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:{muted}; }}
.sheet p {{ margin:0 0 4px; font-size:14px; color:{ink}; }}
.sheet code {{ display:block; margin:3px 0; padding:6px 10px; border-radius:10px; background:color-mix(in srgb, {border} 40%, transparent);
  font:400 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; color:{ink}; overflow-wrap:anywhere; }}
@media print {{ .modal {{ display:none !important; }} }}
</style>"""


def wrap_document(palette, body):
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><base href="about:srcdoc"><meta name="viewport" '
        'content="width=device-width,initial-scale=1">'
        + build_css(palette)
        + f'</head><body>{quality_view.DEFS}{body}</body></html>'
    )


def build_modal(identifier, title, subtitle, body):
    return (
        f'<div class="modal" id="{identifier}"><a class="back" href="#" aria-label="Cerrar"></a><div class="sheet" role="dialog" '
        f'aria-label="{esc(title)}"><a class="close" href="#" aria-label="Cerrar">✕</a><h3>{esc(title)}</h3>'
        f'<div class="q">{esc(subtitle)}</div>{body}</div></div>'
    )


def build_case_modal(case):
    case_id, short, attack, expected, owasp, tests = case
    category = (
        f"{owasp} · {security_map.OWASP[owasp]}"
        if owasp in security_map.OWASP
        else "No corresponde a una categoría: vigila que cada control tenga su prueba"
    )
    threat = threat_of(case_id)
    belongs = (
        f"{threat[0]} · {threat[1]}. Lo detiene: {', '.join(i18n.translate_text(name) for name in threat[2])}."
        if threat
        else "Ninguna en concreto: es la prueba de que las demás existen."
    )
    body = (
        f'<h4>Ataque</h4><p>{esc(attack)}</p><h4>Resultado esperado</h4><p>{esc(expected)}</p>'
        f'<h4>Tecnología</h4><p>{esc(TECH_NAMES[TECH[case_id]])}</p>'
        f'<h4>OWASP Top 10 (2021)</h4><p>{esc(category)}</p><h4>Amenaza que cubre</h4><p>{esc(belongs)}</p>'
        f'<h4>Prueba que lo verifica</h4>' + "".join(f"<code>{esc(test)}</code>" for test in tests)
    )
    return build_modal(f"c-{case_id}", f"{case_id} · {short}", "Se repite en cada push y pull request.", body)


def lock_mark(cx, cy, size, color):
    """The padlock of the plan as a flat mark in the accent color, with no disc (D-280)."""
    return (
        f'<svg x="{cx - size / 2:.1f}" y="{cy - size / 2:.1f}" width="{size}" height="{size}" viewBox="0 0 72 72" '
        f'aria-hidden="true"><rect x="22" y="33" width="28" height="21" rx="4" fill="{color}"/>'
        f'<path d="M27 33v-6a9 9 0 0 1 18 0v6" fill="none" stroke="{color}" stroke-width="4.5"/></svg>'
    )


def place_logo(svg, x, y, size):
    """A logo of doc_views or quality_view placed with its top-left corner at (x, y)."""
    frame = f'<svg x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" '
    return svg.replace('<svg class="logo" ', frame, 1).replace('<svg class="qa-icon" ', frame, 1)


def case_lines(cx, cy, radius):
    """The lines from the lock to the cases: a horizontal trunk to each side and a vertical branch up and down to each
    case, so every turn is a right angle. A dot marks where a branch leaves the trunk."""
    paths, dots = [], set()
    for case_id, (x, y) in CASE_PLACES.items():
        edge = y + radius if y < cy else y - radius
        paths.append(f"M{cx} {cy} H{x} V{edge}" if x != cx else f"M{cx} {cy} V{edge}")
        if x != cx:
            dots.add((x, cy))
    return paths, sorted(dots)


def build_cases_html(mode):
    """The lock of the plan with its ten cases around it; each case is a link to its pop-up."""
    palette = charts.get_palette(mode)
    ink, muted, card, accent = palette["strong_text"], palette["reference"], palette["card"], palette["accent"]
    width, height, cx, cy, radius = 1000, 580, 500, 290, 40
    paths, dots = case_lines(cx, cy, radius)
    lines = [
        f'<path d="{d}" fill="none" stroke="{accent}" stroke-width="2" stroke-opacity=".6" stroke-linejoin="miter"/>'
        for d in paths
    ] + [f'<circle cx="{x}" cy="{y}" r="4" fill="{accent}"/>' for x, y in dots]
    nodes = []
    for case in CASES:
        case_id, short, attack, expected, owasp, tests = case
        x, y = CASE_PLACES[case_id]
        tech = TECH[case_id]
        # The text goes outward, away from the lines: above the cases of the upper half, below those of the lower half.
        names = doc_views.wrap(short, 17)[:2]
        if y < cy:
            chip_y, name_ys = y - radius - 12, [y - radius - 32 - 17 * (len(names) - 1 - k) for k in range(len(names))]
        else:
            chip_y, name_ys = y + radius + 22, [y + radius + 42 + 17 * k for k in range(len(names))]
        label = "".join(
            f'<text x="{x}" y="{line_y}" text-anchor="middle" font-size="15.5" fill="{ink}">{esc(line)}</text>'
            for line, line_y in zip(names, name_ys)
        )
        chip = (
            f'<text x="{x}" y="{chip_y}" text-anchor="middle" font-size="15" fill="{muted}">'
            f'<tspan font-weight="700" fill="{ink}">{esc(case_id)}</tspan> · {esc(owasp)}</text>'
        )
        logo = place_logo(doc_views.flat_logo("brand", tech), x - 32, y - 32, 64)
        nodes.append(
            f'<a href="#c-{case_id}" aria-label="{esc(case_id)}: {esc(short)} ({esc(TECH_NAMES[tech])})">'
            f'<title>{esc(case_id)} · {esc(TECH_NAMES[tech])} · {esc(attack)}</title>'
            f'<circle class="node" cx="{x}" cy="{y}" r="{radius}" fill="{card}" stroke="{accent}" stroke-width="2"/>'
            f'{logo}{chip}{label}</a>'
        )
    # D-280: the core is a border with a translucent fill, so it sits on the white sheet and on every theme.
    # The card under it hides the lines that meet at its centre.
    centre = (
        f'<circle cx="{cx}" cy="{cy}" r="96" fill="{accent}" fill-opacity=".08"/>'
        f'<circle cx="{cx}" cy="{cy}" r="82" fill="{card}"/>'
        f'<circle class="core" cx="{cx}" cy="{cy}" r="82" fill="{accent}" fill-opacity=".14" stroke="{accent}" '
        f'stroke-width="2"/>'
        + lock_mark(cx, cy - 14, 64, accent)
        + f'<text x="{cx}" y="{cy + 42}" text-anchor="middle" font-size="18" font-weight="700" fill="{ink}">Plan de pruebas</text>'
        f'<text x="{cx}" y="{cy + 60}" text-anchor="middle" font-size="14" fill="{muted}">{len(CASES)} casos · pytest</text>'
    )
    body = (
        f'<svg class="plan" viewBox="0 0 {width} {height}" role="img" aria-label="Los diez casos de prueba de seguridad" '
        f'font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">{"".join(lines)}{centre}{"".join(nodes)}</svg>'
        '<p class="note">Pulsa un caso para ver su ataque, su resultado esperado y la prueba que lo verifica.</p>'
        + "".join(build_case_modal(case) for case in CASES)
    )
    return wrap_document(palette, body)


def orthogonal(start, end, half_width, half_height, gap=6):
    """The arrow between two boxes with right angles only: straight down or up where the boxes share columns, straight
    across where they share rows, and otherwise out of the side of the first box and down or up into the second."""
    (x1, y1), (x2, y2) = start, end
    down = 1 if y2 > y1 else -1
    if abs(x2 - x1) < 2 * half_width - 40:  # one above the other: a vertical line in the middle of the shared columns
        x = (max(x1, x2) - half_width + min(x1, x2) + half_width) / 2
        return f"M{x:.1f} {y1 + down * half_height:.1f} V{y2 - down * (half_height + gap):.1f}"
    right = 1 if x2 > x1 else -1
    if abs(y2 - y1) < 2 * half_height - 20:  # side by side: a horizontal line in the middle of the shared rows
        y = (y1 + y2) / 2
        return f"M{x1 + right * half_width:.1f} {y:.1f} H{x2 - right * (half_width + gap):.1f}"
    return f"M{x1 + right * half_width:.1f} {y1:.1f} H{x2:.1f} V{y2 - down * (half_height + gap):.1f}"
