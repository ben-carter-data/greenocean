"""«Controles de datos» (D-541): what each load brought, which rows were left out and why, the quality evidence of the
latest measure and the button that checks it again. Its tab «Catálogo de controles» lives in bi/control_catalog.py.
"""

import html
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from bi import (
    charts,
    compact_table,
    control_catalog,
    git_workflow,
    i18n,
    lineage,
    project,
    quality,
    quality_evidence,
    quality_live,
    quality_method,
    quality_metrics,
    quality_view,
    quality_viewer,
    queries,
    weeks,
)
from bi.app_frame import (
    build_external_link_html,
    build_info_card_html,
    get_profile,
    is_author,
    keep_context,
    open_card,
    show_chart,
    show_info_cards,
    show_page_bar,
    show_section_intro,
    show_view_tabs,
)
from bi.constants import (
    ADMIN_UNLOCKED,
    ALL_VALUES,
    FLAG_NAMES,
    GIT_TAB_LOG,
    GIT_TAB_PARAMETER,
    MANIFEST_FILE,
    PAGE_GIT,
    PAGE_METHOD,
    PAGE_OPERATIONS,
    QUALITY_VIEW_KEY,
    REASON_NAMES,
    REASON_TEXTS,
    REJECTED_ROW_LABELS,
    REPORT_PARAMETER,
    SOURCE_NAMES,
    VIEW_PARAMETER,
    WINDOW_OF_VIEW,
    WINDOW_PAGES,
)
from bi.data_access import (
    format_chile_time,
    get_database_version,
    parse_run_start,
    read_download_manifest,
    read_indicator,
    read_latest_run,
    read_lineage,
    read_match_coverage,
    to_chile_time,
)
from bi.i18n import tr
from etl import etl

# region Constants
QUALITY_PICK_KEY = "qa_pick"


QUALITY_OPEN_KEY = "qa_open"
# endregion


# region Load figures and excluded rows
def show_load_figures(latest_run):
    """Three cards with the row counts of the latest load."""
    figures = [
        ("Filas leídas", latest_run["rows_read"]),
        ("Filas cargadas", latest_run["rows_loaded"]),
        ("Filas rechazadas", latest_run["rows_rejected"]),
    ]
    for column, (label, count) in zip(st.columns(3), figures):
        with column, open_card(f"load_{label}"):
            st.markdown(
                f'<div class="kpi-label">{label}</div><div class="kpi-value">{charts.format_thousands(count)}</div>',
                unsafe_allow_html=True,
            )


def show_flag_donut(mode):
    """Card: weekly prices used in the indicators against those left out."""
    flag_counts = read_indicator("quality_flag_counts")
    totals = flag_counts.groupby("flag")["weekly_prices"].sum()
    with open_card("flag_donut", "Estado de los precios semanales"):
        palette = charts.get_palette(mode)
        rows = pd.DataFrame(
            {"label": [FLAG_NAMES.get(flag, flag) for flag in totals.index], "value": totals.to_numpy()}
        )
        rows["value_label"] = rows["value"].map(charts.format_thousands)
        colors = [
            palette["accent"]
            if flag == "SIN_MARCA"
            else palette["rise"]
            if flag == etl.FLAG_OUTLIER
            else palette["reference"]
            for flag in totals.index
        ]
        donut_column, legend_column = st.columns([1, 1], vertical_alignment="center")
        with donut_column:
            show_chart(charts.draw_donut(rows, colors, mode))
        with legend_column:
            for label, value_label, color in zip(rows["label"], rows["value_label"], colors):
                st.markdown(
                    f'<span style="color:{color}">●</span> {html.escape(label)}: **{value_label}**',
                    unsafe_allow_html=True,
                )


def show_quality_details():
    """Card: match coverage (K7)."""
    keys_with_margin, consumer_keys = read_match_coverage()
    with open_card("quality_details", "Cobertura del cruce", kpi="K7"):
        st.markdown(
            f'<div class="kpi-value">{keys_with_margin} de {consumer_keys}</div>'
            f'<div class="kpi-note">claves de frutas y verduras del consumidor tienen '
            f'margen ({charts.format_percent(keys_with_margin / consumer_keys * 100)})'
            f'</div>',
            unsafe_allow_html=True,
        )


