"""«Calidad» (D-194): is the published data good today? Measured on the real database.

Six dimensions (completeness, uniqueness, validity, consistency, timeliness and the dbt
tests), each with the indicators that measure it, the value read from datos.duckdb on
every load, the reference it is judged against and a verdict in words. Where a figure
can be compared with the previous load, it is. Nothing here is written by hand except
the thresholds, which are the project's own and are shown beside each figure.

read_measures() reads the database; the build_*_html() functions draw the measures as HTML documents for st.iframe
(CSS only, no script). D-257: the main view is one diagram where each piece opens its detail in a pop-up (a CSS :target
sheet); what was set aside, the loads and the audit controls have their own tabs. D-273: that diagram is the pipeline of
quality: the rows of the latest load go through the three gates, each gate says which dimensions it measures, the rejected
rows leave at the second, and every gate flows into the verdict. All are pure enough to test without a server.
"""

import html
from datetime import date, datetime, timezone

from bi import charts, live_mark, quality, quality_metrics, quality_view, queries, static_files, weeks

# region Constants
# The project's thresholds, shown next to each figure so a verdict can be disputed.
LAST_WEEK_MIN_SHARE = 0.75  # rows of the latest week vs the median of the 8 before
REJECTED_MAX_SHARE = 0.01  # rows rejected over rows read
FLAGGED_MAX_SHARE = 0.05  # prices set apart (outliers, units) over all weekly prices
DATA_MAX_DAYS = 14  # days between the latest week and today
LOAD_MAX_DAYS = 9  # days since the last load: the cadence is weekly
REASONS = {"NON_POSITIVE_PRICE": "precio cero o negativo"}
FLAGS = {
    "ATIPICO": "precio atípico para su serie",
    "UNIDAD_NO_CONVERTIBLE": "unidad que no se puede llevar a kilo o unidad",
}
ICONS = {
    "completitud": "calendar",
    "unicidad": "database",
    "validez": "shield",
    "consistencia": "parity",
    "actualidad": "gear",
    "pruebas": "layers",
}
TITLES = {
    "completitud": "Completitud",
    "unicidad": "Unicidad",
    "validez": "Validez",
    "consistencia": "Consistencia",
    "actualidad": "Actualidad",
    "pruebas": "Pruebas dbt",
}
QUESTIONS = {
    "completitud": "¿Están todos los datos esperados?",
    "unicidad": "¿Ningún precio aparece dos veces?",
    "validez": "¿Cada valor tiene un formato y un rango permitidos?",
    "consistencia": "¿Los datos concuerdan entre sí?",
    "actualidad": "¿Son los últimos disponibles?",
    "pruebas": "¿Pasó cada prueba automática de dbt?",
}
STATUS_WORDS = {"ok": "Bien", "warn": "Revisar", "fail": "Falla", "info": "Informativo"}

WEEKS_SQL = (
    """SELECT week_start, count(*) AS filas FROM weekly_price GROUP BY week_start ORDER BY week_start DESC LIMIT 9"""
)
EXPECTED_WEEKS_SQL = (
    """SELECT date_diff('week', CAST(min(week_start) AS DATE), CAST(max(week_start) AS DATE)) + 1 FROM weekly_price"""
)
FLAGS_SQL = """SELECT COALESCE(flag, 'SIN_MARCA') AS marca, count(*) FROM weekly_price GROUP BY ALL"""
REJECTIONS_SQL = """SELECT reason, source, count(*) FROM rejection GROUP BY ALL ORDER BY 3 DESC"""
RUNS_SQL = """SELECT run_id, started_at, status, rows_read, rows_loaded, rows_rejected FROM etl_run ORDER BY run_id"""
TESTS_SQL = """SELECT r.status, count(*) FROM dbt_node AS n JOIN dbt_result AS r USING (unique_id)
WHERE n.resource_type = 'test' GROUP BY ALL"""


