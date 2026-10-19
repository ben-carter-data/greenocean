"""«Calidad y auditoría» as the author's mockup: a four-step timeline of the evidence
(Fuentes → Ejecución y dbt → Warehouse → Resultados) and, under each step, its cards:
a glossy illustration, a status pill, a title and the real figure behind it.

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

The page is one block of HTML with its CSS scoped under .qa-page (no script), for
st.markdown(unsafe_allow_html=True). The detailed evidence goes in a collapsed
st.expander labelled EXPANDER_LABEL, inside st.container(key=EXPANDER_KEY): the CSS
also dresses that expander as the full-width bar of the mockup.
"""
import html
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts  # noqa: E402
from etl import etl  # noqa: E402

EXPANDER_LABEL = "Evidencia detallada · Reglas dbt · Archivos · Última carga →"
EXPANDER_KEY = "qa_evidence"
EXPANDER_ICON = ":material/description:"

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


def build_evidence(checks, files, manifest, run, build, parity, format_time):
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


def build_step_mark(kind, step):
    return (f'<span class="qa-mark qa-{kind}" role="img" aria-label="{html.escape(step)}: {STEP_WORDS[kind]}">'
            f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{STEP_MARKS[kind]}"/></svg></span>')


def build_card_html(icon, title, status, detail, explanation, compact):
    kind = classify(status)
    return (f'<div class="qa-card{" qa-compact" if compact else ""}" title="{html.escape(explanation, quote=True)}">'
            f'{build_icon_svg(icon)}<div class="qa-body">'
            f'<span class="qa-pill qa-{kind}">{html.escape(status)}</span>'
            f'<div class="qa-title">{html.escape(title)}</div>'
            f'<div class="qa-detail">{build_detail_html(detail)}</div></div></div>')


def build_detail_html(detail):
    """Each «·» part kept whole, so a line breaks between figures, never inside one."""
    parts = detail.split(" · ")
    if len(parts) == 1:
        return html.escape(detail)
    return " · ".join(f'<span class="qa-seg">{html.escape(part)}</span>' if len(part) <= 30
                      else html.escape(part) for part in parts)


def build_overview_css(mode):
    palette = charts.get_palette(mode)
    dark = palette["base"] != charts.BASE_LIGHT
    line = "rgba(148,163,184,.22)" if dark else "rgba(15,40,80,.10)"
    soft = palette["reference"] if dark else palette["text"]
    hover = "rgba(255,255,255,.035)" if dark else "rgba(21,101,216,.045)"
    icon_shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,40,90,.18)"
    bar = palette["card"]
    pills = "".join(f".qa-page .qa-{kind}{{--qa-c:{color};}}" for kind, color in PILL_COLORS.items())
    return f"""<style>
.qa-page{{container-type:inline-size;color:{palette['text']};font-family:inherit;margin:0 0 6px;}}
.qa-page .qa-defs{{position:absolute;width:0;height:0;overflow:hidden;}}
{pills}
.qa-page .qa-head{{display:flex;flex-wrap:wrap;align-items:flex-start;justify-content:space-between;gap:10px 24px;margin-bottom:22px;}}
.qa-page h1.qa-h1{{margin:0;padding:0;font-size:2.05rem;line-height:1.15;font-weight:800;letter-spacing:-.02em;color:{palette['strong_text']};}}
.qa-page .qa-sub{{margin:6px 0 0;font-size:1.02rem;color:{soft};}}
.qa-page .qa-run{{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;padding-top:6px;font-size:.9rem;color:{palette['strong_text']};}}
.qa-page .qa-chip{{display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;font-weight:600;font-size:.88rem;
  color:var(--qa-c);background:color-mix(in srgb,var(--qa-c) {"18%" if dark else "12%"},transparent);}}
.qa-page .qa-chip::before{{content:"";width:8px;height:8px;border-radius:50%;background:var(--qa-c);box-shadow:0 0 0 3px color-mix(in srgb,var(--qa-c) 25%,transparent);}}
.qa-page .qa-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));}}
.qa-page .qa-col{{position:relative;padding:0 14px 8px;min-width:0;}}
.qa-page .qa-col+.qa-col{{border-left:1px solid {line};}}
.qa-page .qa-step{{position:relative;display:flex;align-items:center;gap:12px;height:34px;margin:0 -14px 14px;padding:0 14px;}}
.qa-page .qa-col+.qa-col .qa-step{{border-left:0;}}
.qa-page .qa-step::before,.qa-page .qa-step::after{{content:"";flex:1;height:2px;border-radius:2px;background:var(--qa-line,{line});}}
.qa-page .qa-col:first-child .qa-step::before,.qa-page .qa-col:last-child .qa-step::after{{flex:.15;opacity:0;}}
.qa-page .qa-step-name{{font-size:.86rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:{palette['strong_text']};white-space:nowrap;}}
.qa-page .qa-step .qa-mark{{position:absolute;right:-14px;top:50%;transform:translateY(-50%);z-index:1;}}
.qa-page .qa-step.qa-ok{{--qa-line:linear-gradient(90deg,{line},color-mix(in srgb,{PILL_COLORS['ok']} 75%,transparent));}}
.qa-page .qa-mark{{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,color-mix(in srgb,var(--qa-c) 55%,#fff),var(--qa-c) 70%);
  box-shadow:0 0 0 4px {palette['background']},0 4px 10px -2px color-mix(in srgb,var(--qa-c) 60%,transparent);}}
.qa-page .qa-mark svg{{width:18px;height:18px;fill:none;stroke:#fff;stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round;}}
.qa-page .qa-card{{display:flex;flex-direction:column;align-items:center;gap:6px;padding:10px 8px 18px;border-radius:16px;transition:background .18s ease,transform .18s ease;}}
.qa-page .qa-card:hover{{background:{hover};transform:translateY(-2px);}}
.qa-page .qa-icon{{width:84px;height:84px;flex:none;filter:drop-shadow(0 10px 12px {icon_shadow});}}
.qa-page .qa-body{{display:flex;flex-direction:column;align-items:center;gap:6px;width:100%;}}
.qa-page .qa-pill{{display:inline-block;max-width:100%;padding:3px 11px;border-radius:12px;font-size:.72rem;text-wrap:balance;font-weight:650;line-height:1.5;
  color:#fff;background:linear-gradient(180deg,color-mix(in srgb,var(--qa-c) 82%,#fff),var(--qa-c));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.35),0 3px 8px -3px color-mix(in srgb,var(--qa-c) 70%,transparent);text-align:center;}}
.qa-page .qa-title{{align-self:stretch;margin-top:4px;font-size:1.02rem;font-weight:750;line-height:1.25;color:{palette['strong_text']};}}
.qa-page .qa-detail{{align-self:stretch;font-size:.9rem;line-height:1.45;color:{soft};overflow-wrap:anywhere;}}
.qa-page .qa-compact{{flex-direction:row;flex-wrap:wrap;align-items:center;gap:6px 12px;padding:6px 6px 14px;}}
.qa-page .qa-compact .qa-icon{{width:62px;height:62px;}}
.qa-page .qa-compact .qa-body{{display:contents;}}
.qa-page .qa-compact .qa-pill{{flex:0 1 auto;}}
.qa-page .qa-compact .qa-title{{flex:1 0 100%;font-size:.98rem;margin-top:0;}}
.qa-page .qa-compact .qa-detail{{flex:1 0 100%;font-size:.88rem;}}
.qa-page .qa-seg{{white-space:nowrap;}}
@container (max-width:700px){{
  .qa-page .qa-grid{{grid-template-columns:repeat(2,minmax(0,1fr));row-gap:18px;}}
  .qa-page .qa-col:nth-child(3){{border-left:0;}}
  .qa-page .qa-step{{margin:0 0 14px;padding:0;}}
  .qa-page .qa-step::before{{display:none;}}
  .qa-page .qa-col:last-child .qa-step::after{{flex:1;opacity:1;}}
  .qa-page .qa-step .qa-mark{{position:static;transform:none;order:3;}}
  .qa-page .qa-step::after{{order:2;}}
}}
@container (max-width:520px){{
  .qa-page .qa-grid{{grid-template-columns:minmax(0,1fr);row-gap:8px;}}
  .qa-page .qa-col{{padding:0 0 4px 22px;border-left:2px solid {line}!important;}}
  .qa-page .qa-col:last-child{{border-left-color:transparent!important;}}
  .qa-page .qa-step{{margin-left:-22px;padding-left:0;}}
  .qa-page .qa-step .qa-mark{{order:-1;margin-left:-14px;}}
  .qa-page .qa-col:last-child .qa-step::before{{display:block;flex:none;width:14px;height:14px;margin-left:-7px;border-radius:50%;
    background:{palette['background']};border:2px solid {line};order:-1;}}
  .qa-page .qa-card{{flex-direction:row;align-items:flex-start;gap:14px;padding:6px 0 14px;}}
  .qa-page .qa-icon,.qa-page .qa-compact .qa-icon{{width:64px;height:64px;}}
  .qa-page .qa-body,.qa-page .qa-compact .qa-body{{display:flex;align-items:flex-start;}}
  .qa-page .qa-compact{{flex-wrap:nowrap;}}
  .qa-page .qa-compact .qa-title{{flex:none;}}
  .qa-page h1.qa-h1{{font-size:1.65rem;}}
}}
.st-key-{EXPANDER_KEY} details{{border:1px solid {palette['card_border']};border-radius:14px;background:{bar};
  box-shadow:0 8px 20px -16px rgba(0,0,0,.45);}}
.st-key-{EXPANDER_KEY} details summary{{padding-top:14px;padding-bottom:14px;}}
.st-key-{EXPANDER_KEY} details summary p{{font-size:1rem;font-weight:600;color:{palette['strong_text']};}}
</style>"""


