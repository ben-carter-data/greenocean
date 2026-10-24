"""«Arquitectura de seguridad» (D-200, D-249): the threat model of GreenOcean, read as a process.

Each row is one threat, from left to right: the threat and its OWASP Top 10 (2021) category, the controls that mitigate
it, the automated test cases that verify those controls on every push (S-01 to S-10 of docs/SEGURIDAD.md) and the
asset it protects. Under the rows, the loop of continuous improvement that produced every control: review, attack as an
intruder, fix before publishing, turn the attack into a test, repeat it on every push. The platform's own sign-in is
dashed and labelled as declared by the author, because the repository cannot verify it. Secret values never appear.

build_security_html() returns one HTML document for st.iframe (CSS only, no script).
"""
import html

from bi import charts, doc_views, quality_view, storage_map

WIDTH, HEIGHT = 1000, 620
# Controls: (number, title, short line, what it protects, how, files, tests, verifiable in the repository).
CONTROLS = [
    (1, "SQL público con límites", "una sentencia de lectura · sin archivos ni web · 10 s · 5.000 filas · 1 GB",
     "Las tablas de precios y el servidor. El estudio SQL está abierto a cualquier visitante: los datos son públicos.",
     "La consulta debe ser una sola sentencia SELECT o WITH, sin funciones que lean archivos ni direcciones web; se corta a "
     "los 10 segundos, devuelve como máximo 5.000 filas y usa como máximo 1 GB de memoria.",
     "bi/sql_explorer.py",
     ["tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files",
      "tests/test_sql_explorer.py::test_slow_query_is_interrupted"], True),
    (2, "Base en solo lectura", "motor sin acceso externo · configuración bloqueada",
     "La base servida: nadie puede cambiar un dato desde el panel.",
     "DuckDB abre etl/datos.duckdb en solo lectura, sin acceso a archivos ni a internet y con la configuración bloqueada: "
     "aunque una consulta esquivara el filtro, el motor responde «Permission Error».",
     "bi/queries.py · bi/sql_explorer.py",
     ["tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed"], True),
    (3, "Clave de control", "evita ejecuciones accidentales · tiempo constante",
     "El botón «Ejecutar pipeline ahora»: con él, lo máximo que se puede hacer es lanzar el workflow semanal.",
     "La clave vive en los secretos del panel, fuera del repositorio, y se compara con hmac.compare_digest. Antes de la "
     "clave el botón no existe. No hay límite de intentos: riesgo aceptado por el autor.",
     "bi/control.py · bi/dashboard.py",
     ["tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe",
      "tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code"], True),
    (4, "Token protegido", "nunca en pantalla ni en los errores · aviso antes de vencer",
     "El token de GitHub con el que el panel lanza el workflow.",
     "Vive en los secretos del panel. Los errores de GitHub se describen con su código y su causa, nunca con el token, "
     "los encabezados ni la dirección completa; el panel avisa cuando faltan menos de 14 días para que venza.",
     "bi/control.py",
     ["tests/test_control.py::test_github_error_never_shows_the_token",
      "tests/test_control.py::test_t54_token_warning_is_highlighted_under_14_days"], True),
    (5, "Ningún secreto en Git", "el repositorio es público",
     "Las claves: el código se puede leer sin cuenta.",
     ".gitignore excluye los secretos y una prueba busca tokens en cada archivo versionado.",
     ".gitignore",
     ["tests/test_security.py::test_no_secret_is_tracked_by_git"], True),
    (6, "Privilegio mínimo del job", "solo contents e issues",
     "El repositorio y la cuenta: el job semanal no puede hacer más que lo que necesita.",
     "El workflow semanal solo puede escribir contenido (el commit de la base) y crear issues (el informe).",
     ".github/workflows/semanal.yml",
     ["tests/test_security.py::test_the_weekly_job_has_least_privilege"], True),
    (7, "Inicio de sesión externo", "declarado por el autor · no verificable en el repositorio",
     "Administrar GitHub y Streamlit Community Cloud: ejecutar el workflow desde GitHub, cambiar secretos o reiniciar la app.",
     "Ambas plataformas piden iniciar sesión con la cuenta del autor. Es una configuración de GitHub y de Streamlit Cloud: "
     "declarada por el autor y no verificable desde el repositorio.",
     "", [], False),
]
# Threats: (id, threat, OWASP categories, numbers of its controls, its test cases in docs/SEGURIDAD.md, asset (mark, name)).
THREATS = [
    ("T1", "Leer secretos o archivos del servidor con SQL", "A03 · A05", [1, 2], ["S-01", "S-02"],
     ("duckdb", "Servidor y base servida")),
    ("T2", "Colgar el panel con consultas pesadas", "A04", [1], ["S-03"], ("streamlit", "Disponibilidad del panel")),
    ("T3", "Lanzar el pipeline sin permiso", "A01 · A07", [3], ["S-04", "S-05", "S-10"], ("github", "Workflow semanal")),
    ("T4", "Robar el token o la clave", "A02 · A09", [4, 5], ["S-06", "S-07"], ("lock", "Secretos")),
    ("T5", "Abusar de los permisos del workflow", "A01", [6], ["S-08"], ("git", "Repositorio")),
    ("T6", "Tomar la administración de GitHub o Streamlit", "A07", [7], [], ("author", "Cuentas del autor")),
]
OWASP = {"A01": "Pérdida de control de acceso", "A02": "Fallas criptográficas", "A03": "Inyección",
         "A04": "Diseño inseguro", "A05": "Configuración de seguridad incorrecta",
         "A07": "Fallas de identificación y autenticación", "A09": "Fallas en el registro y el monitoreo"}
