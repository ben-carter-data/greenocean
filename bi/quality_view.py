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
import html
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
    ("reconcile", "Reconciliación fuente → base", "Verificado · pruebas automáticas",
     "120 precios por ejecución · auditoría 400 de 400.",
     "Cada ejecución de las pruebas reconstruye 120 precios semanales desde las filas crudas de "
     "ODEPA, sin el ETL. En la auditoría del 18-10-2026 coincidieron 400 de 400."),
    ("calculator", "Recálculo independiente de indicadores", "Verificado · pruebas automáticas",
     "SQL y Python coinciden.",
     "Las alertas K6 se calculan en Python y en SQL y deben coincidir (D-049); las variaciones del "
     "Resumen se comparan con un cálculo SQL independiente."),
    ("chart", "Concordancia cálculo → pantalla", "Verificado · muestra",
     "Familias, ranking y margen coinciden.",
     "Las cifras de familias, ranking y margen de la semana del 05-10-2026 se recalcularon a mano "
     "por región y coinciden con lo que muestra el panel (D-144, D-146)."),
    ("warning", "Contraste con otra fuente", "Pendiente",
     "ODEPA es la única fuente oficial de estos datos.",
     "No hay una comparación independiente de precios con otra fuente equivalente."),
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
        build_part = dict(models=int(build["models"]), tests=int(build["tests"]),
                          passing=int(build["passing"]), ok=bool(build["ok"]),
                          built_at=f"{built_at:%d-%m-%Y}" if built_at is not None else "")
    parity_part = None
    if parity:
        parity_part = dict(rows=int(parity["rows"][1]), rejections=int(parity["rejections"][1]),
                           backup_rows=int(parity["rows"][0]), backup_rejections=int(parity["rejections"][0]),
                           ok=bool(parity["ok"]))
    return dict(
        rejections=int(rejections) if rejections is not None else None,
        run_id=int(run["run_id"]) if str(run["run_id"]).isdigit() else run["run_id"], run_started=format_time(run["started_at"]), run_status=str(run["status"]),
        run_ok=run["status"] == etl.STATUS_LOADED,
        manifest_present=bool(manifest), manifest_files=len(files),
        files_matching=matching, files_total=len(files), files_failed=failed,
        weeks=int(checks["weeks"] or 0), first_week=format_week(checks["first"]),
        last_week=format_week(checks["last"]),
        build=build_part,
        checks=dict(integrity_ok=bool(checks["integrity_ok"]), foreign_keys=int(checks["foreign_keys"]),
                    duplicates=int(checks["duplicates"]), invalid=int(checks["invalid"])),
        parity=parity_part)


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
    files_total, matching, failed = (evidence["files_total"], evidence["files_matching"],
                                     evidence["files_failed"])
    integrity = ("Falla detectada" if failed else "Verificado" if files_total and matching == files_total
                 else "Pendiente de comprobación")
    sources = [
        ("files", "Origen y archivos",
         "Registro disponible" if evidence["manifest_present"] else "Sin registro disponible",
         f"{evidence['manifest_files']} archivos registrados en manifest.json.",
         "Cada descarga queda con su fecha y su huella SHA-256. Esto identifica las descargas; "
         "no certifica cada precio."),
        ("shield", "Integridad de archivos originales", integrity,
         f"{matching} de {files_total} huellas coinciden · {plural(failed, 'discrepancia', 'discrepancias')}.",
         "Los archivos locales se comparan con la huella registrada; los ausentes no se consideran "
         "verificados."),
        ("calendar", "Cobertura temporal", "Disponible",
         f"{evidence['weeks']} semanas · {evidence['first_week']} → {evidence['last_week']}.",
         "Es cobertura registrada, no confirmación de que la fuente esté al día."),
    ]
    build = evidence["build"]
    run = [
        ("gear", "Última carga registrada", "Superada" if evidence["run_ok"] else "Falla registrada",
         f"Ejecución {evidence['run_id']} · estado {evidence['run_status']}.",
         f"Ejecución {evidence['run_id']} · {evidence['run_started']} (Chile). Es evidencia de la carga "
         "guardada, no del último intento remoto."),
        ("layers", "Pruebas dbt de la última construcción",
         ("Superadas" if build["ok"] else "Falla detectada") if build else "Pendiente · sin resultado dbt",
         f"{build['passing']} de {build['tests']} pruebas · {build['models']} modelos." if build
         else "La base aún no trae el resultado de dbt.",
         (f"Construcción del {build['built_at']}. Si una prueba falla, la base publicada no se reemplaza."
          if build else "La base aún no trae el resultado de dbt.")),
    ]
    checks = evidence["checks"]
    database_ok = checks["integrity_ok"] and not any(checks[key] for key in ("foreign_keys", "duplicates", "invalid"))
    database_detail = (f"{plural(checks['foreign_keys'], 'referencia inválida', 'referencias inválidas')} · "
                       f"{plural(checks['duplicates'], 'duplicado', 'duplicados')} · "
                       f"{plural(checks['invalid'], 'formato inválido', 'formatos inválidos')}.")
    if not checks["integrity_ok"]:
        database_detail = "Lectura completa con error · " + database_detail
    parity = evidence["parity"]
    if parity and parity["ok"]:
        parity_detail = (f"{thousands(parity['rows'])} precios · {thousands(parity['rejections'])} rechazos · "
                         "misma suma.")
    elif parity:
        parity_detail = (f"SQLite {thousands(parity['backup_rows'])} y DuckDB {thousands(parity['rows'])} precios · "
                         f"{thousands(parity['backup_rejections'])} y {thousands(parity['rejections'])} "
                         "rechazos · no coinciden.")
    else:
        parity_detail = "Sin respaldo SQLite para comparar."
    warehouse = [
        ("database", "Comprobación de la base actual",
         "Verificado · alcance limitado" if database_ok else "Falla detectada", database_detail,
         "DuckDB leída completa: referencias entre tablas, claves duplicadas y precios utilizables con "
         "formato inválido."),
        ("parity", "Paridad SQLite ↔ DuckDB",
         ("Verificado" if parity["ok"] else "Falla detectada") if parity else "Pendiente · sin respaldo",
         parity_detail,
         "El respaldo SQLite y el data warehouse DuckDB deben tener los mismos precios, los mismos "
         "rechazos y la misma suma de precios (D-154)."),
    ]
    return list(zip(STEP_NAMES, [sources, run, warehouse, list(RESULT_CARDS)]))


