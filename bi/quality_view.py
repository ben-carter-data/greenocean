"""«Calidad y auditoría» as a story (D-176): the method (the six data quality dimensions
of the DAMA-DMBOK), four stages of the pipeline (Fuentes → Transformación → Warehouse →
Resultados), each with its role in quality, its figure, its verdict and the controls it
runs as small glossy illustrations, then the anomalies box (the rejected rows) and the
status bar. Hovering a dimension, a stage, a control or the box explains its part.

Nothing here reads data. bi/dashboard.py computes the same evidence it always did
(bi.quality, bi.lineage, the latest etl_run row) and hands it over through
build_evidence(); build_overview_html() only draws it. The evidence dict:

    run_id          int|str  latest etl_run.run_id
    run_started     str      its start, already formatted in Chilean time ("13-10-2026 15:35")
    run_status      str      etl_run.status ("LOADED", "FAILED", …)
    run_ok          bool     run_status == etl.STATUS_LOADED
    manifest_present bool    agent/downloads/manifest.json was read
    manifest_files  int      files registered in the manifest
    files_matching  int      local files whose SHA-256 equals the registered one
    files_total     int      files checked (same as manifest_files)
    files_failed    int      local files whose SHA-256 differs
    weeks           int      distinct weeks in weekly_price
    first_week      str      first week, "dd-mm-yyyy"
    last_week       str      last week, "dd-mm-yyyy"
    build           dict|None  last dbt build: models, tests, passing (int), ok (bool),
                               built_at (str "dd-mm-yyyy"); None before a build
    checks          dict     integrity_ok (bool), foreign_keys, duplicates, invalid (int)
    parity          dict|None  rows, rejections (DuckDB), backup_rows, backup_rejections
                               (SQLite), ok (bool); None without a SQLite backup
    rejections      int|None rows in the rejection table (None: taken from parity)

The page is one block of HTML with its CSS scoped under .qa-page (no script), for
st.markdown(unsafe_allow_html=True); the hover explanations are CSS only.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts  # noqa: E402
from etl import etl  # noqa: E402

EXPANDER_KEY = "qa_evidence"

# Pill colors, the same in every theme: solid with white text (≥ 4.5:1 on each).
PILL_COLORS = {"ok": "#15934a", "pending": "#d97706", "fail": "#d02f2f"}
STEP_NAMES = ["Fuentes", "Ejecución y dbt", "Warehouse", "Resultados"]

# The audits of the last column are automated tests and a dated manual sample
# (D-144, D-146, D-049): their figures are the ones the page always stated.
RESULT_CARDS = [
    (
        "reconcile",
        "Reconciliación fuente → base",
        "Verificado · pruebas automáticas",
        "120 precios por ejecución · auditoría manual del 18-10-2026: 400 de 400.",
        "Cada ejecución de las pruebas reconstruye 120 precios semanales desde las filas crudas de "
        "ODEPA, sin el ETL. En la auditoría del 18-10-2026 coincidieron 400 de 400.",
    ),
    (
        "calculator",
        "Recálculo independiente de indicadores",
        "Verificado · pruebas automáticas",
        "SQL y Python coinciden.",
        "Las alertas K6 se calculan en Python y en SQL y deben coincidir (D-049); las variaciones del "
        "Resumen se comparan con un cálculo SQL independiente.",
    ),
    (
        "chart",
        "Concordancia cálculo → pantalla",
        "Verificado · muestra",
        "Familias, ranking y margen coinciden.",
        "Las cifras de familias, ranking y margen de la semana del 05-10-2026 se recalcularon a mano "
        "por región y coinciden con lo que muestra el panel (D-144, D-146).",
    ),
    (
        "warning",
        "Contraste con otra fuente",
        "Pendiente",
        "ODEPA es la única fuente oficial de estos datos.",
        "No hay una comparación independiente de precios con otra fuente equivalente.",
    ),
]


# region Evidence
def format_week(value):
    """'2022-01-03' (or a date) -> '03-01-2022'."""
    text = str(value)[:10]
    parts = text.split("-")
    return f"{parts[2]}-{parts[1]}-{parts[0]}" if len(parts) == 3 and len(parts[0]) == 4 else text


def build_evidence(checks, files, manifest, run, build, parity, format_time, rejections=None):
    """The evidence dict from the objects show_operations_page already holds:
    checks and files from read_quality_evidence, manifest from read_download_manifest,
    run = read_latest_run() (row with run_id, started_at, status), build =
    lineage.summarize_build(...) or None, parity = read_parity(...) or None, and
    format_time(started_at) -> the Chilean time text (e.g.
    lambda value: format_chile_time(parse_run_start(value)))."""
    matching = sum(item["status"].startswith("Verificado") for item in files)
    failed = sum(item["status"].startswith("Falla") for item in files)
    build_part = None
    if build:
        built_at = build.get("built_at")
        build_part = dict(
            models=int(build["models"]),
            tests=int(build["tests"]),
            passing=int(build["passing"]),
            ok=bool(build["ok"]),
            built_at=f"{built_at:%d-%m-%Y}" if built_at is not None else "",
        )
    parity_part = None
    if parity:
        parity_part = dict(
            rows=int(parity["rows"][1]),
            rejections=int(parity["rejections"][1]),
            backup_rows=int(parity["rows"][0]),
            backup_rejections=int(parity["rejections"][0]),
            ok=bool(parity["ok"]),
        )
    return dict(
        rejections=int(rejections) if rejections is not None else None,
        run_id=int(run["run_id"]) if str(run["run_id"]).isdigit() else run["run_id"],
        run_started=format_time(run["started_at"]),
        run_status=str(run["status"]),
        run_ok=run["status"] == etl.STATUS_LOADED,
        manifest_present=bool(manifest),
        manifest_files=len(files),
        files_matching=matching,
        files_total=len(files),
        files_failed=failed,
        weeks=int(checks["weeks"] or 0),
        first_week=format_week(checks["first"]),
        last_week=format_week(checks["last"]),
        build=build_part,
        checks=dict(
            integrity_ok=bool(checks["integrity_ok"]),
            foreign_keys=int(checks["foreign_keys"]),
            duplicates=int(checks["duplicates"]),
            invalid=int(checks["invalid"]),
        ),
        parity=parity_part,
    )


def classify(status):
    """A status pill's kind by its first word (D-120)."""
    if status.startswith("Falla") or status.startswith("Sin registro"):
        return "fail"
    if status.startswith("Pendiente"):
        return "pending"
    return "ok"


