"""«Seguridad» (D-200): what a visitor can try, the barriers that stop it and the protected
asset behind them, in one view. Every barrier names the automated test that attacks it on
every push, so the view states nothing the tests do not prove. Secret values never appear.

build_security_html() returns one HTML document for st.iframe (CSS only, no script).
"""
import html

from bi import charts, database_map, project, quality_view

STAGE_WIDTH, STAGE_HEIGHT = 1000, 530
ROW_Y = (80, 260, 440)
BARRIER_X = (330, 510, 690)
VISITOR = (80, 260)
ASSET_X = 895

ROWS = [
    dict(door="Consultas SQL", asset=("duckdb", "datos.duckdb", "solo se leen las tablas de precios"),
         attempt="Escribir SQL que lea los secretos del servidor, escriba archivos o salga a internet.",
         barriers=[
             dict(icon="shield", title="Filtro de la consulta", line="solo SELECT · una instrucción · sin archivos ni web",
                  how="Antes de ejecutar: la consulta debe empezar con SELECT o WITH, ser una sola instrucción y no nombrar "
                      "funciones que leen archivos ni direcciones web.",
                  test="tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files"),
             dict(icon="gear", title="Motor sin acceso externo", line="DuckDB no abre archivos ni internet",
                  how="Aunque alguien esquivara el filtro, DuckDB se abre sin acceso a archivos ni a internet y con la "
                      "configuración bloqueada: responde «Permission Error».",
                  test="tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed"),
             dict(icon="layers", title="Solo lectura y topes", line="segundos, memoria y filas limitados",
                  how="La base se abre en solo lectura. Cada consulta se corta a los pocos segundos, con memoria y filas "
                      "limitadas: nadie puede cambiar datos ni colgar la app.",
                  test="tests/test_sql_explorer.py::test_slow_query_is_interrupted"),
         ]),
    dict(door="Clave de control", asset=("github", "Pipeline", "lanzar una carga, igual que el martes"),
         attempt="Adivinar la clave para lanzar el pipeline o abrir los accesos del autor.",
         barriers=[
             dict(icon="calculator", title="Comparación segura", line="tiempo constante · cualquier carácter",
                  how="La clave se compara en tiempo constante: lo que tarda la respuesta no da pistas. Acepta ñ, tildes "
                      "y emojis sin fallar.",
                  test="tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe"),
             dict(icon="warning", title="5 intentos y bloqueo", line="15 min para todos los visitantes",
                  how="Tras 5 claves incorrectas en 15 minutos, el acceso se bloquea 15 minutos, incluso para la clave "
                      "correcta. El contador es uno para todos: abrir otra sesión no lo reinicia.",
                  test="tests/test_control.py::test_d199_five_wrong_codes_lock_even_the_right_one_for_fifteen_minutes"),
             dict(icon="files", title="Desbloqueo por sesión", line="no queda en la URL ni en cookies",
                  how="Abrir con la clave vale solo para esa pestaña del navegador. Un enlace copiado no lleva el acceso.",
                  test="tests/test_dashboard.py::test_d199_the_code_box_survives_any_character_and_locks_after_five_wrong_codes"),
         ]),
    dict(door="Código público", asset=("secret", "Secretos", "token de GitHub y clave de control"),
         attempt="Buscar claves en el repositorio, en los mensajes de error o abusar de los permisos del workflow.",
         barriers=[
             dict(icon="database", title="Secretos fuera de git", line="ningún token en el repositorio",
                  how="Los secretos viven en Streamlit Cloud, no en el código. .gitignore los excluye y una prueba busca "
                      "tokens en cada archivo versionado.",
                  test="tests/test_security.py::test_no_secret_is_tracked_by_git"),
             dict(icon="parity", title="Token nunca en pantalla", line="ni en la página ni en los errores",
                  how="Los errores de GitHub se describen con su código y su causa, nunca con el token, los encabezados ni "
                      "la dirección completa.",
                  test="tests/test_control.py::test_github_error_never_shows_the_token"),
             dict(icon="reconcile", title="Permisos mínimos", line="el job: contents e issues, nada más",
                  how="El workflow semanal solo puede escribir contenido (el commit de la base) y crear issues.",
                  test="tests/test_security.py::test_the_weekly_job_has_least_privilege"),
         ]),
]
LOCK = ('<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs><radialGradient id="disc-lock" cx="35%" cy="28%" r="85%">'
        '<stop offset="0" stop-color="#b9a7ff"/><stop offset="1" stop-color="#5b3fd1"/></radialGradient></defs>'
        '<circle cx="36" cy="36" r="31" fill="url(#disc-lock)"/><ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>'
        '<rect x="24" y="33" width="24" height="18" rx="4" fill="#fff"/><path d="M28 33v-5a8 8 0 0 1 16 0v5" fill="none" '
        'stroke="#fff" stroke-width="4"/><circle cx="36" cy="41" r="2.6" fill="#5b3fd1"/></svg>')