def summarize_step(cards):
    """'fail' when one card fails, 'pending' when one waits, else 'ok'."""
    kinds = {classify(card[2]) for card in cards}
    return "fail" if "fail" in kinds else "pending" if "pending" in kinds else "ok"
# endregion


# region Illustrations
# One set of gradients for every illustration of the page (ids prefixed qa-).
def stop(offset, color, opacity=1):
    return f'<stop offset="{offset}" stop-color="{color}" stop-opacity="{opacity}"/>'


def linear(name, top, bottom, x2=0, y2=1):
    return (f'<linearGradient id="qa-{name}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
            f'{stop(0, top)}{stop(1, bottom)}</linearGradient>')


DEFS = ('<svg class="qa-defs" width="0" height="0" aria-hidden="true" focusable="false"><defs>'
        + linear("blue", "#8fd0ff", "#1f6fe0") + linear("blue-deep", "#3d8bf0", "#0d3b96")
        + linear("blue-side", "#2563d6", "#0b2e7a", 1, 0)
        + linear("green", "#6ff0a6", "#0e9f4f") + linear("paper", "#ffffff", "#d3def0")
        + linear("paper-back", "#e9f0fa", "#b4c4dc")
        + linear("silver", "#ffffff", "#a8b4c6", 1, 0) + linear("silver-top", "#ffffff", "#c9d3e1")
        + linear("amber", "#ffe07a", "#f08c00") + linear("dark", "#3a4250", "#0f141c")
        + '<linearGradient id="qa-gloss" x1="0" y1="0" x2="0" y2="1">'
        + stop(0, "#ffffff", .85) + stop(1, "#ffffff", 0) + '</linearGradient>'
        + '<radialGradient id="qa-shadow" cx=".5" cy=".5" r=".5">'
        + stop(0, "#0b1f3a", .32) + stop(1, "#0b1f3a", 0) + '</radialGradient>'
        + '</defs></svg>')


def shadow(cx=48, cy=88, rx=30, ry=5):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#qa-shadow)"/>'


def check_badge(cx, cy, r):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#qa-green)" stroke="#ffffff" stroke-width="2.5"/>'
            f'<ellipse cx="{cx}" cy="{cy - r * .45}" rx="{r * .62}" ry="{r * .38}" fill="url(#qa-gloss)" opacity=".7"/>'
            f'<path d="M{cx - r * .45:.1f} {cy + r * .02:.1f} l{r * .3:.1f} {r * .32:.1f} l{r * .6:.1f} {-r * .62:.1f}" '
            f'fill="none" stroke="#ffffff" stroke-width="{r * .24:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')


def cylinder(cx, top, width, height, bands=2):
    """A glossy database: silver body, blue bands, a lit top."""
    rx, ry = width / 2, width * .17
    left, right, bottom = cx - rx, cx + rx, top + height
    parts = [f'<path d="M{left} {top} V{bottom} A{rx} {ry} 0 0 0 {right} {bottom} V{top} Z" fill="url(#qa-silver)"/>']
    for index in range(bands):
        y = top + height * (index + 1) / (bands + 1)
        parts.append(f'<path d="M{left} {y - 2.6} A{rx} {ry} 0 0 0 {right} {y - 2.6} V{y + 2.6} '
                     f'A{rx} {ry} 0 0 1 {left} {y + 2.6} Z" fill="url(#qa-blue-deep)"/>')
    parts.append(f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="url(#qa-silver-top)" '
                 'stroke="#ffffff" stroke-width="1"/>')
    parts.append(f'<rect x="{left + width * .14}" y="{top + ry}" width="{width * .1}" height="{height - ry}" '
                 'rx="2" fill="#ffffff" opacity=".55"/>')
    return "".join(parts)


def gear_path(cx, cy, outer, inner, teeth):
    points = []
    for index in range(teeth * 4):
        angle = math.pi * 2 * index / (teeth * 4) - math.pi / 2
        radius = outer if index % 4 in (1, 2) else inner
        points.append(f"{cx + radius * math.cos(angle):.1f},{cy + radius * math.sin(angle):.1f}")
    return "M" + " L".join(points) + " Z"


def icon_files():
    return (shadow(46, 88, 32, 5)
            + '<rect x="16" y="14" width="44" height="58" rx="5" fill="url(#qa-paper-back)" transform="rotate(-8 38 43)"/>'
            + '<rect x="12" y="20" width="9" height="56" rx="3" fill="url(#qa-blue-deep)"/>'
            + '<rect x="18" y="16" width="46" height="62" rx="5" fill="url(#qa-paper)" stroke="#c4d2e8" stroke-width="1"/>'
            + "".join(f'<rect x="25" y="{y}" width="{w}" height="4" rx="2" fill="#5aa2f2"/>'
                      for y, w in ((27, 30), (36, 24), (45, 28), (54, 18)))
            + '<rect x="20" y="18" width="42" height="14" rx="4" fill="url(#qa-gloss)" opacity=".6"/>'
            + '<circle cx="64" cy="62" r="18" fill="url(#qa-green)" stroke="#ffffff" stroke-width="3"/>'
            + '<ellipse cx="64" cy="54" rx="11" ry="6" fill="url(#qa-gloss)" opacity=".7"/>'
            + "".join(f'<path d="M{64 - r} {66} a{r} {r} 0 0 1 {2 * r} 0" fill="none" stroke="#ffffff" '
                      f'stroke-width="2" stroke-linecap="round"/>' for r in (3, 6.5, 10))
            + '<path d="M64 66 v6 M57.5 66 v4 M70.5 66 v5" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>')


