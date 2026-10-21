"""«Calidad» (D-194): is the published data good today? Measured on the real database.

Six dimensions (completeness, uniqueness, validity, consistency, timeliness and the dbt
tests), each with the indicators that measure it, the value read from datos.duckdb on
every load, the reference it is judged against and a verdict in words. Where a figure
can be compared with the previous load, it is. Nothing here is written by hand except
the thresholds, which are the project's own and are shown beside each figure.

read_measures() reads the database; build_page_html() draws the measures as one HTML
document for st.iframe (CSS only, no script). Both are pure enough to test without a server.
"""
import html
from datetime import date, datetime, timezone

from bi import audit_trace, charts, database_map, queries, quality, quality_view

# The project's thresholds, shown next to each figure so a verdict can be disputed.
LAST_WEEK_MIN_SHARE = 0.75   # rows of the latest week vs the median of the 8 before
REJECTED_MAX_SHARE = 0.01    # rows rejected over rows read
FLAGGED_MAX_SHARE = 0.05     # prices set apart (outliers, units) over all weekly prices
DATA_MAX_DAYS = 14           # days between the latest week and today
LOAD_MAX_DAYS = 9            # days since the last load: the cadence is weekly
REASONS = {"NON_POSITIVE_PRICE": "precio cero o negativo"}
FLAGS = {"ATIPICO": "precio atípico para su serie", "UNIDAD_NO_CONVERTIBLE": "unidad que no se puede llevar a kilo o unidad"}
ICONS = {"completitud": "calendar", "unicidad": "database", "validez": "shield", "consistencia": "parity",
         "actualidad": "gear", "pruebas": "layers"}
TITLES = {"completitud": "Completitud", "unicidad": "Unicidad", "validez": "Validez", "consistencia": "Consistencia",
          "actualidad": "Actualidad", "pruebas": "Pruebas dbt"}
QUESTIONS = {"completitud": "¿Están todos los datos esperados?", "unicidad": "¿Ningún precio aparece dos veces?",
             "validez": "¿Cada valor tiene un formato y un rango permitidos?", "consistencia": "¿Los datos concuerdan entre sí?",
             "actualidad": "¿Son los últimos disponibles?", "pruebas": "¿Pasó cada prueba automática de dbt?"}
STATUS_WORDS = {"ok": "Bien", "warn": "Revisar", "fail": "Falla", "info": "Informativo"}

WEEKS_SQL = """SELECT week_start, count(*) AS filas FROM weekly_price GROUP BY week_start ORDER BY week_start DESC LIMIT 9"""
EXPECTED_WEEKS_SQL = """SELECT date_diff('week', CAST(min(week_start) AS DATE), CAST(max(week_start) AS DATE)) + 1 FROM weekly_price"""
FLAGS_SQL = """SELECT COALESCE(flag, 'SIN_MARCA') AS marca, count(*) FROM weekly_price GROUP BY ALL"""
REJECTIONS_SQL = """SELECT reason, source, count(*) FROM rejection GROUP BY ALL ORDER BY 3 DESC"""
RUNS_SQL = """SELECT run_id, started_at, status, rows_read, rows_loaded, rows_rejected FROM etl_run ORDER BY run_id"""
TESTS_SQL = """SELECT r.status, count(*) FROM dbt_node AS n JOIN dbt_result AS r USING (unique_id)
WHERE n.resource_type = 'test' GROUP BY ALL"""


def read_measures(database_file=queries.DATABASE_FILE, backup_file=None):
    """Every raw figure of the page, from the database; the verdicts come later."""
    with queries.open_database(database_file) as connection:
        weeks, first, last = connection.execute(quality.COVERAGE_SQL).fetchone()
        measures = dict(
            weeks=weeks, first=first, last=last,
            expected_weeks=connection.execute(EXPECTED_WEEKS_SQL).fetchone()[0],
            per_week=connection.execute(WEEKS_SQL).fetchall(),
            total_rows=connection.execute("SELECT count(*) FROM weekly_price").fetchone()[0],
            flags=dict(connection.execute(FLAGS_SQL).fetchall()),
            rejections=connection.execute(REJECTIONS_SQL).fetchall(),
            runs=connection.execute(RUNS_SQL).fetchall(),
            tests=dict(connection.execute(TESTS_SQL).fetchall()),
            foreign_keys=connection.execute(quality.FOREIGN_KEYS_SQL).fetchone()[0],
            duplicates=connection.execute(quality.DUPLICATES_SQL).fetchone()[0],
            invalid=connection.execute(quality.INVALID_SQL).fetchone()[0])
    parity = quality.check_parity(**({"backup_file": backup_file} if backup_file else {}), database_file=database_file)
    measures["parity"] = parity
    return measures