def describe_reasons(rejections):
    """«NON_POSITIVE_PRICE (201): un precio … es cero o negativo», one per reason."""
    return "; ".join(
        f"{row['reason']} ({charts.format_thousands(row['rejected_rows'])}): "
        f"{REASON_TEXTS.get(row['reason'], 'motivo sin descripción')}"
        for row in rejections.to_dict("records")
    )


def build_excluded_cards(latest_run, rejections, flag_totals):
    """What was left out of the indicators, and why: rejected, outliers, no unit."""
    rejected = int(rejections["rejected_rows"].sum()) if not rejections.empty else 0
    share = charts.format_percent(rejected / latest_run["rows_read"] * 100, decimals=3)
    rejected_text = (
        f"{charts.format_thousands(rejected)} de "
        f"{charts.format_thousands(latest_run['rows_read'])} filas leídas ({share}). "
        + (f"Motivo: {describe_reasons(rejections)}." if rejected else "La última ejecución no rechazó filas.")
    )
    outliers = int(flag_totals.get(etl.FLAG_OUTLIER, 0))
    unconvertible = int(flag_totals.get(etl.FLAG_UNIT_NOT_CONVERTIBLE, 0))
    return [
        build_info_card_html(
            "Filas rechazadas",
            rejected_text,
            label="RN-11 · no se cargan",
            note="Se guardan tal como venían en la tabla `rejection`; nunca se borran en silencio.",
            is_warning=True,
        ),
        build_info_card_html(
            "Precios atípicos",
            f"{charts.format_thousands(outliers)} precios "
            "semanales a más de 5 veces, o menos de 1/5, de la mediana de su "
            "producto esa semana.",
            label="RN-12 · fuera de los indicadores",
            note="Siguen en `weekly_price` con la marca `ATIPICO`.",
        ),
        build_info_card_html(
            "Unidad no convertible",
            f"{charts.format_thousands(unconvertible)}"
            " precios semanales en unidades con un rango o sin cantidad "
            "declarada (un atado de 1,5 a 2 kilos, una docena de atados): no "
            "se pueden llevar a kilo ni a unidad.",
            label="RN-05 · sin precio comparable",
            note="Siguen en `weekly_price` con la marca `UNIDAD_NO_CONVERTIBLE`, sin margen.",
        ),
    ]


def build_rejected_rows_table(rejected_rows):
    """The rejected rows as ODEPA sent them, with readable columns in Spanish."""
    records = []
    for row in rejected_rows.to_dict("records"):
        original = json.loads(row["original_row"])
        record = {
            "Fuente": SOURCE_NAMES.get(row["source"], row["source"]),
            "Motivo": REASON_NAMES.get(row["reason"], row["reason"]),
        }
        record.update({label: original[key] for key, label in REJECTED_ROW_LABELS.items() if key in original})
        records.append(record)
    return pd.DataFrame(records)


def format_outliers(outliers):
    """The outliers with readable columns in Spanish."""
    outliers = outliers.drop(columns="key_label").copy()
    outliers["week_start"] = [weeks.week_range(value, year=True) for value in outliers["week_start"]]  # D-374
    outliers["source"] = outliers["source"].map(SOURCE_NAMES)
    outliers.columns = [
        "Semana",
        "Fuente",
        "Canal",
        "Región",
        "Producto",
        "Variedad",
        "Calidad",
        "Unidad",
        "Precio",
        "Observaciones",
    ]
    return outliers