def icon_shield():
    outline = "M48 8 L78 19 V44 C78 64 64 78 48 86 C32 78 18 64 18 44 V19 Z"
    return (shadow(48, 89, 28, 4.5)
            + f'<path d="{outline}" fill="url(#qa-silver)" stroke="#9fb0c6" stroke-width="1"/>'
            + '<path d="M48 15 L72 24 V44 C72 60 61 72 48 79 C35 72 24 60 24 44 V24 Z" fill="url(#qa-green)"/>'
            + '<path d="M48 15 L72 24 V36 C60 33 40 40 24 46 V24 Z" fill="url(#qa-gloss)" opacity=".55"/>'
            + '<path d="M35 46 l9 9 l17 -19" fill="none" stroke="#ffffff" stroke-width="7" '
            'stroke-linecap="round" stroke-linejoin="round"/>')


def icon_calendar():
    cells = "".join(f'<rect x="{24 + col * 12.5}" y="{44 + row * 11}" width="9" height="7.5" rx="1.6" '
                    f'fill="{"#2f80ed" if (row + col) % 3 else "#7fb6f7"}"/>'
                    for row in range(3) for col in range(4))
    return (shadow(48, 89, 32, 5)
            + '<rect x="16" y="18" width="64" height="66" rx="9" fill="url(#qa-paper)" stroke="#c4d2e8"/>'
            + '<path d="M16 27 a9 9 0 0 1 9 -9 h46 a9 9 0 0 1 9 9 v9 h-64 Z" fill="url(#qa-blue)"/>'
            + '<rect x="18" y="20" width="60" height="7" rx="3.5" fill="url(#qa-gloss)" opacity=".55"/>'
            + "".join(f'<rect x="{x}" y="10" width="7" height="18" rx="3.5" fill="url(#qa-silver)" '
                      'stroke="#8fa1b8"/>' for x in (30, 59))
            + cells)


def icon_gear():
    return (shadow(48, 89, 30, 5)
            + f'<path d="{gear_path(48, 46, 37, 29, 10)}" fill="url(#qa-blue-deep)"/>'
            + f'<path d="{gear_path(48, 44, 36, 28, 10)}" fill="url(#qa-blue)"/>'
            + '<ellipse cx="44" cy="26" rx="20" ry="9" fill="url(#qa-gloss)" opacity=".5"/>'
            + check_badge(48, 45, 17))


def icon_layers():
    def slab(y, top, side):
        return (f'<path d="M48 {y} L80 {y + 14} L48 {y + 28} L16 {y + 14} Z" fill="url(#qa-{top})"/>'
                f'<path d="M16 {y + 14} L48 {y + 28} V{y + 34} L16 {y + 20} Z" fill="url(#qa-{side})"/>'
                f'<path d="M80 {y + 14} L48 {y + 28} V{y + 34} L80 {y + 20} Z" fill="#0b3a92"/>'
                f'<path d="M48 {y + 2} L72 {y + 13} L48 {y + 16} L24 {y + 13} Z" fill="url(#qa-gloss)" opacity=".45"/>')
    return shadow(48, 88, 32, 5) + slab(50, "blue", "blue-side") + slab(34, "blue", "blue-side") + slab(18, "paper", "blue-side")


def icon_database():
    return (shadow(46, 89, 30, 5) + cylinder(44, 18, 50, 62, 2)
            + '<circle cx="72" cy="70" r="13" fill="url(#qa-dark)" stroke="#ffffff" stroke-width="2.5"/>'
            + '<circle cx="69" cy="70" r="5" fill="#ffd43b"/><circle cx="77" cy="68" r="2.5" fill="#ffd43b"/>')


def icon_parity():
    return (shadow(48, 89, 36, 5) + cylinder(28, 20, 34, 40, 2) + cylinder(66, 44, 30, 36, 2)
            + '<path d="M50 18 C62 14 72 18 76 30" fill="none" stroke="url(#qa-blue)" stroke-width="5" stroke-linecap="round"/>'
            + '<path d="M70 28 L77 36 L82 25 Z" fill="#1f6fe0"/>'
            + '<path d="M44 82 C32 86 20 80 18 70" fill="none" stroke="url(#qa-blue)" stroke-width="5" stroke-linecap="round"/>'
            + '<path d="M24 72 L17 63 L12 74 Z" fill="#1f6fe0"/>')


def icon_reconcile():
    def arrow(y, flip):
        shape = (f'<path d="M14 {y} h44 v-9 l24 17 l-24 17 v-9 h-44 Z" fill="url(#qa-blue)"/>'
                 f'<path d="M14 {y + 16} h44 v9 l6 -4 v-9 h-50 Z" fill="url(#qa-blue-side)"/>'
                 f'<rect x="16" y="{y + 2}" width="40" height="5" rx="2.5" fill="url(#qa-gloss)" opacity=".6"/>')
        return f'<g transform="translate(96 0) scale(-1 1)">{shape}</g>' if flip else shape
    return shadow(48, 88, 32, 5) + arrow(14, False) + arrow(48, True)


def icon_calculator():
    keys = "".join(f'<rect x="{28 + col * 14}" y="{44 + row * 11}" width="10" height="8" rx="2" '
                   f'fill="{"#ffffff" if col < 2 else "#cfe3ff"}"/>' for row in range(3) for col in range(3))
    return (shadow(50, 89, 26, 5)
            + '<rect x="24" y="12" width="52" height="74" rx="10" fill="url(#qa-blue-deep)"/>'
            + '<rect x="20" y="10" width="52" height="74" rx="10" fill="url(#qa-blue)"/>'
            + '<rect x="27" y="18" width="38" height="18" rx="4" fill="url(#qa-paper)"/>'
            + '<rect x="22" y="12" width="48" height="10" rx="5" fill="url(#qa-gloss)" opacity=".45"/>'
            + keys)


