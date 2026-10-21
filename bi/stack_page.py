"""«Stack y evidencia» (D-211): the project's stack in 30 seconds, for a recruiter.

One row of 3D brand logos, in the order the data meets them. Each logo explains on hover
what it does here, and a click opens the page of the app where it is at work. Under it,
three real figures, read from the served database and the repository, never typed.

Pure functions: no Streamlit. bi/dashboard.py draws the HTML and hands over the addresses.
"""
import base64
import html
import re
from pathlib import Path

from bi import brand_icons, charts, database_map, queries

REPOSITORY = Path(__file__).resolve().parent.parent
# Disc colors (light top, dark bottom, glyph) beyond database_map.BRANDS.
EXTRA_DISCS = {"pytest": ("#7fc4ff", "#1f6fb5", "#ffffff"), "streamlit": ("#ff8f98", "#e0303f", "#ffffff"),
               "sql": ("#b7a6ff", "#5b3fd0", "#ffffff")}
# (key, name, what it does here, destination page title). The page titles are the
# dashboard's view names; the dashboard turns them into addresses.
STACK = [
    ("python", "Python", "Descarga los CSV de ODEPA y el IPC del INE, y orquesta cada carga.", "Pipeline y arquitectura"),
    ("sqlite", "SQLite", "Aterrizaje: guarda las filas de ODEPA tal como llegan, y el respaldo de la base.",
     "Modelo de datos"),
    ("apacheparquet", "Parquet", "Capa bronce: la copia literal de cada fuente, por año, en formato columnar.",
     "Modelo de datos"),
    ("dbt", "dbt", "Transforma bronce en staging, intermedio y marts, con sus pruebas de datos.",
     "Pipeline y arquitectura"),
    ("sql", "SQL", "Todas las reglas y los indicadores son consultas SQL; el panel deja escribir las propias.",
     "Consultas SQL"),
    ("duckdb", "DuckDB", "Motor del data warehouse y base servida que el panel lee en solo lectura.", "Modelo de datos"),
    ("pytest", "pytest", "Cientos de pruebas que recalculan las cifras desde la fuente y atacan la seguridad.",
     "Monitoreo"),
    ("github", "GitHub Actions", "Corre el pipeline cada martes y las pruebas en cada push.", "Ejecuciones"),
    ("streamlit", "Streamlit", "Publica este panel con un enlace público, sin servidor que mantener.", "Dashboard"),
]


def count_pytest_tests(tests_dir=REPOSITORY / "tests"):
    """Test functions written in the repository (a parametrized one counts once)."""
    return sum(len(re.findall(r"^def test_", path.read_text(encoding="utf-8"), re.MULTILINE))
               for path in Path(tests_dir).glob("test_*.py"))


def read_figures(database_file=queries.DATABASE_FILE, tests_dir=REPOSITORY / "tests"):
    """{prices, tests, loads}: weekly prices served, automatic tests (pytest + dbt) and recorded loads."""
    connection = queries.open_database(database_file)
    try:
        prices = connection.execute("SELECT count(*) FROM weekly_price").fetchone()[0]
        dbt_tests = connection.execute("SELECT count(*) FROM dbt_node WHERE resource_type = 'test'").fetchone()[0]
        loads = connection.execute("SELECT count(*) FROM etl_run").fetchone()[0]
    finally:
        connection.close()
    return {"prices": prices, "tests": count_pytest_tests(tests_dir) + dbt_tests, "loads": loads}


def format_number(value):
    return f"{value:,}".replace(",", ".")


def disc_logo(key):
    """The 3D mark as an image: st.html strips inline SVG gradients, a data: image keeps them."""
    svg = disc_svg(key).replace('<svg class="logo"', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return f'<img class="logo" alt="" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}">'


def disc_svg(key):
    if key in database_map.BRANDS:
        return database_map.brand_logo(key, "-stack")
    top, bottom, glyph = EXTRA_DISCS[key]
    body = (f'<text x="36" y="43" text-anchor="middle" font-family="ui-monospace, Menlo, monospace" font-weight="800" '
            f'font-size="19" fill="{glyph}">SQL</text>' if key == "sql" else
            f'<g fill="{glyph}" transform="translate(17 17) scale(1.58)">{brand_icons.logo_body(key)}</g>')
    return (f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>'
            f'<radialGradient id="disc-{key}-stack" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></radialGradient></defs>'
            f'<circle cx="36" cy="36" r="31" fill="url(#disc-{key}-stack)"/>'
            f'<ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>{body}</svg>')


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border = (palette["strong_text"], palette["text"], palette["reference"],
                                      palette["card"], palette["card_border"])
    shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    return f"""<style>
.stack {{ display:flex; flex-wrap:wrap; justify-content:center; gap:18px 6px; margin:18px 0 30px; }}
.stack a {{ position:relative; width:102px; display:flex; flex-direction:column; align-items:center; text-decoration:none !important;
  outline:none; }}
.stack .logo {{ width:78px; height:78px; filter:drop-shadow(0 14px 12px {shadow}); transition:transform .25s ease; }}
.stack a:hover .logo, .stack a:focus .logo {{ transform:translateY(-6px) scale(1.06); }}
.stack b {{ margin-top:6px; color:{ink}; font:600 14px/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.stack .tip {{ position:absolute; z-index:40; top:calc(100% + 6px); left:50%; transform:translateX(-50%); width:230px;
  padding:10px 12px; border-radius:12px; background:{card}; border:1px solid {border}; color:{text}; text-align:left;
  box-shadow:0 18px 40px rgba(0,0,0,{'.5' if dark else '.18'}); font:400 12.5px/1.45 -apple-system, sans-serif;
  display:none; pointer-events:none; }}
.stack .tip i {{ display:block; margin-top:6px; color:{muted}; font-style:normal; font-size:11.5px; }}
.stack a:hover .tip, .stack a:focus .tip {{ display:block; }}
.evidence {{ display:flex; justify-content:center; gap:56px; flex-wrap:wrap; margin:6px 0 4px; }}
.evidence div {{ text-align:center; }}
.evidence strong {{ display:block; color:{ink}; font:600 34px/1.1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-variant-numeric:tabular-nums; }}
.evidence span {{ color:{muted}; font-size:13px; }}
</style>"""


def build_stack_html(palette, figures, addresses):
    """The logos, each a link to its page with a hover explanation, and the three figures."""
    logos = []
    for key, name, what, page in STACK:
        logos.append(f'<a class="stack-item" href="{html.escape(addresses[page], quote=True)}" target="_self" '
                     f'aria-label="{html.escape(name)}: {html.escape(what)}">{disc_logo(key)}<b>{html.escape(name)}</b>'
                     f'<span class="tip" role="tooltip">{html.escape(what)}<i>Clic: verlo en uso.</i></span></a>')
    evidence = [(figures["prices"], "precios semanales procesados"),
                (figures["tests"], "pruebas automáticas (pytest y dbt)"),
                (figures["loads"], "cargas semanales registradas")]
    numbers = "".join(f'<div><strong>{format_number(value)}</strong><span>{html.escape(label)}</span></div>'
                      for value, label in evidence)
    return build_css(palette) + f'<div class="stack">{"".join(logos)}</div><div class="evidence">{numbers}</div>'
