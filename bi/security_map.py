"""«Arquitectura de seguridad» (D-200, D-249, D-254): GreenOcean as a network of trust zones.

The drawing is a topology like a security network diagram: the Internet with its two kinds of people, the Streamlit
Community Cloud zone (a public part, open to anyone, and the author's part, behind the control code), the GitHub zone
and, at the bottom, the loop of continuous improvement. Every piece is a real one of this project. The numbered green
badges are the controls (CONTROLS), the red triangles the threats T1 to T6 (THREATS, OWASP Top 10 2021) placed on the
path where each one acts, and under each piece the cases S-01 to S-14 of docs/PLAN_PRUEBAS.md that verify it on every
push. The platform's own sign-in is dashed and labelled as declared by the author, because the repository cannot
verify it. Secret values never appear.

build_security_html() returns one HTML document for st.iframe (CSS only, no script).
"""

import html

from bi import charts, doc_views, quality_view, storage_map

# Controls: (number, title, short line, what it protects, how, files, tests, verifiable in the repository).
CONTROLS = [
    (
        1,
        "SQL público con límites",
        "una sentencia de lectura · sin archivos ni web · 10 s · 5.000 filas · 1 GB",
        "Las tablas de precios y el servidor. El estudio SQL está abierto a cualquier visitante: los datos son públicos.",
        "La consulta debe ser una sola sentencia SELECT o WITH, sin funciones que lean archivos ni direcciones web; se corta a "
        "los 10 segundos, devuelve como máximo 5.000 filas y usa como máximo 1 GB de memoria.",
        "bi/sql_explorer.py",
        [
            "tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files",
            "tests/test_sql_explorer.py::test_slow_query_is_interrupted",
        ],
        True,
    ),
    (
        2,
        "Base en solo lectura",
        "motor sin acceso externo · configuración bloqueada",
        "La base servida: nadie puede cambiar un dato desde el panel.",
        "DuckDB abre etl/datos.duckdb en solo lectura, sin acceso a archivos ni a internet y con la configuración bloqueada: "
        "aunque una consulta esquivara el filtro, el motor responde «Permission Error».",
        "bi/queries.py · bi/sql_explorer.py",
        ["tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed"],
        True,
    ),
    (
        3,
        "Clave de control",
        "evita ejecuciones accidentales · tiempo constante",
        "El botón «Ejecutar pipeline ahora»: con él, lo máximo que se puede hacer es lanzar el workflow semanal.",
        "La clave vive en los secretos del panel, fuera del repositorio, y se compara con hmac.compare_digest. Antes de la "
        "clave el botón no existe. No hay límite de intentos: riesgo aceptado por el autor.",
        "bi/control.py · bi/dashboard.py",
        [
            "tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe",
            "tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code",
        ],
        True,
    ),
    (
        4,
        "Token protegido",
        "nunca en pantalla ni en los errores · aviso antes de vencer",
        "El token de GitHub con el que el panel lanza el workflow.",
        "Vive en los secretos del panel. Los errores de GitHub se describen con su código y su causa, nunca con el token, "
        "los encabezados ni la dirección completa; el panel avisa cuando faltan menos de 14 días para que venza.",
        "bi/control.py",
        [
            "tests/test_control.py::test_github_error_never_shows_the_token",
            "tests/test_control.py::test_t54_token_warning_is_highlighted_under_14_days",
        ],
        True,
    ),
    (
        5,
        "Ningún secreto en Git",
        "el repositorio es público",
        "Las claves: el código se puede leer sin cuenta.",
        ".gitignore excluye los secretos y una prueba busca tokens en cada archivo versionado.",
        ".gitignore",
        ["tests/test_security.py::test_no_secret_is_tracked_by_git"],
        True,
    ),
    (
        6,
        "Privilegio mínimo del job",
        "solo contents e issues",
        "El repositorio y la cuenta: el job semanal no puede hacer más que lo que necesita.",
        "El workflow semanal solo puede escribir contenido (la base en el release y su puntero) y crear issues (el informe).",
        ".github/workflows/semanal.yml",
        ["tests/test_security.py::test_the_weekly_job_has_least_privilege"],
        True,
    ),
    (
        7,
        "Inicio de sesión externo",
        "declarado por el autor · no verificable en el repositorio",
        "Administrar GitHub y Streamlit Community Cloud: ejecutar el workflow desde GitHub, cambiar secretos o reiniciar la app.",
        "Ambas plataformas piden iniciar sesión con la cuenta del autor. Es una configuración de GitHub y de Streamlit Cloud: "
        "declarada por el autor y no verificable desde el repositorio.",
        "",
        [],
        False,
    ),
]
# Threats: (id, threat, OWASP categories, numbers of its controls, its test cases in docs/PLAN_PRUEBAS.md, asset (mark, name)).
THREATS = [
    (
        "T1",
        "Leer secretos o archivos del servidor con SQL",
        "A03 · A05",
        [1, 2],
        ["S-01", "S-02"],
        ("duckdb", "Servidor y base servida"),
    ),
    ("T2", "Colgar el panel con consultas pesadas", "A04", [1], ["S-03"], ("streamlit", "Disponibilidad del panel")),
    (
        "T3",
        "Lanzar el pipeline sin permiso",
        "A01 · A07",
        [3],
        ["S-04", "S-05", "S-10"],
        ("github", "Workflow semanal"),
    ),
    ("T4", "Robar el token o la clave", "A02 · A09", [4, 5], ["S-06", "S-07"], ("lock", "Secretos")),
    ("T5", "Abusar de los permisos del workflow", "A01", [6], ["S-08"], ("git", "Repositorio")),
    ("T6", "Tomar la administración de GitHub o Streamlit", "A07", [7], [], ("author", "Cuentas del autor")),
]
OWASP = {
    "A01": "Pérdida de control de acceso",
    "A02": "Fallas criptográficas",
    "A03": "Inyección",
    "A04": "Diseño inseguro",
    "A05": "Configuración de seguridad incorrecta",
    "A07": "Fallas de identificación y autenticación",
    "A09": "Fallas en el registro y el monitoreo",
}
# The loop of continuous improvement, as the procedure of docs/PLAN_PRUEBAS.md describes it: (title, line, detail).
LOOP = [
    (
        "Revisar",
        "puertas y activos",
        "Inventario de lo que se alcanza desde internet y de lo que protege, con el OWASP Top 10 como guía.",
    ),
    ("Atacar", "como un intruso", "Cada puerta se ataca con el código del panel y un secreto falso, nunca el real."),
    (
        "Corregir",
        "antes de publicar",
        "Cada hallazgo se corrige antes de publicar y queda en docs/DECISIONES.md (por ejemplo D-199).",
    ),
    ("Probar", "el ataque es una prueba", "Cada ataque se vuelve una prueba automática en tests/: S-01 a S-14."),
    ("Repetir", "en cada push", "pruebas.yml corre todas las pruebas en cada push y pull request."),
]
WIDTH, HEIGHT = 1000, 676
# Pieces of the topology: key -> (kind, centre x, centre y, title, line, control number or None, label x, wrap, cases).
NODES = {
    "visitor": ("person:visitor", 120, 56, "Visitante", "cualquier persona, sin cuenta", None, 152, 30, ""),
    "author": ("person:author", 400, 56, "Administrador", "el autor del proyecto", None, 432, 30, ""),
    "gate": (
        "gate",
        720,
        56,
        "Inicio de sesión de GitHub y Streamlit",
        "declarado por el autor · no verificable aquí",
        7,
        752,
        30,
        "",
    ),
    "panel": ("brand:streamlit", 120, 215, "Panel web", "Streamlit · solo lectura", None, 152, 30, ""),
    "filter": (
        "icon:shield",
        120,
        300,
        "Filtro de consultas",
        "una sentencia · sin archivos ni web · 10 s · 5.000 filas",
        1,
        152,
        30,
        "S-01 · S-03",
    ),
    "engine": (
        "brand:duckdb",
        120,
        385,
        "Motor DuckDB",
        "sin acceso externo · configuración bloqueada",
        2,
        152,
        30,
        "S-02",
    ),
    "base": ("cylinder", 120, 470, "datos.duckdb", "la base servida, tomada del release", None, 152, 30, ""),
    "code": ("lock", 400, 215, "Clave de control", "evita ejecuciones accidentales", 3, 432, 22, "S-04 · S-05 · S-10"),
    "secrets": ("lock", 400, 300, "Secretos del panel", "token de GitHub y clave de control", 4, 432, 22, "S-07"),
    "ci": (
        "brand:pytest",
        640,
        215,
        "pruebas.yml · pytest",
        "ataca cada control en cada push y pull request",
        None,
        672,
        44,
        "S-01 a S-14",
    ),
    "repo": (
        "brand:git",
        640,
        300,
        "Repositorio público",
        "sin ningún secreto · Streamlit despliega la rama main",
        5,
        672,
        44,
        "S-06",
    ),
    "workflow": (
        "brand:github",
        640,
        395,
        "Workflow semanal",
        "la carga de cada martes · solo escribe contenido e issues",
        6,
        672,
        44,
        "S-08",
    ),
}
NODE_TIPS = {
    "visitor": "Cualquier persona con el enlace público. Lee el panel y usa el estudio SQL sin iniciar sesión: los datos son públicos.",
    "author": "El autor. Mantiene el código y los secretos; para lanzar la carga a mano desde el panel usa la clave de control.",
    "panel": "La aplicación de Streamlit (bi/dashboard.py). Lee etl/datos.duckdb en solo lectura: ninguna página puede cambiar un dato.",
    "base": "etl/datos.duckdb: la base servida. Solo se publica si pasan las 31 pruebas de dbt y la carga lee al menos el 90 % de las filas de la anterior.",
    "ci": "El workflow pruebas.yml corre pytest en cada push y pull request: los casos S-01 a S-14 de docs/PLAN_PRUEBAS.md. Su resultado avisa; no detiene la publicación de main.",
}
# Threat markers: threat id -> (x, y, line label, label side).
THREAT_SPOTS = {
    "T1": (120, 258),
    "T2": (120, 112),
    "T3": (400, 112),
    "T4": (364, 352),
    "T5": (622, 430),
    "T6": (696, 32),
}
# Straight links: (path, dashed, label (x, y, text) or None).
LINKS = [
    ("M120 78 V191", False, (156, 116, "consulta SQL")),
    ("M120 237 V277", False, (156, 262, "una sentencia")),
    ("M120 322 V362", False, None),
    ("M120 407 V443", False, None),
    ("M400 78 V191", False, (436, 116, "HTTPS · clave")),
    ("M400 237 V277", False, None),
    ("M400 322 V395 H618", False, (424, 388, "API de GitHub")),
    ("M640 417 V322", False, (656, 352, "release de la base")),
    ("M640 278 V237", False, (656, 268, "en cada push")),
    ("M618 300 H594", False, None),
    ("M720 80 V128", True, None),
    ("M720 100 H540 V128", True, None),
]


