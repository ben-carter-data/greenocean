"""Where two databases meet (D-197, D-237): every crossing between stores, read top to bottom.

A crossing is the point where data leaves one store and enters another. Each one is a row that
says, with nothing hidden behind a hover: from which store to which, how it happens, what
travels, what both sides share (the key they join on) and, where it can be measured here, the
check of now. The eight crossings come in the order of the story: the data enters, is
transformed and published, is checked by another path, and is remembered by the next load.
The stores are drawn with the same cylinders, folders and marks as «Dónde viven los datos»."""
import html

from bi import charts, database_map, queries, storage_map

BACKUP_TABLES = ["dim_product", "dim_region", "dim_channel", "dim_date", "weekly_price", "rejection", "etl_run"]
RAW_NOTE = "no se puede comprobar aquí: raw.db no está en este servidor"

# (key, from (kind, mark), to (kind, mark), from label, to label, mechanism, short: what travels, short: shared key,
#  full: what travels, full: what both sides share, check key). The short texts are read in the row; the full ones, on hover.
CROSSINGS = [
    ("odepa_raw", ("source", "odepa"), ("db", "sqlite"), "ODEPA", "raw.db", "descarga con Python",
     "CSV públicos, sin cambiar un valor", "archivo + SHA-256",
     "Los CSV públicos, una fila de texto por observación, sin cambiar un valor.",
     "El nombre del archivo y su huella SHA-256, anotada en manifest.json.", "raw"),
    ("ine_bronze", ("source", "ine"), ("files", "apacheparquet"), "INE · IPC", "Bronce", "directo, sin pasar por SQLite",
     "IPC de alimentos, mensual", "el mes del índice",
     "El índice de precios de alimentos, mensual. Por diseño no toca raw.db: no es una fuente de precios de ODEPA.",
     "El mes del índice, que dbt cruza luego con las semanas.", "ine"),
    ("raw_bronze", ("db", "sqlite"), ("files", "apacheparquet"), "raw.db", "Bronce", "lectura de solo lectura",
     "todas las filas, a Parquet", "fuente y año",
     "Todas las filas crudas, un Parquet por fuente y año, con las columnas como texto.",
     "La fuente y el año del archivo: cada Parquet es una carpeta file_year=AAAA.", "raw"),
    ("bronze_work", ("files", "apacheparquet"), ("db", "duckdb"), "Bronce", "Base de trabajo", "dbt lee los Parquet",
     "filas con tipos, reglas y marcas", "la semana (week_start)",
     "Las filas del bronce, ya con tipos, reglas de calidad y marcas. Aquí se cruzan ODEPA y el INE.",
     "La semana (week_start): ipc_weekly lleva el IPC de cada mes a cada semana de precios.", "work"),
    ("work_served", ("db", "duckdb"), ("db", "duckdb"), "Base de trabajo", "datos.duckdb", "ATTACH de solo lectura y CREATE TABLE AS",
     "las 12 tablas servidas", "los mismos nombres de tabla",
     "Las nueve tablas del modelo, más la traza de dbt y el registro de cargas.",
     "Los mismos nombres de tabla; la base servida se reemplaza entera al final, nunca a medias.", "served"),
    ("raw_backup", ("db", "sqlite"), ("db", "sqlite"), "raw.db", "datos.db", "ETL en Python (etl/etl.py)",
     "las mismas filas, sin dbt", "las mismas reglas de negocio",
     "Las mismas filas crudas, validadas y llevadas a precio semanal por un camino independiente de dbt.",
     "Las mismas reglas de negocio: por eso su resultado debe dar las mismas cifras que la base servida.", "raw"),
    ("served_backup", ("db", "duckdb"), ("db", "sqlite"), "datos.duckdb", "datos.db", "comparación de tres cifras",
     "nada se copia: se comparan", "filas, rechazos y suma",
     "Nada se copia: solo se comparan las filas de weekly_price, las filas rechazadas y la suma de los precios.",
     "Las tablas del modelo estrella: el respaldo SQLite tiene siete de las doce.", "parity"),
    ("history", ("db", "duckdb"), ("python", "python"), "datos.duckdb", "Próxima carga", "etl_run arrastrado",
     "el historial de cargas", "el número de carga (run_id)",
     "El historial de cargas: la carga nueva lo lee de la base servida y le agrega su fila. En la primera vez lo leyó de datos.db.",
     "El número de carga (run_id), que también guarda cada fila de rejection.", "history"),
]
# The story in four moments: (title, what it answers, how many crossings it holds).
PHASES = [("Entra el dato", "de la fuente al bronce", 3),
          ("Se transforma y se publica", "dbt construye y la base servida se reemplaza", 2),
          ("Se comprueba por otro camino", "un respaldo calculado sin dbt y la paridad", 2),
          ("Se recuerda", "la carga siguiente parte de aquí", 1)]
