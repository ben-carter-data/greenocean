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
                 "Combinaciones de semana, producto, región, canal y unidad con más de una fila.\n" + quality.DUPLICATES_SQL))
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
                 "Precios utilizables con precio nulo o no positivo, unidad vacía o fecha que no es lunes.\n" + quality.INVALID_SQL))
    # Consistency
    rows.append(("consistencia", "Referencias sin destino", thousands(measures["foreign_keys"]),
                 "toda clave apunta a una fila que existe", "ok" if measures["foreign_keys"] == 0 else "fail",
                 "Precios sin producto, región, canal o fecha, y rechazos sin carga.\n" + quality.FOREIGN_KEYS_SQL))
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
def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"], palette["card"],
                                              palette["card_border"], palette["accent"])
    colors = {"ok": quality_view.PILL_COLORS["ok"], "warn": quality_view.PILL_COLORS["pending"],
              "fail": quality_view.PILL_COLORS["fail"], "info": muted}
    raised = ("0 1px 0 rgba(255,255,255,.06) inset, 0 22px 44px -28px rgba(0,0,0,.9)" if dark
              else "0 1px 0 #fff inset, 0 22px 44px -30px rgba(15,27,45,.45), 0 6px 12px -10px rgba(15,27,45,.2)")
    shade = "rgba(0,0,0,.55)" if dark else "rgba(15,40,90,.18)"
    states = "".join(f".ql .s-{key}{{--c:{color};}}" for key, color in colors.items())
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:300 13.5px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
{states}
.ql {{ padding:4px 2px 8px; }}
.ql .about {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:10px 22px; margin:2px 0 14px; }}
.ql .about div {{ padding-left:12px; border-left:2px solid color-mix(in srgb, {accent} 55%, transparent); }}
.ql .about b {{ display:block; font-size:10px; font-weight:500; letter-spacing:.11em; text-transform:uppercase; color:{muted}; margin-bottom:2px; }}
.ql .verdict {{ display:flex; align-items:center; gap:10px; margin:0 0 16px; padding:9px 16px; border-radius:12px; border:1px solid {border};
  background:linear-gradient(180deg, color-mix(in srgb, var(--c) {'16%' if dark else '9%'}, {card}), {card}); color:{ink}; font-size:14px; }}
.ql .verdict i {{ width:18px; height:18px; border-radius:50%; background:var(--c); color:#fff; display:inline-grid; place-items:center;
  font:700 11px/1 sans-serif; font-style:normal; flex:none; }}
.ql .grid {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:14px; }}
.ql .group {{ position:relative; padding:14px 16px 12px; border-radius:18px; border:1px solid {border}; box-shadow:{raised};
  background:linear-gradient(180deg, color-mix(in srgb, {card} 92%, {'#fff' if not dark else '#000'}), {card}); }}