def compact(sql):
    """A query on one line, so its tooltip stays short."""
    return " ".join(sql.split())


def share(part, whole):
    return part / whole if whole else 0.0


def percent(value, digits=1):
    return f"{value * 100:.{digits}f} %".replace(".", ",")


def thousands(value):
    return charts.format_thousands(value)


def median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def parse_day(text):
    return date.fromisoformat(str(text)[:10])


def build_indicators(measures, now=None):
    """[(dimension, label, value, reference, status, detail)] from the raw measures.
    status: ok, warn, fail or info; detail says how it is measured, for the hover."""
    now = now or datetime.now(timezone.utc)
    today = now.date()
    rows = []
    # Completeness
    gaps = measures["expected_weeks"] - measures["weeks"]
    rows.append(("completitud", "Semanas sin hueco", f"{measures['weeks']} de {measures['expected_weeks']}",
                 "ninguna semana falta entre la primera y la última", "ok" if gaps == 0 else "fail",
                 f"Semanas con precios entre {measures['first']} y {measures['last']}, contadas contra las que "
                 f"debería haber (una por lunes). Faltan {gaps}."))
    per_week = measures["per_week"]
    if len(per_week) >= 4:
        latest = per_week[0][1]
        typical = median([count for _, count in per_week[1:]])
        ratio = share(latest, typical)
        rows.append(("completitud", "Precios de la última semana", thousands(latest),
                     f"{percent(ratio, 0)} de lo típico ({thousands(round(typical))}); mínimo {percent(LAST_WEEK_MIN_SHARE, 0)}",
                     "ok" if ratio >= LAST_WEEK_MIN_SHARE else "warn",
                     f"Filas de weekly_price de la semana {per_week[0][0]} frente a la mediana de las {len(per_week) - 1} "
                     "semanas anteriores. Una caída fuerte suele ser una descarga incompleta."))
    # Uniqueness
    rows.append(("unicidad", "Claves duplicadas", thousands(measures["duplicates"]),
                 "producto, región, canal, unidad y semana: una sola fila", "ok" if measures["duplicates"] == 0 else "fail",
                 "Combinaciones de semana, producto, región, canal y unidad con más de una fila.\n" + compact(quality.DUPLICATES_SQL)))
    # Validity
    read = measures["runs"][-1][3] if measures["runs"] else 0
    rejected = sum(count for _, _, count in measures["rejections"])
    rows.append(("validez", "Filas rechazadas", thousands(rejected),
                 f"{percent(share(rejected, read), 3)} de {thousands(read)} leídas; máximo {percent(REJECTED_MAX_SHARE, 0)}",
                 "ok" if share(rejected, read) <= REJECTED_MAX_SHARE else "warn",
                 "Filas de origen que la validación apartó, cada una con su motivo, en la tabla rejection."))
    flagged = sum(count for name, count in measures["flags"].items() if name != "SIN_MARCA")
    total = measures["total_rows"]
    rows.append(("validez", "Precios apartados de los indicadores", thousands(flagged),
                 f"{percent(share(flagged, total))} de {thousands(total)}; máximo {percent(FLAGGED_MAX_SHARE, 0)}",
                 "ok" if share(flagged, total) <= FLAGGED_MAX_SHARE else "warn",
                 "Precios marcados como atípicos o con unidad no convertible: quedan en la base pero fuera de los "
                 "indicadores."))
    rows.append(("validez", "Formatos inválidos", thousands(measures["invalid"]), "precio positivo, unidad y lunes válidos",
                 "ok" if measures["invalid"] == 0 else "fail",
                 "Precios utilizables con precio nulo o no positivo, unidad vacía o fecha que no es lunes.\n" + compact(quality.INVALID_SQL)))
    # Consistency
    rows.append(("consistencia", "Referencias sin destino", thousands(measures["foreign_keys"]),
                 "toda clave apunta a una fila que existe", "ok" if measures["foreign_keys"] == 0 else "fail",
                 "Precios sin producto, región, canal o fecha, y rechazos sin carga.\n" + compact(quality.FOREIGN_KEYS_SQL)))
    parity = measures.get("parity")
    if parity:
        rows.append(("consistencia", "Paridad SQLite ↔ DuckDB", "misma suma" if parity["ok"] else "no coinciden",
                     f"{thousands(parity['rows'][1])} precios y {thousands(parity['rejections'][1])} rechazos en las dos",
                     "ok" if parity["ok"] else "fail",
                     "El ETL en Python y dbt, por caminos independientes, deben dar los mismos precios, rechazos y suma."))
    else:
        rows.append(("consistencia", "Paridad SQLite ↔ DuckDB", "sin respaldo aquí", "se comprueba donde está datos.db",
                     "info", "El respaldo SQLite no está en este servidor, así que esta comparación no se puede hacer aquí."))
    # Timeliness
    behind = (today - parse_day(measures["last"])).days
    rows.append(("actualidad", "Días desde la última semana", f"{behind}", f"semana {measures['last']}; máximo {DATA_MAX_DAYS}",
                 "ok" if behind <= DATA_MAX_DAYS else "warn",
                 "Días entre el lunes de la última semana con precios y hoy."))
    if measures["runs"]:
        run_id, started, status, *_ = measures["runs"][-1]
        age = (today - parse_day(started)).days
        good = status == "LOADED"
        rows.append(("actualidad", "Última carga", f"hace {age} día" + ("" if age == 1 else "s"), f"carga {run_id} · {status}; máximo {LOAD_MAX_DAYS} días",
                     "ok" if good and age <= LOAD_MAX_DAYS else "fail" if not good else "warn",
                     "El pipeline corre cada martes y deja una fila en etl_run por ejecución real."))
    # dbt tests
    passed, failed = measures["tests"].get("pass", 0), sum(n for s, n in measures["tests"].items() if s != "pass")
    rows.append(("pruebas", "Pruebas de dbt", f"{passed} de {passed + failed}", "todas superadas en la última construcción",
                 "ok" if failed == 0 and passed else "fail" if failed else "info",
                 "Las pruebas de datos de dbt: claves únicas y no nulas, valores aceptados y relaciones entre tablas."))
    return rows


