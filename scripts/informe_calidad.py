"""Writes docs/calidad/INFORME.md from the files of docs/calidad and adds the measurement to its history (D-323).

    python scripts/informe_calidad.py [--anterior medicion_anterior.json] [--cuerpo cuerpo.md]

Every number comes from the measurement (medicion.json), the baseline (linea_base.json) and the goals (metas.json); the
judgements from the author's review: the ISO grades in rubrica.json, the OWASP and Twelve-Factor review below. With
--cuerpo it also writes the comparison with the previous measurement, the body of the pull request «Actualizar medición
de calidad». It never changes the code.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import quality_method  # noqa: E402
from bi import quality_metrics as q  # noqa: E402

REPORT_PATH = q.FOLDER / "INFORME.md"
STANDARDS = (
    "la ISO/IEC 25010 (calidad del producto), 25012 e ISO 8000 (calidad de los datos), ISO/IEC 5055 (calidad del "
    "código), ISO/IEC 29119 (pruebas), WCAG 2.1 AA (accesibilidad), ISO/IEC/IEEE 42010 y el modelo C4 (arquitectura), los "
    "ADR, OWASP Top 10, Twelve-Factor App y las métricas DORA"
)
# The author's review by category (D-320), once per version; the measured figures are filled in from the measurement.
OWASP = [
    (
        "A01 Control de acceso",
        "El panel solo lee; ejecutar el pipeline pide la clave del autor",
        "tests/test_security.py",
    ),
    (
        "A02 Fallas criptográficas",
        "No se guarda información personal; la base publicada lleva huella SHA-256 que se comprueba al descargar",
        "bi/served_database.py",
    ),
    (
        "A03 Inyección",
        "{b608} avisos B608 de Bandit revisados uno por uno: identificadores de constantes o enteros, valores como "
        "parámetros; la consola SQL ejecuta el SQL del visitante por diseño, solo SELECT y en una conexión de solo lectura",
        "bi/sql_explorer.py",
    ),
    ("A04 Diseño inseguro", "Las decisiones de seguridad están en ADR y en el plan de pruebas", "docs/ADR.md"),
    ("A05 Configuración", "Secretos solo en st.secrets; workflows con los permisos mínimos", "tests/test_security.py"),
    ("A06 Componentes vulnerables", "pip-audit: {audit}", "docs/calidad/medicion.json"),
    ("A07 Autenticación", "Una sola clave para la acción de operar; sin cuentas de usuario", "bi/control.py"),
    (
        "A08 Integridad",
        "Huella de la base publicada; el pipeline no publica si una prueba falla",
        "tests/test_pipeline_gate.py",
    ),
    ("A09 Registro y monitoreo", "Historial de cargas y aviso de carga fallida para quien opera", "bi/control.py"),
    ("A10 SSRF", "No se hacen solicitudes a direcciones que el visitante escriba", "revisión de lectura"),
]
TWELVE_FACTORS = [
    ("I Código base", "Aplicado: un repositorio"),
    (
        "II Dependencias",
        "Parcial: declaradas en requirements*.txt, con versión máxima donde rompió (duckdb<2) pero no fijas",
    ),
    ("III Configuración", "Aplicado: secretos en st.secrets y variables de entorno"),
    ("IV Servicios de apoyo", "Aplicado: la base es un archivo publicado en un release"),
    ("V Construir, publicar, ejecutar", "Aplicado: GitHub Actions y release «base-actual»"),
    ("VI Procesos", "Aplicado: el panel no guarda estado en disco"),
    ("VII Enlace de puertos", "Aplicado: Streamlit"),
    ("VIII Concurrencia", "No aplica"),
    ("IX Desechabilidad", "Parcial: arranque rápido, pero descarga la base al iniciar"),
    ("X Paridad desarrollo y producción", "Parcial: panel en Python 3.14 y pipeline en 3.11 o 3.12"),
    ("XI Registros", "Parcial: el agente escribe archivos de registro, no un flujo"),
    ("XII Procesos de administración", "Aplicado: etl/pipeline.py --local"),
]


def es(value, decimals=0):
    return q.number(value, decimals)


def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def table(head, rows):
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(cell(item) for item in row) + " |" for row in rows]
    return "\n".join(lines)


def state(ok):
    return "cumple" if ok else "no medido" if ok is None else "**no cumple**"


def goal(row):
    return q.goal_text(row["goal"]) + (f" {row['unit']}" if row["unit"] else "")


def grade(value):
    return "no verificado" if value is None else f"{value} / 4"


def lowest_module(coverage):
    modules = coverage.get("modulos") or {}
    return min(modules.items(), key=lambda pair: pair[1]) if modules else ("—", None)


def audit_text(report):
    files = report.get("pip_audit", {}).get("archivos", {})
    parts = []
    for name, item in files.items():
        found = item.get("vulnerabilidades")
        parts.append(
            f"{es(found)} en {name}" if found is not None else f"no verificado en {name} ({item.get('motivo')})"
        )
    return "; ".join(parts) or "no verificado"


def practices(report, rows):
    ok = {row["key"]: row["ok"] for row in rows}
    ruff, mypy, cx, fn = report["ruff"], report["mypy"], report["complejidad"], report["funciones"]
    coverage, bandit, secrets = report["cobertura"], report["bandit"], report["secretos"]
    sql, dbt, process, dead = (
        report["sql"],
        report["dbt"].get("ultima_construccion", {}),
        report["proceso"],
        report["codigo_muerto"],
    )
    name, low = lowest_module(coverage)
    worst = cx["mas_complejas"][0] if cx.get("mas_complejas") else (None, "—", "—")

    def both(*keys):
        return state(all(ok[key] for key in keys)) if all(ok[key] is not None for key in keys) else "no medido"

    formatted = ruff["formato"]
    return [
        (
            "1 · Estilo y formato",
            "Ruff (lint + format)",
            "0 avisos E, F y W; 0 archivos sin formatear",
            f"{es(ruff['errores_sin_largo_de_linea'])} avisos E, F y W; {es(formatted['por_reformatear'])} de "
            f"{es((formatted['por_reformatear'] or 0) + (formatted['ya_formateados'] or 0))} archivos sin formatear; "
            f"{es(ruff['por_codigo'].get('E501'))} líneas de más de 120 columnas (E501, fuera de la meta: ver límites)",
            both("ruff_avisos", "archivos_sin_formatear"),
        ),
        (
            "2 · SQL",
            "SQLFluff (DuckDB)",
            "sin meta",
            f"{es(sql['bi/queries.sql']['violaciones'])} avisos en bi/queries.sql; "
            f"{es(sql['dbt/models']['violaciones'])} en los modelos de dbt",
            "sin meta",
        ),
        (
            "3 · Tipado",
            "mypy",
            "0 errores; 100 % de funciones con tipos en los módulos principales",
            f"{es(mypy['errores'])} errores en {mypy['modulos']} módulos; {es(mypy['con_tipo_de_retorno'])} de "
            f"{es(mypy['funciones'])} funciones con tipo de retorno",
            both("mypy_errores", "funciones_con_tipos_pct"),
        ),
        (
            "4 · Complejidad",
            "Ruff C901 · radon",
            "≤ 6 funciones sobre 10",
            f"{es(cx['funciones_sobre_10'])} funciones sobre 10 (la peor, {worst[2]}, con {worst[0]}); "
            f"{es(fn['mas_de_50_lineas'])} funciones de más de 50 líneas (la mayor, {fn['mas_larga'][1]}, con "
            f"{es(fn['mas_larga'][0])}); promedio radon {cx['promedio_radon']['nota']} ({es(cx['promedio_radon']['valor'], 1)})",
            state(ok["complejidad_sobre_10"]),
        ),
        (
            "5 · Código muerto",
            "vulture",
            "sin meta",
            f"{len(dead['funciones_sin_uso'])} funciones sin uso ({', '.join(dead['funciones_sin_uso'])}) y "
            f"{es(dead['variables_o_atributos_sin_uso'])} variables o atributos de baja confianza",
            "sin meta",
        ),
        (
            "6 · Pruebas y cobertura",
            "pytest + coverage",
            "0 pruebas fallidas; ≥ 90 % total; ≥ 70 % en cada módulo",
            f"{es(report['pruebas']['pruebas'])} pruebas, {es(coverage['pruebas_ok'])} pasan; cobertura total "
            f"{es(coverage['total'], 1)} %; lógica crítica {es(coverage['logica_critica'], 1)} %; módulo más bajo "
            f"{name} ({es(low, 1)} %)",
            both("pruebas_fallidas", "cobertura_total", "cobertura_por_modulo"),
        ),
        (
            "7 · Seguridad",
            "Bandit · pip-audit · detect-secrets",
            "0 altos; 0 vulnerabilidades; 0 secretos sin revisar",
            f"Bandit: {bandit['alta']} altos, {bandit['media']} medios y {bandit['baja']} bajos; pip-audit: "
            f"{audit_text(report)}; secretos: {secrets['candidatos']} candidatos, {secrets['falsos_positivos']} "
            f"falsos positivos revisados y {secrets['sin_clasificar']} sin clasificar",
            both("bandit_altos", "pip_audit_vulnerabilidades", "secretos_sin_clasificar"),
        ),
        (
            "8 · Datos y dbt",
            "dbt",
            "pruebas pasando",
            f"{es(dbt.get('pruebas_ok'))} de {es(dbt.get('pruebas_total'))} pruebas en la última carga; "
            f"{sum(report['dbt']['modelos_por_capa'].values())} modelos en tres capas (se lee el registro de la carga)",
            "sin meta",
        ),
        (
            "9 · Proceso",
            "Conventional Commits · pre-commit · CI",
            "commits convencionales desde D-323; pre-commit; CI con lint, tipos y cobertura",
            f"{es(process['conventional_commits'])} de {es(process['commits'])} commits siguen Conventional Commits "
            f"(todos los de D-323; los anteriores usan «D-nnn: …»); pre-commit "
            f"{'configurado' if process['pre_commit_configurado'] else 'sin configurar'}; CI: "
            + "; ".join(f"{name} ({', '.join(tools)})" for name, tools in sorted(process["ci"].items())),
            "sin meta",
        ),
    ]


def not_improved(report):
    cx, fn, ruff = report["complejidad"], report["funciones"], report["ruff"]
    names = ", ".join(f"{name} ({value})" for value, _, name in cx.get("mas_complejas", []))
    items = [
        f"{es(cx['funciones_sobre_10'])} funciones siguen sobre la complejidad 10 (las mayores: {names}). Son funciones "
        "que dibujan páginas del panel; dividirlas sin cambiar la interfaz necesita pruebas de interfaz que aún no "
        "existen. Por eso la meta quedó en 6 y no en 0.",
        f"{es(fn['mas_de_50_lineas'])} funciones pasan de 50 líneas; la mayor, {fn['mas_larga'][1]} "
        f"({es(fn['mas_larga'][0])} líneas), es el CSS del panel en una cadena. Partir bi/dashboard.py por páginas y "
        "sacar el CSS a archivos es un cambio grande que se dejó fuera para no cambiar el comportamiento.",
        f"{es(ruff['por_codigo'].get('E501'))} líneas pasan de 120 columnas: casi todas son textos del panel en español "
        "e inglés, que el formateador no parte. pyproject.toml deja E501 fuera de las reglas y la meta; el número se "
        "sigue midiendo aparte para que no se oculte.",
        f"SQLFluff marca {es(report['sql']['bi/queries.sql']['violaciones'])} avisos en bi/queries.sql y "
        f"{es(report['sql']['dbt/models']['violaciones'])} en dbt: el SQL de dbt es la lógica del pipeline, que esta "
        "mejora no debía tocar.",
    ]
    files = report["pip_audit"]["archivos"]
    if any(item.get("vulnerabilidades") is None for item in files.values()):
        items.append(
            f"pip-audit no audita requirements-pipeline.txt con Python {report['python']}: dbt pide 3.11 o 3.12. El "
            "workflow «calidad» corre con 3.11 y sí lo audita."
        )
    if "gitleaks" in report["secretos"].get("nota", ""):
        items.append(
            "gitleaks no está instalado: se usó detect-secrets y una búsqueda de patrones de claves en el historial."
        )
    dora = report["dora"]
    if any(isinstance(dora.get(name), dict) and dora[name].get("estado") for name in ("semanal", "pruebas")):
        items.append(
            "Las métricas DORA del historial de GitHub Actions quedaron sin verificar en este equipo (no se pudo "
            "consultar la API); en el workflow sí se consultan."
        )
    failed = q.values(report)["pruebas_fallidas"]
    if failed:
        items.append(
            f"{es(failed)} pruebas fallan: las que consultan los enlaces públicos del repositorio "
            "(test_t54_every_public_link_answers) esperan que se llame «greenocean» en GitHub (D-319), y el cambio de "
            "nombre lo hace el autor."
        )
    items.append(
        "La auditoría automática de accesibilidad (axe-core) no cubre todo WCAG: falta recorrer cada página con teclado "
        "y con un lector de pantalla, y probar con personas."
    )
    items.append(
        f"El {es(report['datos']['pct_series_con_dato'], 1)} % de las series de las últimas 12 semanas tiene dato en la "
        "última: ODEPA no publica cada serie cada semana, y el proyecto nunca interpola un precio."
    )
    return items


def build_report(baseline, report, goals, rubric, history):
    rows = q.rows(baseline, report, goals)
    passed, measured = q.met(q.values(report), goals)
    before_passed, before_measured = q.met(q.values(baseline), goals)
    grades = [item["nota"] for item in rubric["caracteristicas"]]
    previous = [item["nota_antes"] for item in rubric["caracteristicas"] if item.get("nota_antes") is not None]
    confirmed = rubric.get("estado") == "confirmada"
    rubric_state = "confirmada por el autor" if confirmed else "borrador, pendiente de confirmación del autor"
    data = report["datos"]
    browsers = report["navegadores"]
    out = [
        "# Método y calidad · Informe de autoevaluación",
        "",
        table(
            ["", ""],
            [
                ("**Proyecto**", "GreenOcean"),
                ("**Tipo**", "Informe de autoevaluación de calidad"),
                ("**Medido**", f"{report['generado']} (commit {report['commit']}, Python {report['python']})"),
                (
                    "**Línea base**",
                    f"{baseline['generado']} (commit {baseline['commit']}), antes de las mejoras de D-323",
                ),
                ("**Autor**", "el autor"),
                (
                    "**Estado**",
                    f"Autoevaluación automática, revisada y aprobada por el autor · rúbrica ISO {rubric_state}",
                ),
            ],
        ),
        "",
        "## Resumen",
        "",
        f"Se evaluó el repositorio completo aplicando, como método de revisión, {STANDARDS}. **Es una autoevaluación, no "
        "una certificación**: nadie externo la revisó y no se declara conformidad con ninguna norma.",
        "",
        f"Resultado: {passed} de {measured} indicadores medidos cumplen su meta (en la línea base, {before_passed} de "
        f"{before_measured}). Promedio de la rúbrica ISO/IEC 25010: {es(sum(grades) / len(grades), 1)} de 4 en las "
        f"{len(grades)} características ({rubric_state}); en D-320, {es(sum(previous) / len(previous), 1)} de 4 en las "
        f"{len(previous)} verificadas.",
        "",
        "Cada número sale de ejecutar una herramienta: scripts/medir_calidad.py los deja con su comando en "
        "docs/calidad/medicion.json, y este informe se genera desde ese archivo con scripts/informe_calidad.py. Lo que "
        "no se pudo medir dice «no verificado».",
        "",
        "## Antes → ahora → meta",
        "",
        table(
            ["Indicador", "Antes", "Ahora", "Meta", "Estado", "Cómo reproducirlo"],
            [
                (
                    row["label"][0],
                    q.show(row["before"], row["unit"]),
                    f"**{q.show(row['now'], row['unit'])}**",
                    goal(row),
                    state(row["ok"]),
                    f"`{row['command']}`",
                )
                for row in rows
            ],
        ),
        "",
        "«Antes» es la línea base, medida antes de cambiar nada. El módulo más bajo de la línea base tenía 0 % porque "
        "dos módulos vacíos (bi/data_browser.py y bi/explorer.py) se contaban; D-323 los retiró. Los avisos de Ruff "
        "cuentan las reglas E, F y W sin el largo de línea en las dos columnas.",
        "",
        "## Rúbrica ISO/IEC 25010",
        "",
        table(["Nota", "Significado"], [(g, text) for g, text, _ in quality_method.GRADE_SCALE]),
        "",
        table(
            ["Característica", "Antes (D-320)", "Ahora", "Evidencia", "Qué falta"],
            [
                (
                    item["nombre"][0],
                    grade(item.get("nota_antes")),
                    grade(item["nota"]),
                    item["evidencia"][0],
                    "; ".join([gap[0] for gap in q.gaps(report, goals).get(item["clave"], [])] + [item["falta"][0]]),
                )
                for item in rubric["caracteristicas"]
            ],
        ),
        "",
        "Qué cambió: la eficiencia ya se mide (tiempos de cada página y consulta, con presupuesto); la compatibilidad, "
        "con tres navegadores y dos versiones de Python en el CI; la usabilidad, con axe-core en las 13 páginas y los "
        "cuatro temas; la mantenibilidad, con Ruff, formato, tipos, pre-commit y CI. La adecuación, la fiabilidad, la "
        "seguridad y la portabilidad mantienen su nota.",
        "",
        "## Calidad de los datos (ISO/IEC 25012)",
        "",
        table(
            ["Indicador", "Valor", "Detalle"],
            [
                (
                    "Precios de la última semana con comparación válida",
                    f"{es(data['pct_comparacion'], 1)} %",
                    f"{es(data['con_comparacion'])} de {es(data['precios_semana'])}",
                ),
                (
                    "Series de las últimas 12 semanas con dato esta semana",
                    f"{es(data['pct_series_con_dato'], 1)} %",
                    f"{es(data['series_con_dato'])} de {es(data['series_activas'])}",
                ),
                (
                    "Días desde el fin de la última semana con datos",
                    es(data["dias_desde_ultima_semana"]),
                    f"semana del {data['semana']}",
                ),
                ("Días desde la última carga", es(data["dias_desde_ultima_carga"]), f"medido el {data['medido']}"),
            ],
        ),
        "",
        "Límites declarados: ODEPA publica 9 de las 16 regiones; los precios son nominales (el real descuenta la "
        "inflación general de alimentos); el margen existe solo para frutas y verduras.",
        "",
        "## Navegadores, accesibilidad y rendimiento",
        "",
        table(
            ["Página", "Carga", "Violaciones WCAG 2.1 AA"],
            [
                (name, q.show(page["seconds"], "s"), es(page["violations"]))
                for name, page in browsers["paginas"].items()
            ],
        ),
        "",
        table(
            ["Navegador", "Comprobaciones superadas", "Fallos"],
            [
                (
                    name.capitalize(),
                    f"{item['passed']} / {item['checks']}",
                    ", ".join(f"{fail['page']} {fail['size']}" for fail in item["failed"]) or "—",
                )
                for name, item in browsers["navegadores"].items()
            ],
        ),
        "",
        f"Cada página se abre a 1440 × 790, 1920 × 1000 y en un teléfono en horizontal (844 × 390). La consulta más "
        f"lenta es {report['consultas']['mas_lenta'][0]} ({q.show(report['consultas']['mas_lenta'][1], 's')}, mediana de "
        "tres ejecuciones).",
        "",
        "## Buenas prácticas de código",
        "",
        table(["Práctica", "Herramienta", "Meta", "Medido", "Estado"], practices(report, rows)),
        "",
        "## OWASP Top 10 (revisión por categoría)",
        "",
        table(
            ["Categoría", "Revisión", "Evidencia"],
            [
                (
                    name,
                    text.format(b608=report["bandit"]["por_regla"].get("B608", 0), audit=audit_text(report)),
                    f"`{where}`",
                )
                for name, text, where in OWASP
            ],
        ),
        "",
        "No hubo prueba de penetración.",
        "",
        "## Twelve-Factor App",
        "",
        table(["Factor", "Estado"], TWELVE_FACTORS),
        "",
        "## DORA",
        "",
        f"- **Frecuencia de despliegue:** una carga por semana; la base registra {report['dora']['cargas_registradas']} "
        f"cargas entre el {report['dora']['primera']} y el {report['dora']['ultima']}.",
    ]
    for name in ("semanal", "pruebas"):
        item = report["dora"].get(name, {})
        out.append(
            f"- **Workflow {name}:** "
            + (
                f"{item['ejecuciones']} ejecuciones terminadas, {item['fallidas']} fallidas."
                if "ejecuciones" in item
                else "no verificado (no se pudo consultar la API de GitHub)."
            )
        )
    out += [
        "",
        "## Historial de mediciones",
        "",
        table(
            ["Medición", "Commit", "Cumplen la meta", "Cobertura", "Ruff", "mypy", "WCAG", "Página más lenta"],
            [
                (
                    entry["generado"],
                    entry["commit"],
                    "{} de {}".format(*q.met(entry["valores"], goals)),
                    q.show(entry["valores"].get("cobertura_total"), "%"),
                    es(entry["valores"].get("ruff_avisos")),
                    es(entry["valores"].get("mypy_errores")),
                    es(entry["valores"].get("violaciones_wcag")),
                    q.show(entry["valores"].get("segundos_por_pagina"), "s"),
                )
                for entry in reversed(history.get("mediciones", []))
            ],
        ),
        "",
        "## Qué se mide solo y qué se revisa a mano",
        "",
        table(["Qué", "Cómo", "Frecuencia"], [(what[0], how[0], when[0]) for what, how, when in q.SCHEDULE]),
        "",
        "## Lo que no se pudo mejorar, y por qué",
        "",
        *[f"- {item}" for item in not_improved(report)],
        "",
        "## Cómo se aprueba",
        "",
        "- **Una medición:** el workflow «calidad» la propone en un pull request «Actualizar medición de calidad»; la "
        "página la muestra solo cuando el autor lo fusiona.",
        "- **La rúbrica:** el autor revisa docs/calidad/rubrica.json y cambia «estado» a «confirmada» y «revisada_por» a "
        "«el autor»; hasta entonces la página dice «borrador, pendiente de su confirmación».",
        "- **Las metas:** solo el autor las cambia, en docs/calidad/metas.json.",
        "",
        "## Cómo reproducir",
        "",
        "- `python scripts/medir_calidad.py --tools <entorno>/bin --node-path <node_modules>` escribe la medición.",
        "- `python scripts/verificar_calidad.py docs/calidad/medicion.json` la compara con las metas.",
        "- `python scripts/informe_calidad.py` escribe este informe y agrega la medición al historial.",
        "",
        "Las herramientas de calidad no son dependencias del proyecto: viven en un entorno aparte, con las versiones "
        "del workflow «calidad».",
        "",
    ]
    return "\n".join(out)


def build_pull_request(previous, report, goals):
    """The body of «Actualizar medición de calidad»: every indicator against the previous measurement, and the measured
    evidence of each ISO characteristic for the author's draft review."""
    rows = q.rows(previous, report, goals)
    passed, measured = q.met(q.values(report), goals)
    lines = [
        f"Medición del {report['generado']} (commit {report['commit']}), comparada con la anterior "
        f"({previous.get('generado', '—')}, commit {previous.get('commit', '—')}). {passed} de {measured} indicadores "
        "cumplen su meta.",
        "",
        table(
            ["Indicador", "Anterior", "Nueva", "Meta", "Estado"],
            [
                (
                    row["label"][0],
                    q.show(row["before"], row["unit"]),
                    q.show(row["now"], row["unit"]),
                    goal(row),
                    state(row["ok"]),
                )
                for row in rows
            ],
        ),
        "",
        "Borrador de evidencia por característica ISO/IEC 25010 (pendiente de confirmación del autor):",
        "",
    ]
    for key in sorted({row["iso"] for row in rows}):
        own = [row for row in rows if row["iso"] == key]
        lines.append(
            f"- **{key}:** "
            + "; ".join(f"{row['label'][0]} {q.show(row['now'], row['unit'])} ({state(row['ok'])})" for row in own)
        )
    lines += [
        "",
        "Nada se publica en la página «Método y calidad» hasta que el autor fusione este pull request. El workflow no "
        "cambió código: solo docs/calidad/medicion.json, historial.json e INFORME.md.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anterior", default="", help="the previous measurement, for the pull request body")
    parser.add_argument("--cuerpo", default="", help="where to write the pull request body")
    arguments = parser.parse_args()
    baseline, report = q.read(q.BASELINE_FILE), q.read(q.REPORT_FILE)
    goals, rubric = q.read(q.GOALS_FILE), q.read(q.RUBRIC_FILE)
    history = q.add_to_history(q.read(q.HISTORY_FILE), report)
    q.HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(build_report(baseline, report, goals, rubric, history), encoding="utf-8")
    if arguments.cuerpo:
        previous = q.read(Path(arguments.anterior)) if arguments.anterior else {}
        Path(arguments.cuerpo).write_text(build_pull_request(previous, report, goals), encoding="utf-8")
    print(f"escrito {REPORT_PATH.relative_to(q.FOLDER.parent.parent)}")


if __name__ == "__main__":
    main()