def icon_chart():
    bars = "".join(f'<rect x="{x}" y="{86 - h - 4}" width="12" height="{h}" rx="2.5" fill="url(#qa-blue)"/>'
                   f'<rect x="{x + 9}" y="{86 - h - 4}" width="3" height="{h}" fill="#0d3b96" opacity=".5"/>'
                   for x, h in ((16, 30), (32, 46), (48, 60), (64, 40)))
    return (shadow(48, 88, 36, 5)
            + '<path d="M12 82 h72" stroke="#9fb0c6" stroke-width="3" stroke-linecap="round"/>' + bars
            + check_badge(70, 66, 15))


def icon_warning():
    return (shadow(48, 88, 34, 5)
            + '<path d="M48 10 C52 10 54 12 56 15 L86 70 C89 76 86 82 79 82 H17 C10 82 7 76 10 70 L40 15 '
            'C42 12 44 10 48 10 Z" fill="url(#qa-amber)" stroke="#ffffff" stroke-width="3"/>'
            + '<path d="M48 16 L60 38 C52 34 42 36 34 40 L45 18 Z" fill="url(#qa-gloss)" opacity=".6"/>'
            + '<rect x="43.5" y="32" width="9" height="28" rx="4.5" fill="#ffffff"/>'
            + '<circle cx="48" cy="70" r="5.2" fill="#ffffff"/>')


ICONS = {"files": icon_files, "shield": icon_shield, "calendar": icon_calendar, "gear": icon_gear,
         "layers": icon_layers, "database": icon_database, "parity": icon_parity,
         "reconcile": icon_reconcile, "calculator": icon_calculator, "chart": icon_chart,
         "warning": icon_warning}


def build_icon_svg(name):
    return (f'<svg class="qa-icon" viewBox="0 0 96 96" aria-hidden="true" focusable="false">'
            f'{ICONS[name]()}</svg>')
# endregion


# region Markup
STEP_MARKS = {"ok": "M7 12.5 l3.2 3.2 L17 9", "pending": "M12 7 v6 M12 16.6 v.4", "fail": "M8.5 8.5 l7 7 M15.5 8.5 l-7 7"}
STEP_WORDS = {"ok": "comprobaciones superadas", "pending": "con comprobaciones pendientes",
              "fail": "con una falla detectada"}
# The story (D-176): four stages of the pipeline, each with its role in data quality,
# its main figure, its verdict and, as small illustrations, the controls it runs.
STAGES = [
    ("files", "Fuentes", "Archivos identificados",
     "Prevenir: cada archivo de ODEPA queda identificado antes de entrar. Si no se sabe qué entró, "
     "no se puede auditar nada después."),
    ("gear", "Transformación", "Reglas de calidad",
     "Detectar y aislar: la validación rechaza la fila que no cumple una regla y la guarda con su motivo; "
     "dbt prueba cada modelo en cada construcción."),
    ("database", "Warehouse", "Consistencia de la base",
     "Verificar: la base publicada se lee completa y se compara con el respaldo. Si una prueba falla, "
     "la base anterior sigue publicada."),
    ("chart", "Resultados", "Cálculos contrastados",
     "Publicar con prueba: las cifras del panel se recalculan por otro camino (SQL frente a Python, "
     "filas crudas frente a la base) antes de confiar en ellas."),
]
# The method: the six data quality dimensions of the DAMA-DMBOK, each with the
# controls of this project that measure it. Status comes from the evidence.
DIMENSIONS = [
    ("Completitud", "Están todos los datos esperados: cada semana entre la primera y la última, y los "
                    "precios de cada región que ODEPA publicó.", "Cobertura temporal · pruebas dbt not_null."),
    ("Unicidad", "Ningún precio aparece dos veces: una fila por producto, región, canal y semana.",
                 "Claves duplicadas en la base · prueba dbt unique."),
    ("Validez", "Cada valor tiene el formato y el rango permitidos: precio numérico y positivo, unidad "
                "convertible, fecha real.", "Validación del ETL (rechazos) · formato de precios · accepted_values."),
    ("Consistencia", "Los datos concuerdan entre sí y entre copias: referencias entre tablas, y el mismo "
                     "total en SQLite y en DuckDB.", "Referencias entre tablas · paridad SQLite ↔ DuckDB."),
    ("Exactitud", "Las cifras reflejan la fuente: se reconstruyen desde las filas crudas y por otro "
                  "camino de cálculo. Sin segunda fuente oficial, el contraste externo queda pendiente.",
                  "Reconciliación fuente → base · recálculo SQL y Python · muestra manual."),
    ("Actualidad", "Los datos son los últimos disponibles: la carga semanal corre cada martes y queda "
                   "registrada con su resultado.", "Última carga registrada · cobertura hasta la última semana."),
]
DIMENSION_WORDS = {"ok": "cumplida", "pending": "pendiente", "fail": "con falla"}