PERSON = ('<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs><radialGradient id="disc-person" cx="35%" cy="28%" r="85%">'
          '<stop offset="0" stop-color="#9fb3c8"/><stop offset="1" stop-color="#3d4f66"/></radialGradient></defs>'
          '<circle cx="36" cy="36" r="31" fill="url(#disc-person)"/><ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>'
          '<circle cx="36" cy="29" r="8" fill="#fff"/><path d="M21 52c2-9 8-13 15-13s13 4 15 13z" fill="#fff"/></svg>')


def asset_logo(slug):
    return LOCK if slug == "secret" else database_map.brand_logo(slug, "-sec")


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:300 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
.stage {{ position:relative; width:100%; max-width:{STAGE_WIDTH}px; aspect-ratio:{STAGE_WIDTH}/{STAGE_HEIGHT}; margin:0 auto; }}
.stage > svg {{ position:absolute; inset:0; width:100%; height:100%; overflow:visible; }}
.arrow {{ fill:none; stroke:{accent}; stroke-width:2; stroke-linecap:round; opacity:.85; }}
.door {{ font-size:12.5px; fill:{ink}; font-weight:500; }}
.node {{ position:absolute; width:168px; margin-left:-84px; display:flex; flex-direction:column; align-items:center; text-align:center;
  outline:none; transform:translateY(-36px); }}
.logo, .qa-icon {{ display:block; width:62px; height:62px; filter:drop-shadow(0 10px 9px {shadow}); transition:transform .25s ease; }}
.node.big .logo {{ width:76px; height:76px; }}
.node:hover .logo, .node:focus .logo, .node:hover .qa-icon, .node:focus .qa-icon {{ transform:translateY(-4px) scale(1.05); }}
.node b {{ margin-top:5px; font-weight:500; font-size:13.5px; color:{ink}; line-height:1.2; }}
.node small {{ color:{muted}; font-size:11.5px; line-height:1.25; }}
.node a {{ margin-top:2px; font-size:11px; color:{accent}; text-decoration:none; }}
.node a:hover {{ text-decoration:underline; }}
.ok {{ position:absolute; top:0; left:calc(50% + 18px); width:18px; height:18px; border-radius:50%; background:#22b35a; color:#fff;
  font:700 10px/18px sans-serif; text-align:center; box-shadow:0 0 0 3px {palette['background']}; }}
.tip {{ position:absolute; z-index:40; left:50%; top:calc(100% + 6px); width:290px; padding:12px 14px; border-radius:14px; text-align:left;
  background:{card}; border:1px solid {border}; box-shadow:0 18px 40px rgba(0,0,0,{'.5' if dark else '.18'}); color:{text};
  font-size:12.5px; line-height:1.45; display:none; pointer-events:none; transform:translateX(-50%); }}
