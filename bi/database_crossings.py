"""Where two databases meet (D-197): every crossing between stores, with how it happens,
what travels, what the two sides share and, where it can be measured here, the live check."""
import html

from bi import database_map, queries

BACKUP_TABLES = ["dim_product", "dim_region", "dim_channel", "dim_date", "weekly_price", "rejection", "etl_run"]
RAW_NOTE = "no se puede comprobar aquí: raw.db no está en este servidor"

# (key, from (kind, slug), to (kind, slug), from label, to label, mechanism, what travels, what both share, check key)
CROSSINGS = [
    ("odepa_raw", ("source", "odepa"), ("brand", "sqlite"), "ODEPA", "raw.db", "descarga con Python",
     "Los CSV públicos de precios, una fila de texto por observación, sin cambiar un valor.",
     "El nombre del archivo y su huella SHA-256, anotada en manifest.json.", "raw"),
    ("raw_bronze", ("brand", "sqlite"), ("brand", "apacheparquet"), "raw.db", "Bronce", "lectura en solo lectura",
     "Todas las filas crudas, un Parquet por fuente y año, con las columnas como texto.",
     "La fuente y el año del archivo: cada Parquet es una carpeta file_year=AAAA.", "raw"),
    ("ine_bronze", ("source", "ine"), ("brand", "apacheparquet"), "INE", "Bronce", "directo, sin pasar por SQLite",
     "El índice de precios de alimentos, mensual. Por diseño no toca raw.db: no es una fuente de precios de ODEPA.",
     "El mes del índice, que dbt cruza luego con las semanas.", "ine"),
    ("bronze_work", ("brand", "apacheparquet"), ("brand", "dbt"), "Bronce", "Base de trabajo de dbt", "dbt lee los Parquet",
     "Las filas del bronce, ya con tipos, reglas de calidad y marcas. Aquí se cruzan ODEPA y el INE.",
     "La semana (week_start): ipc_weekly lleva el IPC de cada mes a cada semana de precios.", "work"),
    ("work_served", ("brand", "dbt"), ("brand", "duckdb"), "Base de trabajo", "datos.duckdb", "ATTACH en solo lectura y CREATE TABLE AS",
     "Las nueve tablas del modelo, más la traza de dbt y el registro de cargas.",
     "Los mismos nombres de tabla; la base servida se reemplaza entera al final, nunca a medias.", "served"),
    ("served_backup", ("brand", "duckdb"), ("brand", "sqlite"), "datos.duckdb", "datos.db", "comparación de tres cifras",
     "Nada se copia: solo se comparan las filas de weekly_price, las filas rechazadas y la suma de los precios.",
     "Las tablas del modelo estrella: el respaldo SQLite tiene siete de las doce.", "parity"),
    ("history", ("brand", "duckdb"), ("brand", "python"), "datos.duckdb", "Próxima carga", "etl_run arrastrado",
     "El historial de cargas: la carga nueva lo lee de la base servida y le agrega su fila. En la primera vez lo leyó de datos.db.",
     "El número de carga (run_id), que también guarda cada fila de rejection.", "history"),
]


def read_checks(database_file=queries.DATABASE_FILE, backup_file=None):
    """{crossing key: (status, text)} of what can be measured in this server."""
    from bi import quality
    checks = {key: ("pending", RAW_NOTE) for key in ("raw",)}
    checks["ine"] = ("info", "El IPC publicado se guarda también como ine_ipc_source, la copia cruda de los archivos del INE.")
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
                         f"{runs} cargas registradas; {rejection_runs} cargas de rechazos sin su fila en etl_run.")
    parity = quality.check_parity(**({"backup_file": backup_file} if backup_file else {}), database_file=database_file)
    if parity is None:
        checks["parity"] = ("pending", "datos.db no está en este servidor")
    else:
        text = (f"{database_map.thousands(parity['rows'][1])} filas y {database_map.thousands(parity['rejections'][1])} rechazos "
                f"en la base servida; {database_map.thousands(parity['rows'][0])} y "
                f"{database_map.thousands(parity['rejections'][0])} en el respaldo.")
        checks["parity"] = ("ok" if parity["ok"] else "fail", text)
    return checks


STATUS_WORDS = {"ok": "Comprobado ahora", "fail": "No coincide", "warn": "Revisar", "pending": "Pendiente", "info": "Dato"}


def endpoint(kind_slug, suffix):
    kind, slug = kind_slug
    return database_map.source_logo(slug) if kind == "source" else database_map.brand_logo(slug, suffix)


def build_css(palette):
    ink, text, muted, _card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    status = {"ok": palette.get("positive", "#13825a"), "fail": palette.get("negative", "#c0392b"),
              "warn": "#b7791f", "pending": muted, "info": muted}
    rules = "".join(f".st-{key} {{ color:{value}; }}" for key, value in status.items())
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text};
  font:300 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
.row {{ display:grid; grid-template-columns:minmax(190px,.9fr) minmax(210px,1fr) minmax(210px,1fr) minmax(210px,1fr);
  gap:18px; align-items:center; padding:14px 6px; border-bottom:1px solid {border}; }}
.row:last-child {{ border-bottom:0; }}
.pair {{ display:flex; align-items:center; gap:8px; }}
.pair .logo {{ width:58px; height:58px; filter:drop-shadow(0 6px 8px rgba(15,39,71,.25)); flex:none; }}
.pair .arrow {{ color:{accent}; font-size:22px; line-height:1; }}
.names {{ font-weight:400; color:{ink}; }} .names small {{ display:block; font-weight:300; color:{muted}; font-size:12px; }}
.how {{ font-weight:400; color:{ink}; }}
.lab {{ display:block; font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:{muted}; margin-bottom:2px; }}
.chk {{ font-size:13px; }} .chk b {{ font-weight:500; display:block; }}
{rules}
.head {{ display:grid; grid-template-columns:minmax(190px,.9fr) minmax(210px,1fr) minmax(210px,1fr) minmax(210px,1fr);
  gap:18px; padding:0 6px 8px; border-bottom:1px solid {border}; font-size:11px; letter-spacing:.06em;
  text-transform:uppercase; color:{muted}; }}
@media (max-width:760px) {{ .row, .head {{ grid-template-columns:1fr; }} .head {{ display:none; }} }}
</style>"""


def build_crossings_html(palette, checks):
    rows = []
    for index, (key, origin, target, from_label, to_label, how, travels, shared, check) in enumerate(CROSSINGS):
        status, text = checks.get(check, ("pending", "sin medir"))
        rows.append(
            f'<div class="row" id="x-{key}"><div><div class="pair">{endpoint(origin, f"a{index}")}<span class="arrow">→</span>'
            f'{endpoint(target, f"b{index}")}</div><div class="names">{html.escape(from_label)} → {html.escape(to_label)}'
            f'<small>{html.escape(how)}</small></div></div>'
            f'<div><span class="lab">Qué viaja</span>{html.escape(travels)}</div>'
            f'<div><span class="lab">Con qué se cruzan</span>{html.escape(shared)}</div>'
            f'<div class="chk st-{status}"><span class="lab">Comprobación</span><b>{STATUS_WORDS[status]}</b>{html.escape(text)}</div></div>')
    return f'<!doctype html><html lang="es"><head><meta charset="utf-8">{build_css(palette)}</head><body>{"".join(rows)}</body></html>'