def dimension_status(statuses):
    return "fail" if "fail" in statuses else "warn" if "warn" in statuses else "ok" if "ok" in statuses else "info"


def group_indicators(indicators):
    """{dimension: [indicator, …]} in the order of ICONS."""
    return {key: [row for row in indicators if row[0] == key] for key in ICONS}


def build_verdict(indicators):
    """One sentence for the whole page, and its status."""
    statuses = [row[4] for row in indicators]
    judged = [status for status in statuses if status != "info"]
    ok = sum(status == "ok" for status in judged)
    kind = dimension_status(judged)
    if kind == "ok":
        return "ok", f"Los {len(judged)} indicadores medidos están dentro de su umbral."
    names = [row[1] for row in indicators if row[4] in ("warn", "fail")]
    return kind, f"{ok} de {len(judged)} indicadores dentro de su umbral. A revisar: {', '.join(names)}."


# region Markup
# D-220: the pipeline on top and, under each stop, the dimensions watched there, in order.
COLUMNS = [["completitud"], ["actualidad"], ["validez", "pruebas"], ["consistencia", "unicidad"]]
PLACES = {key: index for index, keys in enumerate(COLUMNS) for key in keys}
SPINE = [
    ("Fuentes", "ODEPA e INE", ["odepa", "ine"], "descarga"),
    ("Aterrizaje y bronce", "raw.db y Parquet", ["sqlite", "apacheparquet"], "lee dbt"),
    ("dbt", "reglas, modelos y pruebas", ["dbt"], "publica"),
    ("datos.duckdb", "la base que lee el panel", ["duckdb"], ""),
]
ABOUT = (("Propósito", "Detectar a tiempo que algo está mal, antes de usar una cifra."),
         ("Cómo se lee", "Bajo cada etapa del pipeline van las dimensiones que se vigilan en ella. Cada cifra se mide en la base de esta "
                         "carga y se juzga contra el umbral que lleva debajo. Pasa el cursor para ver cómo se mide."),
         ("Quién la usa", "Quien opera el pipeline y decide si una carga puede publicarse."))


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"], palette["card"],
                                              palette["card_border"], palette["accent"])
    colors = {"ok": quality_view.PILL_COLORS["ok"], "warn": quality_view.PILL_COLORS["pending"],
              "fail": quality_view.PILL_COLORS["fail"], "info": muted}
    shade = "rgba(0,0,0,.55)" if dark else "rgba(15,40,90,.2)"
    states = "".join(f".ql .s-{key}{{--c:{color};}}" for key, color in colors.items())
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:300 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
{states}
.ql {{ padding:2px 2px 6px; }}
.ql .top {{ display:flex; align-items:center; gap:10px; margin:0 0 6px; color:{ink}; font-size:14px; }}
.ql .top i.ok {{ width:20px; height:20px; border-radius:50%; background:var(--c); color:#fff; display:inline-grid; place-items:center;
  font:700 12px/1 sans-serif; font-style:normal; flex:none; box-shadow:0 0 0 4px color-mix(in srgb, var(--c) 22%, transparent); }}