# The loop of continuous improvement, as docs/SEGURIDAD.md «3. Método» describes it: (title, line, detail).
LOOP = [
    ("Revisar", "puertas y activos", "Inventario de lo que se alcanza desde internet y de lo que protege, con el OWASP Top 10 como guía."),
    ("Atacar", "como un intruso", "Cada puerta se ataca con el código del panel y un secreto falso, nunca el real."),
    ("Corregir", "antes de publicar", "Cada hallazgo se corrige antes de publicar y queda en docs/DECISIONES.md (por ejemplo D-199)."),
    ("Probar", "el ataque es una prueba", "Cada ataque se vuelve una prueba automática en tests/: S-01 a S-10."),
    ("Repetir", "en cada push", "pruebas.yml corre todas las pruebas en cada push y pull request."),
]
COLUMNS = (("Amenaza · OWASP", 20), ("Mitigación", 312), ("Verificación", 622), ("Activo protegido", 832))
ROW_TOP, ROW_HEIGHT, ROW_GAP = 46, 58, 8
CARDS = {"threat": (20, 262), "mitigation": (312, 282), "verification": (622, 180), "asset": (832, 150)}
LOOP_TOP = 470


def esc(value):
    return html.escape(str(value))


def wrap(text, width):
    return doc_views.wrap(text, width)


def lock_mark(x, y, size):
    """The secrets: a padlock on a lit disc."""
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 72 72" aria-hidden="true"><defs>'
            '<radialGradient id="disc-lock-map" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="#b9a7ff"/>'
            '<stop offset="1" stop-color="#5b3fd1"/></radialGradient></defs><circle cx="36" cy="36" r="31" '
            'fill="url(#disc-lock-map)"/><rect x="24" y="33" width="24" height="18" rx="4" fill="#fff"/>'
            '<path d="M28 33v-5a8 8 0 0 1 16 0v5" fill="none" stroke="#fff" stroke-width="4"/>'
            '<circle cx="36" cy="41" r="2.6" fill="#5b3fd1"/></svg>')


def asset_mark(mark, x, y, size):
    if mark == "lock":
        return lock_mark(x, y, size)
    if mark in ("duckdb", "sqlite"):
        return storage_map.cylinder(x + 3, y, size - 6, size, mark, "sec-asset", glyph_size=13)
    kind = "person" if mark == "author" else "brand"
    return doc_views.disc_logo(kind, mark).replace('<svg class="logo" ', f'<svg x="{x}" y="{y}" width="{size}" height="{size}" ', 1)