def show_excluded_rows(latest_run):
    """Which rows were left out, why, and the rows themselves folded."""
    rejections = read_indicator("k8_rejected_rows")
    flag_totals = read_indicator("quality_flag_counts").groupby("flag")["weekly_prices"].sum()
    show_section_intro(
        "Qué quedó fuera y por qué", "Tres grupos de datos que no entran a los indicadores; ninguno se borra.", True
    )
    show_info_cards(build_excluded_cards(latest_run, rejections, flag_totals))
    rejected_rows = build_rejected_rows_table(read_indicator("quality_rejected_rows"))
    with st.expander(
        f"Ver las {charts.format_thousands(len(rejected_rows))} filas rechazadas, tal como venían", expanded=False
    ):
        if rejected_rows.empty:
            st.info("La última ejecución no rechazó filas.")
        else:
            reasons = sorted(rejected_rows["Motivo"].unique())
            if len(reasons) > 1:
                reason = st.selectbox("Motivo", reasons, key="rejected_reason")
                rejected_rows = rejected_rows[rejected_rows["Motivo"] == reason]
            st.dataframe(rejected_rows, hide_index=True)
    outliers = format_outliers(read_indicator("quality_outliers"))
    with st.expander(f"Ver los {charts.format_thousands(len(outliers))} precios atípicos", expanded=False):
        st.dataframe(outliers, hide_index=True)
    units = read_indicator("quality_unconvertible_units")
    units["source"] = units["source"].map(SOURCE_NAMES)
    units.columns = ["Fuente", "Canal", "Producto", "Variedad", "Calidad", "Precios semanales"]
    with st.expander("Ver los precios con unidad no convertible, por producto", expanded=False):
        st.dataframe(units, hide_index=True)
    st.caption(
        "Consultas: `quality_rejected_rows`, `quality_outliers` y `quality_unconvertible_units` en `bi/queries.sql`."
    )


# endregion


# region Quality evidence
def show_quality_tab(mode):
    """What the latest load read and kept, then what was left out and why (D-057)."""
    show_section_intro("Calidad de datos", "Qué se cargó en la última ejecución, qué quedó fuera y por qué.")
    latest_run = read_latest_run()
    show_load_figures(latest_run)
    donut_column, details_column = st.columns([3, 2])
    with donut_column:
        show_flag_donut(mode)
    with details_column:
        show_quality_details()
    show_excluded_rows(latest_run)


@st.cache_data
def read_parity(database_version):
    """SQLite backup against DuckDB, once per load (D-154)."""
    return quality.check_parity()


@st.cache_data(ttl=300, show_spinner=False)
def read_rejection_count(database_version):
    """Rows the validation set apart, for the anomalies box of the quality page (D-176)."""
    return int(queries.run_sql("SELECT count(*) AS n FROM rejection").iloc[0, 0])


@st.cache_data(ttl=300, show_spinner=False)
def read_quality_evidence(database_version, manifest_text, file_versions):
    """Invalidate checks when either the database, manifest or local source files change."""
    return quality.check_database(), quality.check_source_files(json.loads(manifest_text), MANIFEST_FILE.parent)


def open_quality_evidence():
    """A card chosen in the pills opens its dialog once; the pills clear themselves."""
    st.session_state[QUALITY_OPEN_KEY] = st.session_state.get(QUALITY_PICK_KEY)
    st.session_state[QUALITY_PICK_KEY] = None


def show_recheck_button():
    """«Volver a medir», in the page bar (D-271): every tab can use it and none loses a row to it."""
    rechecked = st.session_state.get("qa_rechecked_at")
    st.button(
        "Volver a medir",
        icon=":material/refresh:",
        key="qa_recheck_page",
        on_click=recheck_quality,
        help="Descarta lo guardado y mide de nuevo sobre la base publicada. Cada indicador se mide en la base de la "
        "última carga; cada control abre los datos que lo respaldan."
        + (f" Medido de nuevo a las {to_chile_time(rechecked):%H:%M:%S}." if rechecked else ""),
    )


def recheck_quality():
    """Run every check again, now: the caches of the board are dropped (D-171)."""
    read_quality_evidence.clear()
    read_quality_measures.clear()
    read_parity.clear()
    read_lineage.clear()
    st.session_state["qa_rechecked_at"] = datetime.now(timezone.utc)


@st.cache_data(ttl=300, show_spinner=False)
def read_quality_measures(database_version):
    """The raw figures of the «Calidad» view, read from the database on every load (D-196)."""
    return quality_live.read_measures()