.ql .about {{ position:relative; margin-left:auto; flex:none; }}
.ql .about > span {{ display:inline-grid; place-items:center; width:20px; height:20px; border-radius:50%; border:1px solid {muted}; color:{muted};
  font:500 12px/1 serif; font-style:italic; cursor:default; }}
.ql .about .tip {{ top:calc(100% + 6px); right:0; left:auto; width:340px; }}
.ql .about:hover .tip, .ql .about:focus-within .tip {{ display:block; }}
.ql .stage {{ display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); column-gap:26px; align-items:start; }}
.ql .cell {{ position:relative; min-height:0; }}
.ql .gate {{ position:relative; padding:4px 2px 0; }}
.ql .gate:hover, .ql .gate:focus-within {{ z-index:30; }}
.ql .gh {{ display:flex; align-items:center; gap:10px; margin-bottom:4px; }}
.ql .qa-icon {{ width:46px; height:46px; flex:none; filter:drop-shadow(0 7px 7px {shade}); }}
.ql .gh b {{ display:block; font-size:15px; font-weight:500; color:{ink}; line-height:1.2; }}
.ql .gh small {{ display:block; color:{muted}; font-size:11.5px; line-height:1.25; }}
.ql .ind {{ position:relative; display:grid; grid-template-columns:9px 1fr auto; gap:0 8px; padding:3px 0; cursor:default; outline:none; }}
.ql .ind > i {{ width:8px; height:8px; margin-top:6px; border-radius:50%; background:var(--c); box-shadow:0 0 0 3px color-mix(in srgb, var(--c) 22%, transparent); }}
.ql .ind span {{ color:{ink}; font-size:12.5px; }}
.ql .ind strong {{ font-weight:500; color:{ink}; font-variant-numeric:tabular-nums; font-size:13px; text-align:right; }}
.ql .ind em {{ grid-column:2 / 4; color:{muted}; font-size:11px; font-style:normal; line-height:1.3; }}
.ql .tip {{ position:absolute; z-index:60; left:0; top:calc(100% + 2px); width:270px; padding:10px 12px; border-radius:12px; background:{card};
  border:1px solid {border}; box-shadow:0 18px 36px -14px rgba(0,0,0,.65); font-size:12px; line-height:1.45; color:{text}; white-space:pre-wrap;
  display:none; pointer-events:none; text-align:left; font-weight:300; }}