STATUS_WORDS = {"ok": "Comprobado ahora", "fail": "No coincide", "warn": "Revisar", "pending": "No medible aquí",
                "info": "Dato"}
STATUS_COLORS = {"ok": "#22b35a", "fail": "#d03b3b", "warn": "#d97706", "pending": "#d97706", "info": "#8a94a6"}


def read_checks(database_file=queries.DATABASE_FILE, backup_file=None):
    """{crossing key: (status, text)} of what can be measured in this server."""
    from bi import quality
    checks = {key: ("pending", RAW_NOTE) for key in ("raw",)}
    checks["ine"] = ("info", "El IPC se guarda también crudo, como ine_ipc_source.")
    with queries.open_database(database_file) as connection:
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
        weeks = connection.execute("SELECT count(*) FROM ipc_weekly").fetchone()[0] if "ipc_weekly" in tables else 0
        unmatched = connection.execute("SELECT count(DISTINCT week_start) FROM weekly_price WHERE week_start NOT IN "
                                         "(SELECT week_start FROM ipc_weekly)").fetchone()[0] if "ipc_weekly" in tables else 0
        runs, rejection_runs = connection.execute(
            "SELECT (SELECT count(*) FROM etl_run), (SELECT count(DISTINCT run_id) FROM rejection "
            "WHERE run_id NOT IN (SELECT run_id FROM etl_run))").fetchone()
    checks["work"] = ("ok" if unmatched == 0 else "warn",
                      f"{database_map.thousands(weeks)} semanas con índice; {unmatched} semanas de precios sin índice.")
    checks["served"] = ("ok", f"{len(tables)} tablas en la base servida, publicadas de una vez.")
    checks["history"] = ("ok" if rejection_runs == 0 else "fail",
                         f"{runs} cargas registradas; {rejection_runs} rechazos sin su carga.")
    parity = quality.check_parity(**({"backup_file": backup_file} if backup_file else {}), database_file=database_file)
    if parity is None:
        checks["parity"] = ("pending", "datos.db no está en este servidor")
    else:
        text = (f"{database_map.thousands(parity['rows'][1])} filas y {database_map.thousands(parity['rejections'][1])} rechazos "
                f"en la base servida; {database_map.thousands(parity['rows'][0])} y "
                f"{database_map.thousands(parity['rejections'][0])} en el respaldo.")
        checks["parity"] = ("ok" if parity["ok"] else "fail", text)
    return checks