def icon(name, x, y, size):
    return quality_view.build_icon_svg(name).replace('<svg class="qa-icon" ', f'<svg x="{x}" y="{y}" width="{size}" height="{size}" ', 1)


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    shadow = "rgba(0,0,0,.4)" if dark else "rgba(15,39,71,.14)"
    hovers = "".join(f"svg:has(#row-{t[0]}:hover, #row-{t[0]}:focus) #tip-{t[0]} {{ opacity:1; }}" for t in THREATS)
    hovers += "".join(f"svg:has(#loop-{index}:hover, #loop-{index}:focus) #tip-loop-{index} {{ opacity:1; }}"
                      for index in range(len(LOOP)))
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
svg.sec {{ display:block; width:100%; height:auto; overflow:visible; }}
.col {{ font-size:12.5px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; fill:{ink}; }}
.card {{ fill:{card}; stroke:{border}; stroke-width:1.1; filter:drop-shadow(0 6px 8px {shadow}); }}
.card.threat {{ stroke:#e0703a; }}
.card.declared {{ stroke-dasharray:5 4; }}
.row {{ outline:none; cursor:default; }}
.row:hover .card, .row:focus .card {{ stroke:{accent}; }}
.tid {{ font-size:12px; font-weight:700; fill:#e0703a; }}
.owasp {{ font-size:12px; fill:{muted}; }}
.title {{ font-size:13.5px; font-weight:600; fill:{ink}; }}
.detail {{ font-size:12.5px; fill:{muted}; }}
.case {{ font:600 12.5px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{ink}; }}
.line {{ fill:none; stroke:{accent}; stroke-width:1.8; }}
.num circle {{ fill:#22b35a; }}
.num.declared circle {{ fill:none; stroke:#8a94a6; stroke-width:1.6; stroke-dasharray:3 2; }}
.num text {{ font-size:11.5px; font-weight:700; fill:#fff; text-anchor:middle; }}
.num.declared text {{ fill:{ink}; }}
.band {{ fill:{'rgba(255,255,255,.025)' if dark else 'rgba(15,39,71,.03)'}; stroke:{border}; stroke-dasharray:6 6; }}
.band-title {{ font-size:12.5px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; fill:{ink}; }}
.band-sub {{ font-size:12.5px; fill:{muted}; }}
.step {{ outline:none; cursor:default; }}
.step:hover .card, .step:focus .card {{ stroke:{accent}; }}
.step-n {{ font-size:12px; font-weight:700; fill:{accent}; }}
.loop-label {{ font-size:12.5px; fill:{ink}; paint-order:stroke; stroke:{palette['background']}; stroke-width:5px; }}
.tip {{ opacity:0; pointer-events:none; transition:opacity .15s ease; }}
.tip div {{ position:absolute; width:330px; padding:12px 14px; border-radius:14px; background:{card}; border:1px solid {border};
  box-shadow:0 18px 40px rgba(0,0,0,{'.55' if dark else '.2'}); color:{text}; font-size:12.5px; line-height:1.45; }}
.tip b {{ display:block; margin:8px 0 2px; font-size:11px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{muted}; }}
.tip b:first-child {{ margin-top:0; font-size:13px; letter-spacing:0; text-transform:none; color:{ink}; }}
.tip code {{ font:400 11.5px ui-monospace, SFMono-Regular, Menlo, monospace; color:{ink}; overflow-wrap:anywhere; }}
@media print {{ .tip {{ display:none !important; }} }}
{hovers}
</style>"""


def number_mark(number, x, y, declared):
    return (f'<g class="num{" declared" if declared else ""}"><circle cx="{x}" cy="{y}" r="10"/>'
            f'<text x="{x}" y="{y + 4}">{number}</text></g>')


def build_row(index, threat, controls):
    tid, title, owasp, numbers, cases, (mark, asset) = threat
    top = ROW_TOP + index * (ROW_HEIGHT + ROW_GAP)
    middle = top + ROW_HEIGHT / 2
    declared = any(not controls[n][7] for n in numbers)
    parts = []
    # Amenaza
    x, w = CARDS["threat"]
    parts.append(f'<rect class="card threat" x="{x}" y="{top}" width="{w}" height="{ROW_HEIGHT}" rx="12"/>'
                 + icon("warning", x + 8, top + 13, 32)
                 + f'<text class="tid" x="{x + 48}" y="{top + 18}">{tid}</text>'
                 f'<text class="owasp" x="{x + 72}" y="{top + 18}">OWASP {esc(owasp)}</text>')
    for offset, line in enumerate(wrap(title, 30)[:2]):
        parts.append(f'<text class="title" x="{x + 48}" y="{top + 35 + offset * 16}">{esc(line)}</text>')
    # Mitigación
    mx, mw = CARDS["mitigation"]
    parts.append(f'<rect class="card{" declared" if declared else ""}" x="{mx}" y="{top}" width="{mw}" height="{ROW_HEIGHT}" rx="12"/>'
                 + icon("shield", mx + 8, top + 13, 32))
    for offset, number in enumerate(numbers[:2]):
        control = controls[number]
        y = top + (22 if len(numbers) > 1 else 24) + offset * 22
        parts.append(number_mark(number, mx + 58, y - 4, not control[7])
                     + f'<text class="title" x="{mx + 74}" y="{y}">{esc(control[1])}</text>')
    if len(numbers) == 1:
        # The control's short line, whole segments only, never cut in the middle of a phrase.
        shown = ""
        for segment in controls[numbers[0]][2].split(" · "):
            candidate = f"{shown} · {segment}" if shown else segment
            if len(candidate) > 36:
                break
            shown = candidate
        parts.append(f'<text class="detail" x="{mx + 48}" y="{top + 44}">{esc(shown)}</text>')
    # Verificación
    vx, vw = CARDS["verification"]
    parts.append(f'<rect class="card{" declared" if not cases else ""}" x="{vx}" y="{top}" width="{vw}" height="{ROW_HEIGHT}" rx="12"/>')
    if cases:
        parts.append(doc_views.disc_logo("brand", "pytest").replace(
            '<svg class="logo" ', f'<svg x="{vx + 8}" y="{top + 13}" width="32" height="32" ', 1))
        parts.append(f'<text class="case" x="{vx + 48}" y="{top + 25}">{esc(" · ".join(cases))}</text>'
                     f'<text class="detail" x="{vx + 48}" y="{top + 43}">en cada push</text>')
    else:
        parts.append(f'<text class="title" x="{vx + 12}" y="{top + 25}">No verificable aquí</text>'
                     f'<text class="detail" x="{vx + 12}" y="{top + 43}">declarado por el autor</text>')
    # Activo protegido
    ax, aw = CARDS["asset"]
    parts.append(f'<rect class="card" x="{ax}" y="{top}" width="{aw}" height="{ROW_HEIGHT}" rx="12"/>' + asset_mark(mark, ax + 8, top + 13, 32))
    for offset, line in enumerate(wrap(asset, 14)[:2]):
        parts.append(f'<text class="title" x="{ax + 48}" y="{top + (29 if len(wrap(asset, 14)) == 1 else 25) + offset * 16}">{esc(line)}</text>')
    # The process, left to right.
    for left, right in (("threat", "mitigation"), ("mitigation", "verification"), ("verification", "asset")):
        start = CARDS[left][0] + CARDS[left][1]
        parts.append(f'<path class="line" d="M{start} {middle} L{CARDS[right][0] - 2} {middle}" marker-end="url(#sec-head)"/>')
    return f'<g class="row" id="row-{tid}" tabindex="0">{"".join(parts)}</g>'


def build_row_tip(index, threat, controls):
    tid, title, owasp, numbers, cases, (mark, asset) = threat
    top = ROW_TOP + index * (ROW_HEIGHT + ROW_GAP)
    above = index >= 3
    categories = "; ".join(f"{code} {OWASP[code]}" for code in owasp.split(" · "))
    mitigation = "".join(f"<br>{n} · {esc(controls[n][1])}: {esc(controls[n][4])}" for n in numbers)
    tests = sorted({test for n in numbers for test in controls[n][6]})
    evidence = ("".join(f"<br><code>{esc(test)}</code>" for test in tests) if tests
                else "<br>Ninguna: es una configuración de GitHub y de Streamlit Cloud, no del repositorio.")
    return (f'<g class="tip" id="tip-{tid}"><foreignObject x="{CARDS["mitigation"][0]:.0f}" '
            f'y="{(top - 8) if above else (top + ROW_HEIGHT + 8):.0f}" width="330" height="1" overflow="visible">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" style="{"bottom:0" if above else "top:0"}"><b>{tid} · {esc(title)}</b>'
            f'<b>OWASP Top 10 (2021)</b>{esc(categories)}<b>Mitigación</b>{mitigation.removeprefix("<br>")}'
            f'<b>Activo protegido</b>{esc(asset)}: {esc(controls[numbers[0]][3])}'
            f'<b>Verificación · {esc(", ".join(cases) or "sin prueba")}</b>{evidence.removeprefix("<br>")}</div></foreignObject></g>')


def build_loop():
    """The loop of continuous improvement: five steps and the way back to the first."""
    top = LOOP_TOP
    width, gap, left = 170, 22, 20
    parts = [f'<rect class="band" x="12" y="{top}" width="976" height="146" rx="18"/>'
             f'<text class="band-title" x="30" y="{top + 24}">Mejora continua</text>'
             f'<text class="band-sub" x="30" y="{top + 41}">así se llegó a cada control y así se mantiene</text>']
    tips = []
    for index, (title, line, detail) in enumerate(LOOP):
        x = left + 20 + index * (width + gap)
        y = top + 54
        parts.append(f'<g class="step" id="loop-{index}" tabindex="0"><rect class="card" x="{x}" y="{y}" width="{width}" height="58" rx="12"/>'
                     f'<text class="step-n" x="{x + 12}" y="{y + 22}">{index + 1}</text>'
                     f'<text class="title" x="{x + 28}" y="{y + 22}">{esc(title)}</text>'
                     f'<text class="detail" x="{x + 12}" y="{y + 42}">{esc(line)}</text></g>')
        if index < len(LOOP) - 1:
            parts.append(f'<path class="line" d="M{x + width} {y + 29} L{x + width + gap - 2} {y + 29}" marker-end="url(#sec-head)"/>')
        tx = min(max(x + width / 2 - 165, 8), WIDTH - 338)
        tips.append(f'<g class="tip" id="tip-loop-{index}"><foreignObject x="{tx:.0f}" y="{y - 8}" width="330" height="1" '
                    f'overflow="visible"><div xmlns="http://www.w3.org/1999/xhtml" style="bottom:0"><b>{index + 1} · {esc(title)}</b>'
                    f'{esc(detail)}</div></foreignObject></g>')
    first = left + 20 + width / 2
    last = left + 20 + (len(LOOP) - 1) * (width + gap) + width / 2
    bottom = top + 54 + 58
    parts.append(f'<path class="line" d="M{last} {bottom} V{bottom + 20} H{first} V{bottom + 2}" marker-end="url(#sec-head)"/>'
                 f'<text class="loop-label" x="{(first + last) / 2}" y="{bottom + 24}" text-anchor="middle">'
                 'cada revisión vuelve a empezar</text>')
    return "".join(parts), "".join(tips)


def build_security_html(palette):
    """The threats, each from its mitigation to its verification and its asset, and the loop that keeps them."""
    controls = {control[0]: control for control in CONTROLS}
    head = (f'<defs><marker id="sec-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>')
    columns = "".join(f'<text class="col" x="{x}" y="28">{esc(name)}</text>' for name, x in COLUMNS)
    rows = "".join(build_row(index, threat, controls) for index, threat in enumerate(THREATS))
    tips = "".join(build_row_tip(index, threat, controls) for index, threat in enumerate(THREATS))
    loop, loop_tips = build_loop()
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body>{quality_view.DEFS}<svg class="sec" viewBox="0 0 {WIDTH} {HEIGHT}" '
            f'preserveAspectRatio="xMidYMid meet" role="img" aria-label="Arquitectura de seguridad">{head}{columns}{rows}{loop}'
            f'{tips}{loop_tips}</svg></body></html>')