# The three gates of D-245 and the dimensions each watches: (gate, question it answers, dimensions). Accuracy has no
# indicator of its own: its controls run in pytest on the new base, before it is published, so it is watched at the third.
GATE_VIEW = [
    ("Puerta 1 · el archivo", "¿Llegó completo y al día?", ["completitud", "actualidad"]),
    ("Puerta 2 · cada fila", "¿Cada fila es válida?", ["validez"]),
    (
        "Puerta 3 · la base",
        "¿La base es coherente y pasó sus pruebas?",
        ["consistencia", "unicidad", "pruebas", "exactitud"],
    ),
]
# The three gates: (title, what is stopped, what happens to the data, where, evidence).
GATES = [
    (
        "Puerta 1 · el archivo",
        "Un CSV vacío o con columnas distintas no se guarda; un archivo con muchas menos filas que el anterior o una semana "
        "faltante detiene la carga.",
        "No entra nada de ese archivo y la base publicada no cambia.",
        "agent/agent.py y etl/etl.py",
        "tests/test_agent.py, tests/test_etl_run.py",
    ),
    (
        "Puerta 2 · cada fila",
        "Un precio no positivo o con formato inválido se rechaza; una unidad no convertible o un precio atípico se marca.",
        "La fila rechazada queda en la tabla rejection con su motivo; el precio marcado queda en la base, fuera de los "
        "indicadores.",
        "modelos intermedios de dbt (int_prices__validated, int_prices__outlier_flagged)",
        "pruebas de dbt",
    ),
    (
        "Puerta 3 · la base",
        "Si falla una prueba de dbt, si la carga lee menos del 90 % de la anterior o si pytest falla sobre la base nueva "
        "(incluida la paridad con SQLite), la base no se publica.",
        "La base publicada sigue igual: el workflow se detiene antes de publicarla, GitHub Actions lo marca en rojo y avisa "
        "al autor por correo (D-269).",
        "etl/pipeline.py y .github/workflows/semanal.yml",
        "tests/test_pipeline_gate.py",
    ),
]
SOURCES = {"wholesale": "mayorista", "consumer": "consumidor"}
# The six dimensions of data quality around healthy data: (key, name, icon, side). Five are measured by the indicators (the dbt
# tests count with consistency); accuracy is measured by the audit controls of the «Resultados» step, which check the
# figures against the source.
HUB = [
    ("exactitud", "Exactitud", "calculator", "left"),
    ("validez", "Validez", "shield", "left"),
    ("unicidad", "Unicidad", "database", "left"),
    ("actualidad", "Actualidad", "gear", "right"),
    ("completitud", "Completitud", "calendar", "right"),
    ("consistencia", "Consistencia", "parity", "right"),
]
HUB_DIMENSIONS = {"consistencia": ["consistencia", "pruebas"]}
HUB_QUESTIONS = dict(
    QUESTIONS,
    exactitud="¿Las cifras coinciden con la fuente?",
    consistencia="¿Los datos concuerdan entre sí y pasaron sus pruebas?",
)
RESULTS_STEP = "Resultados"
# What each gate box asks, short, so the diagram fits one screen; its pop-up and its hover ask the whole question.
GATE_BOX_QUESTIONS = ["¿Completo y al día?", "¿Cada fila es válida?", "¿Coherente y probada?"]
NUMBER_WORDS = {1: "un", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete"}
# endregion


# region Reading the measures
def read_measures(database_file=queries.DATABASE_FILE, backup_file=None):
    """Every raw figure of the page, from the database; the verdicts come later."""
    with queries.open_database(database_file) as connection:
        weeks, first, last = connection.execute(quality.COVERAGE_SQL).fetchone()
        measures = dict(
            weeks=weeks,
            first=first,
            last=last,
            expected_weeks=connection.execute(EXPECTED_WEEKS_SQL).fetchone()[0],
            per_week=connection.execute(WEEKS_SQL).fetchall(),
            total_rows=connection.execute("SELECT count(*) FROM weekly_price").fetchone()[0],
            flags=dict(connection.execute(FLAGS_SQL).fetchall()),
            rejections=connection.execute(REJECTIONS_SQL).fetchall(),
            runs=connection.execute(RUNS_SQL).fetchall(),
            tests=dict(connection.execute(TESTS_SQL).fetchall()),
            foreign_keys=connection.execute(quality.FOREIGN_KEYS_SQL).fetchone()[0],
            duplicates=connection.execute(quality.DUPLICATES_SQL).fetchone()[0],
            invalid=connection.execute(quality.INVALID_SQL).fetchone()[0],
        )
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
    rows.append(
        (
            "completitud",
            "Semanas sin hueco",
            f"{measures['weeks']} de {measures['expected_weeks']}",
            "ninguna semana falta entre la primera y la última",
            "ok" if gaps == 0 else "fail",
            f"Semanas con precios entre {measures['first']} y {measures['last']}, contadas contra las que "
            f"debería haber (una por lunes). Faltan {gaps}.",
        )
    )
    per_week = measures["per_week"]
    if len(per_week) >= 4:
        latest = per_week[0][1]
        typical = median([count for _, count in per_week[1:]])
        ratio = share(latest, typical)
        rows.append(
            (
                "completitud",
                "Precios de la última semana",
                thousands(latest),
                f"{percent(ratio, 0)} de lo típico ({thousands(round(typical))}); mínimo {percent(LAST_WEEK_MIN_SHARE, 0)}",
                "ok" if ratio >= LAST_WEEK_MIN_SHARE else "warn",
                f"Filas de weekly_price de la semana {weeks.week_range(per_week[0][0], year=True)} frente a la mediana "
                f"de las {len(per_week) - 1} "
                "semanas anteriores. Una caída fuerte suele ser una descarga incompleta.",
            )
        )
    # Uniqueness
    rows.append(
        (
            "unicidad",
            "Claves duplicadas",
            thousands(measures["duplicates"]),
            "producto, región, canal, unidad y semana: una sola fila",
            "ok" if measures["duplicates"] == 0 else "fail",
            "Combinaciones de semana, producto, región, canal y unidad con más de una fila.\n"
            + compact(quality.DUPLICATES_SQL),
        )
    )
    # Validity
    read = measures["runs"][-1][3] if measures["runs"] else 0
    rejected = sum(count for _, _, count in measures["rejections"])
    rows.append(
        (
            "validez",
            "Filas rechazadas",
            thousands(rejected),
            f"{percent(share(rejected, read), quality_metrics.percent_decimals(share(rejected, read) * 100))} de {thousands(read)} leídas; máximo {percent(REJECTED_MAX_SHARE, 0)}",
            "ok" if share(rejected, read) <= REJECTED_MAX_SHARE else "warn",
            "Filas de origen que la validación apartó, cada una con su motivo, en la tabla rejection.",
        )
    )
    flagged = sum(count for name, count in measures["flags"].items() if name != "SIN_MARCA")
    total = measures["total_rows"]
    rows.append(
        (
            "validez",
            "Precios apartados de los indicadores",
            thousands(flagged),
            f"{percent(share(flagged, total))} de {thousands(total)}; máximo {percent(FLAGGED_MAX_SHARE, 0)}",
            "ok" if share(flagged, total) <= FLAGGED_MAX_SHARE else "warn",
            "Precios marcados como atípicos o con unidad no convertible: quedan en la base pero fuera de los "
            "indicadores.",
        )
    )
    rows.append(
        (
            "validez",
            "Formatos inválidos",
            thousands(measures["invalid"]),
            "precio positivo, unidad y lunes válidos",
            "ok" if measures["invalid"] == 0 else "fail",
            "Precios utilizables con precio nulo o no positivo, unidad vacía o fecha que no es lunes.\n"
            + compact(quality.INVALID_SQL),
        )
    )
    # Consistency
    rows.append(
        (
            "consistencia",
            "Referencias sin destino",
            thousands(measures["foreign_keys"]),
            "toda clave apunta a una fila que existe",
            "ok" if measures["foreign_keys"] == 0 else "fail",
            "Precios sin producto, región, canal o fecha, y rechazos sin carga.\n" + compact(quality.FOREIGN_KEYS_SQL),
        )
    )
    parity = measures.get("parity")
    if parity:
        rows.append(
            (
                "consistencia",
                "Paridad SQLite ↔ DuckDB",
                "misma suma" if parity["ok"] else "no coinciden",
                f"{thousands(parity['rows'][1])} precios y {thousands(parity['rejections'][1])} rechazos en las dos",
                "ok" if parity["ok"] else "fail",
                "El ETL en Python y dbt, por caminos independientes, deben dar los mismos precios, rechazos y suma.",
            )
        )
    elif measures["runs"] and measures["runs"][-1][2] == "LOADED":
        # D-270: the backup is never published, so a server has none. The published load built it on its own machine
        # and passed the parity test there: a load that fails it never reaches the release.
        run_id = measures["runs"][-1][0]
        rows.append(
            (
                "consistencia",
                "Paridad SQLite ↔ DuckDB",
                "comprobada en la carga",
                f"la carga {run_id} pasó la prueba de paridad antes de publicarse",
                "ok",
                f"El respaldo SQLite no se publica, así que este servidor no lo tiene. La carga {run_id} lo construyó en "
                "su máquina y pasó ahí la prueba de paridad (tests/test_migration_parity.py) antes de publicar la base: "
                "una carga que no la pasa no se publica.",
            )
        )
    else:
        rows.append(
            (
                "consistencia",
                "Paridad SQLite ↔ DuckDB",
                "sin respaldo aquí",
                "se comprueba donde está datos.db",
                "info",
                "El respaldo SQLite no está en este servidor, así que esta comparación no se puede hacer aquí.",
            )
        )
    # Timeliness
    behind = (today - parse_day(measures["last"])).days
    rows.append(
        (
            "actualidad",
            "Días desde la última semana",
            f"{behind}",
            f"semana {weeks.week_range(measures['last'], year=True)}; máximo {DATA_MAX_DAYS}",
            "ok" if behind <= DATA_MAX_DAYS else "warn",
            "Días entre el lunes de la última semana con precios y hoy.",
        )
    )
    if measures["runs"]:
        run_id, started, status, *_ = measures["runs"][-1]
        age = (today - parse_day(started)).days
        good = status == "LOADED"
        rows.append(
            (
                "actualidad",
                "Última carga",
                f"hace {age} día" + ("" if age == 1 else "s"),
                f"carga {run_id} · {status}; máximo {LOAD_MAX_DAYS} días",
                "ok" if good and age <= LOAD_MAX_DAYS else "fail" if not good else "warn",
                "El pipeline corre cada martes y deja una fila en etl_run por ejecución real.",
            )
        )
    # dbt tests
    passed, failed = measures["tests"].get("pass", 0), sum(n for s, n in measures["tests"].items() if s != "pass")
    rows.append(
        (
            "pruebas",
            "Pruebas de dbt",
            f"{passed} de {passed + failed}",
            "todas superadas en la última construcción",
            "ok" if failed == 0 and passed else "fail" if failed else "info",
            "Las pruebas de datos de dbt: claves únicas y no nulas, valores aceptados y relaciones entre tablas.",
        )
    )
    return rows


# endregion


# region The verdict
def dimension_status(statuses):
    return "fail" if "fail" in statuses else "warn" if "warn" in statuses else "ok" if "ok" in statuses else "info"


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


# endregion


# region Markup
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
    colors = {
        "ok": quality_view.PILL_COLORS["ok"],
        "warn": quality_view.PILL_COLORS["pending"],
        "fail": quality_view.PILL_COLORS["fail"],
        "info": muted,
    }
    states = "".join(f".qp .s-{key}{{--c:{color};}}" for key, color in colors.items())
    states += "".join(f".qp .k-{key}{{--c:{color};}}" for key, color in quality_view.PILL_COLORS.items())
    shade = "rgba(0,0,0,.5)" if dark else "rgba(15,40,90,.18)"
    return static_files.style(
        "quality_live.css",
        {
            'var(--go-text)': text,
            'var(--go-states)': states,
            'var(--go-muted)': muted,
            'var(--go-pipeline-palette)': build_pipeline_css(palette),
            'var(--go-card)': card,
            'var(--go-border)': border,
            'var(--go-6-if-dark-else-25)': '.6' if dark else '.25',
            'var(--go-ink)': ink,
            'var(--go-accent)': accent,
            'var(--go-shade)': shade,
        },
    )


def wrap_document(palette, body):
    # The base keeps the #links of the pop-ups inside this document: in an srcdoc frame they would resolve against the page around it.
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><base href="about:srcdoc"><meta name="viewport" content="width=device-width,initial-scale=1">'
        + build_css(palette)
        + '</head><body>'
        + quality_view.defs()
        + f'<div class="qp">{body}</div></body></html>'
    )