.tip i {{ display:block; margin:8px 0 2px; font:500 10px/1 sans-serif; font-style:normal; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip i:first-child {{ margin-top:0; }}
.tip code {{ font:400 11px/1.35 ui-monospace, SFMono-Regular, Menlo, monospace; overflow-wrap:anywhere; }}
.tip.start {{ left:0; transform:none; }} .tip.end {{ left:auto; right:0; transform:none; }} .tip.up {{ top:auto; bottom:calc(100% + 6px); }}
.node:hover .tip, .node:focus .tip {{ display:block; }}
.node:hover, .node:focus {{ z-index:50; }}
.legend {{ margin:2px 4px 0; font-size:11.5px; color:{muted}; text-align:center; }}
</style>"""


def place(x, y):
    return f"left:{x / STAGE_WIDTH * 100:.3f}%;top:{y / STAGE_HEIGHT * 100:.3f}%"


def build_barrier_html(barrier, x, y, row_index):
    test_path, test_name = barrier["test"].split("::")
    side = " up" if row_index == 2 else ""
    return (f'<div class="node" tabindex="0" style="{place(x, y)}">{quality_view.build_icon_svg(barrier["icon"])}<span class="ok">✓</span>'
            f'<b>{html.escape(barrier["title"])}</b><small>{html.escape(barrier["line"])}</small>'
            f'<a href="{html.escape(project.build_github_url(test_path), quote=True)}" target="_blank" rel="noopener noreferrer">prueba ↗</a>'
            f'<span class="tip{side}" role="tooltip"><i>Cómo detiene</i>{html.escape(barrier["how"])}'
            f'<i>Prueba que lo ataca en cada push</i><code>{html.escape(test_path)} · {html.escape(test_name)}</code></span></div>')


def build_security_html(palette):
    """The whole view as one HTML document."""
    marker = (f'<defs><marker id="head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
              f'<path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>')
    arrows, nodes = [], []
    vx, vy = VISITOR
    for index, (row, y) in enumerate(zip(ROWS, ROW_Y)):
        first = BARRIER_X[0] - 46
        arrows.append(f'<path class="arrow" d="M{vx + 44} {vy} C {vx + 120} {vy}, {first - 110} {y}, {first} {y}" marker-end="url(#head)"/>'
                      f'<text class="door" x="{first - 6}" y="{y - 12}" text-anchor="end">'
                      f'{html.escape(row["door"])}</text>')
        for left, right in zip(BARRIER_X, BARRIER_X[1:] + (ASSET_X,)):
            arrows.append(f'<path class="arrow" d="M{left + 46} {y} H{right - (52 if right == ASSET_X else 46)}" marker-end="url(#head)"/>')
        for x, barrier in zip(BARRIER_X, row["barriers"]):
            nodes.append(build_barrier_html(barrier, x, y, index))
        slug, title, line = row["asset"]
        nodes.append(f'<div class="node big" tabindex="0" style="{place(ASSET_X, y)}">{asset_logo(slug)}<b>{html.escape(title)}</b>'
                     f'<small>{html.escape(line)}</small><span class="tip end{" up" if index == 2 else ""}" role="tooltip">'
                     f'<i>Qué intentaría un atacante</i>{html.escape(row["attempt"])}<i>Qué logra</i>Nada de eso: las tres barreras '
                     f'de la izquierda lo detienen, y cada una tiene una prueba automática que lo intenta en cada push.</span></div>')
    nodes.append(f'<div class="node big" tabindex="0" style="{place(vx, vy)}">{PERSON}<b>Visitante</b><small>cualquiera con el enlace</small>'
                 '<span class="tip start" role="tooltip"><i>Qué puede hacer</i>Leer el panel y consultar las tablas de precios con SQL. '
                 'Tres puertas podrían tentar a un atacante: las consultas SQL, la clave de control y el código público.</span></div>')
    legend = ('<p class="legend">Pasa el cursor por cada barrera para ver cómo detiene el ataque y qué prueba lo comprueba. '
              'Los valores secretos nunca aparecen aquí.</p>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body>{quality_view.DEFS}<div class="stage" aria-label="Seguridad">'
            f'<svg viewBox="0 0 {STAGE_WIDTH} {STAGE_HEIGHT}" aria-hidden="true">{marker}{"".join(arrows)}</svg>'
            f'{"".join(nodes)}</div>{legend}</body></html>')
