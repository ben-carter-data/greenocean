"""«Calidad» (D-194): is the published data good today? Measured on the real database.

Six dimensions (completeness, uniqueness, validity, consistency, timeliness and the dbt
tests), each with the indicators that measure it, the value read from datos.duckdb on
every load, the reference it is judged against and a verdict in words. Where a figure
can be compared with the previous load, it is. Nothing here is written by hand except
the thresholds, which are the project's own and are shown beside each figure.

read_measures() reads the database; build_page_html() draws the measures as one HTML
document for st.iframe (CSS only, no script), laid out by the three quality gates of the pipeline (D-245, D-256):
each indicator under the gate that watches it, then what was set aside, the last loads and the audit controls.
Both are pure enough to test without a server.
"""
import html
from datetime import date, datetime, timezone

from bi import charts, queries, quality, quality_view

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
# D-256: the page follows the path of the data. Each of the three gates of D-245 shows what it stops and, under it,
# the dimensions watched there: (gate, question it answers, dimensions).
GATE_VIEW = [
    ("Puerta 1 · el archivo", "¿El dato llegó completo y al día?", ["completitud", "actualidad"]),
    ("Puerta 2 · cada fila", "¿Cada fila es válida?", ["validez"]),
    ("Puerta 3 · la base", "¿La base publicada es coherente y pasó sus pruebas?", ["consistencia", "unicidad", "pruebas"]),
]
# The three gates of D-245: (title, what is stopped, what happens to the data, where, evidence).
GATES = [
    ("Puerta 1 · el archivo",
     "Un CSV vacío o con columnas distintas no se guarda; un archivo con muchas menos filas que el anterior o una semana "
     "faltante detiene la carga.",
     "No entra nada de ese archivo y la base publicada no cambia.",
     "agent/agent.py y etl/etl.py", "tests/test_agent.py, tests/test_etl_run.py"),
    ("Puerta 2 · cada fila",
     "Un precio no positivo o con formato inválido se rechaza; una unidad no convertible o un precio atípico se marca.",
     "La fila rechazada queda en la tabla rejection con su motivo; el precio marcado queda en la base, fuera de los "
     "indicadores.",
     "modelos intermedios de dbt (int_prices__validated, int_prices__outlier_flagged)", "pruebas de dbt"),
    ("Puerta 3 · la base",
     "Si falla una prueba de dbt, si la carga lee menos del 90 % de la anterior o si pytest falla sobre la base nueva "
     "(incluida la paridad con SQLite), la base no se publica.",
     "La base publicada sigue igual y la carga queda en etl_run como fallida.",
     "etl/pipeline.py y .github/workflows/semanal.yml", "tests/test_pipeline_gate.py"),
]
SOURCES = {"wholesale": "mayorista", "consumer": "consumidor"}
# The six dimensions of data quality around healthy data (D-256): (key, name, icon, side). The first five are measured by the
# indicators; accuracy is measured by the audit controls of the «Resultados» step, which check the figures against the source.
HUB = [("exactitud", "Exactitud", "calculator", "left"), ("validez", "Validez", "shield", "left"),
       ("unicidad", "Unicidad", "database", "left"), ("actualidad", "Actualidad", "gear", "right"),
       ("completitud", "Completitud", "calendar", "right"), ("consistencia", "Consistencia", "parity", "right")]
RESULTS_STEP = "Resultados"


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"], palette["card"],
                                              palette["card_border"], palette["accent"])
    colors = {"ok": quality_view.PILL_COLORS["ok"], "warn": quality_view.PILL_COLORS["pending"],
              "fail": quality_view.PILL_COLORS["fail"], "info": muted}
    states = "".join(f".qp .s-{key}{{--c:{color};}}" for key, color in colors.items())
    states += "".join(f".qp .k-{key}{{--c:{color};}}" for key, color in quality_view.PILL_COLORS.items())
    shade = "rgba(0,0,0,.5)" if dark else "rgba(15,40,90,.18)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:400 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
{states}
.qp {{ padding:2px 2px 8px; }}
.qp .verdict {{ display:flex; align-items:center; gap:12px; margin:0 0 20px; font-size:16px; color:{ink}; }}
.qp .verdict i {{ width:24px; height:24px; border-radius:50%; background:var(--c); color:#fff; display:inline-grid; place-items:center;
  font:700 14px/1 sans-serif; font-style:normal; flex:none; box-shadow:0 0 0 5px color-mix(in srgb, var(--c) 22%, transparent); }}