@st.dialog("Evidencia", width="large")
def show_quality_evidence_dialog(key, mode, context):
    """One card's evidence: what it checks, its rows, its method, and a recheck."""
    st.markdown(f"### {quality_evidence.TITLES[key]}")
    st.markdown(quality_evidence.EXPLANATIONS[key])
    if key == "files":
        st.dataframe(quality_evidence.manifest_frame(context["manifest"]), hide_index=True, width="stretch")
        st.caption(f"Registro: agent/downloads/manifest.json · {len(context['manifest'])} archivos.")
    elif key == "shield":
        st.dataframe(quality_evidence.files_frame(context["files"]), hide_index=True, width="stretch")
        if any(item["actual"] is None for item in context["files"]):
            st.caption(
                "Los archivos CSV no viven en el servidor del panel (no se suben al repositorio): aquí la "
                "huella solo se comprueba cuando el panel corre junto a las descargas."
            )
    elif key == "calendar":
        checks = context["checks"]
        st.markdown(
            f"**{checks['weeks']} semanas**: {quality_view.format_week(checks['first'])} → "
            f"{quality_view.format_week(checks['last'])}."
        )
        missing = queries.run_sql(quality_evidence.MISSING_WEEKS_SQL)
        if missing.empty:
            st.success("Ninguna semana falta entre la primera y la última.", icon=":material/check_circle:")
        else:
            st.dataframe(missing, hide_index=True, width="stretch")
        show_evidence_method(quality_evidence.MISSING_WEEKS_SQL)
    elif key == "gear":
        st.dataframe(queries.run_sql(quality_evidence.RUNS_SQL), hide_index=True, width="stretch")
        show_quality_tab(mode)
    elif key == "layers":
        st.dataframe(
            lineage.build_rule_matrix(context["nodes"], context["results"]),
            hide_index=True,
            width="stretch",
            column_config={
                "Regla": st.column_config.TextColumn(width="small"),
                "Pruebas dbt": st.column_config.NumberColumn(width="small"),
            },
        )
        st.caption("Cada regla del PRD con las pruebas de dbt que la comprueban en cada carga.")
        st.dataframe(queries.run_sql(quality_evidence.DBT_TESTS_SQL), hide_index=True, width="stretch")
        show_evidence_method(quality_evidence.DBT_TESTS_SQL)
    elif key == "database":
        frame = quality_evidence.checks_frame(context["checks"])
        st.dataframe(frame[["comprobación", "casos"]], hide_index=True, width="stretch")
        show_evidence_method("\n\n".join(frame["sql"]))
    elif key == "parity":
        st.dataframe(quality_evidence.parity_frame(context["parity"]), hide_index=True, width="stretch")
        show_evidence_method(quality.PARITY_SQL + "  -- en SQLite y en DuckDB")
    elif key in quality_evidence.TEST_LINKS:
        st.markdown(
            "Esta auditoría corre con las pruebas automáticas en cada cambio del repositorio y en cada carga semanal."
        )
        if is_author():  # D-500: its code and result live in the author's repository
            st.markdown("Su código y su último resultado:")
            for label, address in quality_evidence.test_links(key):
                st.markdown(build_external_link_html(label, address), unsafe_allow_html=True)
    else:
        st.info("Sin evidencia que mostrar: es un límite declarado, no una comprobación.")
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.button(
            "Volver a comprobar",
            icon=":material/refresh:",
            key="qa_recheck",
            on_click=recheck_quality,
            help="Corre de nuevo los controles sobre la base publicada y los archivos.",
        )
        rechecked = st.session_state.get("qa_rechecked_at")
        if rechecked:
            st.caption(f"Comprobado de nuevo a las {to_chile_time(rechecked):%H:%M:%S}.")


def show_evidence_method(sql):
    with st.expander("Método: la consulta que lo comprueba", expanded=False, icon=":material/code:"):
        st.code(sql, language="sql")


# endregion