def thousands(value):
    return charts.format_thousands(value)


def plural(count, singular, plural_form):
    return f"{count} {singular if count == 1 else plural_form}"


def build_columns(evidence):
    """[(step, [(icon, title, status, detail, explanation), …]), …] in timeline order."""
    files_total, matching, failed = (evidence["files_total"], evidence["files_matching"], evidence["files_failed"])
    integrity = (
        "Falla detectada"
        if failed
        else "Verificado"
        if files_total and matching == files_total
        else "Pendiente de comprobación"
    )
    sources = [
        (
            "files",
            "Origen y archivos",
            "Registro disponible" if evidence["manifest_present"] else "Sin registro disponible",
            f"{evidence['manifest_files']} archivos registrados en manifest.json.",
            "Cada descarga queda con su fecha y su huella SHA-256. Esto identifica las descargas; "
            "no certifica cada precio.",
        ),
        (
            "shield",
            "Integridad de archivos originales",
            integrity,
            f"{matching} de {files_total} huellas coinciden · {plural(failed, 'discrepancia', 'discrepancias')}.",
            "Los archivos locales se comparan con la huella registrada; los ausentes no se consideran verificados.",
        ),
        (
            "calendar",
            "Cobertura temporal",
            "Disponible",
            f"{evidence['weeks']} semanas · {evidence['first_week']} → {evidence['last_week']}.",
            "Es cobertura registrada, no confirmación de que la fuente esté al día.",
        ),
    ]
    build = evidence["build"]
    run = [
        (
            "gear",
            "Última carga registrada",
            "Superada" if evidence["run_ok"] else "Falla registrada",
            f"Ejecución {evidence['run_id']} · estado {evidence['run_status']}.",
            f"Ejecución {evidence['run_id']} · {evidence['run_started']} (Chile). Es evidencia de la carga "
            "guardada, no del último intento remoto.",
        ),
        (
            "layers",
            "Pruebas dbt de la última construcción",
            ("Superadas" if build["ok"] else "Falla detectada") if build else "Pendiente · sin resultado dbt",
            f"{build['passing']} de {build['tests']} pruebas · {build['models']} modelos."
            if build
            else "La base aún no trae el resultado de dbt.",
            (
                f"Construcción del {build['built_at']}. Si una prueba falla, la base publicada no se reemplaza."
                if build
                else "La base aún no trae el resultado de dbt."
            ),
        ),
    ]
    checks = evidence["checks"]
    database_ok = checks["integrity_ok"] and not any(checks[key] for key in ("foreign_keys", "duplicates", "invalid"))
    database_detail = (
        f"{plural(checks['foreign_keys'], 'referencia inválida', 'referencias inválidas')} · "
        f"{plural(checks['duplicates'], 'duplicado', 'duplicados')} · "
        f"{plural(checks['invalid'], 'formato inválido', 'formatos inválidos')}."
    )
    if not checks["integrity_ok"]:
        database_detail = "Lectura completa con error · " + database_detail
    parity = evidence["parity"]
    if parity and parity["ok"]:
        parity_detail = (
            f"{thousands(parity['rows'])} precios · {thousands(parity['rejections'])} rechazos · misma suma."
        )
    elif parity:
        parity_detail = (
            f"SQLite {thousands(parity['backup_rows'])} y DuckDB {thousands(parity['rows'])} precios · "
            f"{thousands(parity['backup_rejections'])} y {thousands(parity['rejections'])} "
            "rechazos · no coinciden."
        )
    else:
        parity_detail = "Sin respaldo SQLite para comparar."
    warehouse = [
        (
            "database",
            "Comprobación de la base actual",
            "Verificado · alcance limitado" if database_ok else "Falla detectada",
            database_detail,
            "DuckDB leída completa: referencias entre tablas, claves duplicadas y precios utilizables con "
            "formato inválido.",
        ),
        (
            "parity",
            "Paridad SQLite ↔ DuckDB",
            ("Verificado" if parity["ok"] else "Falla detectada") if parity else "Pendiente · sin respaldo",
            parity_detail,
            "El respaldo SQLite y el data warehouse DuckDB deben tener los mismos precios, los mismos "
            "rechazos y la misma suma de precios (D-154).",
        ),
    ]
    return list(zip(STEP_NAMES, [sources, run, warehouse, list(RESULT_CARDS)]))