def build_step_mark(kind, step):
    return (f'<span class="qa-mark qa-{kind}" role="img" aria-label="{html.escape(step)}: {STEP_WORDS[kind]}">'
            f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{STEP_MARKS[kind]}"/></svg></span>')


def build_detail_html(detail):
    """Each «·» part kept whole, so a line breaks between figures, never inside one."""
    parts = detail.split(" · ")
    if len(parts) == 1:
        return html.escape(detail)
    return " · ".join(f'<span class="qa-seg">{html.escape(part)}</span>' if len(part) <= 30
                      else html.escape(part) for part in parts)


def build_control_html(icon, title, status, detail, explanation, edge):
    """A small illustration of one control; hovering it tells what it checks."""
    kind = classify(status)
    return (f'<div class="qa-control qa-control-{kind}" tabindex="0"><span class="qa-control-dot"></span>'
            f'{build_icon_svg(icon)}<span class="qa-control-name">{html.escape(title)}</span>'
            f'<div class="qa-tip qa-tip-{edge}" role="tooltip"><h4>{html.escape(title)}</h4>'
            f'<span class="qa-pill qa-{kind}">{html.escape(status)}</span>'
            f'<p class="qa-tip-figure">{build_detail_html(detail)}</p>'
            f'<p>{html.escape(explanation)}</p></div></div>')


def stage_verdicts(evidence, columns):
    """Per stage: (kind, chip text, figure lines, footnote)."""
    files_total, matching, failed = evidence["files_total"], evidence["files_matching"], evidence["files_failed"]
    integrity_kind = "fail" if failed else "ok" if files_total and matching == files_total else "pending"
    build, checks, parity = evidence["build"], evidence["checks"], evidence["parity"]
    sources = (integrity_kind,
               {"ok": "Integridad verificada", "pending": "Integridad pendiente", "fail": "Discrepancia en archivos"}[integrity_kind],
               [f"{evidence['manifest_files']} archivos registrados en manifest.json.",
                f"{evidence['weeks']} semanas · {evidence['first_week']} → {evidence['last_week']}."],
               f"Huellas: {matching} de {files_total} coinciden." if integrity_kind == "ok"
               else "Huellas: control pendiente." if integrity_kind == "pending" else f"Huellas: {plural(failed, 'discrepancia', 'discrepancias')}.")
    run_kind = summarize_step(columns[1][1])
    transformation = (run_kind,
                      {"ok": "Pruebas superadas", "pending": "Sin resultado dbt", "fail": "Falla detectada"}[run_kind],
                      [f"{build['passing']} de {build['tests']} pruebas dbt · {build['models']} modelos." if build
                       else "La base aún no trae el resultado de dbt.",
                       f"Ejecución {evidence['run_id']} · {evidence['run_status']}."],
                      f"Construcción del {build['built_at']}." if build and build.get("built_at") else "Cada carga vuelve a probar.")
    warehouse_kind = summarize_step(columns[2][1])
    warehouse = (warehouse_kind,
                 {"ok": "Consistencia verificada", "pending": "Sin respaldo SQLite", "fail": "Falla detectada"}[warehouse_kind],
                 [f"{checks['foreign_keys']} referencias inválidas · {checks['duplicates']} duplicados · "
                  f"{checks['invalid']} formatos inválidos.",
                  ("SQLite ↔ DuckDB: misma suma." if parity["ok"] else "SQLite ↔ DuckDB: no coinciden.") if parity
                  else "Sin respaldo SQLite para comparar."],
                 f"{thousands(parity['rows'])} precios publicados." if parity else "Lectura completa de la base.")
    results_kind = summarize_step([card for card in columns[3][1] if card[0] != "warning"])
    results = (results_kind, {"ok": "Verificado", "pending": "Pendiente de auditoría", "fail": "Falla detectada"}[results_kind],
               ["SQL y Python coinciden.", "Auditoría: 400 de 400 precios."],
               "Pantalla: verificación por muestra · otra fuente: pendiente.")
    return [sources, transformation, warehouse, results]


def dimension_kinds(evidence):
    """The six dimensions, each 'ok', 'pending' or 'fail' from the evidence."""
    checks, parity, build = evidence["checks"], evidence["parity"], evidence["build"]
    files_total, matching, failed = evidence["files_total"], evidence["files_matching"], evidence["files_failed"]
    tests_kind = ("ok" if build["ok"] else "fail") if build else "pending"
    return {
        "Completitud": "ok" if evidence["weeks"] and tests_kind == "ok" else tests_kind if tests_kind != "ok" else "pending",
        "Unicidad": "fail" if checks["duplicates"] else "ok",
        "Validez": "fail" if checks["invalid"] or failed else "ok" if files_total and matching == files_total else "pending",
        "Consistencia": "fail" if checks["foreign_keys"] or not checks["integrity_ok"] or (parity and not parity["ok"])
                        else "ok" if parity else "pending",
        "Exactitud": "ok",
        "Actualidad": "ok" if evidence["run_ok"] else "fail",
    }


def build_dimension_html(name, definition, controls, kind):
    return (f'<div class="qa-dim qa-dim-{kind}" tabindex="0"><span class="qa-dim-dot"></span>{html.escape(name)}'
            f'<div class="qa-tip qa-tip-center" role="tooltip"><h4>{html.escape(name)} · {DIMENSION_WORDS[kind]}</h4>'
            f'<p>{html.escape(definition)}</p><p class="qa-tip-figure">Controles: {html.escape(controls)}</p></div></div>')


def build_overview_css(mode):
    palette = charts.get_palette(mode)
    dark = palette["base"] != charts.BASE_LIGHT
    line = "rgba(148,163,184,.22)" if dark else "rgba(15,40,80,.10)"
    soft = palette["reference"] if dark else palette["text"]
    icon_shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,40,90,.18)"
    card, border, ink, accent = palette["card"], palette["card_border"], palette["strong_text"], palette["accent"]
    raised = ("0 1px 0 rgba(255,255,255,.06) inset, 0 24px 48px -30px rgba(0,0,0,.9), 0 0 0 1px rgba(255,255,255,.03)" if dark
              else "0 1px 0 #fff inset, 0 24px 48px -32px rgba(15,27,45,.45), 0 6px 14px -10px rgba(15,27,45,.18)")
    tip_shadow = "0 18px 40px -16px rgba(0,0,0,.85)" if dark else "0 18px 40px -18px rgba(15,27,45,.45)"
    pills = "".join(f".qa-page .qa-{kind}{{--qa-c:{color};}} .qa-page .qa-control-{kind},.qa-page .qa-dim-{kind},.qa-page .qa-stage-{kind}{{--qa-c:{color};}}"
                    for kind, color in PILL_COLORS.items())
    return f"""<style>
.qa-page{{container-type:inline-size;color:{palette['text']};font-family:inherit;margin:0 0 6px;}}
.qa-page .qa-defs{{position:absolute;width:0;height:0;overflow:hidden;}}
{pills}
.qa-page .qa-head{{display:flex;flex-wrap:wrap;align-items:flex-start;justify-content:space-between;gap:8px 24px;margin-bottom:12px;}}
.qa-page .qa-head > div:first-child{{flex:1 1 380px;}} .qa-page .qa-head .qa-run{{flex:0 0 auto;}}
.qa-page h1.qa-h1{{margin:0;padding:0;font-size:1.9rem;line-height:1.15;font-weight:400;letter-spacing:-.025em;color:{ink};}}
.qa-page .qa-sub{{margin:4px 0 0;font-size:.98rem;font-weight:300;color:{soft};}}
.qa-page .qa-run{{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;padding-top:8px;font-size:.84rem;color:{ink};}}
.qa-page .qa-chip{{display:inline-flex;align-items:center;gap:8px;padding:5px 13px;border-radius:999px;font-weight:500;font-size:.8rem;
  color:var(--qa-c);background:color-mix(in srgb,var(--qa-c) {"18%" if dark else "11%"},transparent);
  box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--qa-c) 35%,transparent);}}
.qa-page .qa-chip::before{{content:"";width:8px;height:8px;border-radius:50%;background:var(--qa-c);box-shadow:0 0 0 3px color-mix(in srgb,var(--qa-c) 25%,transparent);}}
.qa-page .qa-method{{position:relative;z-index:3;display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px;padding:8px 14px;margin-bottom:12px;border-radius:14px;
  border:1px solid {border};background:{card};box-shadow:{raised};}}
.qa-page .qa-method-label{{font-size:.68rem;font-weight:500;letter-spacing:.11em;text-transform:uppercase;color:{soft};margin-right:6px;white-space:nowrap;}}
.qa-page .qa-method-label b{{display:block;font-size:.78rem;letter-spacing:0;text-transform:none;font-weight:400;color:{ink};}}
.qa-page .qa-dim{{position:relative;display:inline-flex;align-items:center;gap:7px;padding:4px 12px 4px 9px;border-radius:999px;font-size:.8rem;color:{ink};
  background:color-mix(in srgb,var(--qa-c) {"14%" if dark else "9%"},{card});border:1px solid color-mix(in srgb,var(--qa-c) 40%,transparent);cursor:default;
  transition:transform .18s ease,box-shadow .18s ease;}}
.qa-page .qa-dim:hover,.qa-page .qa-dim:focus-within{{z-index:30;transform:translateY(-2px);box-shadow:0 10px 18px -12px color-mix(in srgb,var(--qa-c) 70%,transparent);}}
.qa-page .qa-dim-dot{{width:8px;height:8px;border-radius:50%;background:radial-gradient(circle at 35% 30%,color-mix(in srgb,var(--qa-c) 55%,#fff),var(--qa-c) 70%);
  box-shadow:0 1px 2px rgba(0,0,0,.3);}}
.qa-page .qa-method-flow{{margin-left:auto;font-size:.74rem;color:{soft};white-space:nowrap;}}
.qa-page .qa-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0 12px;}}
.qa-page .qa-stage{{position:relative;display:flex;flex-direction:column;align-items:center;text-align:center;gap:3px;padding:6px 8px 8px;border-radius:18px;
  border:1px solid {border};background:linear-gradient(180deg,color-mix(in srgb,{card} 92%,{'#fff' if not dark else '#000'}),{card});box-shadow:{raised};
  transition:transform .22s ease,box-shadow .22s ease;}}
.qa-page .qa-stage:hover,.qa-page .qa-stage:focus-within{{z-index:20;transform:translateY(-3px);}}
.qa-page .qa-step{{display:flex;align-items:center;gap:10px;align-self:stretch;height:30px;margin-bottom:4px;}}
.qa-page .qa-step-number{{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;font-size:.72rem;font-weight:500;color:var(--qa-c);
  border:1.5px solid var(--qa-c);background:color-mix(in srgb,var(--qa-c) 10%,transparent);}}
.qa-page .qa-step-name{{font-size:.74rem;font-weight:500;letter-spacing:.11em;text-transform:uppercase;color:{ink};white-space:nowrap;}}
.qa-page .qa-step::after{{content:"";flex:1;height:2px;border-radius:2px;background:linear-gradient(90deg,{line},color-mix(in srgb,var(--qa-c) 75%,transparent));}}
.qa-page .qa-stage:last-child .qa-step::after{{opacity:0;}}
.qa-page .qa-step .qa-mark{{position:absolute;right:-20px;top:9px;z-index:2;}}
.qa-page .qa-mark{{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,color-mix(in srgb,var(--qa-c) 55%,#fff),var(--qa-c) 70%);
  box-shadow:0 0 0 4px {palette['background']},0 4px 10px -2px color-mix(in srgb,var(--qa-c) 60%,transparent);}}
.qa-page .qa-mark svg{{width:16px;height:16px;fill:none;stroke:#fff;stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round;}}
.qa-page .qa-icon{{width:82px;height:82px;flex:none;filter:drop-shadow(0 10px 12px {icon_shadow});transition:transform .22s ease;}}
.qa-page .qa-stage:hover > .qa-icon{{transform:translateY(-4px) scale(1.04);}}
.qa-page .qa-title{{margin-top:2px;font-size:1rem;font-weight:500;line-height:1.25;color:{ink};}}
.qa-page .qa-figure{{font-size:.8rem;line-height:1.4;color:{soft};margin:0;}}
.qa-page .qa-stage .qa-chip{{margin-top:6px;}}
.qa-page .qa-foot{{font-size:.74rem;color:{soft};margin:4px 0 0;}}
.qa-page .qa-controls{{display:flex;justify-content:center;gap:4px;margin-top:8px;padding-top:8px;border-top:1px solid {line};align-self:stretch;}}
.qa-page .qa-control{{position:relative;display:flex;flex-direction:column;align-items:center;gap:2px;width:58px;padding:4px 2px;border-radius:10px;cursor:default;
  transition:background .18s ease;}}
.qa-page .qa-control:hover,.qa-page .qa-control:focus-within{{z-index:25;background:color-mix(in srgb,{accent} 8%,transparent);}}
.qa-page .qa-control .qa-icon{{width:34px;height:34px;filter:drop-shadow(0 4px 5px {icon_shadow});}}
.qa-page .qa-control:hover .qa-icon{{transform:translateY(-3px) scale(1.08);}}
.qa-page .qa-control-name{{font-size:.6rem;line-height:1.15;color:{soft};text-align:center;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;}}
.qa-page .qa-control-dot{{position:absolute;top:4px;right:8px;width:7px;height:7px;border-radius:50%;background:var(--qa-c);box-shadow:0 0 0 2px {card};}}
.qa-page .qa-tip{{position:absolute;z-index:8;top:calc(100% + 6px);left:50%;width:272px;padding:12px 14px;border-radius:14px;text-align:left;
  background:{card};border:1px solid {border};box-shadow:{tip_shadow};opacity:0;pointer-events:none;transform:translate(-50%,6px);
  transition:opacity .18s ease,transform .18s ease;font-size:.78rem;line-height:1.45;color:{palette['text']};}}
.qa-page .qa-tip-start{{left:0;transform:translate(0,6px);}} .qa-page .qa-tip-end{{left:auto;right:0;transform:translate(0,6px);}}
.qa-page :is(.qa-control,.qa-dim,.qa-anomaly):hover > .qa-tip,.qa-page :is(.qa-control,.qa-dim,.qa-anomaly):focus-within > .qa-tip,
.qa-page .qa-stage:hover > .qa-tip{{opacity:1;pointer-events:auto;transform:translate(-50%,0);}}
.qa-page :is(.qa-control,.qa-dim,.qa-anomaly):hover > .qa-tip-start,.qa-page .qa-stage:hover > .qa-tip-start{{transform:translate(0,0);}}
.qa-page :is(.qa-control,.qa-dim,.qa-anomaly):hover > .qa-tip-end,.qa-page .qa-stage:hover > .qa-tip-end{{transform:translate(0,0);}}
.qa-page .qa-stage > .qa-tip,.qa-page .qa-anomaly > .qa-tip{{top:auto;bottom:calc(100% - 2px);width:300px;transform:translate(-50%,-6px);}}
.qa-page .qa-anomaly:hover > .qa-tip,.qa-page .qa-anomaly:focus-within > .qa-tip{{transform:translate(-50%,0);}}
.qa-page .qa-stage:hover > .qa-tip{{transform:translate(-50%,0);}}
.qa-page .qa-stage:hover > .qa-tip-start,.qa-page .qa-stage:hover > .qa-tip-end{{transform:translate(0,0);}}
.qa-page .qa-stage:has(.qa-control:hover) > .qa-tip{{opacity:0;}}
.qa-page .qa-tip h4{{margin:0 0 4px;font-size:.84rem;font-weight:500;color:{ink};}}
.qa-page .qa-tip p{{margin:4px 0 0;}}
.qa-page .qa-tip .qa-tip-figure{{color:{ink};}}
.qa-page .qa-tip .qa-tip-role{{font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:{soft};margin:0 0 2px;}}
.qa-page .qa-pill{{display:inline-block;max-width:100%;padding:2px 10px;border-radius:12px;font-size:.7rem;font-weight:500;line-height:1.5;
  color:#fff;background:linear-gradient(180deg,color-mix(in srgb,var(--qa-c) 82%,#fff),var(--qa-c));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.35),0 3px 8px -3px color-mix(in srgb,var(--qa-c) 70%,transparent);}}
.qa-page .qa-seg{{white-space:nowrap;}}
.qa-page .qa-anomaly{{position:relative;z-index:1;}} .qa-page .qa-anomaly:hover,.qa-page .qa-anomaly:focus-within{{z-index:25;}}
.qa-page .qa-anomaly{{grid-column:2 / 4;display:flex;align-items:center;gap:14px;margin:12px 40px 0;padding:8px 16px;border-radius:14px;
  border:1px solid color-mix(in srgb,{PILL_COLORS['pending']} 55%,transparent);background:color-mix(in srgb,{PILL_COLORS['pending']} {"12%" if dark else "7%"},{card});
  box-shadow:{raised};cursor:default;}}
.qa-page .qa-anomaly .qa-icon{{width:46px;height:46px;filter:drop-shadow(0 6px 8px {icon_shadow});}}
.qa-page .qa-anomaly-label{{font-size:.64rem;letter-spacing:.11em;text-transform:uppercase;color:{PILL_COLORS['pending']};font-weight:500;}}
.qa-page .qa-anomaly-figure{{font-size:1rem;color:{ink};font-weight:500;line-height:1.3;}}
.qa-page .qa-anomaly-note{{font-size:.76rem;color:{soft};}}
.qa-page .qa-anomaly-link{{position:absolute;left:-40px;top:-14px;width:40px;height:28px;border-left:2px dashed {PILL_COLORS['pending']};
  border-bottom:2px dashed {PILL_COLORS['pending']};border-radius:0 0 0 10px;opacity:.8;}}
.qa-page .qa-anomaly-word{{position:absolute;left:-150px;top:-6px;width:104px;text-align:right;font-size:.7rem;color:{PILL_COLORS['pending']};}}
.qa-page .qa-bar{{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;margin-top:14px;padding:9px 16px;border-radius:12px;border:1px solid {border};
  background:linear-gradient(180deg,color-mix(in srgb,var(--qa-c) {"16%" if dark else "9%"},{card}),color-mix(in srgb,var(--qa-c) {"8%" if dark else "4%"},{card}));
  font-size:.8rem;color:{ink};}}
.qa-page .qa-bar .qa-bar-mark{{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:50%;background:var(--qa-c);color:#fff;font-size:.66rem;}}
.qa-page .qa-bar b{{font-weight:500;}}
.qa-page .qa-bar .qa-bar-flow{{margin-left:auto;font-size:.74rem;color:{soft};}}
@container (max-width:860px){{
  .qa-page .qa-grid{{grid-template-columns:repeat(2,minmax(0,1fr));row-gap:14px;}}
  .qa-page .qa-step .qa-mark{{display:none;}}
  .qa-page .qa-anomaly{{grid-column:1 / 3;margin:0;}}
  .qa-page .qa-anomaly-link,.qa-page .qa-anomaly-word{{display:none;}}
}}
.st-key-{EXPANDER_KEY} .qa-open-label{{font-size:.72rem;font-weight:500;letter-spacing:.11em;text-transform:uppercase;color:{palette['reference']};white-space:nowrap;}}
</style>"""


