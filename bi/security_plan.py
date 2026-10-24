"""«Plan de pruebas de seguridad» (D-258): the ten test cases and the procedure that runs them, as two clickable diagrams.

The cases S-01 to S-10 live here and only here (the document used to hold them in a long table): each is a node around the
lock of the plan, and a click opens its attack, its expected result, its OWASP Top 10 (2021) category, the threat it
belongs to and the test that verifies it. The procedure is a cycle of five steps, as in a software life cycle, with the
way back when a case fails. The pop-ups are CSS sheets opened with :target, with no script; the document anchors itself
(<base href="about:srcdoc">) because in an srcdoc frame a #link would otherwise resolve against the page around it.
"""
import html
import math

from bi import charts, doc_views, quality_view, security_map

# (id, short name, attack, expected result, OWASP code or «—», the tests that verify it)
CASES = [
    ("S-01", "SQL que lee secretos", "19 consultas SQL para leer secretos o escribir archivos", "Rechazada; el secreto nunca aparece", "A03",
     ["tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files"]),
    ("S-02", "Órdenes directas al motor", "9 órdenes directas al motor", "Error de permiso", "A05",
     ["tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed"]),
    ("S-03", "Consultas sin fin", "Consultas sin fin o de millones de filas", "Cortada a los 10 segundos; como máximo 5.000 filas", "A04",
     ["tests/test_sql_explorer.py::test_slow_query_is_interrupted", "tests/test_sql_explorer.py::test_result_is_limited_and_flagged"]),
    ("S-04", "Clave con ñ o emojis", "Clave con ñ, tildes o emojis", "«Clave incorrecta.», sin error", "A07",
     ["tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe"]),
    ("S-05", "Probar claves sin parar", "Probar claves sin parar", "«Clave incorrecta.» cada vez, sin bloqueo: riesgo aceptado por el autor (ver el resumen)", "A07",
     ["tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time"]),
    ("S-06", "Tokens en el repositorio", "Buscar tokens en el repositorio", "Ninguno", "A02",
     ["tests/test_security.py::test_no_secret_is_tracked_by_git"]),
    ("S-07", "Error de GitHub", "Provocar un error de GitHub", "El mensaje nunca muestra el token", "A09",
     ["tests/test_control.py::test_github_error_never_shows_the_token"]),
    ("S-08", "Permisos del workflow", "Abusar de los permisos del workflow", "Solo contenido e issues", "A01",
     ["tests/test_security.py::test_the_weekly_job_has_least_privilege"]),
    ("S-09", "Control sin prueba", "Afirmar un control sin prueba", "Cada control de la arquitectura de seguridad apunta a una prueba que existe", "—",
     ["tests/test_security.py::test_every_control_of_the_map_points_to_a_test_that_exists"]),
    ("S-10", "Pipeline sin la clave", "Lanzar el pipeline sin la clave", "El botón no existe antes de la clave", "A01",
     ["tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code"]),
]
# The procedure: (mark, title, line, how it is done).
SOP_STEPS = [
    ("git", "Preparar", "copia limpia y secreto falso",
     "Clonar el repositorio e instalar requirements.txt. Las pruebas crean su propio secreto falso: el real nunca se usa."),
    ("pytest", "Ejecutar", "los diez casos con pytest",
     "python -m pytest -q tests/test_security.py tests/test_control.py tests/test_sql_explorer.py tests/test_dashboard.py"),
    ("reconcile", "Comprobar", "contra el resultado esperado",
     "Cada caso S-01 a S-10 tiene su resultado esperado en el esquema de casos; cada prueba lo compara y falla si no se cumple."),
    ("github", "Registrar", "la evidencia",
     "La salida de pytest en local y, en GitHub, el resultado de pruebas.yml junto al commit. Toda corrección queda en "
     "docs/DECISIONES.md."),
    ("shield", "Decidir", "pasa o falla",
     "Pasa: el cambio queda verificado. Falla: se corrige y se vuelve al paso 2."),
]
CI_NOTE = "En GitHub, pruebas.yml hace los pasos 2 a 4 en cada push; su resultado avisa, pero no detiene la publicación de main."


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
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"], palette["card"],
                                              palette["card_border"], palette["accent"])
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
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><base href="about:srcdoc"><meta name="viewport" '
            'content="width=device-width,initial-scale=1">' + build_css(palette) + f'</head><body>{quality_view.DEFS}{body}</body></html>')