# endregion


# region Gates and verdict
def hub_measure(key, indicators, columns):
    """(status, headline) of one dimension: its indicators, or for accuracy the audit controls of the results step."""
    if key == "exactitud":
        cards = next((cards for step, cards in columns if step == RESULTS_STEP), [])
        if not cards:
            return "info", "sin controles aquí"
        kinds = [quality_view.classify(card[2]) for card in cards]
        status = "fail" if "fail" in kinds else "warn" if "pending" in kinds else "ok"
        return status, f"{kinds.count('ok')} de {len(kinds)} controles verificados"
    keys = HUB_DIMENSIONS.get(key, [key])
    rows = [row for row in indicators if row[0] in keys]
    judged = [row for row in rows if row[4] != "info"]
    if not rows:
        return "info", "sin indicadores"
    return dimension_status(
        [row[4] for row in rows]
    ), f"{sum(row[4] == 'ok' for row in judged)} de {len(judged)} indicadores bien"


def gate_measure(index, indicators):
    keys = GATE_VIEW[index][2]
    rows = [row for row in indicators if row[0] in keys]
    judged = [row for row in rows if row[4] != "info"]
    return dimension_status(
        [row[4] for row in rows]
    ) if rows else "info", f"{sum(row[4] == 'ok' for row in judged)} de {len(judged)} bien"


