"""«Método y calidad» (D-320): how the project was evaluated against software and data quality standards.

A self-assessment, never a certification: every number comes from a real run of a tool, recorded with its command in
docs/calidad/medicion.json by scripts/medir_calidad.py; what could not be run says «no verificado». The grades go from 0 to 4
and each one cites its evidence. Pure functions: no Streamlit; bi/dashboard.py draws the HTML. Texts are written in both
languages here, so the page never depends on the render-time translation.
"""

import html
import json
from functools import lru_cache
from pathlib import Path

from bi import charts, i18n

REPORT_FILE = Path(__file__).resolve().parent.parent / "docs" / "calidad" / "medicion.json"
NOT_VERIFIED = "no verificado"
SIDEBAR_LINE = "Evaluado según ISO/IEC 25010 · 25012"
# Result of each check: the word shown and its colour class.
# For a standard the words say how far it was applied (never «cumple la norma»); for a threshold, where the measure falls.
STATES = {
    "ok": ("Aplicado", "Applied"),
    "partial": ("Parcial", "Partial"),
    "fail": ("No aplicado", "Not applied"),
    "unknown": ("No verificado", "Not verified"),
}
THRESHOLD_STATES = {
    "ok": ("Dentro del umbral", "Within threshold"),
    "partial": ("Parcial", "Partial"),
    "fail": ("Fuera del umbral", "Outside threshold"),
    "unknown": ("No verificado", "Not verified"),
}
GRADE_SCALE = [
    ("0", "no existe o no funciona", "absent or not working"),
    ("1", "existe pero es débil o está medido en contra", "exists but weak, or measured against"),
    ("2", "existe con huecos importantes", "exists with important gaps"),
    ("3", "sólido, con huecos menores medidos", "solid, with small measured gaps"),
    ("4", "sólido y verificado de punta a punta", "solid and verified end to end"),
]


@lru_cache(maxsize=1)
def read_report():
    """The measurements of docs/calidad/medicion.json."""
    return json.loads(REPORT_FILE.read_text(encoding="utf-8"))


def t(spanish, english):
    return english if i18n.is_english() else spanish


def number(value, decimals=0):
    """A figure with the decimal mark and the thousands mark of the reader's language."""
    text = f"{value:,.{decimals}f}"
    if i18n.is_english():
        return text
    return text.replace(",", "§").replace(".", ",").replace("§", ".")


def state_chip(key, threshold=False):
    spanish, english = (THRESHOLD_STATES if threshold else STATES)[key]
    return f'<span class="qm-state qm-{key}">{html.escape(t(spanish, english))}</span>'


def grade_chip(grade):
    if grade is None:
        return f'<span class="qm-grade qm-unknown">{html.escape(t("n/v", "n/v"))}</span>'
    return f'<span class="qm-grade qm-g{grade}">{grade} / 4</span>'


def build_table(head, rows, widths=None):
    """A table whose cells are already HTML; the first column in bold."""
    columns = "".join(f"<th>{html.escape(cell)}</th>" for cell in head)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="qm-table" tabindex="0"><table><thead><tr>{columns}</tr></thead><tbody>{body}</tbody></table></div>'


def text_cell(spanish, english):
    return html.escape(t(spanish, english))


def code_cell(command):
    return f'<code class="qm-code">{html.escape(command)}</code>'


def figures(report):
    """The numbers every sentence of the page quotes, read once from the report."""
    functions, ruff, complexity = report["funciones"], report["ruff"], report["complejidad"]
    coverage, bandit, mypy = report["cobertura"], report["bandit"], report["mypy"]
    return {
        "loc": number(functions["lineas_de_codigo"]),
        "functions": number(functions["funciones"]),
        "long": functions["mas_de_50_lineas"],
        "params": functions["mas_de_5_parametros"],
        "longest": number(functions["mas_larga"][0]),
        "longest_name": functions["mas_larga"][1].split(":")[1],
        "ruff": number(ruff["errores"]),
        "ruff_long": number(ruff["por_codigo"].get("E501", 0)),
        "ruff_other": ruff["errores_sin_largo_de_linea"],
        "dupes": ruff["por_codigo"].get("F601", 0),
        "fmt": ruff["formato"]["por_reformatear"],
        "fmt_total": ruff["formato"]["por_reformatear"] + ruff["formato"]["ya_formateados"],
        "cc_over": complexity["funciones_sobre_10"],
        "cc_worst": complexity["mas_complejas"][0][0],
        "cc_worst_name": complexity["mas_complejas"][0][2],
        "cc_avg": number(complexity["promedio_radon"]["valor"], 1),
        "cc_grade": complexity["promedio_radon"]["nota"],
        "tests": number(report["pruebas"]["pruebas"]),
        "test_files": report["pruebas"]["archivos_de_prueba"],
        "cov": number(coverage["total"], 1),
        "cov_core": number(coverage["logica_critica"], 1),
        "cov_bronze": number(coverage["modulos_criticos"]["etl/bronze.py"], 1),
        "cov_ine": number(coverage["modulos_criticos"]["etl/ine.py"], 1),
        "cov_pipeline": number(coverage["modulos_criticos"]["etl/pipeline.py"], 1),
        "bandit_high": bandit["alta"],
        "bandit_medium": bandit["media"],
        "bandit_low": bandit["baja"],
        "b608": bandit["por_regla"].get("B608", 0),
        "mypy_deep": mypy["errores_revisando_cuerpos_sin_tipos"],
        "typed": mypy["con_tipo_de_retorno"],
        "mypy_functions": mypy["funciones"],
        "sql_queries": report["sql"]["bi/queries.sql"]["violaciones"],
        "sql_dbt": report["sql"]["dbt/models"]["violaciones"],
        "sql_template": report["sql"]["dbt/models"]["principales"].get("TMP", 0),
        "commits": number(report["proceso"]["commits"]),
        "conventional": report["proceso"]["conventional_commits"],
        "dead_functions": len(report["codigo_muerto"]["funciones_sin_uso"]),
        "dead_variables": report["codigo_muerto"]["variables_o_atributos_sin_uso"],
        "secret_candidates": report["secretos"]["candidatos"],
        "secret_false": report["secretos"]["falsos_positivos"],
        "secret_open": report["secretos"]["sin_clasificar"],
        "secret_files": report["secretos"]["archivos_revisados"],
        "dbt_ok": report["dbt"]["ultima_construccion"]["pruebas_ok"],
        "dbt_total": report["dbt"]["ultima_construccion"]["pruebas_total"],
        "dbt_models": sum(report["dbt"]["modelos_por_capa"].values()),
        "adr": report["adr"]["adr"],
        "decisions": report["adr"]["decisiones"],
        "date": report["generado"][:10],
        "commit": report["commit"],
    }