.qp h2 {{ display:flex; align-items:center; gap:10px; margin:26px 0 4px; font-size:17px; font-weight:600; color:{ink}; }}
.qp h2 b {{ display:inline-grid; place-items:center; width:26px; height:26px; border-radius:50%; background:{accent}; color:{palette['background']};
  font:700 13px/1 sans-serif; flex:none; }}
.qp .lead {{ margin:0 0 14px 36px; color:{muted}; font-size:13.5px; }}
.qp svg.hub {{ display:block; width:100%; height:auto; margin:0 0 4px; }}
.qp .gates {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:16px; align-items:stretch; }}
.qp .gate {{ display:flex; flex-direction:column; border:1px solid {border}; border-radius:16px; background:{card}; padding:16px 18px;
  box-shadow:0 12px 24px -18px {shade}; }}
.qp .gate h3 {{ margin:0; font-size:16px; font-weight:600; color:{ink}; }}
.qp .gate .q {{ margin:2px 0 8px; color:{accent}; font-size:13.5px; font-weight:500; }}
.qp .gate .stops {{ margin:0 0 4px; font-size:13px; color:{text}; }}
.qp .gate .stops b, .qp .gate .where b {{ color:{ink}; font-weight:600; }}
.qp .gate .where {{ margin:auto 0 0; padding-top:10px; border-top:1px solid {border}; font-size:12.5px; color:{muted}; }}
.qp .gate .where code {{ font:400 12px ui-monospace, SFMono-Regular, Menlo, monospace; color:{ink}; overflow-wrap:anywhere; }}
.qp .dim {{ display:flex; align-items:center; gap:8px; margin:14px 0 2px; font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:{muted}; }}
.qp .dim .qa-icon {{ width:24px; height:24px; flex:none; filter:drop-shadow(0 3px 3px {shade}); }}
.qp .ind {{ display:grid; grid-template-columns:10px 1fr auto; gap:0 10px; align-items:baseline; padding:7px 0; border-bottom:1px solid color-mix(in srgb, {border} 60%, transparent); cursor:default; }}
.qp .ind:last-of-type {{ border-bottom:0; }}
.qp .ind > i {{ width:10px; height:10px; border-radius:50%; background:var(--c); box-shadow:0 0 0 3px color-mix(in srgb, var(--c) 22%, transparent); align-self:center; }}
.qp .ind span {{ color:{ink}; font-size:14px; }}
.qp .ind strong {{ font-size:16px; font-weight:600; color:{ink}; font-variant-numeric:tabular-nums; text-align:right; }}
.qp .ind em {{ grid-column:2 / 4; color:{muted}; font-size:12.5px; font-style:normal; line-height:1.35; }}
.qp .two {{ display:grid; grid-template-columns:minmax(0, 1.25fr) minmax(0, 1fr); gap:16px; margin-top:6px; }}
.qp table {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
.qp .panel {{ border:1px solid {border}; border-radius:16px; background:{card}; padding:6px 16px 10px; }}
.qp caption {{ text-align:left; padding:10px 0 6px; font-size:13px; font-weight:600; color:{ink}; }}
.qp th {{ text-align:left; padding:6px 8px 6px 0; font-size:11.5px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:{muted}; border-bottom:1px solid {border}; }}
.qp td {{ padding:8px 8px 8px 0; border-bottom:1px solid color-mix(in srgb, {border} 55%, transparent); vertical-align:top; color:{ink}; }}
.qp tr:last-child td {{ border-bottom:0; }}
.qp td.n, .qp th.n {{ text-align:right; padding-right:0; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.qp td small {{ display:block; color:{muted}; font-size:12.5px; }}
.qp code {{ font:500 12.5px ui-monospace, SFMono-Regular, Menlo, monospace; color:{ink}; }}
.qp .tag {{ display:inline-block; padding:1px 8px; border-radius:999px; font-size:12px; font-weight:600; color:var(--c);
  border:1px solid color-mix(in srgb, var(--c) 55%, transparent); background:color-mix(in srgb, var(--c) 12%, transparent); white-space:nowrap; }}
.qp .audit {{ border:1px solid {border}; border-radius:16px; background:{card}; padding:6px 16px 10px; }}
.qp .audit td.ic {{ width:40px; padding-right:6px; }}
.qp .audit td.ic .qa-icon {{ width:30px; height:30px; filter:drop-shadow(0 3px 3px {shade}); }}
.qp .audit tr.step td {{ padding:14px 0 4px; font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:{muted}; border-bottom:1px solid {border}; }}
.qp .audit td.st {{ white-space:nowrap; }}
.qp .legend {{ margin:10px 0 0; font-size:12.5px; color:{muted}; }}
@media (max-width:900px) {{ .qp .gates, .qp .two {{ grid-template-columns:1fr; }} }}
</style>"""


def hub_measure(key, indicators, columns):
    """(status, headline) of one dimension: its indicators, or for accuracy the audit controls of the results step."""
    if key == "exactitud":
        cards = next((cards for step, cards in columns if step == RESULTS_STEP), [])
        if not cards:
            return "info", "sin controles aquí"
        kinds = [quality_view.classify(card[2]) for card in cards]
        status = "fail" if "fail" in kinds else "warn" if "pending" in kinds else "ok"
        return status, f"{kinds.count('ok')} de {len(kinds)} controles verificados"
    rows = [row for row in indicators if row[0] == key]
    judged = [row for row in rows if row[4] != "info"]
    if not rows:
        return "info", "sin indicadores"
    return dimension_status([row[4] for row in rows]), f"{sum(row[4] == 'ok' for row in judged)} de {len(judged)} indicadores bien"


def build_hub_html(palette, indicators, columns):
    """The six dimensions around healthy data, each with its status and how many of its measures pass."""
    ink, muted, card, border, accent = (palette["strong_text"], palette["reference"], palette["card"], palette["card_border"],
                                        palette["accent"])
    colors = {"ok": quality_view.PILL_COLORS["ok"], "warn": quality_view.PILL_COLORS["pending"],
              "fail": quality_view.PILL_COLORS["fail"], "info": muted}
    width, height, cx, cy, radius = 1000, 318, 500, 159, 84
    box_w, box_h = 292, 70
    parts, lines = [], []
    rows = {"left": 0, "right": 0}
    for key, name, icon, side in HUB:
        row = rows[side]
        rows[side] += 1
        x = 12 if side == "left" else width - 12 - box_w
        y = 14 + row * 100
        status, headline = hub_measure(key, indicators, columns)
        color = colors[status]
        edge = x + box_w if side == "left" else x
        lines.append(f'<line x1="{edge}" y1="{y + box_h / 2}" x2="{cx}" y2="{cy}" stroke="{color}" stroke-width="1.8" stroke-opacity=".75"/>'
                     f'<circle cx="{edge}" cy="{y + box_h / 2}" r="5" fill="{card}" stroke="{color}" stroke-width="2"/>')
        icon_svg = quality_view.build_icon_svg(icon).replace('<svg class="qa-icon" ', f'<svg x="{x + 14}" y="{y + 15}" width="40" height="40" ', 1)
        parts.append(f'<g><title>{html.escape(name)}: {html.escape(headline)}</title>'
                     f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="35" fill="{card}" stroke="{color}" stroke-width="1.6"/>'
                     f'{icon_svg}<text x="{x + 66}" y="{y + 31}" font-size="17" font-weight="700" fill="{ink}">{html.escape(name)}</text>'
                     f'<text x="{x + 66}" y="{y + 53}" font-size="13.5" fill="{muted}">{html.escape(headline)}</text>'
                     f'<circle cx="{x + box_w - 26}" cy="{y + box_h / 2}" r="7" fill="{color}"/></g>')
    centre = (f'<defs><radialGradient id="qa-hub" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="#4a8df0"/>'
              f'<stop offset="1" stop-color="#0d3b96"/></radialGradient></defs>'
              f'<circle cx="{cx}" cy="{cy}" r="{radius + 10}" fill="{accent}" fill-opacity=".14"/>'
              f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="url(#qa-hub)"/>'
              + quality_view.build_icon_svg("database").replace('<svg class="qa-icon" ', f'<svg x="{cx - 28}" y="{cy - 52}" width="56" height="56" ', 1)
              + f'<text x="{cx}" y="{cy + 32}" text-anchor="middle" font-size="19" font-weight="700" fill="#fff">Datos sanos</text>'
              f'<text x="{cx}" y="{cy + 52}" text-anchor="middle" font-size="12.5" fill="#cfe0ff">6 dimensiones</text>')
    return (f'<svg class="hub" viewBox="0 0 {width} {height}" role="img" aria-label="Las seis dimensiones de la calidad de los datos" '
            f'font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">{"".join(lines)}{centre}{"".join(parts)}</svg>')


def build_indicator_html(label, value, reference, state, detail):
    return (f'<div class="ind s-{state}" title="{html.escape(STATUS_WORDS[state])} · {html.escape(detail)}"><i></i>'
            f'<span>{html.escape(label)}</span><strong>{html.escape(value)}</strong><em>{html.escape(reference)}</em></div>')


def build_gate_html(index, groups):
    title, question, keys = GATE_VIEW[index]
    _, stops, outcome, where, evidence = GATES[index]
    body = "".join(f'<div class="dim">{quality_view.build_icon_svg(ICONS[key])}{html.escape(TITLES[key])}</div>'
                   + "".join(build_indicator_html(*row[1:]) for row in groups[key]) for key in keys if key in groups)
    return (f'<div class="gate" title="Si no pasa: {html.escape(outcome)}"><h3>{html.escape(title)}</h3>'
            f'<div class="q">{html.escape(question)}</div><p class="stops"><b>Detiene:</b> {html.escape(stops)}</p>{body}'
            f'<p class="where"><b>Dónde:</b> <code>{html.escape(where)}</code></p></div>')


def build_apart_html(rejections, flags):
    """What was set aside, one row per reason: rejected rows (out of the base) and marked prices (in the base, out of the indicators)."""
    rows = []
    for reason, source, count in rejections:
        rows.append(f'<tr><td><code>{html.escape(reason)}</code><small>{html.escape(REASONS.get(reason, "motivo registrado por la validación"))}'
                    f' · fuente {SOURCES.get(source, html.escape(str(source)))}</small></td>'
                    f'<td><span class="tag s-fail">Rechazada</span><small>queda en <code>rejection</code>, fuera de la base</small></td>'
                    f'<td class="n">{thousands(count)}</td></tr>')
    for name, count in sorted(flags.items(), key=lambda item: -item[1]):
        if name != "SIN_MARCA":
            rows.append(f'<tr><td><code>{html.escape(name)}</code><small>{html.escape(FLAGS.get(name, "marca de calidad"))}</small></td>'
                        f'<td><span class="tag s-warn">Marcada</span><small>queda en la base, fuera de los indicadores</small></td>'
                        f'<td class="n">{thousands(count)}</td></tr>')
    body = "".join(rows) or '<tr><td colspan="3">Nada apartado.</td></tr>'
    return ('<div class="panel"><table><caption>Qué se apartó y por qué</caption><thead><tr><th>Motivo</th><th>Qué pasa</th>'
            f'<th class="n">Filas</th></tr></thead><tbody>{body}</tbody></table></div>')


def build_loads_html(runs):
    """The last five loads, newest first: number, day, state, rows read and the change against the load before."""
    rows = []
    for position in range(len(runs) - 1, max(len(runs) - 6, -1), -1):
        run_id, started, status, read, loaded, rejected = runs[position]
        previous = runs[position - 1][3] if position else None
        change = "—" if previous is None else (f"+{thousands(read - previous)}" if read >= previous else f"−{thousands(previous - read)}")
        day = str(started)[:10]
        rows.append(f'<tr title="Carga {run_id}: leyó {thousands(read)} filas, cargó {thousands(loaded)} y rechazó {thousands(rejected)}">'
                    f'<td>{run_id}<small>{day[8:10]}-{day[5:7]}-{day[:4]}</small></td>'
                    f'<td><span class="tag k-{"ok" if status == "LOADED" else "fail"}">{"Cargada" if status == "LOADED" else html.escape(status)}</span></td>'
                    f'<td class="n">{thousands(read)}</td><td class="n">{change}</td></tr>')
    body = "".join(rows) or '<tr><td colspan="4">Sin cargas registradas.</td></tr>'
    return ('<div class="panel"><table><caption>Últimas cargas</caption><thead><tr><th>Carga</th><th>Estado</th>'
            f'<th class="n">Filas leídas</th><th class="n">Cambio</th></tr></thead><tbody>{body}</tbody></table></div>')


def build_audit_html(columns):
    """The audit controls by step, one row each: its mark, what it is, its status and what it found."""
    rows = []
    for step, cards in columns:
        rows.append(f'<tr class="step"><td colspan="4">{html.escape(step)}</td></tr>')
        for icon, title, status, detail, why in cards:
            kind = quality_view.classify(status)
            rows.append(f'<tr title="{html.escape(why)}"><td class="ic">{quality_view.build_icon_svg(icon)}</td>'
                        f'<td>{html.escape(title)}<small>{html.escape(detail)}</small></td>'
                        f'<td class="st"><span class="tag k-{kind}">{html.escape(status)}</span></td></tr>')
    return f'<div class="audit"><table><tbody>{"".join(rows)}</tbody></table></div>'


def build_page_html(palette, indicators, runs, rejections, flags, columns=()):
    """The whole «Calidad y auditoría» view as one HTML document for st.iframe (D-256): the verdict, the three
    gates with their indicators, what was set aside beside the last loads, and the audit controls last."""
    kind, sentence = build_verdict(indicators)
    groups = {key: rows for key, rows in group_indicators(indicators).items() if rows}
    verdict = f'<div class="verdict s-{kind}"><i>{"✓" if kind == "ok" else "!"}</i>{html.escape(sentence)}</div>'
    gates = "".join(build_gate_html(index, groups) for index in range(len(GATE_VIEW)))
    audit = (f'<h2><b>4</b> Controles de auditoría</h2><p class="lead">Lo que demuestra que lo publicado se puede rastrear y repetir. '
             f'Pasa el cursor por una fila para ver qué comprueba.</p>{build_audit_html(columns)}'
             '<p class="legend">Verificado: comprobado en este servidor · Pendiente: no se puede comprobar aquí o tiene una '
             'observación · nada se muestra como verificado sin comprobarse.</p>') if columns else ""
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + '</head><body>' + quality_view.DEFS
            + f'<div class="qp">{verdict}<h2><b>1</b> Las seis dimensiones de la calidad</h2>'
            '<p class="lead">Cada eje se mide en cada carga y se juzga contra su umbral. Pasa el cursor por un eje para ver cuántas de sus medidas pasan.</p>'
            f'{build_hub_html(palette, indicators, columns)}<h2><b>2</b> Las tres puertas: dónde se vigila el dato</h2>'
            '<p class="lead">El dato pasa por tres puertas antes de publicarse. Cada una detiene lo que no cumple, y debajo se '
            f'mide cuánto pasó.</p><div class="gates">{gates}</div>'
            f'<h2><b>3</b> Lo que se apartó y las últimas cargas</h2><div class="two">{build_apart_html(rejections, flags)}'
            f'{build_loads_html(runs)}</div>{audit}</div></body></html>')
# endregion