def gate_dimensions(index):
    """The dimensions of the diagram one gate watches, in its order: the dbt tests count with consistency."""
    keys = []
    for key in GATE_VIEW[index][2]:
        key = next((hub for hub, parts in HUB_DIMENSIONS.items() if key in parts), key)
        if key not in keys:
            keys.append(key)
    return keys


def build_flow(measures):
    """The rows of the latest published load at each stretch of the pipeline, and why the rejected ones were.
    None when there is no load to read them from."""
    loads = [run for run in (measures or {}).get("runs", []) if run[2] == "LOADED"]
    if not loads:
        return None
    run_id, _, _, read, loaded, rejected = loads[-1]
    reasons = [REASONS.get(reason, reason.replace("_", " ").lower()) for reason, _, _ in measures.get("rejections", [])]
    return {
        "run": run_id,
        "read": read,
        "loaded": loaded,
        "rejected": rejected,
        "reasons": list(dict.fromkeys(reasons)),
        "prices": measures.get("total_rows"),
    }


def build_verdict_box(indicators, columns):
    """(status, name, line) of the box every gate flows into: the indicators within their threshold, and the
    accuracy controls still pending, said by name, so the box claims nothing the pop-ups do not show."""
    kind, _ = build_verdict(indicators)
    judged = [row for row in indicators if row[4] != "info"]
    outside = [row for row in judged if row[4] != "ok"]
    name = {"ok": "Datos sanos", "warn": "Datos a revisar", "fail": "Datos con fallas"}[kind]
    line = f"{len(judged)} indicadores" + (
        " dentro de su umbral" if not outside else f" · {len(outside)} fuera de su umbral"
    )
    cards = next((cards for step, cards in columns if step == RESULTS_STEP), [])
    kinds = [quality_view.classify(card[2]) for card in cards]
    failed, pending = kinds.count("fail"), kinds.count("pending")
    if failed:
        line += f" · {failed} control{'es' if failed > 1 else ''} con falla: exactitud"
    elif pending:
        line += f" · {pending} control{'es' if pending > 1 else ''} pendiente{'s' if pending > 1 else ''}: exactitud"
    return ("fail" if failed and kind == "ok" else kind), name, line