# The page fits the height the window leaves by zooming down a little (never below 90 %, to stay
# readable); what does not fit scrolls inside the panel.
FIT_SCRIPT = """<script>
(() => {
  const fit = () => {
    document.body.style.zoom = 1;
    const need = document.documentElement.scrollHeight;
    document.body.style.zoom = Math.max(.9, Math.min(1, innerHeight / need));
  };
  addEventListener("resize", fit);
  addEventListener("load", fit);
  fit();
})();
</script>"""


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    rules = "".join(f".s-{key} {{ --c:{value}; }}" for key, value in STATUS_COLORS.items())
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text};
  font:300 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
{rules}
.x {{ width:100%; max-width:1000px; margin:0 auto; padding:2px 2px 6px; }}
.cols, .row {{ display:grid; grid-template-columns:26px 138px 136px 138px minmax(0,1fr) minmax(0,.85fr) minmax(0,1.2fr); column-gap:10px; align-items:center; }}
.cols {{ padding:0 8px 2px; font-size:11px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.cols span:nth-child(1) {{ grid-column:1 / 5; }}
.phase {{ display:flex; align-items:baseline; gap:10px; margin:6px 2px 2px; }}
.phase b {{ font-size:12.5px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{ink}; }}
.phase span {{ font-size:12px; color:{muted}; }}
.phase i {{ flex:1; height:1px; background:{border}; }}
.row {{ padding:4px 8px; margin:2px 0; border-radius:12px; background:{card}; border:1px solid {border}; }}
.n {{ width:24px; height:24px; border-radius:50%; display:grid; place-items:center; font-size:12px; font-weight:600; color:#fff;
  background:var(--c); }}
.store {{ display:flex; align-items:center; gap:8px; min-width:0; }}
.store b {{ font-size:14px; font-weight:600; color:{ink}; line-height:1.2; }}
.mark {{ flex:none; }}
.link {{ display:flex; flex-direction:column; align-items:center; gap:3px; font-size:12px; text-align:center; color:{muted}; line-height:1.25; }}
.link .line {{ position:relative; width:100%; height:10px; }}
.link .line::before {{ content:""; position:absolute; left:0; right:6px; top:4px; border-top:2px solid {accent}; }}
.link .line::after {{ content:""; position:absolute; right:0; top:0; border-left:9px solid {accent}; border-top:5px solid transparent;
  border-bottom:5px solid transparent; }}
.link .line i {{ display:none; }}
.link.both .line::before {{ left:6px; border-top-style:dashed; }}
.link.both .line i {{ display:block; position:absolute; left:0; top:0; border-right:9px solid {accent}; border-top:5px solid transparent;
  border-bottom:5px solid transparent; }}
.travels, .key {{ font-size:12.5px; line-height:1.3; }}
.travels {{ color:{ink}; }}
.key {{ color:{text}; }}
.check {{ font-size:12.5px; line-height:1.3; color:{text}; }}
.check em {{ display:block; font-style:normal; font-weight:600; color:var(--c); }}
.row {{ position:relative; outline:none; }}
.row:hover, .row:focus {{ border-color:{accent}; z-index:5; }}
.tip {{ position:absolute; z-index:20; right:8px; top:calc(100% + 6px); width:420px; padding:12px 14px; border-radius:14px; background:{card};
  border:1px solid {border}; box-shadow:0 18px 40px rgba(0,0,0,{'.55' if dark else '.2'}); color:{text}; font-size:12.5px; line-height:1.45;
  display:none; pointer-events:none; }}
.tip.up {{ top:auto; bottom:calc(100% + 6px); }}
.tip b {{ display:block; margin:8px 0 2px; font-size:10.5px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip b:first-child {{ margin-top:0; }}
.row:hover .tip, .row:focus .tip {{ display:block; }}
.legend {{ margin:8px 4px 0; font-size:12px; color:{muted}; }}
.legend i {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin:0 5px 0 14px; vertical-align:-1px; background:var(--c); }}
</style>"""


def build_link(label, both=False):
    """The straight line between the two stores, with how the data passes written over it."""
    return (f'<div class="link{" both" if both else ""}"><span>{html.escape(label)}</span>'
            f'<div class="line"><i></i></div></div>')


def build_store(kind_mark, label, key):
    kind, mark = kind_mark
    return f'<div class="store">{storage_map.mini_mark("source" if kind == "source" else kind, mark, key)}<b>{html.escape(label)}</b></div>'


def build_row(number, row, checks):
    key, origin, target, from_label, to_label, how, travels, shared, long_travels, long_shared, check = row
    status, text = checks.get(check, ("pending", "sin medir"))
    both = key == "served_backup"
    up = " up" if number > 4 else ""
    tip = (f'<span class="tip{up}" role="tooltip"><b>{html.escape(from_label)} → {html.escape(to_label)}</b>'
           f'<b>Cómo pasa</b>{html.escape(how)}<b>Qué viaja</b>{html.escape(long_travels)}'
           f'<b>Con qué se cruzan</b>{html.escape(long_shared)}</span>')
    return (f'<div class="row s-{status}" data-crossing="{key}" tabindex="0"><span class="n">{number}</span>'
            f'{build_store(origin, from_label, f"c{number}a")}{build_link(how, both)}{build_store(target, to_label, f"c{number}b")}'
            f'<div class="travels">{html.escape(travels)}</div><div class="key">{html.escape(shared)}</div>'
            f'<div class="check"><em>{STATUS_WORDS[status]}</em>{html.escape(text)}</div>{tip}</div>')


def build_crossings_html(palette, checks):
    """The eight crossings in four moments, each row complete: no hover needed to read it."""
    body, number = [], 1
    for title, sub, count in PHASES:
        body.append(f'<div class="phase"><b>{html.escape(title)}</b><span>{html.escape(sub)}</span><i></i></div>')
        for row in CROSSINGS[number - 1:number - 1 + count]:
            body.append(build_row(number, row, checks))
            number += 1
    assert number - 1 == len(CROSSINGS)
    legend = ('<p class="legend">Cada fila es un punto donde un dato pasa de un almacén a otro.'
              '<span class="s-ok"><i></i></span>comprobado ahora<span class="s-pending"><i></i></span>no medible en este servidor'
              '<span class="s-info"><i></i></span>dato</p>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + '</head><body><div class="x" aria-label="Cruces entre bases">'
            '<div class="cols"><span>Cruce · de dónde a dónde y cómo pasa</span><span>Qué viaja</span><span>Se cruzan por</span>'
            f'<span>Comprobación ahora</span></div>{"".join(body)}{legend}</div>{FIT_SCRIPT}</body></html>')