def build_modal(identifier, title, subtitle, body):
    return (f'<div class="modal" id="{identifier}"><a class="back" href="#" aria-label="Cerrar"></a><div class="sheet" role="dialog" '
            f'aria-label="{esc(title)}"><a class="close" href="#" aria-label="Cerrar">✕</a><h3>{esc(title)}</h3>'
            f'<div class="q">{esc(subtitle)}</div>{body}</div></div>')


def build_case_modal(case):
    case_id, short, attack, expected, owasp, tests = case
    category = f"{owasp} · {security_map.OWASP[owasp]}" if owasp in security_map.OWASP else "No corresponde a una categoría: vigila que cada control tenga su prueba"
    threat = threat_of(case_id)
    belongs = (f"{threat[0]} · {threat[1]}. Lo detiene: {', '.join(threat[2])}." if threat
               else "Ninguna en concreto: es la prueba de que las demás existen.")
    body = (f'<h4>Ataque</h4><p>{esc(attack)}</p><h4>Resultado esperado</h4><p>{esc(expected)}</p>'
            f'<h4>OWASP Top 10 (2021)</h4><p>{esc(category)}</p><h4>Amenaza que cubre</h4><p>{esc(belongs)}</p>'
            f'<h4>Prueba que lo verifica</h4>' + "".join(f"<code>{esc(test)}</code>" for test in tests))
    return build_modal(f"c-{case_id}", f"{case_id} · {short}", "Se repite en cada push y pull request.", body)


def lock_mark(cx, cy, size):
    return security_map.lock_mark(cx - size / 2, cy - size / 2, size)


def build_cases_html(mode):
    """The lock of the plan with its ten cases around it; each case is a link to its pop-up."""
    palette = charts.get_palette(mode)
    ink, muted, card, accent = palette["strong_text"], palette["reference"], palette["card"], palette["accent"]
    width, height, cx, cy, rx, ry = 1000, 560, 500, 280, 392, 196
    lines, nodes = [], []
    for index, case in enumerate(CASES):
        angle = math.radians(-90 + index * 36)
        x, y = cx + rx * math.cos(angle), cy + ry * math.sin(angle)
        case_id, short, attack, expected, owasp, tests = case
        lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{accent}" stroke-width="1.6" stroke-opacity=".55"/>')
        label = "".join(f'<text x="{x:.1f}" y="{y + 54 + 17 * k:.1f}" text-anchor="middle" font-size="15.5" fill="{ink}">{esc(line)}</text>'
                        for k, line in enumerate(doc_views.wrap(short, 17)[:2]))
        nodes.append(f'<a href="#c-{case_id}" aria-label="{esc(case_id)}: {esc(short)}"><title>{esc(case_id)} · {esc(attack)}</title>'
                     f'<circle class="node" cx="{x:.1f}" cy="{y:.1f}" r="38" fill="{card}" stroke="{accent}" stroke-width="2"/>'
                     f'<text x="{x:.1f}" y="{y - 1:.1f}" text-anchor="middle" font-size="18" font-weight="700" fill="{ink}">{esc(case_id)}</text>'
                     f'<text x="{x:.1f}" y="{y + 18:.1f}" text-anchor="middle" font-size="14" fill="{muted}">{esc(owasp)}</text>{label}</a>')
    centre = (f'<defs><radialGradient id="plan-core" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="#4a8df0"/>'
              f'<stop offset="1" stop-color="#0d3b96"/></radialGradient></defs>'
              f'<circle cx="{cx}" cy="{cy}" r="96" fill="{accent}" fill-opacity=".14"/>'
              f'<circle class="core" cx="{cx}" cy="{cy}" r="82" fill="url(#plan-core)"/>' + lock_mark(cx, cy - 14, 64)
              + f'<text x="{cx}" y="{cy + 42}" text-anchor="middle" font-size="18" font-weight="700" fill="#fff">Plan de pruebas</text>'
              f'<text x="{cx}" y="{cy + 60}" text-anchor="middle" font-size="14" fill="#cfe0ff">{len(CASES)} casos · pytest</text>')
    body = (f'<svg class="plan" viewBox="0 0 {width} {height}" role="img" aria-label="Los diez casos de prueba de seguridad" '
            f'font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">{"".join(lines)}{centre}{"".join(nodes)}</svg>'
            '<p class="note">Pulsa un caso para ver su ataque, su resultado esperado y la prueba que lo verifica.</p>'
            + "".join(build_case_modal(case) for case in CASES))
    return wrap_document(palette, body)