def esc(value):
    return html.escape(str(value))


def wrap(text, width):
    return doc_views.wrap(text, width)


def lock_mark(x, y, size):
    """The secrets: a padlock on a lit disc."""
    return (
        f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 72 72" aria-hidden="true"><defs>'
        '<radialGradient id="disc-lock-map" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="#b9a7ff"/>'
        '<stop offset="1" stop-color="#5b3fd1"/></radialGradient></defs><circle cx="36" cy="36" r="31" '
        'fill="url(#disc-lock-map)"/><rect x="24" y="33" width="24" height="18" rx="4" fill="#fff"/>'
        '<path d="M28 33v-5a8 8 0 0 1 16 0v5" fill="none" stroke="#fff" stroke-width="4"/>'
        '<circle cx="36" cy="41" r="2.6" fill="#5b3fd1"/></svg>'
    )


def icon(name, x, y, size):
    return quality_view.build_icon_svg(name).replace(
        '<svg class="qa-icon" ', f'<svg x="{x}" y="{y}" width="{size}" height="{size}" ', 1
    )


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
    hovers = "".join(f"svg:has(#n-{key}:hover, #n-{key}:focus) #tip-n-{key} {{ opacity:1; }}" for key in NODES)
    hovers += "".join(f"svg:has(#t-{t[0]}:hover, #t-{t[0]}:focus) #tip-{t[0]} {{ opacity:1; }}" for t in THREATS)
    hovers += "".join(
        f"svg:has(#loop-{index}:hover, #loop-{index}:focus) #tip-loop-{index} {{ opacity:1; }}"
        for index in range(len(LOOP))
    )
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
svg.sec {{ display:block; width:100%; height:auto; overflow:visible; }}
.zone {{ fill:{'rgba(255,255,255,.03)' if dark else 'rgba(15,39,71,.035)'}; stroke:{border}; stroke-width:1.4; }}
.zone.sub {{ fill:{'rgba(255,255,255,.035)' if dark else 'rgba(255,255,255,.55)'}; stroke-dasharray:6 5; }}
.zone.author {{ stroke:#d9a400; }}
.zone.public {{ stroke:#22b35a; }}
.zone-title {{ font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; fill:{ink}; }}
.zone-sub {{ font-size:11.5px; font-weight:600; letter-spacing:.05em; text-transform:uppercase; fill:{muted}; }}
.node {{ outline:none; cursor:default; }}
.node:hover .halo, .node:focus .halo {{ stroke:{accent}; }}
.halo {{ fill:none; stroke:transparent; stroke-width:2; }}
.title {{ font-size:13.5px; font-weight:600; fill:{ink}; }}
.detail {{ font-size:12px; fill:{muted}; }}
.case {{ font:600 11.5px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{accent}; }}
.chip {{ font:500 11.5px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{muted}; paint-order:stroke; stroke:{palette['background']}; stroke-width:4px; }}
.line {{ fill:none; stroke:{accent}; stroke-width:1.8; }}
.line.dashed {{ stroke:#8a94a6; stroke-dasharray:5 4; }}
.num circle {{ fill:#22b35a; stroke:{palette['background']}; stroke-width:2; }}
.num.declared circle {{ fill:{card}; stroke:#8a94a6; stroke-width:1.6; stroke-dasharray:3 2; }}
.num text {{ font-size:11.5px; font-weight:700; fill:#fff; text-anchor:middle; }}
.num.declared text {{ fill:{ink}; }}
.threat {{ outline:none; cursor:default; }}
.threat text {{ font-size:11.5px; font-weight:700; fill:#e0703a; }}
.threat:hover text, .threat:focus text {{ fill:{ink}; }}
.band {{ fill:{'rgba(255,255,255,.025)' if dark else 'rgba(15,39,71,.03)'}; stroke:{border}; stroke-dasharray:6 6; }}
.band-title {{ font-size:12.5px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; fill:{ink}; }}
.band-sub {{ font-size:12px; fill:{muted}; }}
.step {{ outline:none; cursor:default; }}
.step .card {{ fill:{card}; stroke:{border}; stroke-width:1.1; }}
.step:hover .card, .step:focus .card {{ stroke:{accent}; }}
.step-n {{ font-size:12px; font-weight:700; fill:{accent}; }}
.loop-label {{ font-size:12px; fill:{ink}; paint-order:stroke; stroke:{palette['background']}; stroke-width:5px; }}
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
    return (
        f'<g class="num{" declared" if declared else ""}"><circle cx="{x}" cy="{y}" r="10"/>'
        f'<text x="{x}" y="{y + 4}">{number}</text></g>'
    )


def build_tip(identifier, x, y, up, content):
    """A hover explanation at (x, y), opening below the point or above it."""
    x = min(max(x, 8), WIDTH - 338)
    return (
        f'<g class="tip" id="{identifier}"><foreignObject x="{x:.0f}" y="{y:.0f}" width="330" height="1" overflow="visible">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="{"bottom:0" if up else "top:0"}">{content}</div></foreignObject></g>'
    )


def control_tip(control):
    number, title, line, protects, how, files, tests, verifiable = control
    evidence = (
        "".join(f"<code>{esc(test)}</code><br>" for test in tests)
        if tests
        else "Ninguna: es una configuración de GitHub y de Streamlit Cloud, no del repositorio."
    )
    return (
        f'<b>{number} · {esc(title)}</b>{esc(how)}<b>Protege</b>{esc(protects)}'
        + (f'<b>Archivos</b><code>{esc(files)}</code>' if files else "")
        + f'<b>Pruebas</b>{evidence}'
    )


def build_mark(kind, cx, cy):
    x, y = cx - 22, cy - 22
    if kind.startswith("person:"):
        return doc_views.disc_logo("person", kind[7:]).replace(
            '<svg class="logo" ', f'<svg x="{x}" y="{y}" width="44" height="44" ', 1
        )
    if kind.startswith("brand:"):
        return doc_views.disc_logo("brand", kind[6:]).replace(
            '<svg class="logo" ', f'<svg x="{x}" y="{y}" width="44" height="44" ', 1
        )
    if kind == "lock":
        return lock_mark(x, y, 44)
    if kind == "cylinder":
        return storage_map.cylinder(cx - 20, cy - 25, 40, 50, "duckdb", "sec-base", glyph_size=16)
    if kind == "gate":
        return (
            f'<circle cx="{cx}" cy="{cy}" r="22" fill="none" stroke="#8a94a6" stroke-width="1.6" stroke-dasharray="4 3"/>'
            + icon("shield", cx - 15, cy - 15, 30)
        )
    return icon(kind[5:], x + 2, y + 2, 40)  # icon:<name>


def build_node(key, controls):
    kind, cx, cy, title, line, number, lx, width, cases = NODES[key]
    declared = number is not None and not controls[number][7]
    parts = [
        f'<circle class="halo" cx="{cx}" cy="{cy}" r="29"/>'
        if kind != "cylinder"
        else f'<rect class="halo" x="{cx - 26}" y="{cy - 31}" width="52" height="62" rx="12"/>',
        build_mark(kind, cx, cy),
    ]
    if number is not None:
        parts.append(number_mark(number, cx + 19, cy - 19, declared))
    top = cy - 16 if kind.startswith(("person:", "gate")) and key != "gate" else cy - 8
    if key == "gate":
        top = cy - 18
    parts.append(f'<text class="title" x="{lx}" y="{top}">{esc(wrap(title, width)[0])}</text>')
    lines = wrap(title, width)[1:] if len(wrap(title, width)) > 1 else []
    row = 1
    for extra in lines:
        parts.append(f'<text class="title" x="{lx}" y="{top + 14 * row}">{esc(extra)}</text>')
        row += 1
    for detail in wrap(line, width)[: 2 if key != "gate" else 3]:
        parts.append(f'<text class="detail" x="{lx}" y="{top + 14 * row}">{esc(detail)}</text>')
        row += 1
    if cases:
        parts.append(f'<text class="case" x="{lx}" y="{top + 14 * row}">{esc(cases)}</text>')
    return f'<g class="node" id="n-{key}" tabindex="0">{"".join(parts)}</g>'


def build_node_tip(key, controls):
    kind, cx, cy, title, line, number, lx, width, cases = NODES[key]
    content = control_tip(controls[number]) if number is not None else f"<b>{esc(title)}</b>{esc(NODE_TIPS[key])}"
    up = cy > 330
    return build_tip(f"tip-n-{key}", lx - 10 if lx < 600 else lx - 20, cy + 52 if not up else cy - 36, up, content)


def build_threat(tid, controls):
    x, y = THREAT_SPOTS[tid]
    return (
        f'<g class="threat" id="t-{tid}" tabindex="0"><rect x="{x - 13}" y="{y - 13}" width="46" height="26" fill="transparent"/>'
        f'{icon("warning", x - 11, y - 11, 22)}'
        f'<text x="{x + 14}" y="{y + 4}">{tid}</text></g>'
    )


def build_threat_tip(threat, controls):
    tid, title, owasp, numbers, cases, (mark, asset) = threat
    x, y = THREAT_SPOTS[tid]
    categories = "; ".join(f"{code} {OWASP[code]}" for code in owasp.split(" · "))
    mitigation = "<br>".join(f"{n} · {esc(controls[n][1])}" for n in numbers)
    return build_tip(
        f"tip-{tid}",
        x + 20 if x < 600 else x - 340,
        y + 14 if y < 330 else y - 14,
        y >= 330,
        f'<b>{tid} · {esc(title)}</b><b>OWASP Top 10 (2021)</b>{esc(categories)}<b>La detienen</b>{mitigation}'
        f'<b>Activo protegido</b>{esc(asset)}<b>Verificación</b>'
        + (esc(", ".join(cases)) + " en cada push" if cases else "No verificable aquí: lo declara el autor"),
    )


def build_zones():
    return (
        '<rect class="zone" x="20" y="8" width="960" height="94" rx="18" stroke-dasharray="6 6"/>'
        '<text class="zone-title" x="36" y="26">Internet</text>'
        '<rect class="zone" x="20" y="130" width="570" height="402" rx="18"/>'
        '<text class="zone-title" x="150" y="152">Streamlit Community Cloud</text>'
        '<rect class="zone sub public" x="32" y="162" width="314" height="358" rx="14"/>'
        '<text class="zone-sub" x="150" y="180">Pública · sin cuenta</text>'
        '<rect class="zone sub author" x="356" y="162" width="226" height="266" rx="14"/>'
        '<text class="zone-sub" x="412" y="180">Del autor · con clave</text>'
        '<rect class="zone" x="610" y="130" width="370" height="402" rx="18"/>'
        '<text class="zone-title" x="626" y="152">GitHub · repositorio público</text>'
    )


def build_links():
    out = []
    for path, dashed, label in LINKS:
        out.append(f'<path class="line{" dashed" if dashed else ""}" d="{path}" marker-end="url(#sec-head)"/>')
    for path, dashed, label in LINKS:
        if label and label[2]:
            out.append(f'<text class="chip" x="{label[0]}" y="{label[1]}">{esc(label[2])}</text>')
    return "".join(out)


def build_loop():
    """The loop of continuous improvement: five steps and the way back to the first."""
    top = 544
    width, gap, left = 170, 22, 31
    parts = [
        f'<rect class="band" x="12" y="{top}" width="976" height="124" rx="18"/>'
        f'<text class="band-title" x="30" y="{top + 24}">Mejora continua</text>'
        f'<text class="band-sub" x="190" y="{top + 24}">así se llegó a cada control y así se mantiene</text>'
    ]
    tips = []
    for index, (title, line, detail) in enumerate(LOOP):
        x = left + index * (width + gap)
        y = top + 36
        parts.append(
            f'<g class="step" id="loop-{index}" tabindex="0"><rect class="card" x="{x}" y="{y}" width="{width}" height="50" rx="12"/>'
            f'<text class="step-n" x="{x + 12}" y="{y + 21}">{index + 1}</text>'
            f'<text class="title" x="{x + 28}" y="{y + 21}">{esc(title)}</text>'
            f'<text class="detail" x="{x + 12}" y="{y + 39}">{esc(line)}</text></g>'
        )
        if index < len(LOOP) - 1:
            parts.append(
                f'<path class="line" d="M{x + width} {y + 25} L{x + width + gap - 2} {y + 25}" marker-end="url(#sec-head)"/>'
            )
        tips.append(
            build_tip(
                f"tip-loop-{index}", x + width / 2 - 165, y - 8, True, f'<b>{index + 1} · {esc(title)}</b>{esc(detail)}'
            )
        )
    first = left + width / 2
    last = left + (len(LOOP) - 1) * (width + gap) + width / 2
    bottom = top + 36 + 50
    parts.append(
        f'<path class="line" d="M{last} {bottom} V{bottom + 18} H{first} V{bottom + 2}" marker-end="url(#sec-head)"/>'
        f'<text class="loop-label" x="{(first + last) / 2}" y="{bottom + 22}" text-anchor="middle">'
        'cada revisión vuelve a empezar</text>'
    )
    return "".join(parts), "".join(tips)


def build_security_html(palette):
    """The topology of trust zones with its controls and threats, and the loop that keeps them."""
    controls = {control[0]: control for control in CONTROLS}
    head = (
        f'<defs><marker id="sec-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>'
    )
    nodes = "".join(build_node(key, controls) for key in NODES)
    threats = "".join(build_threat(threat[0], controls) for threat in THREATS)
    tips = "".join(build_node_tip(key, controls) for key in NODES)
    tips += "".join(build_threat_tip(threat, controls) for threat in THREATS)
    loop, loop_tips = build_loop()
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        + build_css(palette)
        + f'</head><body>{quality_view.DEFS}<svg class="sec" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'preserveAspectRatio="xMidYMid meet" role="img" aria-label="Arquitectura de seguridad">{head}{build_zones()}'
        f'{build_links()}{nodes}{threats}{loop}{tips}{loop_tips}</svg></body></html>'
    )