def build_intro(report):
    f = figures(report)
    commit, date = f["commit"], f["date"]
    scale = "".join(f"<li><b>{grade}</b> · {html.escape(t(es, en))}</li>" for grade, es, en in GRADE_SCALE)
    return (
        f'<div class="qm-text"><h3>{html.escape(t("Qué se evaluó y con qué enfoque", "What was assessed, and how"))}</h3>'
        f'<p>{html.escape(t(f"Se evaluó el repositorio completo de GreenOcean (el commit {commit}, medido el {date}): el pipeline, el panel, la base y los documentos. Es una autoevaluación hecha por el autor aplicando el marco de la ISO/IEC 25010 (calidad del producto), 25012 y 8000 (calidad de los datos) y 5055 (calidad del código), con las pruebas de la ISO/IEC 29119, la arquitectura según la ISO/IEC/IEEE 42010 y el modelo C4, las decisiones como ADR, y las listas de OWASP Top 10 y Twelve-Factor App.", f"The whole GreenOcean repository was assessed (commit {commit}, measured on {date}): the pipeline, the dashboard, the database and the documents. It is a self-assessment by the author, applying ISO/IEC 25010 (product quality), 25012 and 8000 (data quality) and 5055 (code quality), with ISO/IEC 29119 for testing, ISO/IEC/IEEE 42010 and the C4 model for architecture, ADRs for decisions, and the OWASP Top 10 and Twelve-Factor App checklists."))}</p>'
        f'<p>{html.escape(t("No es una certificación: ningún organismo la revisó ni se declara conformidad con ninguna norma. Las normas se usaron como método de revisión; cada nota cita su evidencia (un archivo, una métrica o un comando) y lo que no se pudo medir aquí se marca «no verificado».", "It is not a certification: no body reviewed it and no conformity with any standard is claimed. The standards were used as a review method; every grade cites its evidence (a file, a metric or a command), and whatever could not be measured here is marked “not verified”."))}</p>'
        f'<p>{html.escape(t("Las mediciones salen de ejecutar herramientas reales (Ruff, SQLFluff, mypy, radon, vulture, pytest con cobertura, Bandit, pip-audit y detect-secrets) con scripts/medir_calidad.py, que deja cada número con su comando en docs/calidad/medicion.json.", "The measurements come from running real tools (Ruff, SQLFluff, mypy, radon, vulture, pytest with coverage, Bandit, pip-audit and detect-secrets) with scripts/medir_calidad.py, which writes every number with its command to docs/calidad/medicion.json."))}</p>'
        f'<h4>{html.escape(t("Escala de notas", "Grading scale"))}</h4><ul class="qm-scale">{scale}</ul></div>'
    )