def build_overview_html(evidence, mode):
    """The page as one HTML block: the head, the method strip, the four stages with
    their controls, the anomalies box and the status bar (D-176)."""
    columns = build_columns(evidence)
    verdicts = stage_verdicts(evidence, columns)
    kinds = [kind for kind, *_ in verdicts]
    overall = "fail" if "fail" in kinds else "pending" if "pending" in kinds else "ok"
    run_line = (f"Ejecución {evidence['run_id']} · {evidence['run_started']} (Chile) · "
                f"{evidence['run_status']}")
    head_chip = {"ok": "Verificación completa", "pending": "Verificación parcial", "fail": "Verificación con falla"}[overall]
    head = (f'<div class="qa-head"><div><h1 class="qa-h1">Calidad y auditoría</h1>'
            '<p class="qa-sub">Cómo verificamos los datos, desde el origen hasta la pantalla.</p></div>'
            f'<div class="qa-run"><span>{html.escape(run_line)}</span>'
            f'<span class="qa-chip qa-{"ok" if evidence["run_ok"] else "fail"}">'
            f'{"Carga correcta" if evidence["run_ok"] else "Carga con falla"}</span>'
            f'<span class="qa-chip qa-{overall}">{head_chip}</span></div></div>')
    dimension_kind = dimension_kinds(evidence)
    method = ('<div class="qa-method"><span class="qa-method-label">Método<b>Seis dimensiones de calidad · DAMA-DMBOK</b></span>'
              + "".join(build_dimension_html(name, definition, controls, dimension_kind[name])
                        for name, definition, controls in DIMENSIONS)
              + '<span class="qa-method-flow">prevenir → detectar → aislar → verificar → publicar</span></div>')
    stages = []
    for position, ((icon, step, title, role), (kind, chip, figures, foot), (_, cards)) in enumerate(zip(STAGES, verdicts, columns)):
        last = position == len(STAGES) - 1
        edge = "start" if position == 0 else "end" if last else "center"
        mark = "" if last else build_step_mark(kind, step)
        controls = "".join(build_control_html(*card, edge=edge) for card in cards)
        stages.append(
            f'<section class="qa-stage qa-stage-{kind}" aria-label="{html.escape(step)}">'
            f'<div class="qa-step"><span class="qa-step-number">0{position + 1}</span>'
            f'<span class="qa-step-name">{html.escape(step)}</span>{mark}</div>'
            f'{build_icon_svg(icon)}<div class="qa-title">{html.escape(title)}</div>'
            + "".join(f'<p class="qa-figure">{html.escape(figure)}</p>' for figure in figures)
            + f'<span class="qa-chip qa-{kind}">{html.escape(chip)}</span><p class="qa-foot">{html.escape(foot)}</p>'
            f'<div class="qa-controls">{controls}</div>'
            f'<div class="qa-tip qa-tip-{edge}" role="tooltip"><p class="qa-tip-role">Rol en la calidad</p>'
            f'<h4>{html.escape(step)} · {html.escape(title)}</h4><p>{html.escape(role)}</p></div></section>')
    rejections = evidence.get("rejections")
    if rejections is None and evidence["parity"]:
        rejections = evidence["parity"]["rejections"]
    rejection_text = f"{thousands(rejections)} rechazos registrados" if rejections is not None else "Rechazos registrados en la base"
    anomaly = (f'<div class="qa-anomaly" tabindex="0"><span class="qa-anomaly-word">Registros rechazados</span><span class="qa-anomaly-link"></span>'
               f'{build_icon_svg("warning")}<div><div class="qa-anomaly-label">Anomalías detectadas</div>'
               f'<div class="qa-anomaly-figure">{html.escape(rejection_text)}</div>'
               '<div class="qa-anomaly-note">Filas de origen que no cumplieron una regla. Consultar motivos y registros.</div></div>'
               '<div class="qa-tip qa-tip-center" role="tooltip"><h4>Aislar, no corregir</h4>'
               '<p>Una fila que no cumple una regla (precio no numérico, unidad no convertible, fecha inválida) no se '
               'arregla a mano ni se interpola: se aparta con su motivo y su fila original en la tabla rejection, y no entra '
               'al data warehouse. Así cada cifra publicada se puede reconstruir desde la fuente.</p>'
               '<p class="qa-tip-figure">Evidencia: «Última carga registrada».</p></div></div>')
    pending = [text for kind, text in ((kinds[0], "integridad de archivos pendiente"), (kinds[1], "sin resultado dbt"),
                                       (kinds[2], "sin respaldo SQLite")) if kind == "pending"]
    if overall == "fail":
        verdict = "Verificación con fallas · revisa la evidencia antes de usar las cifras"
    elif pending:
        verdict = "Verificación completada · " + " · ".join(pending)
    else:
        verdict = "Verificación completada · todos los controles superados"
    bar = (f'<div class="qa-bar qa-{overall}"><span class="qa-bar-mark">{"✓" if overall == "ok" else "!"}</span>'
           f'<b>{html.escape(verdict)}</b><span class="qa-bar-flow">Contraste con otra fuente: pendiente (ODEPA es la única oficial)</span></div>')
    return (build_overview_css(mode) + f'<div class="qa-page">{DEFS}{head}{method}'
            f'<div class="qa-grid">{"".join(stages)}{anomaly}</div>{bar}</div>')


build_quality_overview_html = build_overview_html
# endregion