.ql .group:hover, .ql .group:focus-within {{ z-index:20; }}
.ql .head {{ display:flex; align-items:center; gap:12px; margin-bottom:8px; }}
.ql .qa-icon {{ width:56px; height:56px; flex:none; filter:drop-shadow(0 8px 8px {shade}); }}
.ql .head b {{ display:block; font-size:15.5px; font-weight:500; color:{ink}; }}
.ql .head small {{ display:block; color:{muted}; font-size:12px; line-height:1.3; }}
.ql .badge {{ margin-left:auto; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:500; color:#fff; white-space:nowrap;
  background:linear-gradient(180deg, color-mix(in srgb, var(--c) 82%, #fff), var(--c)); }}
.ql .ind {{ position:relative; display:grid; grid-template-columns:10px 1fr auto; gap:0 10px; padding:7px 0; border-top:1px solid color-mix(in srgb, {border} 70%, transparent);
  cursor:default; outline:none; }}
.ql .ind > i {{ width:9px; height:9px; margin-top:6px; border-radius:50%; background:var(--c); box-shadow:0 0 0 3px color-mix(in srgb, var(--c) 22%, transparent); }}
.ql .ind span {{ color:{ink}; font-size:13px; }}
.ql .ind em {{ grid-column:2; color:{muted}; font-size:11.5px; font-style:normal; line-height:1.35; }}
.ql .ind strong {{ grid-row:1; grid-column:3; font-weight:500; color:{ink}; font-variant-numeric:tabular-nums; font-size:13.5px; text-align:right; }}
.ql .tip {{ position:absolute; z-index:30; left:10px; right:10px; top:calc(100% + 2px); padding:10px 12px; border-radius:12px; background:{card};
  border:1px solid {border}; box-shadow:0 18px 36px -16px rgba(0,0,0,.6); font-size:12px; line-height:1.45; color:{text}; white-space:pre-wrap;
  opacity:0; pointer-events:none; transition:opacity .15s ease; font-family:inherit; }}
.ql .ind:hover .tip, .ql .ind:focus .tip {{ opacity:1; }}
.ql .tip code {{ font:400 11px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; }}
.ql h3 {{ margin:20px 0 8px; font-size:10.5px; font-weight:500; letter-spacing:.11em; text-transform:uppercase; color:{muted}; }}
.ql .bottom {{ display:grid; grid-template-columns:1.1fr 1fr; gap:14px; }}
.ql .panel {{ padding:12px 16px 10px; border-radius:18px; border:1px solid {border}; box-shadow:{raised}; background:{card}; }}
.ql .panel h3 {{ margin:0 0 8px; }}
.ql table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
.ql th {{ text-align:right; font-weight:400; color:{muted}; font-size:11px; padding:2px 6px 5px; }} .ql th:first-child, .ql td:first-child {{ text-align:left; }}
.ql td {{ text-align:right; padding:4px 6px; border-top:1px solid color-mix(in srgb, {border} 60%, transparent); font-variant-numeric:tabular-nums; color:{ink}; }}
.ql td.change {{ color:{muted}; }}
.ql .reason {{ display:flex; justify-content:space-between; gap:10px; padding:5px 0; border-top:1px solid color-mix(in srgb, {border} 60%, transparent); color:{ink}; font-size:13px; }}
.ql .reason code {{ font:400 11.5px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; }}
.ql .reason small {{ display:block; color:{muted}; font-size:11.5px; }}
.ql .note {{ margin:8px 0 0; color:{muted}; font-size:11.5px; }}
@media (max-width:900px) {{ .ql .grid, .ql .about, .ql .bottom {{ grid-template-columns:1fr; }} }}
</style>"""


def build_group_html(key, rows):
    status = dimension_status([row[4] for row in rows])
    indicators = "".join(
        f'<div class="ind s-{state}" tabindex="0"><i></i><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong>'
        f'<em>{html.escape(reference)}</em><div class="tip" role="tooltip">{html.escape(detail)}</div></div>'
        for _, label, value, reference, state, detail in rows)
    return (f'<section class="group s-{status}"><div class="head">{quality_view.build_icon_svg(ICONS[key])}'
            f'<div><b>{TITLES[key]}</b><small>{QUESTIONS[key]}</small></div>'
            f'<span class="badge">{STATUS_WORDS[status]}</span></div>{indicators}</section>')


def build_runs_html(runs):
    """The load history with the change of each load against the one before."""
    if not runs:
        return ""
    body = []
    for position, (run_id, started, status, read, loaded, rejected) in enumerate(runs):
        previous = runs[position - 1][3] if position else None
        change = "—" if previous is None else (f"+{thousands(read - previous)}" if read >= previous else f"−{thousands(previous - read)}")
        body.append(f"<tr><td>{run_id} · {html.escape(str(started)[:10])}{'' if status == 'LOADED' else ' · ' + html.escape(status)}</td>"
                    f"<td>{thousands(read)}</td><td class=\"change\">{change}</td><td>{thousands(loaded)}</td><td>{thousands(rejected)}</td></tr>")
    return ('<table><tr><th>Carga</th><th>Leídas</th><th>Cambio</th><th>Cargadas</th><th>Rechazadas</th></tr>'
            + "".join(reversed(body)) + "</table>")


def build_rejections_html(rejections):
    if not rejections:
        return '<div class="reason"><span>Ninguna fila rechazada en la base.</span></div>'
    return "".join(
        f'<div class="reason"><span><code>{html.escape(reason)}</code><small>{html.escape(REASONS.get(reason, "motivo registrado por la validación"))}'
        f' · fuente {"mayorista" if source == "wholesale" else "consumidor"}</small></span><b>{thousands(count)}</b></div>'
        for reason, source, count in rejections)


def build_page_html(palette, indicators, runs, rejections, flags):
    """The whole «Calidad» view as one HTML document for st.iframe."""
    kind, sentence = build_verdict(indicators)
    groups = "".join(build_group_html(key, rows) for key, rows in group_indicators(indicators).items() if rows)
    about = ('<div class="about"><div><b>Propósito</b>Detectar a tiempo que algo está mal, antes de usar una cifra.</div>'
             '<div><b>Cómo se lee</b>Cada indicador se mide en la base de esta carga y se juzga contra el umbral que aparece '
             'debajo. Pasa el cursor para ver cómo se mide.</div>'
             '<div><b>Quién la usa</b>Quien opera el pipeline y decide si una carga puede publicarse.</div></div>')
    verdict = f'<div class="verdict s-{kind}"><i>{"✓" if kind == "ok" else "!"}</i>{html.escape(sentence)}</div>'
    marks = "".join(f'<div class="reason"><span><code>{html.escape(name)}</code><small>{html.escape(FLAGS.get(name, "marca de calidad"))}</small></span>'
                    f'<b>{thousands(count)}</b></div>' for name, count in sorted(flags.items(), key=lambda item: -item[1])
                    if name != "SIN_MARCA")
    bottom = ('<div class="bottom"><div class="panel"><h3>Historial de cargas</h3>' + build_runs_html(runs)
              + '</div><div class="panel"><h3>Qué se apartó y por qué</h3>' + build_rejections_html(rejections) + marks
              + '<p class="note">Las filas rechazadas no entran a la base. Los precios marcados sí entran, pero quedan fuera de los '
                'indicadores.</p></div></div>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + '</head><body>' + quality_view.DEFS
            + f'<div class="ql">{about}{verdict}<div class="grid">{groups}</div>{bottom}</div></body></html>')
# endregion