def build_standards(report):
    f = figures(report)
    rows = [
        (
            "ISO/IEC 25010",
            t("Calidad del producto: 8 características", "Product quality: 8 characteristics"),
            t(
                "Revisé cada característica con evidencia del repositorio y de las mediciones",
                "Reviewed each characteristic against repository evidence and the measurements",
            ),
            t("Pestaña «ISO 25010»; docs/calidad/INFORME.md", "“ISO 25010” tab; docs/calidad/INFORME.md"),
            "partial",
        ),
        (
            "ISO/IEC 25012 · ISO 8000",
            t(
                "Calidad de los datos: exactitud, completitud, consistencia, vigencia, trazabilidad",
                "Data quality: accuracy, completeness, consistency, currency, traceability",
            ),
            t(
                "Indicadores calculados desde la base y pruebas que recalculan las cifras",
                "Indicators computed from the database, and tests that recompute figures",
            ),
            t(
                f"11 indicadores en vivo; {f['dbt_ok']} de {f['dbt_total']} pruebas dbt; tests/test_data_audit.py",
                f"11 live indicators; {f['dbt_ok']} of {f['dbt_total']} dbt tests; tests/test_data_audit.py",
            ),
            "ok",
        ),
        (
            "ISO/IEC 5055",
            t(
                "Calidad del código: fiabilidad, seguridad, eficiencia, mantenibilidad",
                "Code quality: reliability, security, efficiency, maintainability",
            ),
            t(
                "Ruff, radon, vulture y Bandit sobre bi, etl y agent",
                "Ruff, radon, vulture and Bandit over bi, etl and agent",
            ),
            t(
                f"{f['ruff']} avisos de Ruff; {f['cc_over']} funciones con complejidad sobre 10; Bandit: {f['bandit_high']} altos",
                f"{f['ruff']} Ruff findings; {f['cc_over']} functions over complexity 10; Bandit: {f['bandit_high']} high",
            ),
            "partial",
        ),
        (
            "ISO/IEC 29119",
            t("Pruebas de software", "Software testing"),
            t(
                "pytest con cobertura; plan y trazabilidad de requisitos a pruebas",
                "pytest with coverage; plan and traceability from requirements to tests",
            ),
            t(
                f"{f['tests']} pruebas en {f['test_files']} archivos; cobertura {f['cov']} %; docs/PLAN_PRUEBAS.md",
                f"{f['tests']} tests in {f['test_files']} files; coverage {f['cov']} %; docs/PLAN_PRUEBAS.md",
            ),
            "ok",
        ),
        (
            "ISO/IEC/IEEE 42010 · C4",
            t("Descripción de la arquitectura", "Architecture description"),
            t(
                "Documento de arquitectura por vistas: contexto, contenedores, componentes",
                "Architecture document by views: context, containers, components",
            ),
            t("docs/SAD.md y los diagramas del panel", "docs/SAD.md and the dashboard's diagrams"),
            "ok",
        ),
        (
            "ADR",
            t("Registro de decisiones de arquitectura", "Architecture decision records"),
            t(
                "Cada decisión importante con contexto y consecuencias",
                "Each major decision with context and consequences",
            ),
            t(
                f"{f['adr']} ADR y {f['decisions']} decisiones en docs/DECISIONES.md",
                f"{f['adr']} ADRs and {f['decisions']} decisions in docs/DECISIONES.md",
            ),
            "ok",
        ),
        (
            "OWASP Top 10",
            t("Riesgos de seguridad de aplicaciones", "Application security risks"),
            t(
                "Revisión de cada categoría contra el panel y el pipeline; plan de ataques repetidos en cada cambio",
                "Review of each category against the dashboard and the pipeline; attack plan repeated on every change",
            ),
            t(
                f"Bandit {f['bandit_high']} altos; {f['b608']} avisos de SQL armado revisados; sin prueba de penetración",
                f"Bandit {f['bandit_high']} high; {f['b608']} built-SQL findings reviewed; no penetration test",
            ),
            "partial",
        ),
        (
            "Twelve-Factor App",
            t("Buenas prácticas de aplicaciones desplegables", "Practices for deployable applications"),
            t(
                "Revisión de los 12 factores: 7 aplicados, 4 parciales y 1 que no aplica",
                "Review of the 12 factors: 7 applied, 4 partial and 1 not applicable",
            ),
            t("Informe, sección Twelve-Factor", "Report, Twelve-Factor section"),
            "partial",
        ),
        (
            "CI/CD · DORA",
            t("Integración continua y métricas de entrega", "Continuous integration and delivery metrics"),
            t("Revisé los workflows y las cargas registradas", "Reviewed the workflows and the recorded loads"),
            t(
                "El CI corre pytest y dbt parse; sin lint ni auditoría; DORA: sólo la frecuencia (semanal) se pudo medir",
                "CI runs pytest and dbt parse; no lint or audit; DORA: only the frequency (weekly) could be measured",
            ),
            "partial",
        ),
    ]
    head = [
        t("Estándar", "Standard"),
        t("Qué cubre", "What it covers"),
        t("Cómo lo apliqué", "How I applied it"),
        t("Evidencia", "Evidence"),
        t("Resultado", "Result"),
    ]
    return build_table(
        head,
        [
            (
                f"<b>{html.escape(name)}</b>",
                html.escape(covers),
                html.escape(how),
                html.escape(evidence),
                state_chip(state),
            )
            for name, covers, how, evidence, state in rows
        ],
    )