# endregion


# region Illustrations
# One set of gradients for every illustration of the page (ids prefixed qa-).
def stop(offset, color, opacity=1):
    return f'<stop offset="{offset}" stop-color="{color}" stop-opacity="{opacity}"/>'


def linear(name, top, bottom, x2=0, y2=1):
    return (
        f'<linearGradient id="qa-{name}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
        f'{stop(0, top)}{stop(1, bottom)}</linearGradient>'
    )


DEFS = (
    '<svg class="qa-defs" width="0" height="0" aria-hidden="true" focusable="false"><defs>'
    + linear("blue", "#8fd0ff", "#1f6fe0")
    + linear("blue-deep", "#3d8bf0", "#0d3b96")
    + linear("blue-side", "#2563d6", "#0b2e7a", 1, 0)
    + linear("green", "#6ff0a6", "#0e9f4f")
    + linear("paper", "#ffffff", "#d3def0")
    + linear("paper-back", "#e9f0fa", "#b4c4dc")
    + linear("silver", "#ffffff", "#a8b4c6", 1, 0)
    + linear("silver-top", "#ffffff", "#c9d3e1")
    + linear("amber", "#ffe07a", "#f08c00")
    + linear("dark", "#3a4250", "#0f141c")
    + '<linearGradient id="qa-gloss" x1="0" y1="0" x2="0" y2="1">'
    + stop(0, "#ffffff", 0.85)
    + stop(1, "#ffffff", 0)
    + '</linearGradient>'
    + '<radialGradient id="qa-shadow" cx=".5" cy=".5" r=".5">'
    + stop(0, "#0b1f3a", 0.32)
    + stop(1, "#0b1f3a", 0)
    + '</radialGradient>'
    + '</defs></svg>'
)


def shadow(cx=48, cy=88, rx=30, ry=5):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#qa-shadow)"/>'