# endregion


# region The pipeline
def _pipeline_glow(dark, color):
    return (
        f"0 0 0 1px color-mix(in srgb, {color} 35%, transparent), 0 0 24px -6px color-mix(in srgb, {color} 70%, transparent)"
        if dark
        else "0 8px 18px -14px rgba(15,40,90,.35)"
    )


def build_pipeline_css(palette):
    """The pipeline of quality (D-273): boxes and dashed lines drawn with HTML and CSS, so the words keep their size on
    any window; under 760 px the stretches stack from top to bottom."""
    dark = palette["base"] == charts.BASE_DARK
    ink, muted, card, border, accent = (
        palette["strong_text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    grid = f"color-mix(in srgb, {border} {'38' if dark else '45'}%, transparent)"
    surface = f"color-mix(in srgb, {card} 72%, #000)" if dark else card

    return static_files.fill(
        "quality_pipeline.css",
        {
            'var(--go-accent)': accent,
            'var(--go-border)': border,
            'var(--go-surface)': surface,
            'var(--go-grid)': grid,
            'var(--go-ink)': ink,
            'var(--go-muted)': muted,
            'var(--go-live-mark-css-dark)': live_mark.build_css(dark),
            'var(--go-card)': card,
            'var(--go-pipeline-glow-dark-var-c)': _pipeline_glow(dark, "var(--c)"),
            'var(--go-quality-view-pill-colors-pending)': quality_view.PILL_COLORS["pending"],
            'var(--go-quality-view-pill-colors-fail)': quality_view.PILL_COLORS["fail"],
            'var(--go-14-if-dark-else-9)': '14' if dark else '9',
        },
    )


def _build_pipeline_html_number(value):
    return thousands(value) if value is not None else "—"


def build_pipeline_html(indicators, columns, measures=None):
    """The pipeline of quality (D-273): the rows of the latest load go through the three gates; each gate says what it
    measures and every gate flows into the verdict. Each gate, each dimension, the rejected rows and the verdict open
    their pop-up."""
    flow = build_flow(measures)

    read, loaded = (flow["read"], flow["loaded"]) if flow else (None, None)
    run = f" de la carga {flow['run']}" if flow else ""
    stretches = [
        ("a1", read, f"Filas leídas de los archivos de ODEPA{run}"),
        ("a2", read, "Las mismas filas: la puerta 1 acepta o detiene un archivo entero, no filas sueltas"),
        (
            "a3",
            loaded,
            f"Filas que pasaron la puerta 2: {_build_pipeline_html_number(read)} leídas menos {_build_pipeline_html_number(flow['rejected'] if flow else None)} rechazadas",
        ),
        ("a4", loaded, "Las mismas filas: si la puerta 3 falla, no se publica ninguna"),
    ]
    parts = [
        f'<div class="h" style="grid-area:{area}" title="{html.escape(note)}"><span>{_build_pipeline_html_number(value)}</span></div>'
        for area, value, note in stretches
    ]
    parts.append(
        '<div class="box end" style="grid-area:org" title="Los CSV anuales de ODEPA, descargados por HTTPS">'
        '<span class="kicker">Origen</span><b>Archivos</b><small>CSV de ODEPA</small></div>'
    )
    prices = (
        f"{_build_pipeline_html_number(flow['prices'])} precios"
        if flow and flow["prices"] is not None
        else "Base DuckDB"
    )
    parts.append(
        f'<div class="box end" style="grid-area:base" title="{html.escape(prices)} semanales: las filas válidas, agrupadas '
        f'por semana, producto, región, canal y unidad"><span class="kicker">Carga</span><b>Base</b>'
        f'<small>{html.escape(prices)}</small></div>'
    )
    for index, (title, question, _) in enumerate(GATE_VIEW):
        status, measure = gate_measure(index, indicators)
        kicker, _, name = title.partition(" · ")
        parts.append(
            f'<a class="box gate s-{status}" href="#g-{index}" style="grid-area:g{index + 1}" '
            f'title="{html.escape(title)}: {html.escape(question)} {html.escape(measure)}" '
            f'aria-label="{html.escape(title)}: {html.escape(question)}">'
            f'<span class="kicker">{html.escape(kicker)}</span><b>{html.escape(name[:1].upper() + name[1:])}</b>'
            f'<small>{html.escape(GATE_BOX_QUESTIONS[index])}</small></a>'
        )
        links = []
        for key in gate_dimensions(index):
            dim_status, headline = hub_measure(key, indicators, columns)
            dim_name = dict((hub_key, hub_name) for hub_key, hub_name, *_ in HUB)[key]
            links.append(
                f'<a class="s-{dim_status}" href="#d-{key}" title="{html.escape(dim_name)}: {html.escape(headline)}" '
                f'aria-label="{html.escape(dim_name)}: {html.escape(headline)}">{html.escape(dim_name)}</a>'
            )
        parts.append(
            f'<div class="box mide" style="grid-area:m{index + 1}"><span class="kicker">Mide</span>{"".join(links)}</div>'
        )
        parts.append(
            f'<i class="v vertical-only" style="grid-area:v{index + 1}"></i><i class="v vertical-only" style="grid-area:w{index + 1}"></i>'
        )
    if flow:
        reasons = ", ".join(flow["reasons"]) or "motivo registrado en rejection"
        parts.append(
            f'<a class="box rej" href="#g-1" style="grid-area:rej" title="Filas rechazadas por la puerta 2{run}, con su motivo">'
            f'<span class="kicker">Rechazo</span><b>{_build_pipeline_html_number(flow["rejected"])} filas</b><small>{html.escape(reasons)}</small></a>'
            '<i class="v up vertical-only" style="grid-area:vr"></i>'
        )
    status, name, line = build_verdict_box(indicators, columns)
    count = len([row for row in indicators if row[4] != "info"])
    parts.append(
        f'<a class="box ds s-{status}" href="#d-todos" style="grid-area:ds" aria-label="{html.escape(name)}: ver los {count} '
        f'indicadores"><b>{html.escape(name)}</b><small>{html.escape(line)}</small></a>'
    )
    legend = [
        ("Dentro del umbral", "var(--accent-ok)"),
        ("Rechazo o a revisar", quality_view.PILL_COLORS["pending"]),
        ("Falla", quality_view.PILL_COLORS["fail"]),
    ]
    parts.append(
        '<div class="legend-box" style="grid-area:leg">'
        + "".join(f'<div><i style="--c:{color}"></i>{html.escape(text)}</div>' for text, color in legend)
        + '<div title="Las filas de la última carga publicada, en cada tramo">Cifras: filas por tramo</div></div>'
    )
    words = NUMBER_WORDS
    head = (
        f'<div class="pq-head"><h2>Pipeline de calidad de datos</h2>'
        f'<p>{words[len(GATE_VIEW)].capitalize()} puertas · {words[len(HUB)]} dimensiones · un veredicto</p>'
        '<p class="hint">· pulsa cada pieza para ver su detalle</p>'
        + live_mark.build_html(  # D-510: every figure of the pipeline is measured when the page opens
            'weekly_price, rejection, etl_run y dbt_result se consultan en la Base DuckDB al abrir la página.'
        )
        + '</div>'
    )
    return f'<div class="pq">{head}<div class="pq-grid">{"".join(parts)}</div></div>'


# endregion


# region Indicators and windows
def build_indicator_html(label, value, reference, state, detail):
    """One indicator with how it is measured: its text and, when the measure is a query, the query."""
    text, _, query = detail.partition("\n")
    sql = f"<pre>{html.escape(query)}</pre>" if query else ""
    return (
        f'<div class="ind s-{state}"><i></i><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong>'
        f'<em>{html.escape(reference)}</em><small>{html.escape(text)}</small>{sql}</div>'
    )


def build_modal(identifier, title, question, body):
    return (
        f'<div class="modal" id="{identifier}"><a class="back" href="#" aria-label="Cerrar"></a><div class="sheet" role="dialog" '
        f'aria-label="{html.escape(title)}"><a class="close" href="#" aria-label="Cerrar">✕</a><h3>{html.escape(title)}</h3>'
        f'<div class="q">{html.escape(question)}</div>{body}</div></div>'
    )


def build_dimension_modal(key, name, indicators, columns):
    status, headline = hub_measure(key, indicators, columns)
    if key == "exactitud":
        cards = next((cards for step, cards in columns if step == RESULTS_STEP), [])
        body = (
            "".join(
                f'<div class="ind k-{quality_view.classify(status_text)}"><i></i><span>{html.escape(title)}</span>'
                f'<strong>{html.escape(status_text)}</strong><em>{html.escape(detail)}</em><small>{html.escape(why)}</small></div>'
                for _, title, status_text, detail, why in cards
            )
            or "<p>Sin controles aquí.</p>"
        )
        body = (
            "<p>No hay un indicador de exactitud: se mide con los controles que comparan las cifras con la fuente.</p>"
            + body
        )
    else:
        keys = HUB_DIMENSIONS.get(key, [key])
        body = "".join(build_indicator_html(*row[1:]) for row in indicators if row[0] in keys)
        gate = next((GATE_VIEW[i][0] for i in range(len(GATE_VIEW)) if set(keys) & set(GATE_VIEW[i][2])), "")
        body += f'<h4>Dónde se vigila</h4><p>{html.escape(gate)}. Se mide en cada carga, sobre la base publicada.</p>'
    return build_modal(f"d-{key}", name, f"{HUB_QUESTIONS[key]} {headline}.", body)


def build_gate_modal(index, indicators):
    title, question, keys = GATE_VIEW[index]
    _, stops, outcome, where, evidence = GATES[index]
    body = (
        f'<h4>Qué detiene</h4><p>{html.escape(stops)}</p><h4>Si no pasa</h4><p>{html.escape(outcome)}</p>'
        f'<h4>Dónde está</h4><p><code>{html.escape(where)}</code><br>Pruebas: <code>{html.escape(evidence)}</code></p><h4>Lo que se mide aquí</h4>'
        + "".join(build_indicator_html(*row[1:]) for row in indicators if row[0] in keys)
    )
    return build_modal(f"g-{index}", title, question, body)


def build_all_modal(indicators, sentence):
    """Every measured indicator in one list, by dimension: where the number of the verdict comes from, and how to read it."""
    body = (
        '<p>'
        + html.escape(sentence)
        + ' Verde: dentro del umbral. Ámbar: a revisar o con un control pendiente. Rojo: falla.</p>'
        + "".join(
            f'<h4>{html.escape(TITLES[key])}</h4>'
            + "".join(build_indicator_html(*row[1:]) for row in indicators if row[0] == key)
            for key in ICONS
            if any(row[0] == key for row in indicators)
        )
    )
    return build_modal(
        "d-todos",
        f"Los {len(indicators)} indicadores",
        "Cada uno se mide en cada carga y se juzga contra el umbral que lleva debajo.",
        body,
    )


# endregion


# region Pages
def build_quality_html(palette, indicators, columns, measures=None):
    """The main view (D-273): the pipeline of quality, and a pop-up behind each gate, each dimension and the verdict.
    measures gives the rows of the latest load at each stretch; without it the stretches show a dash."""
    _, sentence = build_verdict(indicators)
    modals = "".join(build_dimension_modal(key, name, indicators, columns) for key, name, _, _ in HUB)
    modals += "".join(build_gate_modal(index, indicators) for index in range(len(GATE_VIEW)))
    modals += build_all_modal(indicators, sentence)
    return wrap_document(palette, build_pipeline_html(indicators, columns, measures) + modals)


def build_apart_html(rejections, flags):
    """What was set aside, one row per reason: rejected rows (out of the base) and marked prices (in the base, out of the indicators)."""
    rows = []
    for reason, source, count in rejections:
        rows.append(
            f'<tr><td><code>{html.escape(reason)}</code><small>{html.escape(REASONS.get(reason, "motivo registrado por la validación"))}'
            f' · fuente {SOURCES.get(source, html.escape(str(source)))}</small></td>'
            f'<td><span class="tag s-fail">Rechazada</span><small>queda en <code>rejection</code>, fuera de la base</small></td>'
            f'<td class="n">{thousands(count)}</td></tr>'
        )
    for name, count in sorted(flags.items(), key=lambda item: -item[1]):
        if name != "SIN_MARCA":
            rows.append(
                f'<tr><td><code>{html.escape(name)}</code><small>{html.escape(FLAGS.get(name, "marca de calidad"))}</small></td>'
                f'<td><span class="tag s-warn">Marcada</span><small>queda en la base, fuera de los indicadores</small></td>'
                f'<td class="n">{thousands(count)}</td></tr>'
            )
    body = "".join(rows) or '<tr><td colspan="3">Nada apartado.</td></tr>'
    return (
        '<div class="panel"><table><caption>Qué se apartó y por qué</caption><thead><tr><th>Motivo</th><th>Qué pasa</th>'
        f'<th class="n">Filas</th></tr></thead><tbody>{body}</tbody></table></div>'
    )


def build_loads_html(runs):
    """The last five loads, newest first: number, day, state, rows read and the change against the load before."""
    rows = []
    for position in range(len(runs) - 1, max(len(runs) - 6, -1), -1):
        run_id, started, status, read, loaded, rejected = runs[position]
        previous = runs[position - 1][3] if position else None
        change = (
            "—"
            if previous is None
            else (f"+{thousands(read - previous)}" if read >= previous else f"−{thousands(previous - read)}")
        )
        day = str(started)[:10]
        rows.append(
            f'<tr title="Carga {run_id}: leyó {thousands(read)} filas, cargó {thousands(loaded)} y rechazó {thousands(rejected)}">'
            f'<td>{run_id}<small>{day[8:10]}-{day[5:7]}-{day[:4]}</small></td>'
            f'<td><span class="tag k-{"ok" if status == "LOADED" else "fail"}">{"Cargada" if status == "LOADED" else html.escape(status)}</span></td>'
            f'<td class="n">{thousands(read)}</td><td class="n">{change}</td></tr>'
        )
    body = "".join(rows) or '<tr><td colspan="4">Sin cargas registradas.</td></tr>'
    return (
        '<div class="panel"><table><caption>Últimas cargas</caption><thead><tr><th>Carga</th><th>Estado</th>'
        f'<th class="n">Filas leídas</th><th class="n">Cambio</th></tr></thead><tbody>{body}</tbody></table></div>'
    )


def build_tables_html(palette, runs, rejections, flags):
    """The tab of what was set aside and the last loads."""
    return wrap_document(
        palette, f'<div class="two">{build_apart_html(rejections, flags)}{build_loads_html(runs)}</div>'
    )


def split_steps(columns):
    """The steps in two runs, in their order, as even as their rows allow (D-271): the tab fits one screen."""
    weights = [len(cards) + 1 for _, cards in columns]  # the step's own heading counts as a row
    total, best, cut = sum(weights), None, 1
    for index in range(1, len(columns)):
        difference = abs(total - 2 * sum(weights[:index]))
        if best is None or difference < best:
            best, cut = difference, index
    return columns[:cut], columns[cut:]


def build_audit_html(columns):
    """The audit controls by step, one row each: its mark, what it is, its status and what it found. The steps sit in
    two panels side by side, in timeline order, so the tab fits one screen; a narrow window stacks them."""
    panels = []
    for half in split_steps(columns):
        rows = []
        for step, cards in half:
            rows.append(f'<tr class="step"><td colspan="3">{html.escape(step)}</td></tr>')
            for icon, title, status, detail, why in cards:
                kind = quality_view.classify(status)
                rows.append(
                    f'<tr title="{html.escape(why)}"><td class="ic">{quality_view.build_icon_svg(icon)}</td>'
                    f'<td>{html.escape(title)}<small title="{html.escape(detail)}">{html.escape(detail)}</small></td>'
                    f'<td class="st"><span class="tag k-{kind}">{html.escape(status)}</span></td></tr>'
                )
        # The widths go first: a fixed table takes them from its first row, which here is a step's heading.
        panels.append(
            '<div class="audit"><table><colgroup><col class="c-ic"><col><col class="c-st"></colgroup>'
            f'<tbody>{"".join(rows)}</tbody></table></div>'
        )
    return f'<div class="audit-pair">{"".join(panels)}</div>'


def build_audit_page_html(palette, columns):
    """The audit tab: every control with its status; the row explains what it checks on hover."""
    return wrap_document(
        palette,
        build_audit_html(columns) + '<p class="legend">Verificado: comprobado en este servidor · '
        'Pendiente: no se puede comprobar aquí o tiene una observación · nada se muestra como verificado sin comprobarse.</p>',
    )


# endregion