def iso_characteristics(report):
    """(characteristic, grade, evidence, what is missing): the eight of ISO/IEC 25010, each grade backed by a measurement."""
    f = figures(report)
    return [
        (
            t("Adecuación funcional", "Functional suitability"),
            3,
            t(
                f"{f['tests']} pruebas; cada cifra del panel se recalcula en tests/test_data_audit.py; requisitos trazados a pruebas (tests/test_prd_traceability.py)",
                f"{f['tests']} tests; every figure of the dashboard is recomputed in tests/test_data_audit.py; requirements traced to tests (tests/test_prd_traceability.py)",
            ),
            t(
                "ODEPA publica 9 de las 16 regiones; los márgenes sólo existen para frutas y verduras",
                "ODEPA publishes 9 of 16 regions; margins exist only for fruit and vegetables",
            ),
        ),
        (
            t("Eficiencia de desempeño", "Performance efficiency"),
            None,
            t(
                "Sin pruebas de carga ni de tiempos: sólo hay un incidente conocido (DuckDB 2 volvió una consulta de 0,1 s a más de 60 s, D-227) y la versión quedó acotada",
                "No load or timing tests: only a known incident (DuckDB 2 turned a 0.1 s query into 60 s+, D-227), and the version was capped",
            ),
            t(
                "Medir tiempos de carga de cada página y de cada consulta, y fijarlos como umbral",
                "Measure the load time of each page and query, and set them as a threshold",
            ),
        ),
        (
            t("Compatibilidad", "Compatibility"),
            2,
            t(
                "El panel corre en Python 3.14 y el pipeline con dbt, sólo en 3.11 o 3.12; español e inglés; sólo se midió el diseño en Chromium",
                "The dashboard runs on Python 3.14 and the pipeline with dbt only on 3.11 or 3.12; Spanish and English; layout measured only in Chromium",
            ),
            t(
                "Probar en Firefox y Safari y en una matriz de versiones de Python en el CI",
                "Test on Firefox and Safari and on a Python version matrix in CI",
            ),
        ),
        (
            t("Usabilidad", "Interaction capability"),
            2,
            t(
                "Cada página se mide a 1440 × 790 y 1920 × 1000 con Playwright (tests/medicion); español e inglés auditados; no hay auditoría de accesibilidad (WCAG) ni pruebas con personas",
                "Each page is measured at 1440 × 790 and 1920 × 1000 with Playwright (tests/medicion); Spanish and English audited; no accessibility (WCAG) audit and no user testing",
            ),
            t(
                "Auditar contraste y teclado, y probar con personas reales",
                "Audit contrast and keyboard use, and test with real people",
            ),
        ),
        (
            t("Fiabilidad", "Reliability"),
            3,
            t(
                f"Una puerta de pruebas impide publicar si algo falla (tests/test_pipeline_gate.py); {f['dbt_ok']} de {f['dbt_total']} pruebas dbt; la carga del 25-10 falló por una prueba demasiado estricta (D-299) y se corrigió",
                f"A test gate stops publication if anything fails (tests/test_pipeline_gate.py); {f['dbt_ok']} of {f['dbt_total']} dbt tests; the 25-10 load failed on an over-strict test (D-299) and was fixed",
            ),
            t(
                f"Tres módulos de ingesta con poca cobertura (bronce {f['cov_bronze']} %, INE {f['cov_ine']} %, pipeline {f['cov_pipeline']} %)",
                f"Three ingestion modules with low coverage (bronze {f['cov_bronze']} %, INE {f['cov_ine']} %, pipeline {f['cov_pipeline']} %)",
            ),
        ),
        (
            t("Seguridad", "Security"),
            3,
            t(
                f"Sin secretos en el árbol ni en el historial ({f['secret_candidates']} candidatos de detect-secrets, {f['secret_false']} falsos positivos revisados); Bandit {f['bandit_high']} altos; pip-audit sin hallazgos en requirements.txt; panel de sólo lectura; hash de la base publicada",
                f"No secrets in the tree or in the history ({f['secret_candidates']} detect-secrets candidates, {f['secret_false']} reviewed false positives); Bandit {f['bandit_high']} high; pip-audit clean on requirements.txt; read-only dashboard; hash of the published database",
            ),
            t(
                "Sin prueba de penetración; dependencias del pipeline sin auditar; gitleaks no instalado",
                "No penetration test; pipeline dependencies not audited; gitleaks not installed",
            ),
        ),
        (
            t("Mantenibilidad", "Maintainability"),
            2,
            t(
                f"Complejidad media {f['cc_grade']} ({f['cc_avg']}) y {f['tests']} pruebas, pero bi/dashboard.py concentra miles de líneas, {f['long']} funciones pasan de 50 líneas (la mayor, {f['longest_name']}, con {f['longest']}), {f['fmt']} de {f['fmt_total']} archivos sin formatear y {f['ruff_long']} líneas largas",
                f"Average complexity {f['cc_grade']} ({f['cc_avg']}) and {f['tests']} tests, but bi/dashboard.py concentrates thousands of lines, {f['long']} functions exceed 50 lines (the longest, {f['longest_name']}, has {f['longest']}), {f['fmt']} of {f['fmt_total']} files unformatted and {f['ruff_long']} long lines",
            ),
            t(
                "Partir el panel por páginas, sacar el CSS a archivos y aplicar un formateador",
                "Split the dashboard by page, move CSS to files and apply a formatter",
            ),
        ),
        (
            t("Portabilidad", "Portability"),
            3,
            t(
                "Corre en local, en Streamlit Cloud y en GitHub Actions; hay un devcontainer; la base es un archivo; un script de macOS queda en scripts/",
                "Runs locally, on Streamlit Cloud and on GitHub Actions; there is a devcontainer; the database is a file; one macOS script sits in scripts/",
            ),
            t(
                "Dependencias sin versión fija y dos versiones de Python según el uso",
                "Dependencies without pinned versions and two Python versions depending on use",
            ),
        ),
    ]


def build_iso(report):
    rows = iso_characteristics(report)
    graded = [grade for _, grade, _, _ in rows if grade is not None]
    average = sum(graded) / len(graded)
    head = [
        t("Característica", "Characteristic"),
        t("Nota", "Grade"),
        t("Evidencia", "Evidence"),
        t("Qué falta", "What is missing"),
    ]
    table = build_table(
        head,
        [
            (f"<b>{html.escape(name)}</b>", grade_chip(grade), html.escape(evidence), html.escape(missing))
            for name, grade, evidence, missing in rows
        ],
    )
    summary = f'<p class="qm-note">{html.escape(t(f"Promedio de las {len(graded)} características verificadas: {number(average, 1)} de 4. La eficiencia de desempeño no se calificó porque no hay medición.", f"Average of the {len(graded)} verified characteristics: {number(average, 1)} out of 4. Performance efficiency was not graded because nothing was measured."))}</p>'
    return summary + table