def check_badge(cx, cy, r):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#qa-green)" stroke="#ffffff" stroke-width="2.5"/>'
        f'<ellipse cx="{cx}" cy="{cy - r * 0.45}" rx="{r * 0.62}" ry="{r * 0.38}" fill="url(#qa-gloss)" opacity=".7"/>'
        f'<path d="M{cx - r * 0.45:.1f} {cy + r * 0.02:.1f} l{r * 0.3:.1f} {r * 0.32:.1f} l{r * 0.6:.1f} {-r * 0.62:.1f}" '
        f'fill="none" stroke="#ffffff" stroke-width="{r * 0.24:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def cylinder(cx, top, width, height, bands=2):
    """A glossy database: silver body, blue bands, a lit top."""
    rx, ry = width / 2, width * 0.17
    left, right, bottom = cx - rx, cx + rx, top + height
    parts = [f'<path d="M{left} {top} V{bottom} A{rx} {ry} 0 0 0 {right} {bottom} V{top} Z" fill="url(#qa-silver)"/>']
    for index in range(bands):
        y = top + height * (index + 1) / (bands + 1)
        parts.append(
            f'<path d="M{left} {y - 2.6} A{rx} {ry} 0 0 0 {right} {y - 2.6} V{y + 2.6} '
            f'A{rx} {ry} 0 0 1 {left} {y + 2.6} Z" fill="url(#qa-blue-deep)"/>'
        )
    parts.append(
        f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="url(#qa-silver-top)" '
        'stroke="#ffffff" stroke-width="1"/>'
    )
    parts.append(
        f'<rect x="{left + width * 0.14}" y="{top + ry}" width="{width * 0.1}" height="{height - ry}" '
        'rx="2" fill="#ffffff" opacity=".55"/>'
    )
    return "".join(parts)


def gear_path(cx, cy, outer, inner, teeth):
    points = []
    for index in range(teeth * 4):
        angle = math.pi * 2 * index / (teeth * 4) - math.pi / 2
        radius = outer if index % 4 in (1, 2) else inner
        points.append(f"{cx + radius * math.cos(angle):.1f},{cy + radius * math.sin(angle):.1f}")
    return "M" + " L".join(points) + " Z"


def icon_files():
    return (
        shadow(46, 88, 32, 5)
        + '<rect x="16" y="14" width="44" height="58" rx="5" fill="url(#qa-paper-back)" transform="rotate(-8 38 43)"/>'
        + '<rect x="12" y="20" width="9" height="56" rx="3" fill="url(#qa-blue-deep)"/>'
        + '<rect x="18" y="16" width="46" height="62" rx="5" fill="url(#qa-paper)" stroke="#c4d2e8" stroke-width="1"/>'
        + "".join(
            f'<rect x="25" y="{y}" width="{w}" height="4" rx="2" fill="#5aa2f2"/>'
            for y, w in ((27, 30), (36, 24), (45, 28), (54, 18))
        )
        + '<rect x="20" y="18" width="42" height="14" rx="4" fill="url(#qa-gloss)" opacity=".6"/>'
        + '<circle cx="64" cy="62" r="18" fill="url(#qa-green)" stroke="#ffffff" stroke-width="3"/>'
        + '<ellipse cx="64" cy="54" rx="11" ry="6" fill="url(#qa-gloss)" opacity=".7"/>'
        + "".join(
            f'<path d="M{64 - r} {66} a{r} {r} 0 0 1 {2 * r} 0" fill="none" stroke="#ffffff" '
            f'stroke-width="2" stroke-linecap="round"/>'
            for r in (3, 6.5, 10)
        )
        + '<path d="M64 66 v6 M57.5 66 v4 M70.5 66 v5" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>'
    )


def icon_shield():
    outline = "M48 8 L78 19 V44 C78 64 64 78 48 86 C32 78 18 64 18 44 V19 Z"
    return (
        shadow(48, 89, 28, 4.5)
        + f'<path d="{outline}" fill="url(#qa-silver)" stroke="#9fb0c6" stroke-width="1"/>'
        + '<path d="M48 15 L72 24 V44 C72 60 61 72 48 79 C35 72 24 60 24 44 V24 Z" fill="url(#qa-green)"/>'
        + '<path d="M48 15 L72 24 V36 C60 33 40 40 24 46 V24 Z" fill="url(#qa-gloss)" opacity=".55"/>'
        + '<path d="M35 46 l9 9 l17 -19" fill="none" stroke="#ffffff" stroke-width="7" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
    )