# region The page
def show_operations_page(mode):
    """Controles de datos in one view (D-220): the quality measured on the real database, each
    dimension under the pipeline stop where it is watched, and the audit controls that back it,
    each opening its evidence. The single-price trace and its pickers left (D-196 → D-220)."""
    show_page_bar(
        PAGE_OPERATIONS,
        "Controles de datos",
        "La calidad medida en cada carga y los controles que demuestran que lo publicado se puede rastrear y repetir.",
        side=show_recheck_button,
        live="weekly_price, rejection, etl_run y dbt_result se consultan en la Base DuckDB al abrir la página.",
    )
    measures = read_quality_measures(get_database_version())
    indicators = quality_live.build_indicators(measures)
    manifest = read_download_manifest()
    run = read_latest_run()
    nodes, results = read_lineage(get_database_version())
    build = lineage.summarize_build(nodes, results)
    versions = tuple(
        (path.name, path.stat().st_size, path.stat().st_mtime_ns) for path in sorted(MANIFEST_FILE.parent.glob("*.csv"))
    )
    checks, files = read_quality_evidence(get_database_version(), json.dumps(manifest, sort_keys=True), versions)
    parity = read_parity(get_database_version())
    evidence = quality_view.build_evidence(
        checks,
        files,
        manifest,
        run,
        build,
        parity,
        lambda value: format_chile_time(parse_run_start(value)),
        rejections=read_rejection_count(get_database_version()),
    )
    # D-257: the diagram is the page; every piece opens its detail in a pop-up. What was set aside and the audit controls
    # have their own tabs, and a failure shows up in all of them.
    columns = quality_view.build_columns(evidence)
    database_ok = checks["integrity_ok"] and not any(checks[key] for key in ("foreign_keys", "duplicates", "invalid"))
    changed_files = [item["file"] for item in files if item["status"].startswith("Falla")]
    if not database_ok:
        st.error(
            "La base publicada no pasa sus controles de integridad. Revisa la evidencia antes de utilizar los resultados."
        )
    palette = charts.get_palette(mode)
    # D-360: only the tab in sight is drawn.
    tab = show_view_tabs(
        QUALITY_VIEW_KEY, ["Calidad", "Auditoría", "Rechazos y cargas", "Catálogo de controles"], palette
    )
    if tab == "Calidad":
        # D-272: the frame takes the drawing's own height (a fixed one cut the gates on a wide window). D-273: the drawing
        # is HTML, so its words keep their size; past 1180 px it would only spread out, so it stops growing there.
        st.markdown(
            '<style>.st-key-qa_hub iframe {display:block; margin:0 auto; max-width:1180px;}</style>',
            unsafe_allow_html=True,
        )
        with st.container(key="qa_hub"):
            st.iframe(quality_live.build_quality_html(palette, indicators, columns, measures), height="content")
    elif tab == "Auditoría":
        st.iframe(quality_live.build_audit_page_html(palette, columns), height="content")
        with st.container(key=quality_view.EXPANDER_KEY, horizontal=True, vertical_alignment="center", gap="small"):
            # D-272: the eleven buttons wait behind one, so they do not take two rows of the screen (and no picker
            # comes back, D-220).
            with st.popover("Abrir la evidencia de un control", icon=":material/folder_open:"):
                st.pills(
                    "Abrir la evidencia de",
                    [title for _, title, _ in quality_evidence.CARDS],
                    key=QUALITY_PICK_KEY,
                    on_change=open_quality_evidence,
                    label_visibility="collapsed",
                )
            if changed_files:
                # The indicators are measured on the published database; only the local copies of the source files
                # differ. D-273: one small line beside the button, not a banner over the controls.
                names = i18n.join_names(changed_files)  # «a y b» or «a and b» (D-380)
                st.markdown(
                    f'<span class="qa-local-note" style="font-size:12.5px; color:{quality_view.PILL_COLORS["pending"]}">'
                    f'⚠ En este equipo, {html.escape(names)} no coincide con su huella '
                    'en manifest.json; los indicadores no cambian.</span>',
                    unsafe_allow_html=True,
                )
    elif tab == "Catálogo de controles":  # D-524: every control, and the sale units nobody has classified yet
        st.markdown(
            '<style>.st-key-controls_frame, .st-key-controls_frame [data-testid="stElementContainer"], '
            ".st-key-controls_frame iframe { height:max(calc(100vh - 324px), 420px) !important; }</style>",
            unsafe_allow_html=True,
        )
        with st.container(key="controls_frame"):
            st.iframe(control_catalog.build_page_html(palette, i18n.get_language(), is_author()), height=420)
    else:
        st.iframe(
            quality_live.build_tables_html(palette, measures["runs"], measures["rejections"], measures["flags"]),
            height="content",
        )
    chosen_card = st.session_state.pop(QUALITY_OPEN_KEY, None)
    if chosen_card in quality_evidence.TITLES.values():
        key = next(key for key, title in quality_evidence.TITLES.items() if title == chosen_card)
        show_quality_evidence_dialog(
            key,
            mode,
            dict(
                manifest=manifest,
                files=files,
                checks=checks,
                parity=parity,
                nodes=nodes,
                results=results,
                evidence=evidence,
            ),
        )