def build_data_quality(report, indicators, counts):
    """ISO/IEC 25012: the live indicators of the loaded database, with the declared limits."""
    f = figures(report)
    status_key = {"ok": "ok", "warn": "partial", "fail": "fail", "info": "unknown"}
    head = [
        t("Dimensión", "Dimension"),
        t("Indicador", "Indicator"),
        t("Valor", "Value"),
        t("Referencia", "Reference"),
        t("Estado", "Status"),
    ]
    translate = i18n.tr
    rows = [
        (
            f"<b>{html.escape(translate(dimension.capitalize()))}</b>",
            html.escape(translate(name)),
            html.escape(translate(value)),
            html.escape(translate(reference)),
            state_chip(status_key.get(status, "unknown"), threshold=True),
        )
        for dimension, name, value, reference, status, _ in indicators
    ]
    limits = [
        t(
            f"Cobertura: {number(counts['prices'])} precios semanales, {counts['weeks']} semanas, {counts['regions']} regiones y {counts['channels']} canales. ODEPA publica 9 de las 16 regiones, así que los promedios nacionales cubren esas 9.",
            f"Coverage: {number(counts['prices'])} weekly prices, {counts['weeks']} weeks, {counts['regions']} regions and {counts['channels']} channels. ODEPA publishes 9 of the 16 regions, so national averages cover those 9.",
        ),
        t(
            "Los precios son nominales; el precio real descuenta la inflación general de alimentos del INE, no la de cada producto.",
            "Prices are nominal; the real price discounts the INE's general food inflation, not each product's own.",
        ),
        t(
            "El margen entre mayorista y consumidor existe sólo para frutas y verduras; el resto de las familias tiene sólo precio al consumidor.",
            "The wholesale-to-consumer margin exists only for fruit and vegetables; other families have consumer price only.",
        ),
        t(
            "Una carga que falla no cambia la base: el panel sigue mostrando la última carga válida.",
            "A failed load does not change the database: the dashboard keeps showing the last valid load.",
        ),
    ]
    notes = "".join(f"<li>{html.escape(item)}</li>" for item in limits)
    grades = [
        (
            t("Exactitud", "Accuracy"),
            3,
            t(
                "Las cifras del panel se recalculan desde la fuente en las pruebas",
                "The dashboard's figures are recomputed from the source in tests",
            ),
        ),
        (
            t("Completitud", "Completeness"),
            2,
            t(
                "Semanas sin hueco, pero 9 de 16 regiones y márgenes sólo en dos familias",
                "No gaps in weeks, but 9 of 16 regions and margins in only two families",
            ),
        ),
        (
            t("Consistencia", "Consistency"),
            3,
            t(
                f"{f['dbt_ok']} de {f['dbt_total']} pruebas dbt y paridad entre SQLite y DuckDB",
                f"{f['dbt_ok']} of {f['dbt_total']} dbt tests and SQLite–DuckDB parity",
            ),
        ),
        (
            t("Vigencia", "Currency"),
            3,
            t(
                "Carga semanal; un fallo se avisa a quien opera y el panel conserva la última carga válida",
                "Weekly load; a failure alerts the operator and the dashboard keeps the last valid load",
            ),
        ),
        (
            t("Trazabilidad", "Traceability"),
            3,
            t(
                "Cada precio conserva su archivo y su huella de origen; el panel enlaza cada cifra a su fuente",
                "Every price keeps its source file and hash; the dashboard links each figure to its source",
            ),
        ),
    ]
    grade_rows = [(f"<b>{html.escape(name)}</b>", grade_chip(grade), html.escape(why)) for name, grade, why in grades]
    return (
        f'<h4>{html.escape(t("Indicadores en vivo de la carga actual", "Live indicators of the current load"))}</h4>'
        + build_table(head, rows)
        + f'<h4>{html.escape(t("Nota por dimensión (ISO/IEC 25012)", "Grade by dimension (ISO/IEC 25012)"))}</h4>'
        + build_table([t("Dimensión", "Dimension"), t("Nota", "Grade"), t("Evidencia", "Evidence")], grade_rows)
        + f'<h4>{html.escape(t("Cobertura y límites declarados", "Coverage and declared limits"))}</h4><ul class="qm-list">{notes}</ul>'
    )