def icon_calendar():
    cells = "".join(
        f'<rect x="{24 + col * 12.5}" y="{44 + row * 11}" width="9" height="7.5" rx="1.6" '
        f'fill="{"#2f80ed" if (row + col) % 3 else "#7fb6f7"}"/>'
        for row in range(3)
        for col in range(4)
    )
    return (
        shadow(48, 89, 32, 5)
        + '<rect x="16" y="18" width="64" height="66" rx="9" fill="url(#qa-paper)" stroke="#c4d2e8"/>'
        + '<path d="M16 27 a9 9 0 0 1 9 -9 h46 a9 9 0 0 1 9 9 v9 h-64 Z" fill="url(#qa-blue)"/>'
        + '<rect x="18" y="20" width="60" height="7" rx="3.5" fill="url(#qa-gloss)" opacity=".55"/>'
        + "".join(
            f'<rect x="{x}" y="10" width="7" height="18" rx="3.5" fill="url(#qa-silver)" stroke="#8fa1b8"/>'
            for x in (30, 59)
        )
        + cells
    )


def icon_gear():
    return (
        shadow(48, 89, 30, 5)
        + f'<path d="{gear_path(48, 46, 37, 29, 10)}" fill="url(#qa-blue-deep)"/>'
        + f'<path d="{gear_path(48, 44, 36, 28, 10)}" fill="url(#qa-blue)"/>'
        + '<ellipse cx="44" cy="26" rx="20" ry="9" fill="url(#qa-gloss)" opacity=".5"/>'
        + check_badge(48, 45, 17)
    )


def icon_layers():
    def slab(y, top, side):
        return (
            f'<path d="M48 {y} L80 {y + 14} L48 {y + 28} L16 {y + 14} Z" fill="url(#qa-{top})"/>'
            f'<path d="M16 {y + 14} L48 {y + 28} V{y + 34} L16 {y + 20} Z" fill="url(#qa-{side})"/>'
            f'<path d="M80 {y + 14} L48 {y + 28} V{y + 34} L80 {y + 20} Z" fill="#0b3a92"/>'
            f'<path d="M48 {y + 2} L72 {y + 13} L48 {y + 16} L24 {y + 13} Z" fill="url(#qa-gloss)" opacity=".45"/>'
        )

    return (
        shadow(48, 88, 32, 5)
        + slab(50, "blue", "blue-side")
        + slab(34, "blue", "blue-side")
        + slab(18, "paper", "blue-side")
    )


def icon_database():
    return (
        shadow(46, 89, 30, 5)
        + cylinder(44, 18, 50, 62, 2)
        + '<circle cx="72" cy="70" r="13" fill="url(#qa-dark)" stroke="#ffffff" stroke-width="2.5"/>'
        + '<circle cx="69" cy="70" r="5" fill="#ffd43b"/><circle cx="77" cy="68" r="2.5" fill="#ffd43b"/>'
    )


def icon_parity():
    return (
        shadow(48, 89, 36, 5)
        + cylinder(28, 20, 34, 40, 2)
        + cylinder(66, 44, 30, 36, 2)
        + '<path d="M50 18 C62 14 72 18 76 30" fill="none" stroke="url(#qa-blue)" stroke-width="5" stroke-linecap="round"/>'
        + '<path d="M70 28 L77 36 L82 25 Z" fill="#1f6fe0"/>'
        + '<path d="M44 82 C32 86 20 80 18 70" fill="none" stroke="url(#qa-blue)" stroke-width="5" stroke-linecap="round"/>'
        + '<path d="M24 72 L17 63 L12 74 Z" fill="#1f6fe0"/>'
    )


def icon_reconcile():
    def arrow(y, flip):
        shape = (
            f'<path d="M14 {y} h44 v-9 l24 17 l-24 17 v-9 h-44 Z" fill="url(#qa-blue)"/>'
            f'<path d="M14 {y + 16} h44 v9 l6 -4 v-9 h-50 Z" fill="url(#qa-blue-side)"/>'
            f'<rect x="16" y="{y + 2}" width="40" height="5" rx="2.5" fill="url(#qa-gloss)" opacity=".6"/>'
        )
        return f'<g transform="translate(96 0) scale(-1 1)">{shape}</g>' if flip else shape

    return shadow(48, 88, 32, 5) + arrow(14, False) + arrow(48, True)