.ql .ind:hover .tip, .ql .ind:focus .tip {{ display:block; }}
.ql .c3 .tip, .ql .c4 .tip, .ql .c2 .gate .tip {{ left:auto; right:0; }}
.ql .low .tip {{ top:auto; bottom:calc(100% + 2px); }}
.ql .spine {{ position:relative; display:flex; flex-direction:column; align-items:center; text-align:center; padding:0; }}
.ql .stem {{ width:2px; height:16px; background:var(--c, {accent}); opacity:.75; border-radius:2px; }}
.ql .stem.none {{ background:transparent; }}
.ql .logos {{ display:flex; gap:6px; justify-content:center; align-items:center; height:58px; }}
.ql .logos .logo {{ width:58px; height:58px; filter:drop-shadow(0 9px 8px {shade}); }}
.ql .logos.two .logo {{ width:50px; height:50px; }}
.ql .spine b {{ margin-top:3px; font-size:13px; font-weight:500; color:{ink}; }}
.ql .spine small {{ color:{muted}; font-size:11px; line-height:1.2; }}
.ql .link {{ position:absolute; top:calc(16px + 29px); left:calc(50% + 62px); width:calc(100% - 124px + 26px); height:2px; background:{accent}; opacity:.85; }}
.ql .link::after {{ content:""; position:absolute; right:-1px; top:-4px; border:5px solid transparent; border-left:8px solid {accent}; border-right:0; }}
.ql .link span {{ position:absolute; left:0; right:0; top:-17px; text-align:center; font-size:10.5px; color:{muted}; }}
.ql .side h4 {{ margin:2px 0 3px; font-size:10.5px; font-weight:500; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.ql .line {{ display:flex; justify-content:space-between; gap:8px; padding:2px 0; color:{ink}; font-size:12px; font-variant-numeric:tabular-nums; position:relative; outline:none; }}
.ql .line code {{ font:400 11px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; }}
.ql .line small {{ color:{muted}; font-size:11px; }}
.ql .line:hover .tip, .ql .line:focus .tip {{ display:block; }}
.ql .side {{ padding-top:6px; }}
.ql .gates {{ display:flex; flex-direction:column; gap:14px; }}
.ql .bottom {{ display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); column-gap:26px; margin-top:16px; padding-top:10px;
  border-top:1px solid color-mix(in srgb, {border} 70%, transparent); }}
.ql .audit {{ margin-top:16px; padding-top:10px; border-top:1px solid color-mix(in srgb, {border} 70%, transparent); }}
.ql .audit > h4, .ql .bottom h4 {{ margin:2px 0 3px; font-size:10.5px; font-weight:500; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.ql .audit > h4 {{ text-align:center; }}
.ql .legend {{ margin:6px 0 0; font-size:11px; color:{muted}; text-align:center; }}
@media (max-width:820px) {{ .ql .stage {{ grid-template-columns:repeat(2, minmax(0, 1fr)); row-gap:10px; }} .ql .link {{ display:none; }} }}
</style>"""


def build_gate_html(key, rows, low=False):
    status = dimension_status([row[4] for row in rows])
    indicators = "".join(
        f'<div class="ind s-{state}" tabindex="0"><i></i><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong>'
        f'<em>{html.escape(reference)}</em><div class="tip" role="tooltip">{html.escape(detail)}</div></div>'
        for _, label, value, reference, state, detail in rows)
    return (f'<div class="gate s-{status}{" low" if low else ""}" title="{html.escape(STATUS_WORDS[status])}">'
            f'<div class="gh">{quality_view.build_icon_svg(ICONS[key])}<div><b>{TITLES[key]}</b>'
            f'<small>{QUESTIONS[key]}</small></div></div>{indicators}</div>')


def build_loads_html(runs):
    """The last loads as short lines: number, day, rows read and the change against the load before."""
    if not runs:
        return ""
    lines = []
    for position in range(len(runs) - 1, max(len(runs) - 5, -1), -1):
        run_id, started, status, read, loaded, rejected = runs[position]
        previous = runs[position - 1][3] if position else None
        change = "" if previous is None else (f" (+{thousands(read - previous)})" if read >= previous else f" (−{thousands(previous - read)})")
        day = str(started)[:10]
        tip = (f"Carga {run_id} · {day} · {status}: leyó {thousands(read)} filas, cargó {thousands(loaded)} y rechazó {thousands(rejected)}.")
        lines.append(f'<div class="line" tabindex="0"><span>{run_id} · {html.escape(day[5:])}'
                     f'{"" if status == "LOADED" else " · " + html.escape(status)}</span>'
                     f'<span>{thousands(read)}<small>{change}</small></span><div class="tip" role="tooltip">{html.escape(tip)}</div></div>')
    return '<div class="side low"><h4>Cargas · filas leídas</h4>' + "".join(lines) + "</div>"


def build_apart_html(rejections, flags):
    """What was set aside and why: rejected rows and marked prices, one line each."""
    lines = []
    for reason, source, count in rejections:
        what = REASONS.get(reason, "motivo registrado por la validación")
        origin = "mayorista" if source == "wholesale" else "consumidor"
        lines.append(f'<div class="line" tabindex="0"><span><code>{html.escape(reason)}</code></span><span>{thousands(count)}</span>'
                     f'<div class="tip" role="tooltip">Filas rechazadas: {html.escape(what)}, fuente {origin}. No entran a la base; '
                     f'quedan en la tabla rejection con su fila original.</div></div>')
    for name, count in sorted(flags.items(), key=lambda item: -item[1]):
        if name != "SIN_MARCA":
            lines.append(f'<div class="line" tabindex="0"><span><code>{html.escape(name)}</code></span><span>{thousands(count)}</span>'
                         f'<div class="tip" role="tooltip">Precios marcados: {html.escape(FLAGS.get(name, "marca de calidad"))}. '
                         'Entran a la base, pero quedan fuera de los indicadores.</div></div>')
    return '<div class="side low"><h4>Qué se apartó y por qué</h4>' + ("".join(lines) or '<div class="line"><span>Nada apartado.</span></div>') + "</div>"


def build_node_html(index, title, subtitle, logos, label, up, down):
    """A pipeline stop: the stems carry the status of the gate that hangs above or below it."""
    marks = "".join(database_map.source_logo(slug) if slug in ("odepa", "ine") else database_map.brand_logo(slug, f"-q{index}")
                    for slug in logos)
    link = f'<span class="link"><span>{html.escape(label)}</span></span>' if label else ""
    return (f'<div class="cell spine"><div class="stem s-{up or "info"}{"" if up else " none"}"></div>'
            f'<div class="logos{" two" if len(logos) > 1 else ""}">{marks}</div><b>{html.escape(title)}</b>'
            f'<small>{html.escape(subtitle)}</small><div class="stem s-{down or "info"}{"" if down else " none"}"></div>{link}</div>')


def build_page_html(palette, indicators, runs, rejections, flags, controls_html=""):
    """The whole «Calidad» view as one HTML document for st.iframe (D-220): the pipeline in one
    line, each stop's dimensions in its column under it, then what was set apart and the loads
    side by side, and the audit controls last. No cards."""
    kind, sentence = build_verdict(indicators)
    groups = {key: rows for key, rows in group_indicators(indicators).items() if rows}
    status = {key: dimension_status([row[4] for row in rows]) for key, rows in groups.items()}
    down = [dimension_status([status[key] for key in keys if key in status]) if any(key in status for key in keys) else None
            for keys in COLUMNS]
    spine = "".join(build_node_html(index, *node[:3], node[3], None, down[index]) for index, node in enumerate(SPINE))
    gates = "".join(f'<div class="cell c{index + 1}"><div class="gates">'
                    + "".join(build_gate_html(key, groups[key]) for key in keys if key in groups) + "</div></div>"
                    for index, keys in enumerate(COLUMNS))
    bottom = f'<div class="bottom">{build_apart_html(rejections, flags)}{build_loads_html(runs)}</div>'
    audit = (f'<div class="audit"><h4>Controles de auditoría</h4>{controls_html}<p class="legend">✓ comprobado aquí · '
             '! no se puede comprobar en este servidor o tiene una observación · nada se muestra como verificado sin '
             'comprobarse.</p></div>') if controls_html else ""
    about = ('<div class="about" tabindex="0"><span>i</span><div class="tip" role="tooltip">'
             + "".join(f"<b>{title}.</b> {html.escape(text)}\n" for title, text in ABOUT).rstrip("\n") + '</div></div>')
    verdict = f'<div class="top s-{kind}"><i class="ok">{"✓" if kind == "ok" else "!"}</i>{html.escape(sentence)}{about}</div>'
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + (f"<style>{audit_trace.build_controls_css(palette)}</style>" if controls_html else "")
            + '</head><body>' + quality_view.DEFS
            + f'<div class="ql">{verdict}<div class="stage">{spine}{gates}</div>{bottom}{audit}</div></body></html>')
# endregion