def code_practices(report):
    """The ten practices: tool, threshold, measured result, state and the ISO characteristic it backs."""
    f = figures(report)
    return [
        (
            "1 · " + t("Estilo y formato", "Style and format"),
            "Ruff (lint + format)",
            t("0 errores", "0 errors"),
            t(
                f"{f['ruff']} avisos ({f['ruff_long']} de largo de línea; {f['ruff_other']} otros, entre ellos {f['dupes']} claves repetidas en diccionarios); {f['fmt']} de {f['fmt_total']} archivos sin formatear",
                f"{f['ruff']} findings ({f['ruff_long']} line length; {f['ruff_other']} others, including {f['dupes']} repeated dictionary keys); {f['fmt']} of {f['fmt_total']} files unformatted",
            ),
            "fail",
            "25010/5055 · " + t("mantenibilidad", "maintainability"),
        ),
        (
            "2 · SQL",
            "SQLFluff (DuckDB)",
            t("0 errores", "0 errors"),
            t(
                f"{f['sql_queries']} avisos en bi/queries.sql; {f['sql_dbt']} en los modelos de dbt, de los cuales {f['sql_template']} son errores de plantilla que impiden analizar el archivo",
                f"{f['sql_queries']} findings in bi/queries.sql; {f['sql_dbt']} in the dbt models, of which {f['sql_template']} are template errors that prevent parsing the file",
            ),
            "fail",
            "25010 · " + t("mantenibilidad", "maintainability"),
        ),
        (
            "3 · " + t("Tipado", "Typing"),
            "mypy",
            t("módulos principales sin errores", "main modules without errors"),
            t(
                f"0 errores, pero sólo porque el código no tiene anotaciones ({f['typed']} de {f['mypy_functions']} funciones con tipo de retorno); al revisar también los cuerpos sin tipos, {f['mypy_deep']} errores",
                f"0 errors, but only because the code has no annotations ({f['typed']} of {f['mypy_functions']} functions with a return type); checking untyped bodies as well, {f['mypy_deep']} errors",
            ),
            "partial",
            "5055 · " + t("fiabilidad", "reliability"),
        ),
        (
            "4 · " + t("Complejidad", "Complexity"),
            "Ruff C901 · radon",
            t("≤ 10 por función; ≤ 50 líneas", "≤ 10 per function; ≤ 50 lines"),
            t(
                f"{f['cc_over']} funciones sobre 10 (la peor, {f['cc_worst_name']}, con {f['cc_worst']}); {f['long']} funciones sobre 50 líneas (la mayor, {f['longest_name']}, con {f['longest']}: CSS en una cadena); promedio {f['cc_grade']} ({f['cc_avg']})",
                f"{f['cc_over']} functions over 10 (the worst, {f['cc_worst_name']}, at {f['cc_worst']}); {f['long']} functions over 50 lines (the longest, {f['longest_name']}, at {f['longest']}: CSS in a string); average {f['cc_grade']} ({f['cc_avg']})",
            ),
            "partial",
            "25010/5055 · " + t("mantenibilidad", "maintainability"),
        ),
        (
            "5 · " + t("Duplicación y código muerto", "Duplication and dead code"),
            "vulture",
            t("sin código muerto", "no dead code"),
            t(
                f"{f['dead_functions']} funciones sin uso (puntos de entrada de pruebas y un auxiliar de diagramas, a propósito) y {f['dead_variables']} variables o atributos que vulture marca con baja confianza, sin revisar uno por uno; la duplicación (DRY) no se midió con herramienta",
                f"{f['dead_functions']} unused functions (test entry points and a diagram helper, on purpose) and {f['dead_variables']} variables or attributes vulture flags at low confidence, not reviewed one by one; duplication (DRY) was not measured with a tool",
            ),
            "partial",
            "5055 · " + t("mantenibilidad", "maintainability"),
        ),
        (
            "6 · " + t("Pruebas y cobertura", "Tests and coverage"),
            "pytest + coverage",
            t("≥ 70 % en lógica de negocio y transformaciones", "≥ 70 % in business logic and transformations"),
            t(
                f"{f['tests']} pruebas; cobertura total {f['cov']} %; lógica crítica {f['cov_core']} %; bajo el umbral: bronce {f['cov_bronze']} %, INE {f['cov_ine']} % y pipeline {f['cov_pipeline']} %",
                f"{f['tests']} tests; total coverage {f['cov']} %; critical logic {f['cov_core']} %; below the threshold: bronze {f['cov_bronze']} %, INE {f['cov_ine']} % and pipeline {f['cov_pipeline']} %",
            ),
            "partial",
            "29119 · " + t("pruebas", "testing"),
        ),
        (
            "7 · " + t("Seguridad", "Security"),
            "Bandit · pip-audit · detect-secrets",
            t("0 hallazgos altos", "0 high findings"),
            t(
                f"Bandit: {f['bandit_high']} altos, {f['bandit_medium']} medios ({f['b608']} de SQL armado, revisados uno por uno: identificadores de constantes o enteros, valores con parámetros; uno ejecuta el SQL del visitante por diseño, en una conexión de sólo lectura) y {f['bandit_low']} bajos; pip-audit: 0 en requirements.txt y no verificado en el pipeline; secretos: {f['secret_candidates']} candidatos, {f['secret_false']} falsos positivos revisados y {f['secret_open']} sin clasificar",
                f"Bandit: {f['bandit_high']} high, {f['bandit_medium']} medium ({f['b608']} built SQL, reviewed one by one: identifiers from constants or integers, values as parameters; one runs the visitor's own SQL by design, on a read-only connection) and {f['bandit_low']} low; pip-audit: 0 on requirements.txt and not verified for the pipeline; secrets: {f['secret_candidates']} candidates, {f['secret_false']} reviewed false positives and {f['secret_open']} unclassified",
            ),
            "ok",
            "OWASP / 27034 · " + t("seguridad", "security"),
        ),
        (
            "8 · " + t("Datos y dbt", "Data and dbt"),
            "dbt",
            t("pruebas pasando; staging, intermediate y marts", "tests passing; staging, intermediate and marts"),
            t(
                f"{f['dbt_ok']} de {f['dbt_total']} pruebas superadas en la última carga; {f['dbt_models']} modelos en tres capas. Esta revisión no ejecutó dbt: lee el registro de la última carga",
                f"{f['dbt_ok']} of {f['dbt_total']} tests passed in the last load; {f['dbt_models']} models in three layers. This review did not run dbt: it reads the record of the last load",
            ),
            "ok",
            "25012 · " + t("datos", "data"),
        ),
        (
            "9 · " + t("Principios de diseño", "Design principles"),
            t("Lista de control", "Checklist"),
            t(
                "nombres claros, una responsabilidad, pocos parámetros",
                "clear names, one responsibility, few parameters",
            ),
            t(
                f"Nombres con prefijos que dicen lo que hacen (build_, read_, show_); pero bi/dashboard.py mezcla páginas, estilos y consultas, {f['params']} funciones tienen más de 5 parámetros (build_lineage_node, 12) y esta revisión retiró unas 4.000 líneas de vistas sin uso (D-318), señal de deuda YAGNI",
                f"Names with prefixes that say what they do (build_, read_, show_); but bi/dashboard.py mixes pages, styles and queries, {f['params']} functions take more than 5 parameters (build_lineage_node, 12) and this review removed about 4,000 lines of unused views (D-318), a sign of YAGNI debt",
            ),
            "partial",
            "25010 · " + t("mantenibilidad", "maintainability"),
        ),
        (
            "10 · " + t("Proceso", "Process"),
            "Conventional Commits · pre-commit · CI",
            t(
                "commits convencionales; pre-commit; CI con los puntos 1 a 8",
                "conventional commits; pre-commit; CI running points 1 to 8",
            ),
            t(
                f"{f['conventional']} de {f['commits']} commits siguen Conventional Commits (usan el formato «D-nnn: …»); no hay .pre-commit-config.yaml; el CI corre pytest y dbt parse, sin lint, tipos ni auditoría",
                f"{f['conventional']} of {f['commits']} commits follow Conventional Commits (they use the “D-nnn: …” format); there is no .pre-commit-config.yaml; CI runs pytest and dbt parse, with no lint, types or audit",
            ),
            "fail",
            t("DORA · mantenibilidad", "DORA · maintainability"),
        ),
    ]