# endregion


# region «Plan de calidad»
def filter_reports(reports, year, month, week, query):
    """The reports the filters of «Informes» leave (D-333): by year, month and data week, and a search over the number,
    the date and the evaluated code."""
    query = query.strip().lower()
    number = None
    for prefix in ("n°", "nº", "no.", "#"):
        if query.startswith(prefix) and query[len(prefix) :].strip().isdigit():
            number = int(query[len(prefix) :].strip())  # «N° 2» is report 2, not any «2»
    kept = []
    for report in reports:
        date = str(report["fecha"])
        if year != ALL_VALUES and date[:4] != year:
            continue
        if month != ALL_VALUES and date[5:7] != month:
            continue
        if week != ALL_VALUES and str(report["semana"]) != week:
            continue
        week_text = weeks.week_range(report["semana"], year=True) if report["semana"] else ""
        haystack = f"{report['numero']} {date} {report['codigo_evaluado']} {report['semana']} {week_text}".lower()
        if number is not None and report["numero"] != number:
            continue
        if number is None and query and query not in haystack:
            continue
        kept.append(report)
    return kept


@st.dialog("Informe de calidad", width="large")
def show_quality_report_dialog(ref):
    """One numbered report as slides (D-333): its own document, so the keyboard, full screen and the PDF work. D-431:
    «ref» is «7» for the weekly series or «C7» for the construction one; the viewer reads only that series."""
    found = quality_metrics.find_report(ref)
    if not found:
        st.warning(tr("Ese informe no existe."))
        return
    reports, number = found
    _, goals, policy = quality_method.read_page()
    nonconformities = quality_metrics.read(quality_metrics.FOLDER / "no_conformidades.json").get("registros", [])
    incidents = quality_metrics.read(quality_metrics.FOLDER / "incidentes_externos.json").get("registros", [])
    st.iframe(
        quality_viewer.build_viewer_html(
            reports,
            number,
            goals,
            policy,
            nonconformities,
            incidents,
            i18n.is_english(),
            project.build_github_url(
                i18n.document_path("PLAN_DE_CALIDAD.md").relative_to(project.PROJECT_DIR).as_posix()
            )
            if is_author()  # D-500
            else "",
        ),
        height=700,
    )


def show_open_report_button(report):
    """The button under a report's detail in «Informes»: it opens the report as slides, with its PDF."""
    if st.button(
        tr("Abrir el informe o su PDF"),
        key=f"cr_reports_open_{quality_metrics.report_ref(report)}",
        icon=":material/description:",
    ):
        show_quality_report_dialog(quality_metrics.report_ref(report))