def build_overview_html(evidence, mode):
    """The page header, the timeline and the four columns of cards, as one HTML block."""
    columns = build_columns(evidence)
    chip_kind = "ok" if evidence["run_ok"] else "fail"
    chip = "Carga correcta" if evidence["run_ok"] else "Carga con falla"
    run_line = (f"Ejecución {evidence['run_id']} · {evidence['run_started']} (Chile) · "
                f"{evidence['run_status']}")
    head = (f'<div class="qa-head"><div><h1 class="qa-h1">Calidad y auditoría</h1>'
            '<p class="qa-sub">Evidencia de extremo a extremo sobre los datos publicados.</p></div>'
            f'<div class="qa-run"><span>{html.escape(run_line)}</span>'
            f'<span class="qa-chip qa-{chip_kind}">{chip}</span></div></div>')
    body = []
    for position, (step, cards) in enumerate(columns):
        last = position == len(columns) - 1
        kind = summarize_step(cards)
        mark = "" if last else build_step_mark(kind, step)
        cards_html = "".join(build_card_html(*card, compact=last) for card in cards)
        body.append(f'<section class="qa-col" aria-label="{html.escape(step)}">'
                    f'<div class="qa-step{"" if last else " qa-" + kind}"><span class="qa-step-name">'
                    f'{html.escape(step)}</span>{mark}</div>{cards_html}</section>')
    return (build_overview_css(mode) + f'<div class="qa-page">{DEFS}{head}'
            f'<div class="qa-grid">{"".join(body)}</div></div>')


build_quality_overview_html = build_overview_html
# endregion