def build_code(report):
    head = [
        t("Práctica", "Practice"),
        t("Herramienta", "Tool"),
        t("Umbral", "Threshold"),
        t("Medido", "Measured"),
        t("Estado", "State"),
        t("Respalda a", "Backs"),
    ]
    return build_table(
        head,
        [
            (
                f"<b>{html.escape(name)}</b>",
                html.escape(tool),
                html.escape(threshold),
                html.escape(result),
                state_chip(state, threshold=True),
                html.escape(backs),
            )
            for name, tool, threshold, result, state, backs in code_practices(report)
        ],
    )


def build_verify(report):
    commands = [
        (
            t(
                "Medirlo todo (escribe docs/calidad/medicion.json)",
                "Measure everything (writes docs/calidad/medicion.json)",
            ),
            "python scripts/medir_calidad.py --tools /ruta/al/entorno/bin",
        ),
        (
            "Ruff · " + t("lint", "lint"),
            f"ruff check bi etl agent tests --select E,F,W --line-length {report['limites']['largo_de_linea']}",
        ),
        (
            "Ruff · " + t("formato", "format"),
            f"ruff format --check bi etl agent tests --line-length {report['limites']['largo_de_linea']}",
        ),
        (
            t("Complejidad", "Complexity"),
            f"ruff check bi etl agent --select C901 --config lint.mccabe.max-complexity={report['limites']['complejidad']}",
        ),
        ("SQLFluff", "sqlfluff lint bi/queries.sql --dialect duckdb"),
        ("mypy", report["mypy"]["orden"].replace("mypy ", "mypy ", 1)),
        (t("Código muerto", "Dead code"), report["codigo_muerto"]["orden"]),
        (t("Pruebas y cobertura", "Tests and coverage"), report["cobertura"]["orden"]),
        ("Bandit", report["bandit"]["orden"]),
        ("pip-audit", "pip-audit -r requirements.txt"),
        (t("Secretos", "Secrets"), report["secretos"]["orden"]),
        ("dbt", "dbt parse --project-dir dbt --profiles-dir dbt"),
    ]
    note = t(
        "Las herramientas de calidad no son dependencias del proyecto: viven en un entorno aparte.",
        "The quality tools are not project dependencies: they live in a separate environment.",
    )
    rows = [(f"<b>{html.escape(label)}</b>", code_cell(command)) for label, command in commands]
    return (
        build_table([t("Qué", "What"), t("Comando", "Command")], rows) + f'<p class="qm-note">{html.escape(note)}</p>'
    )