def trim(start, end, half_width, half_height, gap=8):
    """The segment between two centres, shortened to the edges of their boxes."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    scale = min((half_width + gap) / abs(dx) if dx else 9e9, (half_height + gap) / abs(dy) if dy else 9e9)
    return ((start[0] + dx * scale, start[1] + dy * scale), (end[0] - dx * scale, end[1] - dy * scale))


def build_cycle_html(mode):
    """The procedure as a cycle of five steps, with the way back to step 2 when a case fails."""
    palette = charts.get_palette(mode)
    ink, muted, card, accent = palette["strong_text"], palette["reference"], palette["card"], palette["accent"]
    width, height, cx, cy, rx, ry = 1000, 420, 500, 204, 352, 132
    box_w, box_h = 240, 88
    centres = []
    for index in range(len(SOP_STEPS)):
        angle = math.radians(-90 + index * 72)
        centres.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
    arrows, steps, modals = [], [], []
    for index, (mark, title, line, how) in enumerate(SOP_STEPS):
        x, y = centres[index]
        if index < len(SOP_STEPS) - 1:
            (x1, y1), (x2, y2) = trim(centres[index], centres[index + 1], box_w / 2, box_h / 2)
            arrows.append(f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="{accent}" stroke-width="3" marker-end="url(#cy-head)"/>')
        icon = (doc_views.disc_logo("brand", mark) if mark in doc_views.DISCS else quality_view.build_icon_svg(mark)
                ).replace('<svg class="logo" ', f'<svg x="{x - box_w / 2 + 12:.1f}" y="{y - 22:.1f}" width="48" height="48" ', 1
                          ).replace('<svg class="qa-icon" ', f'<svg x="{x - box_w / 2 + 12:.1f}" y="{y - 24:.1f}" width="48" height="48" ', 1)
        steps.append(f'<a href="#p-{index}" aria-label="Paso {index + 1}: {esc(title)}"><title>{index + 1} · {esc(title)}: {esc(line)}</title>'
                     f'<rect class="node" x="{x - box_w / 2:.1f}" y="{y - box_h / 2:.1f}" width="{box_w}" height="{box_h}" rx="{box_h / 2}" '
                     f'fill="{card}" stroke="{accent}" stroke-width="2"/>{icon}'
                     f'<text x="{x - box_w / 2 + 68:.1f}" y="{y - 6:.1f}" font-size="19" font-weight="700" fill="{ink}">{index + 1} · {esc(title)}</text>'
                     + "".join(f'<text x="{x - box_w / 2 + 68:.1f}" y="{y + 16 + 16 * k:.1f}" font-size="14.5" fill="{muted}">{esc(part)}</text>'
                               for k, part in enumerate(doc_views.wrap(line, 22)[:2])) + '</a>')
        modals.append(build_modal(f"p-{index}", f"{index + 1} · {title}", line, f'<h4>Cómo se hace</h4><p>{esc(how)}</p>'
                                  + ("<h4>Qué pasa después</h4><p>Pasa: el cambio queda verificado. Falla: se corrige y se vuelve al paso 2.</p>"
                                     if index == len(SOP_STEPS) - 1 else "")))
    # The way back: when a case fails, the change is fixed and the run repeats from step 2.
    (bx, by), (ex, ey) = centres[-1], centres[1]
    back = (f'<path d="M{bx + box_w / 2 + 8:.1f} {by:.1f} L{ex - box_w / 2 - 8:.1f} {ey:.1f}" stroke="#d9a400" stroke-width="2.4" '
            f'stroke-dasharray="7 6" marker-end="url(#cy-head-fail)"/>')
    middle = (f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="16" font-weight="600" fill="#d9a400">falla: se corrige y se repite desde el 2</text>'
              f'<text x="{cx}" y="{cy + 26}" text-anchor="middle" font-size="26" font-weight="700" fill="{ink}">Procedimiento</text>'
              f'<text x="{cx}" y="{cy + 50}" text-anchor="middle" font-size="16" fill="{muted}">pasa: el cambio queda verificado ✓</text>')
    defs = (f'<defs><marker id="cy-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
            f'<path d="M0 0 10 5 0 10z" fill="{accent}"/></marker><marker id="cy-head-fail" viewBox="0 0 10 10" refX="8" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 10 5 0 10z" fill="#d9a400"/></marker></defs>')
    body = (f'<svg class="plan" viewBox="0 0 {width} {height}" role="img" aria-label="Procedimiento de pruebas de seguridad" '
            f'font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">{defs}{"".join(arrows)}{back}{middle}{"".join(steps)}</svg>'
            f'<p class="note">{esc(CI_NOTE)} Pulsa un paso para ver cómo se hace.</p>' + "".join(modals))
    return wrap_document(palette, body)