def show_method_page(mode):
    """«Plan de calidad» (D-320, D-323, D-330, D-332, D-333): how the quality of the published data and of the code is
    managed. Two tabs: «Resumen» (each indicator against its acceptable) and «Informes» (the numbered reports)."""
    reports, goals, policy = quality_method.read_page()
    latest = reports[-1] if reports else None
    show_page_bar(
        PAGE_METHOD,
        PAGE_METHOD,
        "Qué medimos de los datos que publicamos y del código que los trata, contra qué aceptable, y cómo vamos.",
    )
    st.markdown(quality_method.build_css(charts.get_palette(mode)), unsafe_allow_html=True)
    st.markdown(quality_method.build_header(latest), unsafe_allow_html=True)
    asked = st.query_params.get(REPORT_PARAMETER)
    # D-432: only once the view is back (D-430): the first run of a reload has none yet, and its rerun would close it.
    if asked and get_profile():
        # A report named in the address (its number or its PDF icon in «Informes») opens once.
        del st.query_params[REPORT_PARAMETER]
        if quality_metrics.find_report(asked):
            show_quality_report_dialog(asked)
    summary, history = st.tabs([tr("Resumen"), tr("Informes")])
    with summary:
        st.markdown(
            quality_method.build_overview(latest, goals, policy, git_workflow.read_failures()), unsafe_allow_html=True
        )
        git_page = WINDOW_PAGES.get(WINDOW_OF_VIEW[PAGE_GIT])  # absent when a test draws this page alone
        if git_page:
            st.page_link(
                git_page,
                label=tr("Ver registro completo"),
                icon=":material/arrow_forward:",
                query_params=keep_context() | {VIEW_PARAMETER: PAGE_GIT, GIT_TAB_PARAMETER: GIT_TAB_LOG},
            )
        if latest and st.button(
            tr("Abrir el último informe"), icon=":material/description:", key="quality_latest_report"
        ):
            show_quality_report_dialog(quality_metrics.report_ref(latest))
    with history:
        # D-431: one series at a time, the weekly first; the construction series (C-1 to C-7) stays readable
        series = [
            name
            for name in (quality_metrics.SERIES_WEEKLY, quality_metrics.SERIES_BUILD)
            if quality_metrics.read_series(name)
        ]
        if len(series) > 1:
            chosen = st.segmented_control(
                tr("Serie"),
                series,
                default=series[0],
                key="quality_series",
                format_func=lambda name: (
                    tr("Semanal") if name == quality_metrics.SERIES_WEEKLY else tr("Construcción (C-1 a C-7)")
                ),
            )
            reports = quality_metrics.read_series(chosen or series[0])
        years = [ALL_VALUES] + sorted({str(item["fecha"])[:4] for item in reports}, reverse=True)
        months = [ALL_VALUES] + sorted({str(item["fecha"])[5:7] for item in reports}, reverse=True)
        data_weeks = [ALL_VALUES] + sorted({str(item["semana"]) for item in reports if item["semana"]}, reverse=True)
        with st.container(horizontal=True, vertical_alignment="bottom", key="quality_filters"):
            year = st.selectbox(tr("Año"), years, key="quality_year", format_func=lambda value: tr(value))
            month = st.selectbox(tr("Mes"), months, key="quality_month", format_func=lambda value: tr(value))
            week = st.selectbox(
                tr("Semana de datos"),
                data_weeks,
                key="quality_week",
                format_func=lambda value: tr(value) if value == ALL_VALUES else i18n.tr_week(value, year=True),
            )
            query = st.text_input(
                tr("Buscar"),
                key="quality_search",
                placeholder=tr("N°, fecha o código"),
                icon=":material/search:",
            )
        shown = filter_reports(reports, year, month, week, query)
        st.markdown(compact_table.build_css(charts.get_palette(mode)), unsafe_allow_html=True)
        if not shown:
            st.caption(tr("Ningún informe coincide."))
        else:
            compact_table.show_compact_rows(
                "cr_reports",
                sorted(shown, key=lambda item: -item["numero"]),
                quality_method.report_summary,
                lambda report: quality_method.build_report_detail(report, reports),
                signature=f"{reports[0].get('serie') if reports else ''}|{year}|{month}|{week}|{query}",
                after_detail=show_open_report_button,
            )


# endregion


# region «Cambios e incidentes»
def show_git_page(mode):
    """«Cambios e incidentes» (D-344): the map of the 15 stations from an idea to a live deployment, and the incident log.
    The professional and the author read it; the diagnoses of the log are the author's (D-345)."""
    author = bool(st.session_state.get(ADMIN_UNLOCKED))
    show_page_bar(
        PAGE_GIT,
        PAGE_GIT,
        "Cómo viaja un cambio desde la idea hasta el despliegue, y las fallas que han ocurrido en el camino.",
    )
    flow, log = st.tabs(
        [tr("Mapa"), tr("Registro de incidentes")],
        default=tr("Registro de incidentes") if st.query_params.get(GIT_TAB_PARAMETER) == GIT_TAB_LOG else None,
    )
    with flow:
        st.iframe(git_workflow.build_map_html(charts.get_palette(mode), i18n.get_language(), author), height="content")
    with log:
        language = i18n.get_language()
        states = [ALL_VALUES, "abierta", "resuelta"]
        state = st.selectbox(tr("Estado"), states, key="incident_state", format_func=lambda value: tr(value), width=220)
        shown = [row for row in git_workflow.read_failures() if state == ALL_VALUES or row["estado"] == state]
        st.markdown(compact_table.build_css(charts.get_palette(mode)), unsafe_allow_html=True)
        if not shown:
            st.caption(tr("Todavía no hay fallas registradas."))
        compact_table.show_compact_rows(
            "cr_incidents",
            shown,
            lambda row: git_workflow.log_summary(row, language),
            lambda row: git_workflow.log_detail(row, language, author),
            signature=state,
        )


# endregion