def build_limits(report):
    f = figures(report)
    limits = [
        t(
            "Es una autoevaluación del propio autor, no una auditoría externa ni una certificación; las notas son un juicio apoyado en evidencia y pueden discutirse.",
            "It is a self-assessment by the author, not an external audit or a certification; the grades are a judgement backed by evidence and can be disputed.",
        ),
        t(
            "No se midió el rendimiento, la accesibilidad (WCAG), la duplicación de código con una herramienta, la tasa de fallos de cambios ni el tiempo de recuperación: figuran como «no verificado».",
            "Performance, accessibility (WCAG), code duplication with a tool, change failure rate and time to restore were not measured: they appear as “not verified”.",
        ),
        t(
            "Las dependencias del pipeline (dbt) no se pudieron auditar con pip-audit porque no se resuelven con el Python de este equipo; gitleaks no está instalado y se usó detect-secrets más una búsqueda de patrones en el historial.",
            "The pipeline dependencies (dbt) could not be audited with pip-audit because they do not resolve on this machine's Python; gitleaks is not installed, so detect-secrets plus a pattern search over the history was used.",
        ),
        t(
            "Cinco pruebas que consultan enlaces públicos del repositorio dependen de que exista en GitHub con el nombre nuevo; no entran en la cobertura ni en el conteo de pruebas aprobadas.",
            "Five tests that query the repository's public links depend on it existing on GitHub under the new name; they are outside the coverage and the passing count.",
        ),
        t(
            "dbt no se ejecutó en esta revisión: los resultados de sus pruebas se leen del registro de la última carga.",
            "dbt was not run in this review: its test results are read from the record of the last load.",
        ),
    ]
    steps = [
        (
            t("Alta", "High"),
            t(
                "Correr en el CI Ruff, Bandit, pip-audit y detect-secrets, y fallar con hallazgos altos",
                "Run Ruff, Bandit, pip-audit and detect-secrets in CI, and fail on high findings",
            ),
        ),
        (
            t("Alta", "High"),
            t(
                f"Partir bi/dashboard.py por páginas y sacar el CSS de {f['longest_name']} a archivos",
                f"Split bi/dashboard.py by page and move the CSS of {f['longest_name']} to files",
            ),
        ),
        (
            t("Alta", "High"),
            t(
                "Cubrir la ingesta con pruebas (bronce, INE y pipeline están bajo el 70 %)",
                "Cover ingestion with tests (bronze, INE and pipeline are under 70 %)",
            ),
        ),
        (
            t("Media", "Medium"),
            t(
                f"Revisar las {f['dupes']} claves repetidas en diccionarios (en los de traducción, bi/i18n_en.py): una repetida con otro valor oculta una entrada",
                f"Review the {f['dupes']} repeated dictionary keys (in the translation dictionaries, bi/i18n_en.py): a repeat with another value hides an entry",
            ),
        ),
        (
            t("Media", "Medium"),
            t(
                "Aplicar un formateador a todo el repositorio y fijar el largo de línea",
                "Apply a formatter to the whole repository and fix the line length",
            ),
        ),
        (
            t("Media", "Medium"),
            t(
                "Anotar tipos en los módulos críticos y activar mypy en el CI",
                "Annotate types in the critical modules and turn on mypy in CI",
            ),
        ),
        (
            t("Media", "Medium"),
            t("Configurar pre-commit y Conventional Commits", "Set up pre-commit and Conventional Commits"),
        ),
        (
            t("Media", "Medium"),
            t(
                f"Bajar a 10 o menos la complejidad de las {f['cc_over']} funciones que la superan",
                f"Bring the {f['cc_over']} over-complex functions down to 10 or less",
            ),
        ),
        (
            t("Baja", "Low"),
            t(
                "SQLFluff con la plantilla de dbt para analizar los modelos",
                "SQLFluff with the dbt templater to parse the models",
            ),
        ),
        (
            t("Baja", "Low"),
            t(
                "Medir tiempos de las páginas y fijarlos como umbral; auditar la accesibilidad",
                "Measure page times and set them as a threshold; audit accessibility",
            ),
        ),
    ]
    limit_items = "".join(f"<li>{html.escape(item)}</li>" for item in limits)
    return (
        f'<h4>{html.escape(t("Limitaciones", "Limitations"))}</h4><ul class="qm-list">{limit_items}</ul>'
        f'<h4>{html.escape(t("Próximos pasos, por prioridad", "Next steps, by priority"))}</h4>'
        + build_table(
            [t("Prioridad", "Priority"), t("Mejora", "Improvement")],
            [(f"<b>{html.escape(p)}</b>", html.escape(text)) for p, text in steps],
        )
        + f'<p class="qm-note">{html.escape(t("Ninguna de estas mejoras se aplicó: esperan la aprobación del autor.", "None of these improvements has been applied: they await the author’s approval."))}</p>'
    )


def build_css(palette):
    ink, text, muted, border, accent, card = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card_border"],
        palette["accent"],
        palette["card"],
    )
    return f"""<style>
.qm-text, .qm-table, .qm-list, .qm-note {{ color:{text}; }}
.qm-pane h3, .qm-pane h4 {{ margin:0 0 6px !important; padding:0 !important; color:{ink}; }}
.qm-pane h3 {{ font-size:18px !important; }}
.qm-pane h4 {{ font-size:13px !important; text-transform:uppercase; letter-spacing:.06em; color:{muted}; margin-top:14px !important; }}
.qm-text p {{ margin:0 0 10px !important; font-size:13.5px; line-height:1.55; }}
.qm-scale {{ margin:4px 0 0; padding-left:18px; font-size:13px; line-height:1.6; }}
.qm-table {{ overflow:auto; max-height:calc(100vh - 330px); border:1px solid {border}; border-radius:10px; margin:6px 0 12px; }}
.qm-table table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:12.5px; margin:0; }}
.qm-table thead th {{ position:sticky; top:0; z-index:1; background:{accent} !important; color:{charts.readable_on(accent)} !important; font-size:11px; font-weight:600;
  text-transform:uppercase; letter-spacing:.05em; padding:7px 10px !important; text-align:left; border:0 !important; }}
.qm-table td {{ padding:7px 10px !important; vertical-align:top; line-height:1.45; border:0 !important; border-bottom:1px solid {border} !important;
  background:transparent !important; color:{text}; }}
.qm-table td:first-child {{ color:{ink}; white-space:nowrap; }}
.qm-table tbody tr:nth-child(even) td {{ background:color-mix(in srgb, {accent} 5%, transparent) !important; }}
.qm-code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; color:{ink}; background:transparent; padding:0; word-break:break-all; }}
.qm-state, .qm-grade {{ display:inline-block; padding:1px 9px; border-radius:999px; font-size:11.5px; font-weight:600; white-space:nowrap; border:1px solid currentColor; }}
.qm-ok {{ color:#199e70; }} .qm-partial {{ color:#d4a017; }} .qm-fail {{ color:{palette["rise"]}; }} .qm-unknown {{ color:{muted}; }}
.qm-g0, .qm-g1 {{ color:{palette["rise"]}; }} .qm-g2 {{ color:#d4a017; }} .qm-g3, .qm-g4 {{ color:#199e70; }}
.qm-list {{ margin:4px 0 10px; padding-left:18px; font-size:13px; line-height:1.55; }}
.qm-note {{ font-size:12.5px; margin:4px 0 8px; color:{muted}; }}
.qm-pane {{ max-height:calc(100vh - 250px); overflow:auto; padding-right:6px; }}
.qm-card {{ background:{card}; }}
</style>"""