def icon_calculator():
    keys = "".join(
        f'<rect x="{28 + col * 14}" y="{44 + row * 11}" width="10" height="8" rx="2" '
        f'fill="{"#ffffff" if col < 2 else "#cfe3ff"}"/>'
        for row in range(3)
        for col in range(3)
    )
    return (
        shadow(50, 89, 26, 5)
        + '<rect x="24" y="12" width="52" height="74" rx="10" fill="url(#qa-blue-deep)"/>'
        + '<rect x="20" y="10" width="52" height="74" rx="10" fill="url(#qa-blue)"/>'
        + '<rect x="27" y="18" width="38" height="18" rx="4" fill="url(#qa-paper)"/>'
        + '<rect x="22" y="12" width="48" height="10" rx="5" fill="url(#qa-gloss)" opacity=".45"/>'
        + keys
    )


def icon_chart():
    bars = "".join(
        f'<rect x="{x}" y="{86 - h - 4}" width="12" height="{h}" rx="2.5" fill="url(#qa-blue)"/>'
        f'<rect x="{x + 9}" y="{86 - h - 4}" width="3" height="{h}" fill="#0d3b96" opacity=".5"/>'
        for x, h in ((16, 30), (32, 46), (48, 60), (64, 40))
    )
    return (
        shadow(48, 88, 36, 5)
        + '<path d="M12 82 h72" stroke="#9fb0c6" stroke-width="3" stroke-linecap="round"/>'
        + bars
        + check_badge(70, 66, 15)
    )


def icon_warning():
    return (
        shadow(48, 88, 34, 5)
        + '<path d="M48 10 C52 10 54 12 56 15 L86 70 C89 76 86 82 79 82 H17 C10 82 7 76 10 70 L40 15 '
        'C42 12 44 10 48 10 Z" fill="url(#qa-amber)" stroke="#ffffff" stroke-width="3"/>'
        + '<path d="M48 16 L60 38 C52 34 42 36 34 40 L45 18 Z" fill="url(#qa-gloss)" opacity=".6"/>'
        + '<rect x="43.5" y="32" width="9" height="28" rx="4.5" fill="#ffffff"/>'
        + '<circle cx="48" cy="70" r="5.2" fill="#ffffff"/>'
    )


ICONS = {
    "files": icon_files,
    "shield": icon_shield,
    "calendar": icon_calendar,
    "gear": icon_gear,
    "layers": icon_layers,
    "database": icon_database,
    "parity": icon_parity,
    "reconcile": icon_reconcile,
    "calculator": icon_calculator,
    "chart": icon_chart,
    "warning": icon_warning,
}


def build_icon_svg(name):
    return f'<svg class="qa-icon" viewBox="0 0 96 96" aria-hidden="true" focusable="false">{ICONS[name]()}</svg>'


# endregion


# The story (D-176): four stages of the pipeline, each with its role in data quality,
# its main figure, its verdict and, as small illustrations, the controls it runs.
STAGES = [
    (
        "files",
        "Fuentes",
        "Archivos identificados",
        "Prevenir: cada archivo de ODEPA queda identificado antes de entrar. Si no se sabe qué entró, "
        "no se puede auditar nada después.",
    ),
    (
        "gear",
        "Transformación",
        "Reglas de calidad",
        "Detectar y aislar: la validación rechaza la fila que no cumple una regla y la guarda con su motivo; "
        "dbt prueba cada modelo en cada construcción.",
    ),
    (
        "database",
        "Warehouse",
        "Consistencia de la base",
        "Verificar: la base publicada se lee completa y se compara con el respaldo. Si una prueba falla, "
        "la base anterior sigue publicada.",
    ),
    (
        "chart",
        "Resultados",
        "Cálculos contrastados",
        "Publicar con prueba: las cifras del panel se recalculan por otro camino (SQL frente a Python, "
        "filas crudas frente a la base) antes de confiar en ellas.",
    ),
]
# endregion
