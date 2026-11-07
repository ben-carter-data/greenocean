"""Streamlit dashboard for the price monitor.

Run it with:  streamlit run bi/dashboard.py

It reads etl/datos.db through the named queries of bi/queries.sql, and the
state of the weekly pipeline through the GitHub API (bi/control.py).
Texts shown to the user are in Spanish; code and comments are in English.
The color modes and chart palettes live in bi/charts.py.
"""

import base64
import hashlib
import html
import importlib
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode

import pandas as pd
import streamlit as st

# region Imports of the project
# Streamlit runs this file as a script, so the project folder is added to the
# import path to reach the other modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bi  # noqa: E402
from bi import (
    activity_bar,
    actions_view,
    compact_table,
    configuration,
    git_workflow,
    github_actions,
    run_monitor,
    app_map,
    app_map_detail,
    overview,  # noqa: F401  read by the tests through this module
    quality_method,
    quality_metrics,
    quality_viewer,
    architecture,
    buttons,
    charts,
    control,
    documents_folder,
    i18n,
    source_study,
    weeks,
    doc_diagrams,
    github_page,
    lineage,
    live_flow,
    operation_center,
    security_map,
    sql_explorer,
    transformation_rules,
    stack_page,
    project,
    queries,
    zoom,
)
from etl import etl  # noqa: E402
from bi.page_weekly import (  # noqa: E402
    show_home_page,
    HOME_LINKS_JS,  # noqa: F401  read by the tests through this module
    NOTHING_MOVED,  # noqa: F401  read by the tests through this module
    read_cached_filter_options,  # noqa: F401  read by the tests through this module
    build_movement_proportions,  # noqa: F401  read by the tests through this module
    build_steps_css,  # noqa: F401  read by the tests through this module
    compare_same_regions,  # noqa: F401  read by the tests through this module
    read_home_model,  # noqa: F401  read by the tests through this module
    sign_test_p_value,  # noqa: F401  read by the tests through this module
    build_regional_movement_model,  # noqa: F401  read by the tests through this module
    read_regional_movement_model,  # noqa: F401  read by the tests through this module
    read_cached_region_calculation,  # noqa: F401  read by the tests through this module
    read_home_trends,  # noqa: F401  read by the tests through this module
    read_channel_cards,  # noqa: F401  read by the tests through this module
    home_alert_rows,  # noqa: F401  read by the tests through this module
    alert_prices,  # noqa: F401  read by the tests through this module
    alert_items,  # noqa: F401  read by the tests through this module
    level_guide_text,  # noqa: F401  read by the tests through this module
    matches_product_search,  # noqa: F401  read by the tests through this module
    keep_direction,  # noqa: F401  read by the tests through this module
    sort_family_products,  # noqa: F401  read by the tests through this module
    show_products_dialog,  # noqa: F401  read by the tests through this module
    draw_products_window,  # noqa: F401  read by the tests through this module
    alert_download_rows,  # noqa: F401  read by the tests through this module
)
from bi.page_analysis import (  # noqa: E402
    show_ba_page,
    ba_green,
    show_stakeholders_page,
    show_price_context_page,
    show_insights_page,
    FAMILY_FOCUS_KEY,  # noqa: F401  read by the tests through this module
    OVERVIEW_WEEK_KEY,  # noqa: F401  read by the tests through this module
    BA_TAB_KEY,  # noqa: F401  read by the tests through this module
    SYSTEM_DECISION_PAGES,  # noqa: F401  read by the tests through this module
    read_ba_history,  # noqa: F401  read by the tests through this module
    read_family_inflation,  # noqa: F401  read by the tests through this module
)
from bi.page_engineering import (  # noqa: E402
    show_diagrams_page,
    show_cicd_tab,
    show_devops_tab,
    show_monitoring_tab,
    show_architecture_page,
    show_kpi_page,
    MODEL_VIEWS,  # noqa: F401  read by the tests through this module
    MODEL_VIEW_KEY,  # noqa: F401  read by the tests through this module
    KPI_QUESTIONS,  # noqa: F401  read by the tests through this module
    KPI_COLUMNS,  # noqa: F401  read by the tests through this module
    KPI_GAP,  # noqa: F401  read by the tests through this module
    KPI_NODE_HEIGHTS,  # noqa: F401  read by the tests through this module
    build_journey_states,  # noqa: F401  read by the tests through this module
    read_database_map,  # noqa: F401  read by the tests through this module
    format_file_size,  # noqa: F401  read by the tests through this module
    read_store_sizes,  # noqa: F401  read by the tests through this module
    build_query_address,  # noqa: F401  read by the tests through this module
    read_catalog_sql,  # noqa: F401  read by the tests through this module
    find_catalog_line,  # noqa: F401  read by the tests through this module
    build_fit_frame_html,  # noqa: F401  read by the tests through this module
    build_architecture_css,  # noqa: F401  read by the tests through this module
    read_kpi_observation,  # noqa: F401  read by the tests through this module
    split_kpi_figure,  # noqa: F401  read by the tests through this module
    kpi_node_positions,  # noqa: F401  read by the tests through this module
    build_kpi_path_html,  # noqa: F401  read by the tests through this module
    build_kpi_impact_html,  # noqa: F401  read by the tests through this module
    show_kpi_tab,  # noqa: F401  read by the tests through this module
)
from bi.page_quality import (  # noqa: E402
    show_operations_page,
    QUALITY_OPEN_KEY,  # noqa: F401  read by the tests through this module
    build_rejected_rows_table,  # noqa: F401  read by the tests through this module
    show_quality_tab,  # noqa: F401  read by the tests through this module
)
from bi.app_frame import (  # noqa: E402
    CHANGE_VIEW,
    OVERVIEW_CLASS_BY_VIEW,
    get_mode,
    settle_theme,
    get_profile,
    settle_profile,
    current_view_name,
    is_public_profile,
    visible_menu_blocks,
    visible_menu_order,
    keep_profile_across_app_reloads,
    user_view_page,
    open_profile_landing,
    leave_author,
    expire_idle_author,
    is_author,
    show_profile_dialog,
    show_quality_alert,
    show_load_alert,
    build_page_address,
    keep_context,
    read_window_views,
    start_window,
    window_view_key,
    read_current_view,
    build_view_path,  # noqa: F401  read by the tests through this module
    apply_style,
    show_app_header,
    show_theme_field,
    show_language_switch,
    build_kpi_code_html,  # noqa: F401  read by the tests through this module
    build_info_card_html,  # noqa: F401  read by the tests through this module
    AUTHOR_SEEN,  # noqa: F401  read by the tests through this module
    AUTHOR_IDLE_SECONDS,  # noqa: F401  read by the tests through this module
    PROFILE_KEEPER_JS,  # noqa: F401  read by the tests through this module
    BAR_VIEWS,  # noqa: F401  read by the tests through this module
    AUTHOR_TICKETS,  # noqa: F401  read by the tests through this module
    choose_profile,  # noqa: F401  read by the tests through this module
    build_base_mode_script,  # noqa: F401  read by the tests through this module
    submit_author_code,  # noqa: F401  read by the tests through this module
    issue_author_ticket,  # noqa: F401  read by the tests through this module
    redeem_author_ticket,  # noqa: F401  read by the tests through this module
    restore_kept_history,  # noqa: F401  read by the tests through this module
    build_greenocean_logo,  # noqa: F401  read by the tests through this module
    build_hint_icon,  # noqa: F401  read by the tests through this module
    build_kpi_link,  # noqa: F401  read by the tests through this module
    show_page_bar,
    show_compact_page_header,
    build_external_link_html,  # noqa: F401  read by the tests through this module
    build_repository_link_html,
    show_view_tabs,
    find_menu_page,
    is_dark_theme,
    describe_state_source,  # noqa: F401  read by the tests through this module
    describe_late_sources,
    show_attribution,
)
from bi.app_style import (  # noqa: E402
    is_dark_surface,  # noqa: F401  read by the tests through this module
    build_sidebar_css,
    MENU_INK,  # noqa: F401  read by the tests through this module
    ACTIVITY_BAR,  # noqa: F401  read by the tests through this module
    build_theme_css,  # noqa: F401  read by the tests through this module
    build_section_colors_css,  # noqa: F401  read by the tests through this module
    build_runs_css,
)
from bi.data_access import (  # noqa: E402
    follow_published_database,
    get_database_version,
    read_latest_week,  # noqa: F401  read by the tests through this module
    current_channel,  # noqa: F401  read by the tests through this module
    scoped,  # noqa: F401  read by the tests through this module
    read_price_alerts,  # noqa: F401  read by the tests through this module
    read_place_alerts,  # noqa: F401  read by the tests through this module
    read_latest_run,
    read_latest_by_source,  # noqa: F401  read by the tests through this module
    to_chile_time,
    format_chile_time,
    parse_run_start,
    read_cached_all_variations,  # noqa: F401  read by the tests through this module
    NATIONAL_KEY,  # noqa: F401  read by the tests through this module
    read_channel_national_prices,  # noqa: F401  read by the tests through this module
    describe_product,  # noqa: F401  read by the tests through this module
    get_secret,
    get_last_github_answers,
    fetch_pipeline_runs,
    read_pipeline_runs,
    read_cached_token_expiration,
    read_lineage,
    read_flow_facts,
)
from bi.constants import (  # noqa: E402  D-541: the fixed names live in bi/constants.py
    PAGE_HOME,
    PAGE_INSIGHTS,
    PAGE_CHANNELS,  # noqa: F401  read by the tests through this module
    PAGE_STAKEHOLDERS,
    PAGE_ANALYSIS,
    BRAND_GREEN_DARK,  # noqa: F401  read by the tests through this module
    BRAND_GREEN_LIGHT,  # noqa: F401  read by the tests through this module
    PAGE_DIAGRAMS,
    PAGE_ARCHITECTURE,
    PAGE_SEASONALITY,
    PAGE_SQL,
    PAGE_RULES,
    PAGE_BA,
    BA_MONTHLY_TAB,  # noqa: F401  read by the tests through this module
    BA_HISTORY_TAB,  # noqa: F401  read by the tests through this module
    BA_TAB_OF_VIEW,
    BA_TABS,  # noqa: F401  read by the tests through this module
    RETIRED_VIEWS,
    PAGE_KPI,
    PAGE_OPERATIONS,
    PAGE_ACTIONS,
    PAGE_CONFIG,
    PAGE_RUNS,
    AUTHOR_ONLY_PAGES,
    NO_ACCESS,
    PAGE_MANUAL,
    PAGE_GLOSSARY,
    PAGE_LINKS,
    PAGE_DOCUMENTATION,
    PAGE_PRD,
    PAGE_CLOSURE,
    PAGE_SAD,
    PAGE_ADR,
    PAGE_SECURITY,
    PAGE_STACK,
    PAGE_FOLDER,
    PAGE_SOURCE_STUDY,
    PAGE_APP_MAP,
    PAGE_METHOD,
    GIT_TAB_PARAMETER,
    GIT_TAB_LOG,
    BA_TAB_PARAMETER,
    PAGE_GIT,
    PAGE_DECISION_INDEX,
    PAGE_TEST_PLAN,
    PAGE_QUALITY_PLAN,
    SECTION_RESOURCES,
    SOURCE_LINKS,
    SECTION_PROJECT,
    SECTION_KPI,
    REPORT_WINDOW,
    SECTION_LINKS,  # noqa: F401  read by the tests through this module
    SECTION_SECURITY,  # noqa: F401  read by the tests through this module
    WINDOWS,
    ROUTE,
    WINDOW_PATHS,
    WINDOW_ICONS,
    ROUTE_LEADS,
    WINDOW_OF_VIEW,
    VIEW_PARAMETER,
    COMPACT_VIEW,
    ALL_VALUES,
    PAGES,  # noqa: F401  read by the tests through this module
    HOME_PAGE,  # noqa: F401  read by the tests through this module
    PAGE_ICONS,
    PAGE_PATHS,
    TAB_GAP,  # noqa: F401  read by the tests through this module
    TAB_PIPELINE,  # noqa: F401  read by the tests through this module
    TABS_BY_PAGE,  # noqa: F401  read by the tests through this module
    PAGE_OF_TAB,
    OLD_PATHS,
    OLD_HOME_TABS,
    OLD_TAB_PAGES,
    TAB_PARAMETER,
    THEME_PARAMETER,
    THEME_STATE,  # noqa: F401  read by the tests through this module
    RETIRED_THEMES,  # noqa: F401  read by the tests through this module
    DEFAULT_THEME,  # noqa: F401  read by the tests through this module
    PROFILE_PARAMETER,
    PROFILE_STATE,  # noqa: F401  read by the tests through this module
    PROFILE_PUBLIC,  # noqa: F401  read by the tests through this module
    PROFILE_PROFESSIONAL,  # noqa: F401  read by the tests through this module
    ROLE_PARAMETER,
    ROLE_STATE,  # noqa: F401  read by the tests through this module
    ROLES,  # noqa: F401  read by the tests through this module
    ROLE_ORDER,  # noqa: F401  read by the tests through this module
    UNSPECIFIED,  # noqa: F401  read by the tests through this module
    GITHUB_CACHE_SECONDS,
    LIVE_SECONDS_WITH_TOKEN,
    LIVE_SECONDS_WITHOUT_TOKEN,
    OPERATION_RECENT_RUNS,
    PROGRESS_POLL_SECONDS,
    SECRET_GITHUB_TOKEN,
    SECRET_READ_TOKEN,
    REPORT_PARAMETER,
    REASON_TEXTS,  # noqa: F401  read by the tests through this module
    DROP_LEVELS,  # noqa: F401  read by the tests through this module
    RISE,  # noqa: F401  read by the tests through this module
    CONTEXT_BASIS_KEY,  # noqa: F401  read by the tests through this module
    BASIS_REAL,  # noqa: F401  read by the tests through this module
    PIPELINE_VIEW_KEY,  # noqa: F401  read by the tests through this module
    PIPELINE_LINEAGE,  # noqa: F401  read by the tests through this module
    ATTRIBUTION_TEXT,
    KPI_PRESENTATION,  # noqa: F401  read by the tests through this module
    HOME_LINK_PARAMETERS,  # noqa: F401  read by the tests through this module
    HOME_REGION_DONE,  # noqa: F401  read by the tests through this module
    HOME_FAMILY_DONE,  # noqa: F401  read by the tests through this module
    RUN_WINDOW_OPEN,
    ADMIN_UNLOCKED,
    FOLDER_DOCUMENTS,
    FOLDER_ORDER,
    FOLDER_ANNEXES,
    FOLDER_SHOWN,
    RETURN_CONTEXT_KEYS,
    PAGE_HISTORY,
    RETURN_TARGET,
    HISTORY_LIMIT,
    HISTORY_STATE_KEYS,
    MENU_BLOCKS,
    DOOR_PAGES,  # noqa: F401  read by the tests through this module
    MENU_BLOCK_OF_VIEW,
    SIDEBAR_TOP_LABELS,  # noqa: F401  read by the tests through this module
    SIDEBAR_LABELS,
    FOLDER_TILES,
    PRODUCT_DIRECTIONS,  # noqa: F401  read by the tests through this module
    CHANNEL_PARAMETER,  # noqa: F401  read by the tests through this module
    QUALITY_VIEW_KEY,  # noqa: F401  read by the tests through this module
    MENU_ORDER,  # noqa: F401  read by the tests through this module
    SIDEBAR_ICONS,
    WINDOW_PAGES,
)

# D-283: every text a reader sees goes through tr, which gives its English when the reader chose English.
tr = i18n.tr
# endregion


# region Style


# endregion


# region Text sections


# endregion


# region Project page


# region «Código y resultados» (C03)


# endregion


# region Report filters and cross filtering (D-069)


# endregion


# endregion


# region Alerts page


# region Contexto del precio (D-094)


# endregion


# region Control center page


def render_run_window(token):
    """The window of the manual run (D-351), redrawn by itself every few seconds while the run goes on: its state, the
    log in a fixed box with a copy button, and the two actions. Minimize hides the window and leaves the run in
    GitHub; Cancel asks first and then stops it; once it ends, «Cancelar» becomes «Cerrar»."""
    watch = st.session_state.get(run_monitor.WATCH)
    if watch is None:
        st.rerun()  # D-379: this copy of the window outlived its run (closed elsewhere): close it for good
    run_monitor.refresh(watch, token, datetime.now(timezone.utc))
    phase = watch["phase"]
    final = run_monitor.is_final(watch)
    show_run_flow(watch, get_mode())
    (
        st.success
        if phase == run_monitor.OK
        else st.error
        if phase in (run_monitor.FAILED, run_monitor.UNCONFIRMED)
        else st.info
    )(tr(run_monitor.PHASE_LABELS[phase]) if phase != run_monitor.RUNNING else run_monitor.indicator(watch))
    if phase == run_monitor.TIMEOUT:
        st.caption(tr("Pasaron {} minutos: la ventana deja de consultar.").format(run_monitor.MAX_MINUTES))
    if watch["url"]:
        st.link_button(tr("Abrir la ejecución en GitHub"), watch["url"], icon=":material/open_in_new:")
    if watch["error"]:
        st.warning(watch["error"])
    if watch["cancel_error"]:
        st.error(watch["cancel_error"], icon=":material/lock:")
    if watch["confirming"] and not final:
        st.warning(tr("¿Seguro que quieres cancelar? Esto detiene la ejecución en GitHub."))
        with st.container(horizontal=True):
            if st.button(tr("Sí, cancelar"), key="run_cancel_yes", type="primary"):
                if is_author():  # D-421: checked on the server before the one write that stops a run
                    run_monitor.cancel(watch, token)
                    logging.getLogger(__name__).info("Autor: ejecución manual cancelada")
                st.rerun(scope="fragment")
            if st.button(tr("No, seguir"), key="run_cancel_no"):
                watch["confirming"] = False
                st.rerun(scope="fragment")
    else:
        with st.container(horizontal=True):
            # D-379: closing is a callback, so it runs before anything else of the refresh and starts by cancelling the
            # window's timer (see close_run_window)
            st.button(tr("Minimizar"), key="run_minimize", icon=":material/minimize:", on_click=minimize_run_window)
            if final:
                st.button(
                    tr("Cerrar"), key="run_close", type="primary", icon=":material/close:", on_click=close_run_window
                )
            elif watch["run_id"] is not None and st.button(
                tr("Cancelar"), key="run_cancel", icon=":material/stop_circle:"
            ):
                watch["confirming"] = True
                st.rerun(scope="fragment")
    text = run_monitor.build_log(watch) or tr("Preparando la ejecución…")
    with st.container(height=260):
        st.code(text, language=None)
    palette = charts.get_palette(get_mode())
    st.iframe(
        run_monitor.build_copy_html(
            text,
            tr("Copiar"),
            tr("Copiado"),
            tr("Seleccionado"),
            ink=palette["strong_text"],
            border=palette["card_border"],
        ),
        height=44,
    )


RUN_WINDOW_KEY = "run_window"  # D-379: the fragment that holds the window's refreshing part
RUN_WINDOW_CLOSING = "run_window_closing"


def request_run_window_close():
    """D-379: close the window in two steps. The refreshing part of the window asks Streamlit for a rerun of itself every
    few seconds; if one of those requests lands while the whole page is rerunning to close the window, Streamlit never
    tells the browser the page run ended and the window stays open with dead buttons (measured: two clicks lost and two
    that took 10 s in six, with a page rerun of 3 s). So the first step reruns only the shell (keyed, with no timer of
    its own), which does not draw the refreshing part: Streamlit cancels its timer right then. The shell then reruns
    the whole page, with nothing left to fire during it."""
    st.session_state[RUN_WINDOW_CLOSING] = True
    st.rerun(RUN_WINDOW_KEY)


def minimize_run_window():
    """The window closes, the run goes on in GitHub and a small indicator in the menu brings it back (D-351)."""
    st.session_state[run_monitor.WATCH]["minimized"] = True
    request_run_window_close()


def close_run_window():
    """The run ended: forget it and close the window."""
    st.session_state.pop(run_monitor.WATCH, None)
    request_run_window_close()


RUN_PHASE_STATES = {
    run_monitor.STARTING: control.RUN_IN_PROGRESS,
    run_monitor.RUNNING: control.RUN_IN_PROGRESS,
    run_monitor.OK: control.RUN_OK,
}


def show_run_flow(watch, mode):
    """D-413: on top of the window, the live flow (D-412) focused on the run: the same model and drawing, fed by the
    window's own follow instead of asking GitHub again. Its HTML only changes when a step does, so the frame is not
    redrawn every few seconds. Under 900 px of width it waits behind «Ver el diagrama» and the steps stay first."""
    run = {
        "state": RUN_PHASE_STATES.get(watch["phase"], control.RUN_FAILED),
        "started_at": watch["started"],
        "url": watch["url"],
    }
    model = live_flow.build_model([run], watch["steps"], read_flow_facts(get_database_version(), i18n.get_language()))
    frame = live_flow.build_html(charts.get_palette(mode), model, focus=True)
    st.markdown(
        "<style>.st-key-rw_flow_narrow {display:none;} @media (max-width:900px) {.st-key-rw_flow {display:none;} "
        ".st-key-rw_flow_narrow {display:block;}}</style>",
        unsafe_allow_html=True,
    )
    with st.container(key="rw_flow"):
        st.iframe(frame, height=RUN_FLOW_HEIGHT)
    with st.container(key="rw_flow_narrow"):
        with st.popover(tr("Ver el diagrama"), icon=":material/account_tree:"):
            st.iframe(frame, height=RUN_FLOW_HEIGHT)


RUN_FLOW_HEIGHT = 330


def show_run_window_shell(token, final):
    """The window's frame (D-379): it never refreshes by itself; it draws the refreshing part, unless the window is being
    closed, in which case it reruns the whole page without drawing it."""
    if st.session_state.pop(RUN_WINDOW_CLOSING, False):
        st.rerun()
    st.fragment(render_run_window, run_every=None if final else PROGRESS_POLL_SECONDS)(token)


def show_run_indicator():
    """D-351: while the run goes on (or just ended) and its window is minimized, a small indicator above the menu says
    where it is; a click opens the window again. Only the author has a run, so only the author sees it."""
    watch = st.session_state.get(run_monitor.WATCH)
    if not watch or not watch["minimized"] or not st.session_state.get(ADMIN_UNLOCKED):
        return
    if st.sidebar.button(
        run_monitor.indicator(watch), key="run_indicator", icon=":material/sync:", type="tertiary", width="stretch"
    ):
        watch["minimized"] = False
        st.session_state[RUN_WINDOW_OPEN] = True
        st.rerun()


def reopen_run_window():
    """The window comes back when the indicator asked for it (a dialog opens from the main script, not the sidebar)."""
    if st.session_state.pop(RUN_WINDOW_OPEN, False):
        show_run_now_dialog(get_secret(SECRET_GITHUB_TOKEN))


def show_token_expiration(token):
    """«Tu token vence en X días», highlighted at 15 days or fewer (D-409). Never the token itself."""
    try:
        expiration = read_cached_token_expiration(token)
    except Exception as error:  # GitHub unreachable or the token was refused
        st.warning(f"No se pudo leer el vencimiento del token: {control.describe_github_error(error)}.")
        return
    sentence, is_urgent = control.describe_token_expiration(expiration, datetime.now(timezone.utc))
    if is_urgent:
        st.warning(sentence, icon=":material/schedule:")
    else:
        st.caption(sentence)


RELOADED_NOTICE = "panel_reloaded"


def reload_panel_data():
    """Read datos.db again (the weekly load or a manual run may have replaced it). D-421: only the Autor's session."""
    if not is_author():
        return
    st.cache_data.clear()
    st.session_state[RELOADED_NOTICE] = True


@st.dialog("Ejecutar el pipeline ahora", width="large", dismissible=False)  # D-413: room for the flow
def show_run_now_dialog(token, access_code=None):
    """The manual run, in a layer above the page (D-149). D-351: no click outside and no X closes it; it follows the
    run and offers «Minimizar» and «Cancelar». With a run already followed it shows that one instead of starting
    another. D-421: there is one key only, the Autor's entry; this window asks for none, checks on the server that the
    session is the Autor's and starts the run at once. `access_code` is no longer read."""
    if not is_author():  # D-421: whatever opened the window, only the Autor's session starts a run
        st.error(tr(NO_ACCESS), icon=":material/lock:")
        return
    if run_monitor.WATCH not in st.session_state:
        st.caption(
            tr(
                "Descarga los archivos de ODEPA, los limpia, los prueba y guarda la base, igual "
                "que la ejecución automática de cada martes. Tarda unos 5 minutos."
            )
        )
        try:
            control.start_workflow_run(token)
        except Exception as error:  # GitHub refused the request or did not answer
            st.error(
                tr("No se pudo iniciar la ejecución: {}.").format(control.describe_github_error(error)),
                icon=":material/error:",
            )
            if st.button(tr("Cerrar"), key="run_start_failed_close"):
                st.rerun()
            return
        # D-421: the record of a launched run: GitHub keeps it (event workflow_dispatch) and the server log says when.
        logging.getLogger(__name__).info("Autor: ejecución manual lanzada en GitHub Actions")
        st.session_state[run_monitor.WATCH] = run_monitor.new_watch(datetime.now(timezone.utc))
        fetch_pipeline_runs.clear()
    show_token_expiration(token)
    final = run_monitor.is_final(st.session_state[run_monitor.WATCH])
    st.fragment(lambda: show_run_window_shell(token, final), key=RUN_WINDOW_KEY)()


def show_admin_card():
    """The Autor's tools on the Operations center (D-202): the manual run (D-149), «Recargar datos» (D-396) and the way
    out. D-421: one key only, the Autor's entry; the page is the Autor's (D-420), so nothing here asks for a key, and
    each action checks the session again on the server."""
    if not is_author():
        return
    token = get_secret(SECRET_GITHUB_TOKEN)
    with st.container(key="runs_admin", horizontal=True, vertical_alignment="center", gap="small"):
        if st.button(
            "Ejecutar pipeline ahora",
            type="primary",
            icon=":material/power_settings_new:",
            key="runs_run_now",
            disabled=not token,
            help="Lanza el pipeline en GitHub Actions."
            if token
            else "Falta el token de GitHub en los secretos del panel.",
        ):
            show_run_now_dialog(token)
        st.markdown(
            '<div class="run-now-label">Ejecutar pipeline ahora</div><div class="run-now-note">'
            'Acceso del autor abierto.</div>',
            unsafe_allow_html=True,
        )
    with st.container(key="runs_tools", horizontal=True, gap="small"):
        st.button(
            "Recargar datos",
            icon=":material/refresh:",
            key="runs_reload",
            width="stretch",
            on_click=reload_panel_data,
            help="Vuelve a leer la base guardada; no ejecuta el pipeline.",
        )
        # D-409: the administration links and the state live in «Configuración», in the menu; here only the way out.
        st.button("Cerrar acceso", icon=":material/lock:", key="author_access_close", on_click=lock_author_access)
    if st.session_state.pop(RELOADED_NOTICE, False):
        latest = read_latest_run()
        st.toast(
            f"Datos recargados · base del {format_chile_time(parse_run_start(latest['started_at']))}.",
            icon=":material/check_circle:",
        )


def lock_author_access():
    """«Cerrar acceso»: the Autor's session ends, as choosing another view does (D-353)."""
    leave_author()


def show_runs_page(mode):
    """Centro de operación (D-165): the weekly run as a path of floating logos, each
    with what it does and where to act, and beside it the facts and the manual run."""
    # D-255 (the author's decision): the page opens on where each piece runs. D-267: in the page bar. D-421: the page is
    # the Autor's, so the manual run sits above the tabs with no key box.
    show_page_bar(
        PAGE_RUNS,
        "Centro de operación",
        "Dónde corre cada pieza, cómo llega un cambio a producción y el "
        "estado de cada paso de la carga semanal, con su log y dónde actuar.",
        side=show_admin_card,
        live="Las ejecuciones se leen de GitHub Actions y etl_run al abrir la página.",
    )
    tab = show_view_tabs(RUNS_VIEW_KEY, list(RUNS_VIEWS), charts.get_palette(mode))
    RUNS_VIEWS[tab](mode)  # D-360: only the tab in sight is drawn


RUNS_VIEW_KEY = "runs_view"
RUNS_VIEWS = {
    "Despliegue": lambda mode: show_devops_tab(mode),
    "Operación": lambda mode: show_runs_tab(mode),
    "CI/CD": lambda mode: show_cicd_tab(mode),
    "Monitoreo": lambda mode: show_monitoring_tab(mode),
}


@st.cache_data(ttl=github_actions.CACHE_SECONDS, show_spinner=False)
def read_actions_model(_read_token, _token):
    """What GitHub says of the workflow runs, kept two minutes so the page spares the request limit (D-339). The tokens
    are not part of the cache key (the leading underscore) and never of what is kept."""
    return github_actions.build_model(_read_token, _token)


def show_workflow_detail(entry):
    """What a workflow line shows when it opens: its latest runs, and what failed in the last failure, with the log in
    a fixed-height box that is closed until asked for (D-348)."""
    if entry["error"]:
        st.warning(entry["error"])
    st.markdown(actions_view.build_runs_table(entry["runs"]), unsafe_allow_html=True)
    failure = entry["failure"]
    if not failure:
        return
    st.markdown(f"**{tr('Último fallo')}**")
    st.link_button(tr("Abrir la ejecución en GitHub"), failure["url"], icon=":material/open_in_new:")
    if failure["error"]:
        st.warning(failure["error"])
    for job in failure["jobs"]:
        st.markdown(f'<div class="ga-failure">{actions_view.build_failure_summary(job)}</div>', unsafe_allow_html=True)
        if job["log_error"]:
            st.warning(job["log_error"])
        elif job["tail"]:
            with st.expander(tr("Últimas {} líneas del log").format(len(job["tail"])), expanded=False):
                with st.container(height=300):
                    st.code("\n".join(job["tail"]), language=None)
                # D-359: the log, ready to paste, and the failed job itself in GitHub; no diagnosis is attempted.
                with st.container(horizontal=True, vertical_alignment="center"):
                    palette = charts.get_palette(get_mode())
                    st.iframe(
                        run_monitor.build_copy_html(
                            "\n".join(job["tail"]),
                            tr("Copiar"),
                            tr("Copiado"),
                            tr("Seleccionado"),
                            ink=palette["strong_text"],
                            border=palette["card_border"],
                        ),
                        height=44,
                        width=120,
                    )
                    if job["url"]:
                        st.link_button(tr("Abrir el job en GitHub"), job["url"], icon=":material/open_in_new:")


def show_actions_page(mode):
    """«GitHub Actions» (D-339), only for the author: the latest runs of the three workflows and what failed in the
    latest one that failed. Read only: it starts, cancels and re-runs nothing. Without the author's key nothing is
    asked of GitHub: the page says it is the author's and stops."""
    if not is_author():  # D-420: the dispatch checks too; a page drawn alone (tests) checks again
        st.info(tr(NO_ACCESS), icon=":material/lock:")
        return
    show_page_bar(
        PAGE_ACTIONS,
        PAGE_ACTIONS,
        "Las últimas ejecuciones de pruebas, carga semanal y calidad, y qué falló en la última que falló. Solo lectura.",
        live="Las ejecuciones se leen de la API de GitHub Actions al abrir la página.",
    )
    model = read_actions_model(get_secret(SECRET_READ_TOKEN), get_secret(SECRET_GITHUB_TOKEN))
    st.markdown(actions_view.build_css(charts.get_palette(mode)), unsafe_allow_html=True)
    if not model["token"]:
        st.warning(tr(actions_view.NO_TOKEN_NOTICE))
    elif model["token_error"]:
        st.error(model["token_error"])
    else:
        note, urgent = actions_view.token_note(model["expiration"])
        (st.warning if urgent else st.caption)(note)
    st.markdown(compact_table.build_css(charts.get_palette(mode)), unsafe_allow_html=True)
    compact_table.show_compact_rows(
        "cr_actions",
        model["workflows"],
        actions_view.workflow_summary,
        lambda entry: actions_view.build_workflow_note(entry),
        signature="actions",
        after_detail=show_workflow_detail,
    )
    st.caption(
        tr("Leído a las {}; se vuelve a leer cada 2 minutos.").format(actions_view.format_time(model["read_at"])[-5:])
    )


@st.cache_data(ttl=300, show_spinner=False)
def read_configuration_model(_token, _read_token):
    """What «Configuración» asks GitHub (D-409), kept five minutes: the date of each token (asked with that token, as
    its own warning does), the latest test runs on main and the report branches (with the read-only token only, D-397).
    The tokens are not part of the cache key (the leading underscore) and never of what is kept: only dates, states and
    error sentences."""
    model = {"tokens": {}, "runs": [], "runs_error": None, "branches": None}
    for name, token in ((SECRET_GITHUB_TOKEN, _token), (SECRET_READ_TOKEN, _read_token)):
        expiration, error = None, None
        if token:
            try:
                expiration = control.read_token_expiration(token)
            except Exception as failure:  # GitHub unreachable or the token refused
                error = github_actions.redact(control.describe_github_error(failure), (_token, _read_token))
        model["tokens"][name] = {"present": bool(token), "expiration": expiration, "error": error}
    try:
        model["runs"] = github_actions.list_runs("pruebas.yml", _read_token or None, 10)
    except Exception as failure:
        model["runs_error"] = github_actions.redact(control.describe_github_error(failure), (_token, _read_token))
    try:
        model["branches"] = github_actions.count_branches(configuration.REPORT_BRANCH, _read_token or None)
    except Exception:
        model["branches"] = None
    return model


@st.dialog("¿Qué pasó?", width="large")
def show_case_dialog(case):
    """One case of the runbook (MANUAL 8.1): its steps in order, each automatic or manual, with its link. A page of the
    panel opens as a page link, in the same visit: a reload would close the author's session."""
    st.markdown(f"<h3 class='cf-case-title'>{html.escape(case['name'])}</h3>", unsafe_allow_html=True)
    for index, step in enumerate(case["steps"]):
        with st.container(key=f"cf_step_{index}", horizontal=True, vertical_alignment="center"):
            st.markdown(configuration.build_step_html(step), unsafe_allow_html=True, width="stretch")
            link = step["link"]
            view = find_menu_page(link["target"]) if link and link["kind"] == "view" else None
            window = WINDOW_PAGES.get(WINDOW_OF_VIEW.get(view)) if view else None
            if window:  # absent when a test draws the page alone
                st.page_link(
                    window,
                    label=link["text"],
                    icon=SIDEBAR_ICONS.get(view, PAGE_ICONS.get(view)),
                    query_params=keep_context() | {VIEW_PARAMETER: view},
                    width="content",
                )


def show_configuration_page(mode):
    """«Configuración» (D-409), only for the author: on one screen, the state of what keeps the app running, one icon
    per case of the runbook with its steps, and the maintenance tasks with their date. It replaces «Enlaces del
    autor». It reads the runbook, the served database and GitHub; it never shows the value of a token."""
    if not is_author():  # D-420: the dispatch checks too; a page drawn alone (tests) checks again
        st.info(tr(NO_ACCESS), icon=":material/lock:")
        return
    show_page_bar(
        PAGE_CONFIG,
        PAGE_CONFIG,
        "La consola del autor: el estado de lo que mantiene la app, qué hacer en cada caso y el mantenimiento. "
        "Nunca muestra el valor de un token.",
    )
    st.markdown(configuration.build_css(charts.get_palette(mode)), unsafe_allow_html=True)
    now = datetime.now(timezone.utc)
    model = read_configuration_model(get_secret(SECRET_GITHUB_TOKEN), get_secret(SECRET_READ_TOKEN))
    labels = {name: configuration.token_label(name) for name in (SECRET_GITHUB_TOKEN, SECRET_READ_TOKEN)}
    latest = read_latest_run()
    runs, _ = read_pipeline_runs()
    failed = control.latest_load_failure(runs)
    reports, _, _ = quality_method.read_page()
    cards = [
        configuration.token_card(
            name.lower(), labels[name].capitalize(), entry["present"], entry["expiration"], entry["error"], now
        )
        for name, entry in model["tokens"].items()
    ] + [
        configuration.load_card(parse_run_start(latest["started_at"]), failed["started_at"] if failed else None, now),
        configuration.report_card(reports[-1] if reports else None, now.date()),
        configuration.ci_card(model["runs"], model["runs_error"]),
        configuration.sources_card(
            describe_late_sources(latest["message"] if latest["status"] == etl.STATUS_LOADED else "")
        ),
    ]
    page = st.container(key="config_page")  # one screen at 1440 x 790 and 1280 x 800 (RNF-06): tighter gaps
    page.markdown(
        f'<p class="cf-band">{html.escape(configuration.t("Estado", "State"))}</p>'
        + configuration.build_cards_html(cards)
        + f'<p class="cf-band cf-next">{html.escape(configuration.t("¿Qué pasó?", "What happened?"))}</p>',
        unsafe_allow_html=True,
    )
    cases = configuration.read_cases()
    with page.container(key="config_cases", horizontal=True):
        for index, case in enumerate(cases):
            if st.button(case["name"], icon=f":material/{case['icon']}:", key=f"config_case_{index}", width="stretch"):
                show_case_dialog(case)
    tokens = [(labels[name], entry["present"], entry["expiration"]) for name, entry in model["tokens"].items()]
    tasks = configuration.maintenance(
        tokens, model["branches"], configuration.read_schedule(), now.date(), configuration.years_listed()
    )
    with page.container(key="config_lower"):
        left, right = st.columns([1, 1.45], gap="small")
        left.markdown(
            f'<p class="cf-band">{html.escape(configuration.t("Mantenimiento", "Maintenance"))}</p>'
            + configuration.build_maintenance_html(tasks),
            unsafe_allow_html=True,
        )
        right.markdown(
            f'<p class="cf-band">{html.escape(configuration.t("Guía de GitHub", "GitHub guide"))}</p>'
            + configuration.build_guide_html(configuration.read_guide()),
            unsafe_allow_html=True,
        )


def show_security_page(mode):
    """The security architecture as a threat model (D-200, D-249): threat, mitigation, verification, asset, and the
    loop of continuous improvement."""
    show_page_bar(
        PAGE_SECURITY,
        SIDEBAR_LABELS[PAGE_SECURITY],
        "Qué amenaza al sistema, qué lo mitiga, qué prueba lo "
        "verifica en cada push y cómo se mejora. El código es público: la seguridad no depende de "
        "esconderlo, sino de las claves, que nunca aparecen.",
    )  # D-398: the test plan opens from «Documentos», not from the header
    # D-277: the drawing keeps its proportion and is never taller than what the window leaves.
    st.markdown(
        '<style>.st-key-sec_frame iframe {display:block; margin:0 auto; '
        f'max-width:calc((100vh - 240px) * {security_map.WIDTH} / {security_map.HEIGHT});}}</style>',
        unsafe_allow_html=True,
    )
    with st.container(key="sec_frame"):
        st.iframe(security_map.build_security_html(charts.get_palette(mode)), height="content")


def show_runs_tab(mode):
    """The stage, refreshed by itself every few seconds while a run is in progress."""
    st.markdown(build_runs_css(mode), unsafe_allow_html=True)
    runs, _ = read_pipeline_runs()
    live = bool(runs) and runs[0]["state"] == control.RUN_IN_PROGRESS
    st.fragment(
        lambda: show_operation_center(mode, live),
        run_every=(LIVE_SECONDS_WITH_TOKEN if get_secret(SECRET_GITHUB_TOKEN) else LIVE_SECONDS_WITHOUT_TOKEN)
        if live
        else None,
    )()


@st.cache_data(ttl=GITHUB_CACHE_SECONDS, show_spinner=False)
def fetch_run_step_details(run_id):
    """Steps of one run with their log addresses. A failure raises, and is not cached."""
    return control.list_run_step_details(run_id, get_secret(SECRET_GITHUB_TOKEN))


def read_operation_runs(live):
    """(runs, step details of the latest, why GitHub failed or ""). While a run is in
    progress GitHub is asked directly, not through the five-minute cache."""
    if live:
        fetch_pipeline_runs.clear()
        fetch_run_step_details.clear()
    runs, error_text = read_pipeline_runs()
    if not runs:
        return runs, {}, error_text
    last_answers = get_last_github_answers()
    try:
        details = fetch_run_step_details(runs[0]["id"])
    except Exception as error:  # GitHub unreachable or refused
        # The traceback goes to the server log (Streamlit Cloud: «Manage app»).
        logging.getLogger(__name__).exception(
            "Centro de operación: los pasos de la ejecución %s no se pudieron leer", runs[0]["id"]
        )
        details = last_answers.get(("details", runs[0]["id"]), {})
        return runs, details, error_text or control.describe_github_error(error)
    last_answers[("details", runs[0]["id"])] = details
    return runs, details, error_text


@st.cache_data(show_spinner=False)
def read_published_figures(database_version):
    """Last week, prices and weeks of the published database."""
    return queries.run_sql(
        "SELECT max(week_start) AS last_week, count(*) AS prices, count(DISTINCT week_start) AS weeks FROM weekly_price"
    ).iloc[0]


def build_operation_fact(label, value, note=""):
    return (
        f'<div class="oc-fact"><span class="oc-fact-label">{html.escape(label)}</span>'
        f'<span class="oc-fact-value">{html.escape(value)}</span>'
        f'<span class="oc-fact-note">{note}</span></div>'
    )


def build_operation_facts(latest_load, published, now):
    """Next run, published data and latest load: what to know before acting."""
    next_run = control.calculate_next_scheduled_run(now)
    hours = int((next_run - now).total_seconds() // 3600)
    wait = f"faltan {hours} h" if hours < 48 else f"faltan {hours // 24} días"
    last_week = pd.Timestamp(published["last_week"])
    return (
        build_operation_fact(
            "Próxima ejecución", f"{to_chile_time(next_run):%d-%m · %H:%M}", f"automática, cada martes · {wait}"
        )
        + build_operation_fact(
            "Datos publicados",
            f"Semana {weeks.week_range(last_week, year=True)}",
            f"{charts.format_thousands(published['prices'])} precios · "
            f"{charts.format_thousands(published['weeks'])} semanas",
        )
        + build_operation_fact(
            "Última carga",
            f"{charts.format_thousands(latest_load['rows_loaded'])} filas",
            f"de {charts.format_thousands(latest_load['rows_read'])} leídas · "
            f"{charts.format_thousands(latest_load['rows_rejected'])} rechazadas",
        )
    )


def build_recent_runs_html(runs):
    """The latest runs, one line each with its colour and a link to its logs."""
    colors = {
        control.RUN_OK: charts.STATUS_COLORS["good"],
        control.RUN_FAILED: charts.STATUS_COLORS["critical"],
        control.RUN_IN_PROGRESS: charts.STATUS_COLORS["running"],
    }
    words = {
        control.RUN_OK: "correcta",
        control.RUN_FAILED: "falló",
        control.RUN_IN_PROGRESS: "en curso",
        control.RUN_SIMULATED_FAILURE: "falla simulada",
    }

    def describe(run):
        return (
            f'{to_chile_time(run["started_at"]):%d-%m %H:%M} · {run["trigger"].lower()} · {words.get(run["state"], "")}'
        )

    # One line each; a narrow column cuts it with «…» and the pointer shows it whole (D-271).
    lines = "".join(
        f'<a class="oc-run" href="{html.escape(run["url"], quote=True)}" target="_blank" rel="noopener noreferrer" '
        f'title="{html.escape(describe(run), quote=True)}">'
        f'<span class="oc-dot" style="background:{colors.get(run["state"], charts.STATUS_COLORS["unknown"])}"></span>'
        f'{html.escape(describe(run))} ↗</a>'
        for run in runs[:OPERATION_RECENT_RUNS]
    )
    return f'<div class="oc-runs"><span class="oc-fact-label">Últimas ejecuciones</span>{lines}</div>'


def show_operation_center(mode, live=False):
    palette = charts.get_palette(mode)
    runs, details, error_text = read_operation_runs(live)
    latest_load = read_latest_run()
    states = operation_center.build_step_states(
        runs[0] if runs else None, details, latest_load["status"] == etl.STATUS_LOADED
    )
    unlocked = bool(st.session_state.get(ADMIN_UNLOCKED))
    # D-271: the latest runs join the facts in the side column, and the path never grows taller than the window
    # leaves, so the whole tab fits one screen.
    stage_column, side_column = st.columns([2.4, 1], gap="large")
    with stage_column, st.container(key="oc_stage_column"):
        st.iframe(operation_center.build_stage_html(palette, states, unlocked), height="content")
    with side_column:
        if error_text:
            st.caption(
                tr("GitHub no respondió ({}); {}.").format(error_text, tr("se muestra la última respuesta guardada"))
            )
        st.markdown(
            build_operation_side_css(palette)
            + build_operation_facts(
                latest_load, read_published_figures(get_database_version()), datetime.now(timezone.utc)
            )
            + (build_recent_runs_html(runs) if runs else ""),
            unsafe_allow_html=True,
        )


def build_operation_side_css(palette):
    return f"""<style>
    /* D-271: the path keeps its proportion (740 × 640) and takes the height the window leaves: the tabs above, the
       short footer below. Its frame follows the drawing's height, so a narrower path is also a shorter page. */
    .st-key-oc_stage_column iframe {{display:block; margin:0 auto; max-width:max(420px, calc((100vh - 270px) * 740 / 640));}}
    /* On a tablet the facts go under the path, which then takes the whole width. */
    @media (max-width:1100px) {{
        [data-testid="stHorizontalBlock"]:has(.st-key-oc_stage_column) {{flex-wrap:wrap !important;}}
        [data-testid="stHorizontalBlock"]:has(.st-key-oc_stage_column) > [data-testid="stColumn"] {{flex:1 1 100% !important; min-width:100% !important;}}
    }}
    .oc-runs .oc-run {{max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:block;}}
    .oc-runs .oc-run .oc-dot {{vertical-align:middle;}}
    .oc-fact {{display:flex; flex-direction:column; gap:1px; padding:10px 0;
        border-bottom:1px solid {palette['card_border']};}}
    .oc-fact-label {{font-size:.68rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase;
        color:{palette['reference']};}}
    .oc-fact-value {{font-size:1.15rem; font-weight:600; color:{palette['strong_text']};
        font-variant-numeric:tabular-nums;}}
    .oc-fact-note {{font-size:.8rem; color:{palette['text']};}}
    .oc-runs {{display:flex; flex-wrap:wrap; align-items:center; gap:4px 20px; padding-top:10px;
        border-top:1px solid {palette['card_border']};}}
    .oc-runs .oc-fact-label {{flex-basis:100%;}}
    .oc-run {{display:flex; align-items:center; font-size:.82rem; color:{palette['text']} !important;
        text-decoration:none !important; padding:2px 0;}}
    .oc-run:hover {{color:{palette['strong_text']} !important;}}
    .oc-dot {{display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; flex-shrink:0;}}
    .st-key-runs_admin {{padding:14px 0 6px;}}
    .st-key-runs_admin .st-key-runs_run_now {{margin:0 6px 0 4px; flex:none;}}
    .st-key-runs_admin .run-now-label, .st-key-runs_admin .run-now-note {{text-align:left; margin:0;}}
    </style>"""


# endregion


# region Architecture page


# endregion


# region Data quality page


# endregion


# region Links page
def build_github_icon_svg(size=22):
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="currentColor" '
        f'aria-hidden="true">{architecture.brand_icons.logo_body("github")}</svg>'
    )


def show_links_page(mode):
    """The repository is the single destination for commits, executions and full
    documents (D-106): one hero with the repository, then its three uses —
    automatización, trazabilidad, documentación — each item opening GitHub in a new
    tab (D-116) with its own copy button. ODEPA and the INE live in «Fuentes» (D-118). D-500: only for the Autor."""
    if not is_author():
        st.info(tr(NO_ACCESS), icon=":material/lock:")
        return
    # Our own trusted markup, in its own frame: st.html sanitises the SVG gradients,
    # filters and buttons the page is made of.
    st.iframe(
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        '<body style="margin:0;background:transparent">'
        + github_page.build_github_page_html(mode)
        + github_page.GITHUB_PAGE_SCRIPT
        + '</body></html>',
        height="content",
    )


# endregion


# region Project documents (D-151)
PROJECT_DOCUMENTS = {
    PAGE_PRD: ("PRD.md", "Qué resuelve el producto, para quién y con qué requisitos."),
    PAGE_CLOSURE: ("ACTA_DE_CIERRE.md", "Cómo empezó el proyecto, qué se aprendió y a quién sirve."),
    PAGE_SAD: ("SAD.md", "Cómo está construido, cómo corre cada semana, dónde viven sus datos y cómo puede crecer."),
    PAGE_ADR: ("ADR.md", "Las decisiones de arquitectura que más pesan: contexto, decisión, opciones y consecuencias."),
    PAGE_MANUAL: ("MANUAL.md", "Cómo operar el proyecto y resolver sus fallas."),
    PAGE_DECISION_INDEX: (
        "INDICE_DECISIONES.md",
        "Las decisiones que cambian la arquitectura, los datos, la seguridad o la operación, por tema.",
    ),
    PAGE_TEST_PLAN: (
        "PLAN_PRUEBAS.md",
        "Qué se prueba, quién participa en la seguridad y con qué criterios se acepta un cambio.",
    ),
    PAGE_GLOSSARY: ("GLOSARIO.md", "Las siglas y los términos del panel y de los documentos."),
    PAGE_QUALITY_PLAN: (
        "PLAN_DE_CALIDAD.md",
        "Qué calidad cuida el proyecto, cómo la mide, quién decide y qué pasa cuando algo falla.",
    ),
}
FOLDER_VIEW_KEY = "folder_view"
DOCUMENT_DIAGRAM = re.compile(r"^\[\[diagrama:(\w+)\]\]\s*$", re.MULTILINE)
# D-247: a document points to the page of the panel where a view lives, instead of copying it: [[vista:Modelo de datos]].
DOCUMENT_VIEW = re.compile(r"\[\[vista:([^\]]+)\]\]")


def build_print_address(page):
    """The address that opens a document and prints it (D-248), on a white sheet from any theme (D-280)."""
    path, _, query = build_page_address(page).partition("?")
    parameters = {key: values[0] for key, values in parse_qs(query).items()}
    reader = get_mode()
    parameters.update({THEME_PARAMETER: PRINT_THEME if is_dark_theme(reader) else reader, PRINT_PARAMETER: reader})
    return f"{path}?{urlencode(parameters)}"


def read_folder_files():
    """Every main document of the folder as the folder shows it, read from its file; the annexes are left out (D-536)."""
    files = []
    for page, family in FOLDER_DOCUMENTS:
        if page in FOLDER_ANNEXES:
            continue
        path = i18n.document_path(PROJECT_DOCUMENTS[page][0])
        files.append(
            documents_folder.describe(path.read_text(encoding="utf-8"))
            | {
                "page": page,
                "family": family,
                "open": build_page_address(page),
                "pdf": build_print_address(page),
                # D-500: only the Autor gets the link to the file in the repository
                "github": project.build_github_url(path.relative_to(project.PROJECT_DIR).as_posix())
                if is_author()
                else "",
            }
        )
    return files


def show_documents_folder(mode):
    """«Documentos del proyecto» (D-282, D-533): the folder of docs/, as files in a grid or a list."""
    files = read_folder_files()
    # D-288: the folder opens as a list, like a file explorer in detail view.
    st.session_state.setdefault(FOLDER_VIEW_KEY, documents_folder.VIEW_LIST)
    show_page_bar(
        PAGE_FOLDER,
        PAGE_FOLDER,
        "Los documentos del proyecto, leídos de docs/: cada uno se abre aquí, se imprime como PDF o se lee en GitHub.",
        side=lambda: st.segmented_control(
            tr("Vista de la carpeta"),
            [documents_folder.VIEW_GRID, documents_folder.VIEW_LIST],
            format_func=tr,
            key=FOLDER_VIEW_KEY,
            label_visibility="collapsed",
            width="content",
        ),
    )
    st.markdown(documents_folder.build_css(charts.get_palette(mode)), unsafe_allow_html=True)
    view = st.session_state.get(FOLDER_VIEW_KEY) or documents_folder.VIEW_LIST
    st.markdown(documents_folder.build_folder_html(files, view), unsafe_allow_html=True)


def show_source_study(mode):
    """«Análisis de la fuente de datos» (D-533): the notebook that studies ODEPA's raw wholesale file. Only the one in the
    language of the visit is listed (D-535); it opens here, read only, with the outputs its file keeps, and downloads."""
    files = source_study.read_files()
    show_page_bar(
        PAGE_SOURCE_STUDY,
        PAGE_SOURCE_STUDY,
        "El estudio del archivo mayorista de ODEPA: cada anomalía encontrada, con su decisión y su solución.",
    )
    palette = charts.get_palette(mode)
    st.markdown(documents_folder.build_css(palette) + source_study.build_css(palette), unsafe_allow_html=True)
    language = i18n.get_language()
    opened = next(
        (
            file
            for file in files
            if file["language"] == language and st.query_params.get(source_study.NOTEBOOK_PARAMETER) == file["language"]
        ),
        None,
    )
    if opened:
        show_notebook(opened)
        return
    st.markdown(source_study.build_head_html(language), unsafe_allow_html=True)
    # Only the notebook of the visit's language is listed (D-443, D-535); the head line names the other one.
    for file in (file for file in files if file["language"] == language):
        address = build_page_address(PAGE_SOURCE_STUDY) + f"&{source_study.NOTEBOOK_PARAMETER}={file['language']}"
        with st.container(key=f"notebook_row_{file['language']}", horizontal=True, vertical_alignment="center"):
            st.markdown(source_study.build_file_html(file, address), unsafe_allow_html=True, width="stretch")
            show_notebook_download(file)


def show_notebook_download(file):
    st.download_button(
        tr("Descargar"),
        file["path"].read_bytes(),
        file_name=file["file"],
        mime="application/x-ipynb+json",
        key=f"notebook_download_{file['language']}",
        icon=":material/download:",
        width="content",
    )


def show_notebook(file):
    """One notebook, read only: its texts, its code and the outputs its file keeps; the panel never runs it."""
    with st.container(key="notebook_path", horizontal=True, vertical_alignment="center"):
        st.markdown(
            source_study.build_path_html(build_page_address(PAGE_SOURCE_STUDY), tr(PAGE_SOURCE_STUDY), file["file"]),
            unsafe_allow_html=True,
            width="stretch",
        )
        show_notebook_download(file)
    # The notebook is already in the visit's language: its texts and outputs are drawn verbatim, never translated.
    for cell in source_study.read_notebook(file["path"])["cells"]:
        source = source_study.text_of(cell["source"])
        if cell["cell_type"] == "markdown":
            st.markdown(i18n.Verbatim(source))
            continue
        st.code(source, language="python")
        outputs = source_study.build_output_html(cell.get("outputs", []))
        if outputs:
            st.html(i18n.Verbatim(outputs))


def build_folder_path_html(title):
    """«Documentos / PRD»: the thin path of a document, back to its folder (D-282)."""
    return (
        f'<nav class="doc-path" aria-label="{tr("Ruta")}"><a href="{html.escape(build_page_address(PAGE_FOLDER), quote=True)}" '
        f'target="_self">{tr(PAGE_FOLDER)}</a><i>/</i><span>{html.escape(tr(SIDEBAR_LABELS.get(title, title)))}</span></nav>'
    )


DOCUMENT_LINK = re.compile(r"\]\((?:\.\./[a-z]+/)?([A-Z_]+\.md)(#[^)]*)?\)")  # D-381: «../negocio/PRD.md» too
HEADING = re.compile(r"^(#{2,4}) (.+)$", re.MULTILINE)


def heading_anchor(text):
    """The anchor GitHub gives a heading, so an index link works the same in GitHub and in the panel (D-279)."""
    return re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")


REPOSITORY_LINK = re.compile(r"\[([^\]]+)\]\(https://github\.com/[^)]*\)")


def link_document_views(text):
    """Each [[vista:…]] of a document as a link to its page in the panel; each link to another document of docs/
    to that document's page, or to GitHub when it has none; each heading with the anchor its index points to."""
    text = DOCUMENT_VIEW.sub(
        lambda match: (
            f"[{match.group(1)}]({build_page_address(find_menu_page(match.group(1)))})"
            if find_menu_page(match.group(1))
            else match.group(1)
        ),
        text,
    )
    pages = {filename: title for title, (filename, _) in PROJECT_DOCUMENTS.items()}

    def document_address(match):
        filename, anchor = match.group(1), match.group(2) or ""
        address = (
            build_page_address(pages[filename])
            if filename in pages
            else project.build_github_url(
                f"docs/{i18n.DOCUMENT_FOLDERS.get(filename, '')}/{filename}".replace("docs//", "docs/")
            )
        )
        return f"]({address}{anchor})"

    text = DOCUMENT_LINK.sub(document_address, text)
    if not is_author():  # D-500: for anyone else, a link to GitHub reads as plain text, in every document
        text = REPOSITORY_LINK.sub(r"\1", text)
    return HEADING.sub(
        lambda match: f'<a id="{heading_anchor(match.group(2))}"></a>\n\n{match.group(1)} {match.group(2)}', text
    )


def show_document_diagram(name, mode):
    """One marker of a document: the document views and the security map in their own frame
    (hover tips and gradients need it, D-205), the live diagrams inline. D-455: the interest map is drawn inline, with the
    panel's icon font."""
    if name in doc_diagrams.INLINE:
        st.markdown(doc_diagrams.INLINE[name](mode), unsafe_allow_html=True)
        return
    st.iframe(doc_diagrams.DOC_DIAGRAMS[name](mode), height=doc_diagrams.HEIGHTS[name])


# D-248: the downloadable document is the page itself, printed by the browser: the same text, diagrams and order.
# Only the document pages carry this stylesheet; it hides the menu and the navigation and lets the page run on.
PRINT_DOCUMENT_CSS = """<style>
@media print {
  /* D-358: every sheet says its number, and the cover has a sheet of its own. */
  @page { size: A4; margin: 12mm 12mm 16mm;
    @bottom-center { content: "__PAGE__ " counter(page) " __OF__ " counter(pages); font: 9pt -apple-system, "Segoe UI", sans-serif; color: #5f6b7c; } }
  .doc-cover { break-after: page; }
  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
  .st-key-app_header, .st-key-doc_actions, .st-key-compact_footer, .st-key-route_footer, .doc-path,
  [data-testid="stElementContainer"]:has(.page-lineage), [data-testid="stCaptionContainer"],
  hr { display: none !important; }
  html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
    height: auto !important; min-height: 0 !important; overflow: visible !important; position: static !important; }
  /* The page is laid out at its screen width and scaled to the sheet, so the paper shows the same lines as the screen. */
  [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: none !important; zoom: 0.86; }
  .st-key-project_document { max-width: none !important; margin: 0 !important; box-shadow: none !important;
    padding: 40px 50px 44px !important; }
  [data-testid="stIFrame"], figure, tr { break-inside: avoid; }
  thead { display: table-header-group; }
  h2, h3 { break-after: avoid; }
}
</style>"""
# D-280: the PDF is always a white sheet. From a dark theme the button reopens the page in the light theme with
# «imprimir=<theme>», which prints it and comes back to the reader's theme.
PRINT_PARAMETER = "imprimir"
PRINT_THEME = charts.MODE_CORPORATE
PRINT_BUTTON_HTML = (
    buttons.build_button_html("Imprimir o guardar como PDF", icon="print", variant="primary", extra="doc-print")
    + r"""
<script>
document.querySelectorAll(".doc-print").forEach((button) => { button.onclick = () => {
  const light = "__LIGHT__";
  if (!light) { window.print(); return; }
  const url = new URL(window.location.href);
  url.searchParams.set("imprimir", url.searchParams.get("tema") || "");
  url.searchParams.set("tema", light);
  if (window.__goRemember) window.__goRemember();  // D-357: the app reloads, the visit keeps its view
  window.location.assign(url.toString());
}; });
</script>"""
)
AUTO_PRINT_SCRIPT = r"""<script>
(() => {
  if (window.__documentPrinted) return;
  window.__documentPrinted = true;
  window.addEventListener("afterprint", () => {
    const url = new URL(window.location.href);
    url.searchParams.set("tema", url.searchParams.get("imprimir"));
    url.searchParams.delete("imprimir");
    if (window.__goRemember) window.__goRemember();
    window.location.replace(url.toString());
  }, { once: true });
  // D-427: print only the document: wait until «Elige tu vista» is gone (the view comes back a moment after the load).
  let tries = 0;
  const ready = () => {
    if (!document.querySelector(".profile-ask")) { window.print(); return; }
    tries += 1;
    if (tries > 40) return;  // after 20 s with the window still open, nothing is printed (no less-than sign: D-280)
    setTimeout(ready, 500);
  };
  setTimeout(ready, 3000);
})();
</script>"""


def build_print_button_html(mode):
    """The print button; from a dark theme it prints the light version of the page (D-280)."""
    return PRINT_BUTTON_HTML.replace("Imprimir o guardar como PDF", tr("Imprimir o guardar como PDF")).replace(
        "__LIGHT__", PRINT_THEME if is_dark_theme(mode) else ""
    )


def show_document_actions(mode, source_label, source_url):
    """The document's source in GitHub and the button that prints the page itself (D-248)."""
    with st.container(
        key="doc_actions", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
    ):
        st.markdown(
            '<div class="doc-source">' + build_repository_link_html(source_label, source_url, "secondary") + '</div>',
            unsafe_allow_html=True,
        )
        st.html(build_print_button_html(mode), unsafe_allow_javascript=True)
    st.markdown(
        PRINT_DOCUMENT_CSS.replace("__PAGE__", tr("Página")).replace("__OF__", tr("de")), unsafe_allow_html=True
    )
    if st.query_params.get(PRINT_PARAMETER) in charts.THEMES:
        st.html(AUTO_PRINT_SCRIPT, unsafe_allow_javascript=True)


@st.cache_data(show_spinner=False)
def read_stack_figures(database_version):
    """The three figures of «Stack y evidencia», once per database."""
    return stack_page.read_figures()


STACK_VIEWS = ["Herramientas", "Flujo del sistema en vivo"]
STACK_VIEW_KEY = "stack_view"


def flow_fetch(read_token):
    """D-412: the weekly workflow's latest runs and the steps of the one to show (in progress, or the latest that
    ended), with the read-only token only (D-397) or none. Three GETs; an error is a sentence, never a crash."""
    try:
        runs = github_actions.list_runs("semanal.yml", read_token or None, 5)
        shown = next(
            (run for run in runs if run["state"] == control.RUN_IN_PROGRESS),
            next((run for run in runs if run["state"] != control.RUN_IN_PROGRESS), None),
        )
        steps = run_monitor.read_steps(run_monitor.fetch_run(shown["id"], read_token or None)["jobs"]) if shown else []
        return runs, steps, None
    except Exception as error:  # GitHub unreachable or the request limit spent: the diagram stays, without state
        return [], [], control.describe_github_error(error)


# D-483: each cached answer is kept per language, because a failure is kept as a sentence in the visitor's language
@st.cache_data(ttl=30, show_spinner=False)
def read_flow_live(_read_token, language=None):
    """While a run goes on: asked again every 30 s."""
    return flow_fetch(_read_token)


@st.cache_data(ttl=120, show_spinner=False)
def read_flow_with_token(_read_token, language=None):
    return flow_fetch(_read_token)


@st.cache_data(ttl=600, show_spinner=False)
def read_flow_without_token(_read_token, language=None):
    """Without a token GitHub allows 60 requests an hour, shared: the answer is kept ten minutes."""
    return flow_fetch(_read_token)


def read_flow_model():
    """The model of the live flow: the slow answer first; while a run goes on, the 30-second one."""
    read_token = get_secret(SECRET_READ_TOKEN)
    language = i18n.get_language()
    runs, steps, error = (read_flow_with_token if read_token else read_flow_without_token)(read_token, language)
    if runs and runs[0]["state"] == control.RUN_IN_PROGRESS:
        runs, steps, error = read_flow_live(read_token, language)
    facts = read_flow_facts(get_database_version(), i18n.get_language())
    model = live_flow.build_model(runs, steps, facts)
    if not is_author():  # D-500: the link to the run opens the author's repository
        model["run_url"] = None
    return model, error


def show_live_flow(mode):
    """«Flujo del sistema en vivo» (D-412), for every view: the real architecture with the latest real run; while a run
    goes on it follows its step, asking again every 30 s. Only the author gets the way to the logs."""
    model, error = read_flow_model()
    st.markdown(
        '<span class="fit-flujo" aria-hidden="true"></span><style>'
        '[data-testid="stElementContainer"]:has(.fit-flujo) + [data-testid="stElementContainer"],'
        '[data-testid="stElementContainer"]:has(.fit-flujo) + [data-testid="stElementContainer"] iframe '
        "{height:max(calc(100vh - 330px), 380px) !important; flex:none !important; min-height:0 !important;}"
        "</style>",
        unsafe_allow_html=True,
    )
    st.iframe(live_flow.build_html(charts.get_palette(mode), model), height=600)
    notes = [error] if error else []
    if st.session_state.get(ADMIN_UNLOCKED):  # D-412: the logs are the author's, in «GitHub Actions»
        notes.append(tr("Los logs de cada paso están en «GitHub Actions», solo para el autor."))
    if notes:
        st.caption(" · ".join(notes))


def show_stack_page(mode):
    """«Stack y evidencia» (D-211, D-266): the stack as an architecture diagram; each tool explains itself and
    opens the page where it works. D-412: its second view is the live flow of the whole system."""
    view_holder = {}

    def choose_view():
        view_holder["view"] = (
            st.segmented_control(
                tr("Vista"),
                STACK_VIEWS,
                default=STACK_VIEWS[0],
                format_func=tr,
                key=STACK_VIEW_KEY,
                label_visibility="collapsed",
            )
            or STACK_VIEWS[0]
        )

    show_page_bar(
        PAGE_STACK,
        PAGE_STACK,
        "Qué hace cada herramienta, cuándo actúa y con cuáles se conecta.",
        side=choose_view,
        live="weekly_price, dbt_node y etl_run se cuentan en la Base DuckDB al abrir la página; las pruebas de pytest, en "
        "la carpeta tests/.",
    )  # D-398: «Mapa de la app» is the next line of the menu, not a link of the header
    if view_holder.get("view") == STACK_VIEWS[1]:
        model_running = read_flow_model()[0]["mode"] == "live"
        st.fragment(show_live_flow, run_every=30 if model_running else None)(mode)
        return
    addresses = {page: build_page_address(page) for *_, page in stack_page.STACK}
    st.html(
        stack_page.build_stack_html(charts.get_palette(mode), read_stack_figures(get_database_version()), addresses)
    )


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


def show_rules_page(mode):
    """«Reglas de transformación» (D-523): what the pipeline does to the data and why, each rule with the problem of the
    source it solves and what would happen without it. It runs in the browser, in its own frame, as «Cambios e
    incidentes»; only the Autor gets the code as links to the repository (D-500)."""
    show_page_bar(
        PAGE_RULES,
        PAGE_RULES,
        "Qué le hacemos a los datos de ODEPA y del INE, y por qué: cada regla con el problema que resuelve y lo que "
        "pasaría sin ella.",
    )
    st.markdown(
        '<style>.st-key-rules_frame, .st-key-rules_frame [data-testid="stElementContainer"], .st-key-rules_frame iframe '
        '{ height:max(calc(100vh - 218px), 480px) !important; }</style>',
        unsafe_allow_html=True,
    )
    with st.container(key="rules_frame"):
        st.iframe(
            transformation_rules.build_page_html(charts.get_palette(mode), i18n.get_language(), is_author()),
            height=480,
        )


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

            def open_report_button(report):
                if st.button(
                    tr("Abrir el informe o su PDF"),
                    key=f"cr_reports_open_{quality_metrics.report_ref(report)}",
                    icon=":material/description:",
                ):
                    show_quality_report_dialog(quality_metrics.report_ref(report))

            compact_table.show_compact_rows(
                "cr_reports",
                sorted(shown, key=lambda item: -item["numero"]),
                quality_method.report_summary,
                lambda report: quality_method.build_report_detail(report, reports),
                signature=f"{reports[0].get('serie') if reports else ''}|{year}|{month}|{week}|{query}",
                after_detail=open_report_button,
            )


def show_app_map_page(mode):
    """«Mapa de la app» (D-285): the whole system in one view; the stack is its summary."""
    show_page_bar(
        PAGE_APP_MAP,
        PAGE_APP_MAP,
        "Todo el sistema en una vista: cada tecnología, su rol, cuándo actúa y con qué se conecta.",
    )
    addresses = {node[7]: build_page_address(node[7]) for node in app_map.NODES.values()}
    facts = read_app_map_facts(get_database_version())
    st.html(app_map.build_map_html(charts.get_palette(mode), addresses, facts), unsafe_allow_javascript=True)


@st.cache_data(show_spinner=False)
def read_app_map_facts(database_version):
    """D-441: what the map reads from the system, once per database: the dbt models and tests, the loads, the served
    tables, the manifest, the workflows, the requirements and the goals; and from the panel itself, its menu and the tabs
    of the Operations center, so the map never repeats them by hand."""
    menu = [
        (title, [SIDEBAR_LABELS.get(page, page) for page in pages])
        for _, title, pages in MENU_BLOCKS
        if pages is not SOURCE_LINKS
    ]
    return app_map_detail.read_facts(queries.DATABASE_FILE, menu=menu, runs_tabs=list(RUNS_VIEWS))


CODE_SPAN = re.compile(r"`([^`\n]+)`")


def soften_code_breaks(text):
    """D-297: a name in code may break only after «_», «/», «.» or «::», never in the middle of a word: a zero-width
    space after each of them (in the page only; the file keeps its text)."""
    return CODE_SPAN.sub(lambda match: "`" + re.sub(r"(::|[_/.](?=\w))", "\\1\u200b", match.group(1)) + "`", text)


def show_project_document(mode, title):
    """A document of docs/ as a page: the same text as in GitHub, its diagrams drawn
    from the live project, no code."""
    filename, lead = PROJECT_DOCUMENTS[title]
    # D-283: the document in the language of the visit, from docs/ or docs/en/.
    path = i18n.document_path(filename)
    text = path.read_text(encoding="utf-8")
    source = path.relative_to(project.PROJECT_DIR).as_posix()
    st.markdown(build_folder_path_html(title), unsafe_allow_html=True)
    show_compact_page_header(title, lead)
    show_document_actions(mode, f"{source} {tr('en GitHub')}", project.build_github_url(source))
    # D-288: the document opens with its cover, read from its header table; the title and the table do not repeat.
    header = documents_folder.read_header(text)
    related = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: (
            f'<a href="{html.escape(match.group(2), quote=True)}" target="_self">{html.escape(match.group(1))}</a>'
        ),
        link_document_views(documents_folder.field(header, "related")).split("<a id=", 1)[0],
    )
    cover = documents_folder.build_cover_html(text, related)
    text = soften_code_breaks(documents_folder.strip_header_table(re.sub(r"\A# .*\n", "", text)))
    st.markdown(documents_folder.build_cover_css(charts.get_palette(mode)), unsafe_allow_html=True)
    with st.container(key="project_document"):
        st.markdown(cover, unsafe_allow_html=True)
        position = 0
        for marker in DOCUMENT_DIAGRAM.finditer(text):
            st.markdown(link_document_views(text[position : marker.start()]), unsafe_allow_html=True)
            show_document_diagram(marker.group(1), mode)
            position = marker.end()
        st.markdown(link_document_views(text[position:]), unsafe_allow_html=True)
    st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)
    st.html(zoom.TIP_SCRIPT, unsafe_allow_javascript=True)


# endregion


# region Entry point


SHOW_PAGE_BY_TITLE = {
    PAGE_DOCUMENTATION: lambda mode: show_project_document(mode, PAGE_PRD),
    PAGE_PRD: lambda mode: show_project_document(mode, PAGE_PRD),
    PAGE_CLOSURE: lambda mode: show_project_document(mode, PAGE_CLOSURE),
    PAGE_SAD: lambda mode: show_project_document(mode, PAGE_SAD),
    PAGE_ADR: lambda mode: show_project_document(mode, PAGE_ADR),
    PAGE_STACK: lambda mode: show_stack_page(mode),
    PAGE_SECURITY: lambda mode: show_security_page(mode),
    PAGE_SQL: lambda mode: sql_explorer.show_sql_explorer_page(
        mode,
        # D-514: no row of chips under the bar; the studio's limits sit beside «Ejecutar», and the editor is taller
        header=lambda: show_page_bar(PAGE_SQL, "Consultas SQL", sql_explorer.DESCRIPTION),
    ),
    PAGE_RULES: lambda mode: show_rules_page(mode),
    PAGE_HOME: show_home_page,
    PAGE_DIAGRAMS: show_diagrams_page,
    PAGE_INSIGHTS: lambda mode: show_insights_page(mode),
    PAGE_STAKEHOLDERS: lambda mode: show_stakeholders_page(mode),
    PAGE_ANALYSIS: lambda mode: show_ba_page(mode),  # D-456: its method is a tab of «Análisis»
    PAGE_BA: lambda mode: show_ba_page(mode),
    PAGE_SEASONALITY: show_price_context_page,
    PAGE_KPI: show_kpi_page,
    PAGE_ARCHITECTURE: show_architecture_page,
    PAGE_OPERATIONS: show_operations_page,
    PAGE_RUNS: show_runs_page,
    PAGE_ACTIONS: lambda mode: show_actions_page(mode),
    PAGE_CONFIG: lambda mode: show_configuration_page(mode),
    PAGE_MANUAL: lambda mode: show_project_document(mode, PAGE_MANUAL),
    PAGE_GLOSSARY: lambda mode: show_project_document(mode, PAGE_GLOSSARY),
    PAGE_DECISION_INDEX: lambda mode: show_project_document(mode, PAGE_DECISION_INDEX),
    PAGE_TEST_PLAN: lambda mode: show_project_document(mode, PAGE_TEST_PLAN),
    PAGE_QUALITY_PLAN: lambda mode: show_project_document(mode, PAGE_QUALITY_PLAN),
    PAGE_FOLDER: lambda mode: show_documents_folder(mode),
    PAGE_SOURCE_STUDY: lambda mode: show_source_study(mode),
    PAGE_APP_MAP: lambda mode: show_app_map_page(mode),
    PAGE_METHOD: lambda mode: show_method_page(mode),
    PAGE_GIT: lambda mode: show_git_page(mode),
    PAGE_LINKS: show_links_page,
}


# Tablets and narrow windows: the menu folds once per visit, so the page gets the
# whole width; once the reader opens it again it stays open (D-057). Streamlit
# already folds it on phones; computers keep it open.
NARROW_SCREEN_WIDTH = 1024
# Every diagram animates by default, with no toggle (D-131); after 20 s without a
# mouse move, key, touch or scroll the page pauses CSS and SVG animations, and the
# next movement resumes them — so a forgotten tab does not keep spending resources.
IDLE_ANIMATION_SCRIPT = """<script>(() => {
    if (window.greenoceanIdleBound) { return; }
    window.greenoceanIdleBound = true;
    const IDLE_MS = 20000;
    let timer = null;
    const setPaused = (paused) => {
        document.documentElement.classList.toggle('greenocean-idle', paused);
        document.querySelectorAll('svg').forEach((svg) => {
            try { paused ? svg.pauseAnimations() : svg.unpauseAnimations(); } catch (_) {}
        });
    };
    const wake = () => {
        if (document.documentElement.classList.contains('greenocean-idle')) { setPaused(false); }
        clearTimeout(timer);
        timer = setTimeout(() => setPaused(true), IDLE_MS);
    };
    ['mousemove', 'pointerdown', 'keydown', 'wheel', 'touchstart', 'scroll'].forEach((name) =>
        window.addEventListener(name, wake, { passive: true, capture: true }));
    wake();
})();</script>"""
FOLD_SIDEBAR_SCRIPT = f"""<script>
(() => {{
// D-166: a phone turned sideways shows the computer layout, menu included. Streamlit
// folded the menu when the page opened upright, so it opens again on turning.
const phoneLandscape = window.matchMedia("(orientation: landscape) and (max-height: 500px)");
// D-473: Streamlit marks the menu with data-collapsed; older versions, with aria-expanded.
const isOpen = (sidebar) => sidebar.dataset.collapsed === "false" || sidebar.getAttribute("aria-expanded") === "true";
const openMenu = () => {{
    let attempts = 0;
    const open = () => {{
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const button = document.querySelector('[data-testid="stExpandSidebarButton"]');
        if (sidebar && isOpen(sidebar)) {{ return; }}
        if (button) {{ button.click(); }} else if (attempts++ < 40) {{ setTimeout(open, 100); }}
    }};
    open();
}};
if (!window.greenoceanPhoneTurnBound) {{
    window.greenoceanPhoneTurnBound = true;
    phoneLandscape.addEventListener("change", (event) => {{ if (event.matches) {{ openMenu(); }} }});
    if (phoneLandscape.matches) {{ openMenu(); }}
}}
if (phoneLandscape.matches) {{ return; }}
if (window.innerWidth >= {NARROW_SCREEN_WIDTH}) {{ return; }}
try {{ if (sessionStorage.getItem("sidebarFolded")) {{ return; }} }} catch (error) {{ return; }}
let tries = 0;
const fold = () => {{
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    const button = document.querySelector('[data-testid="stSidebarCollapseButton"] button');
    if (sidebar && button && isOpen(sidebar)) {{
        button.click();
        try {{ sessionStorage.setItem("sidebarFolded", "yes"); }} catch (error) {{}}
    }} else if (sidebar && !isOpen(sidebar)) {{
        try {{ sessionStorage.setItem("sidebarFolded", "yes"); }} catch (error) {{}}
    }} else if (tries++ < 40) {{
        setTimeout(fold, 100);
    }}
}};
fold();
}})();
</script>"""


def order_windows():
    """The data-first route, followed by documentation and links."""
    return ROUTE + [SECTION_PROJECT, SECTION_RESOURCES, SECTION_KPI]


def number_window(window, order):
    """«02 · Dashboard»: its step in the route; the links page has no number."""
    if window not in ROUTE:
        return window
    return f"{order.index(window) + 1:02d} · {window}"


def window_of_page(page):
    """The window a navigation entry draws (its title carries a number)."""
    return page.title.split(" · ", 1)[-1]


def synchronize_window_view(window):
    """Apply a deep-linked view before its header widget is instantiated."""
    views = read_window_views(window)
    key = window_view_key(window)
    requested = user_view_page(st.query_params.get(VIEW_PARAMETER))  # D-502
    if requested in RETIRED_VIEWS:
        requested = RETIRED_VIEWS[requested]
        st.query_params[VIEW_PARAMETER] = requested
    if requested in views and requested != st.session_state.get(f"{key}_synced"):
        st.session_state[key] = requested
        st.session_state[f"{key}_synced"] = requested
    if st.session_state.get(key) not in views:
        st.session_state[key] = views[0]


def choose_window_view(window):
    """The view of a window: from the address when a link asks for one, then from the
    selector; ◀ ▶ step through them without leaving the window (D-065). D-502: never a view
    the Usuario's menu does not lead to."""
    views = read_window_views(window)
    key = window_view_key(window)
    requested = user_view_page(st.query_params.get(VIEW_PARAMETER))
    if requested in RETIRED_VIEWS:
        requested = RETIRED_VIEWS[requested]
        st.query_params[VIEW_PARAMETER] = requested
    if requested in views and requested != st.session_state.get(f"{key}_synced"):
        st.session_state[key] = requested
    if st.session_state.get(key) not in views:
        st.session_state[key] = views[0]
    view = st.session_state[key]
    st.session_state[f"{key}_synced"] = view
    if view == views[0]:
        st.query_params.pop(VIEW_PARAMETER, None)
    else:
        st.query_params[VIEW_PARAMETER] = view
    return view


def render_window(window, pages=None):
    """Draw one section: its view selector, the chosen view, the route and the footer."""
    mode = get_mode()
    apply_style(mode)
    st.session_state[COMPACT_VIEW] = window == REPORT_WINDOW
    synchronize_window_view(window)
    show_app_header(window)
    view = choose_window_view(window)
    with st.container(key="report_page" if window == REPORT_WINDOW else "window_page"):
        overview_class = OVERVIEW_CLASS_BY_VIEW.get(view)
        if overview_class:
            st.markdown(
                f'<span class="overview-viewport-marker {overview_class}" aria-hidden="true"></span>',
                unsafe_allow_html=True,
            )
        show_page(view, mode)
    if view in COMPACT_FOOTER_VIEWS:
        show_compact_footer(window, pages, view)
    elif view not in OVERVIEW_CLASS_BY_VIEW:
        if pages:
            show_route_footer(window, pages, view)
        show_attribution()
    show_dashboard_menu_fold(view, mode)
    st.html(
        PHONE_LAYOUT_HTML
        + FOLD_SIDEBAR_SCRIPT
        + RELOAD_HOME_SCRIPT
        + IDLE_ANIMATION_SCRIPT
        + build_visit_history_script(),
        unsafe_allow_javascript=True,
    )


# D-462: a dashboard opens with the menu folded, so its charts get the width; the button that unfolds it beats in the
# green of GreenOcean (D-450), so it is seen. It folds once per page opened: a menu the reader opens stays open while
# the reader works on that page. A phone turned sideways keeps its menu open (D-166).
DASHBOARD_FOLD_SCRIPT = r"""<script>
(() => {
    const view = "__VIEW__";
    const fold = "__FOLD__" === "yes";
    const wide = window.innerWidth >= __WIDE__ && !window.matchMedia("(orientation: landscape) and (max-height: 500px)").matches;
    // D-466: the page before in this load of the app; each load (an address typed, a reload) is an entry and opens the menu
    const last = window.__goMenuView === undefined ? null : window.__goMenuView;
    window.__goMenuView = view;
    if (last === view) return;
    // Streamlit marks the menu with data-collapsed (aria-expanded in older versions)
    const isOpen = (sidebar) => sidebar.dataset.collapsed === "false" || sidebar.getAttribute("aria-expanded") === "true";
    let tries = 0;
    const act = () => {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const button = last === null
            ? document.querySelector('[data-testid="stExpandSidebarButton"]')
            : document.querySelector('[data-testid="stSidebarCollapseButton"] button');
        if (sidebar && button && (last === null) !== isOpen(sidebar)) { button.click(); return; }
        if (sidebar && (last === null) === isOpen(sidebar)) return;
        if (tries++ < 40) setTimeout(act, 100);
    };
    if (last === null ? wide : fold && wide) act();
})();
</script>"""


def show_dashboard_menu_fold(view, mode):
    """D-462, D-463, D-466: on going to a dashboard or a page of diagrams the menu folds and its button beats in green;
    elsewhere it stays. Each load of the app, its entry, opens it."""
    is_dashboard = view in FOLD_MENU_VIEWS
    if is_dashboard:
        green = ba_green(mode)
        st.markdown(
            f"""<style>
@keyframes go-menu-beat {{ 0%, 100% {{ filter:drop-shadow(0 0 2px {green}); opacity:1; }}
  50% {{ filter:drop-shadow(0 0 9px {green}); opacity:.55; }} }}
[data-testid="stSidebarCollapseButton"] button, [data-testid="stExpandSidebarButton"] {{ color:{green} !important;
  animation:go-menu-beat 1.6s ease-in-out infinite; }}
[data-testid="stSidebarCollapseButton"] button *, [data-testid="stExpandSidebarButton"] * {{ color:{green} !important; }}
@media (prefers-reduced-motion:reduce) {{ [data-testid="stSidebarCollapseButton"] button,
  [data-testid="stExpandSidebarButton"] {{ animation:none; filter:drop-shadow(0 0 4px {green}); }} }}
</style>""",
            unsafe_allow_html=True,
        )
    # the page as a neutral key: a page name in a script reads as Spanish text to the English layer (D-443)
    key = hashlib.sha1(view.encode(), usedforsecurity=False).hexdigest()[:10]
    script = (
        DASHBOARD_FOLD_SCRIPT.replace("__VIEW__", key)
        .replace("__FOLD__", "yes" if is_dashboard else "no")
        .replace("__WIDE__", str(NARROW_SCREEN_WIDTH))
    )
    st.html(script, unsafe_allow_javascript=True)


# D-166: the panel is read in landscape. A phone held upright sees one screen asking to
# turn it (no page can rotate a phone: only the reader can); turned, the phone gets
# the computer layout in miniature, every page whole, and no empty band on top.
# Tablets and computers never match these queries. Plain fills only: st.html strips
# SVG gradients.
PHONE_LAYOUT_HTML = """<style>
.go-rotate {display:none;}
@media (max-width:600px) and (orientation:portrait) {
  .go-rotate {display:flex; position:fixed; inset:0; z-index:2147483647; flex-direction:column;
    align-items:center; justify-content:center; gap:10px; padding:48px 32px 72px; text-align:center;
    background:radial-gradient(120% 70% at 50% 30%, #17406f 0%, #0f2747 55%, #0a1b33 100%);
    color:#cfd6e2; font-family:"Source Sans Pro",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
  .go-rotate .go-brand {font-size:26px; font-weight:600; color:#6ee7b7;}
  .go-rotate .go-brand span {color:#7dd3fc;}
  .go-rotate .go-sub {font-size:13px; color:#98a2b3;}
  .go-rotate .go-phone {position:relative; width:80px; height:150px; margin:56px 0 44px; border-radius:16px;
    background:#174a7c; border:5px solid #c3ccd8; box-shadow:0 24px 30px rgba(0,0,0,.45);
    animation:go-turn 3.2s cubic-bezier(.65,0,.35,1) infinite;}
  .go-rotate .go-phone i {position:absolute; display:block; border-radius:3px;}
  .go-rotate h2 {margin:0; font-size:30px; font-weight:600; color:#ffffff; line-height:1.2;}
  .go-rotate p {margin:0; max-width:300px; font-size:16px; line-height:1.45;}
  @keyframes go-turn {0%,18% {transform:rotate(0deg);} 45%,72% {transform:rotate(-90deg);} 100% {transform:rotate(0deg);}}
}
@media (orientation:landscape) and (max-height:500px) {
  /* The computer layout drawn at 1/0.62 the width, then shrunk back to the screen. */
  .stApp {transform:scale(.62); transform-origin:0 0; width:161.3vw !important; height:161.3vh !important;}
  /* Streamlit sizes its scrolling area to the screen height: it must grow with the scale. */
  [data-testid="stAppViewContainer"] > div, [data-testid="stMain"], [data-testid="stSidebar"] {height:161.3vh !important; max-height:none !important;}
  /* D-504: the menu's column grows with its sidebar, so its footer still ends at the bottom of the screen. */
  [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {min-height:calc(161.3vh - 72px) !important;}
  [data-testid="stHeader"] {display:none !important;}
  [data-testid="stMainBlockContainer"] {padding-top:.4rem !important;}
}
</style>
<div class="go-rotate" role="alertdialog" aria-label="Gira tu teléfono">
  <div class="go-brand">Green<span>Ocean</span></div>
  <div class="go-sub">Monitor de precios de alimentos</div>
  <div class="go-phone" aria-hidden="true">
    <i style="left:24px;top:4px;width:22px;height:5px;background:#0a1b33"></i>
    <i style="left:7px;top:18px;width:10px;height:110px;background:#6ee7b7;opacity:.6"></i>
    <i style="left:23px;top:18px;width:40px;height:9px;background:#ffffff;opacity:.5"></i>
    <i style="left:25px;top:44px;width:12px;height:12px;border-radius:50%;background:#7dd3fc"></i>
    <i style="left:45px;top:44px;width:12px;height:12px;border-radius:50%;background:#6ee7b7"></i>
    <i style="left:25px;top:66px;width:12px;height:12px;border-radius:50%;background:#fda4af"></i>
    <i style="left:45px;top:66px;width:12px;height:12px;border-radius:50%;background:#fde68a"></i>
    <i style="left:23px;top:94px;width:40px;height:6px;background:#ffffff;opacity:.35"></i>
  </div>
  <h2>Gira tu teléfono</h2>
  <p>El panel se lee en horizontal: así ves el pipeline completo y el menú de un vistazo.</p>
</div>"""


def show_menu_steps(view, pages):
    """«← Anterior» and «Siguiente →»: the pages before and after this one in the menu (D-250)."""
    order = visible_menu_order()
    if view not in order:
        return
    position = order.index(view)
    for step, text in ((-1, "← Anterior: {}"), (1, "Siguiente: {} →")):
        if 0 <= position + step < len(order):
            neighbour = order[position + step]
            st.page_link(
                pages[WINDOW_OF_VIEW[neighbour]],
                label=tr(text).format(tr(SIDEBAR_LABELS.get(neighbour, neighbour))),
                icon=SIDEBAR_ICONS.get(neighbour, PAGE_ICONS.get(neighbour)),
                query_params=keep_context() | {VIEW_PARAMETER: neighbour},
            )


def show_folder_steps(view, pages):
    """«← Anterior» and «Siguiente →» among the main documents of the folder (D-282); an annex leads back to the folder,
    so no step shows a document the folder does not list (D-536)."""
    if view in FOLDER_ANNEXES:
        neighbours = [("← Anterior: {}", PAGE_FOLDER)]
    else:
        position = FOLDER_SHOWN.index(view)
        neighbours = [
            (text, FOLDER_SHOWN[position + step])
            for step, text in ((-1, "← Anterior: {}"), (1, "Siguiente: {} →"))
            if 0 <= position + step < len(FOLDER_SHOWN)
        ]
    for text, neighbour in neighbours:
        st.page_link(
            pages[WINDOW_OF_VIEW[neighbour]],
            label=tr(text).format(tr(SIDEBAR_LABELS.get(neighbour, neighbour))),
            icon=SIDEBAR_ICONS.get(neighbour, PAGE_ICONS.get(neighbour)),
            query_params=keep_context() | {VIEW_PARAMETER: neighbour},
        )


def show_route_footer(window, pages, view=None):
    """«← Volver» and «Siguiente →» with what the next step proves; same window."""
    if view in FOLDER_ORDER:
        st.divider()
        with st.container(
            key="route_footer", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
        ):
            show_folder_steps(view, pages)
        return
    if view in MENU_BLOCK_OF_VIEW:
        st.divider()
        with st.container(
            key="route_footer", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
        ):
            show_menu_steps(view, pages)
        return
    if window not in ROUTE:
        return
    position = ROUTE.index(window)
    st.divider()
    with st.container(
        key="route_footer", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
    ):
        if position > 0:
            back = ROUTE[position - 1]
            st.page_link(pages[back], label=f"← Volver: {back}", query_params=keep_context())
        if position < len(ROUTE) - 1:
            following = ROUTE[position + 1]
            st.page_link(
                pages[following],
                label=f"Siguiente: {following} →",
                help=f"Muestra {ROUTE_LEADS[following]}.",
                query_params=keep_context(),
            )
    if position < len(ROUTE) - 1:
        st.caption(f"Siguiente paso: {ROUTE_LEADS[ROUTE[position + 1]]}.")


# D-233: the pages that fit the window close with one short footer instead of the two long ones.
COMPACT_FOOTER_VIEWS = {
    PAGE_SQL,
    PAGE_RULES,
    PAGE_OPERATIONS,
    PAGE_RUNS,
    PAGE_ACTIONS,
    PAGE_CONFIG,
    PAGE_SECURITY,
    PAGE_STACK,
    PAGE_FOLDER,
    PAGE_SOURCE_STUDY,
    PAGE_APP_MAP,
    PAGE_METHOD,
    PAGE_GIT,
}


def show_compact_footer(window, pages, view=None):
    """The route links and the data source in two short lines."""
    summary = lineage.summarize_build(*read_lineage(get_database_version()))
    with st.container(key="compact_footer"):
        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            if pages and view in MENU_BLOCK_OF_VIEW:
                show_menu_steps(view, pages)
            elif pages and window in ROUTE:
                position = ROUTE.index(window)
                if position > 0:
                    back = ROUTE[position - 1]
                    st.page_link(pages[back], label=f"← Volver: {back}", query_params=keep_context())
                if position < len(ROUTE) - 1:
                    following = ROUTE[position + 1]
                    st.page_link(
                        pages[following],
                        label=f"Siguiente: {following} →",
                        help=f"Siguiente paso: {ROUTE_LEADS[following]}.",
                        query_params=keep_context(),
                    )
            st.markdown(f'<div class="page-lineage">{lineage.build_badge_html(summary)}</div>', unsafe_allow_html=True)
        st.caption(tr(ATTRIBUTION_TEXT))


def show_page(view, mode):
    """Draw one page; an Autor's page only for the Autor's session (D-420), checked here on the server whatever the
    address or the menu say. Anyone else reads that there is no access."""
    if view in AUTHOR_ONLY_PAGES and not is_author():
        st.info(tr(NO_ACCESS), icon=":material/lock:")
        return
    view = user_view_page(view)  # D-502: the Usuario view never draws a page of another view
    SHOW_PAGE_BY_TITLE[view](mode)


def render_page(title):
    """Draw one view alone, as tests and old callers do."""
    mode = get_mode()
    apply_style(mode)
    show_page(title, mode)
    show_attribution()


def build_window_page(window, order, start, pages):
    """A navigation entry that draws one section, numbered by its step in the route."""
    return st.Page(
        lambda: render_window(window, pages),
        title=number_window(window, order),
        icon=WINDOW_ICONS[window],
        url_path=WINDOW_PATHS[window],
        visibility="hidden" if window == SECTION_KPI else "visible",
        default=window == start,
    )


def build_redirect_page(url_path, view, windows_by_title):
    """A hidden page at an old address that opens its window on the same view (D-065)."""

    def redirect():
        parameters = {key: value for key, value in st.query_params.to_dict().items()}
        window = WINDOW_OF_VIEW[view]
        if view != read_window_views(window)[0]:
            parameters[VIEW_PARAMETER] = view
        st.switch_page(windows_by_title[window], query_params=parameters)

    return st.Page(redirect, title=view, url_path=url_path, visibility="hidden")


def redirect_moved_tab(current_page, windows_by_title):
    """Keep deep links with ?seccion=… working: they open the view that holds that tab."""
    tab = st.query_params.get(TAB_PARAMETER)
    current_window = window_of_page(current_page)
    special_view = next(
        (
            target
            for (old_page, old_tab), target in OLD_TAB_PAGES.items()
            if old_tab == tab and WINDOW_OF_VIEW.get(old_page) == current_window
        ),
        None,
    )
    view = special_view or PAGE_OF_TAB.get(OLD_HOME_TABS.get(tab, tab))
    if not view:
        return
    st.query_params.pop(TAB_PARAMETER, None)
    window = WINDOW_OF_VIEW[view]
    parameters = {key: value for key, value in st.query_params.to_dict().items()}
    if view != read_window_views(window)[0]:
        parameters[VIEW_PARAMETER] = view
    if window != window_of_page(current_page) or st.query_params.get(VIEW_PARAMETER) != parameters.get(VIEW_PARAMETER):
        st.switch_page(windows_by_title[window], query_params=parameters)


def restore_return_context():
    encoded = st.query_params.pop("_ctx", None)
    if not encoded or len(encoded) > 16000:
        return
    try:
        snapshot = json.loads(base64.b64decode(encoded, validate=True))
        if isinstance(snapshot, dict):
            for key in RETURN_CONTEXT_KEYS:
                value = snapshot.get(key)
                if key == "dashboard_top_n":
                    if isinstance(value, int) and not isinstance(value, bool) and 8 <= value <= 20:
                        st.session_state[key] = value
                elif key == "dashboard_product":
                    if (
                        isinstance(value, dict)
                        and isinstance(value.get("key"), dict)
                        and all(isinstance(value["key"].get(field), str) for field in queries.KEY_COLUMNS)
                        and isinstance(value.get("name"), str)
                    ):
                        st.session_state[key] = value
                elif key == "analysis_channels":
                    if isinstance(value, list) and all(isinstance(item, str) for item in value):
                        st.session_state[key] = value
                elif isinstance(value, str):
                    st.session_state[key] = value
    except (ValueError, TypeError, UnicodeDecodeError):
        pass


# region Return (D-423): «Volver» walks back a short history kept in the session, with no page reload.
# The parameters every address carries (theme, language, view) never make a new step.
CONTEXT_PARAMETERS = {THEME_PARAMETER, i18n.LANGUAGE_PARAMETER, PROFILE_PARAMETER, ROLE_PARAMETER, "_ctx"}


def read_page_state():
    """The part of the session that makes this page what it is, as plain JSON values."""
    state = {}
    for key, value in st.session_state.items():
        if str(key).split("@")[0] in HISTORY_STATE_KEYS:
            try:
                state[key] = json.loads(json.dumps(value))
            except (TypeError, ValueError):
                continue
    return state


def record_page_visit(window):
    """One step of the history per page: the window, its own parameters and its state. Running the same page again
    only refreshes its state, so the last step is always what the page showed last."""
    parameters = {key: value for key, value in st.query_params.to_dict().items() if key not in CONTEXT_PARAMETERS}
    step = {"window": window, "params": parameters, "state": read_page_state()}
    history = st.session_state.setdefault(PAGE_HISTORY, [])
    if history and (history[-1]["window"], history[-1]["params"]) == (window, parameters):
        history[-1] = step
    else:
        history.append(step)
    del history[:-HISTORY_LIMIT]


def follow_return(windows_by_title):
    """The page «Volver» asked for, opened in this same session (st.switch_page, no reload)."""
    target = st.session_state.pop(RETURN_TARGET, None)
    if target and target["window"] in windows_by_title:
        st.switch_page(windows_by_title[target["window"]], query_params=target["params"] | keep_context())


# endregion


def build_visit_history_script():
    snapshot = {key: st.session_state[key] for key in RETURN_CONTEXT_KEYS if key in st.session_state}
    encoded = json.dumps(snapshot, ensure_ascii=True, default=str).replace("<", "\\u003c")
    return """<script>(() => {
    try {
        if (!document.documentElement.dataset.greenoceanLinksBound) {
            document.documentElement.dataset.greenoceanLinksBound = 'true';
            document.addEventListener('click', event => {
                if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
                const anchor = event.target.closest && event.target.closest('a[href]');
                if (!anchor || anchor.hasAttribute('download')) return;
                // Only internal navigation forces the same tab (D-113): this app may run
                // behind an iframe wrapper, where forcing target=_self on an external
                // link (GitHub, ODEPA…) makes the destination refuse to be framed.
                if (anchor.hostname === location.hostname) anchor.target = '_self';
            }, true);
        }
        const url = new URL(location.href); url.searchParams.delete('_ctx');
        const identity = url.pathname + '|' + ['vista','kpi','consulta'].map(k => url.searchParams.get(k) || '').join('|');
        const pending = sessionStorage.getItem('greenoceanReturning');
        if (pending && pending !== identity) return;
        if (pending) sessionStorage.removeItem('greenoceanReturning');
        const rows = JSON.parse(sessionStorage.getItem('greenoceanTrail') || '[]');
        const record = {url:url.pathname + url.search, identity, filters:__FILTERS__};
        if (rows.length && rows[rows.length-1].identity === identity) rows[rows.length-1] = record;
        else rows.push(record);
        sessionStorage.setItem('greenoceanTrail', JSON.stringify(rows.slice(-30)));
    } catch (_) {}
    })();</script>""".replace("__FILTERS__", encoded)


RELOAD_HOME_SCRIPT = """<script>
(() => {
    if (document.documentElement.dataset.greenoceanReloadHandled === "true") return;
    document.documentElement.dataset.greenoceanReloadHandled = "true";
    // A reload just to sync the theme's base mode (D-099): stay on this page.
    try {
        if (sessionStorage.getItem("greenoceanThemeReload")) {
            sessionStorage.removeItem("greenoceanThemeReload");
            return;
        }
    } catch (_) {}
    const navigation = performance.getEntriesByType("navigation")[0];
    if (!navigation || navigation.type !== "reload") return;
    const current = new URL(window.location.href);
    const home = new URL("/", current);
    for (const name of ["tema"]) {
        if (current.searchParams.has(name)) home.searchParams.set(name, current.searchParams.get(name));
    }
    home.searchParams.set("vista", "__HOME__");
    try {
        const trail = JSON.parse(sessionStorage.getItem('greenoceanTrail') || '[]');
        const last = trail[trail.length - 1];
        if (last && last.filters && Object.keys(last.filters).length) {
            home.searchParams.set('_ctx', btoa(unescape(encodeURIComponent(JSON.stringify(last.filters)))));
        }
    } catch (_) {}
    if (current.pathname !== home.pathname || current.search !== home.search || current.hash) {
        window.location.replace(home.href);
    }
})();
</script>""".replace("__HOME__", PAGE_HOME)


SOURCE_ICON_SVG = (
    '<svg class="nav-source-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">'
    '<path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zM5 5h6v2H5v12h12v-6h2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"/></svg>'
)


SIDEBAR_NAV_VERSION = 13  # D-453: the two dashboard tiles open «Negocio · BA y BI»
# D-286: the sources start folded; the documents are a folder at the end of the menu, not a section.
FOLDED_BY_DEFAULT = {"fuentes"}
FOLDER_TILE_BLOCK = "documentos"
# D-287: the sources are a tile of their own beside the folder; their links open in a floating panel.
SOURCES_TILE_BLOCK = "fuentes"
# D-442, D-452, D-453: the two dashboards are tiles, not lines, at the head of «Negocio · BA y BI».
DASHBOARD_TILES = [PAGE_HOME, PAGE_BA]  # D-494
# D-463, D-516: the pages whose dashboards, diagrams or SQL editor want the width: the menu folds on going to them.
FOLD_MENU_VIEWS = [
    *DASHBOARD_TILES,
    PAGE_SQL,
    PAGE_RULES,
    PAGE_DIAGRAMS,
    PAGE_ARCHITECTURE,
    PAGE_STACK,
    PAGE_APP_MAP,
    PAGE_SECURITY,
    PAGE_GIT,
    PAGE_RUNS,
]
TILE_BLOCKS = {FOLDER_TILE_BLOCK, SOURCES_TILE_BLOCK}


def show_sidebar_navigation(windows_by_title, current_window, order):
    """The menu (D-213, D-231): flat sections by kind of reader, open by default, each a folder
    that a click folds; under each title, its pages with their icon."""
    st.sidebar.markdown(build_sidebar_css(get_mode()), unsafe_allow_html=True)
    if st.session_state.get("sidebar_nav_version") != SIDEBAR_NAV_VERSION:
        for key, *_ in MENU_BLOCKS:
            st.session_state[f"nav_open_{key}"] = key not in FOLDED_BY_DEFAULT
        st.session_state["sidebar_nav_version"] = SIDEBAR_NAV_VERSION
    current_view = read_current_view(current_window)
    show_profile_indicator()  # D-373: first, right under the logo
    show_run_indicator()  # D-351
    show_load_alert(windows_by_title)  # D-298: first in the menu, where nothing covers it
    for key, title, pages in visible_menu_blocks():
        if key in TILE_BLOCKS:
            continue  # D-286, D-287: the folder and the sources live in the footer, always in sight
        open_key = f"nav_open_{key}"
        is_open = st.session_state.get(open_key, True)
        with st.sidebar.container(key=f"nav_block_{key}"):
            show_menu_block(windows_by_title, current_window, current_view, key, title, pages, open_key, is_open)
    show_sidebar_footer(current_window, lambda: show_footer_tiles(windows_by_title, current_window, current_view))


SHOW_SOURCES_SCRIPT = r"""<script>
setTimeout(() => {
  const links = document.querySelectorAll(".nav-source-link");
  const menu = document.querySelector("[data-testid='stSidebarContent']");
  const footer = document.querySelector(".st-key-sidebar_footer");
  if (!links.length || !menu || !footer) { return; }
  const hidden = links[links.length - 1].getBoundingClientRect().bottom - footer.getBoundingClientRect().top + 12;
  if (hidden > 0) { menu.scrollBy({top: hidden, behavior: "smooth"}); }
}, 200);
</script>"""


def show_footer_tiles(windows_by_title, current_window, current_view):
    """The tiles of the footer (D-287) in one compact row (D-538): the two folders (D-533), then the data sources. The
    Usuario view has no folders (D-502): its row holds the sources alone."""
    with st.container(key="sidebar_tiles", horizontal=True, gap="small"):
        if not is_public_profile():
            for index, view in enumerate(FOLDER_TILES):
                show_folder_tile(windows_by_title, current_window, current_view, view, index)
        # D-540: the stack of each area, names only, for every view: it opens no other page.
        for key, title, _, names in activity_bar.STACK_AREAS:
            with st.container(key=f"stack_tile_{key}"):
                with st.popover(tr(title), help=tr(title)):
                    st.markdown(activity_bar.build_stack_html(title, names), unsafe_allow_html=True)
        with st.container(key="sources_tile"):
            with st.popover(tr("Fuentes"), help=tr("Fuentes de datos")):
                st.markdown(f"**{tr('Fuentes de datos')}**")
                for name, url in SOURCE_LINKS:
                    st.markdown(
                        buttons.build_link_html(tr(name), url, icon="external", variant="text", external=True),
                        unsafe_allow_html=True,
                    )


def show_dashboard_tile(windows_by_title, current_window, current_view, view):
    """D-442: «Semanal», the weekly summary of prices, as a large tile, and «Análisis» under it (D-456, D-494).
    D-453: they open the section «Negocio · BA y BI»; a tile stays lit while its page is open."""
    window = WINDOW_OF_VIEW[view]
    active = window == current_window and current_view == view
    index = DASHBOARD_TILES.index(view)
    # «_lit», not «_nav_current»: the current line of a section draws its bar where the tile draws its icon.
    with st.container(key=f"nav_dashboard_tile_{index}" + ("_lit" if active else "")):
        st.page_link(
            windows_by_title[window],
            label=tr(SIDEBAR_LABELS.get(view, view)),
            icon=SIDEBAR_ICONS.get(view, PAGE_ICONS.get(view)),
            query_params=keep_context() | {VIEW_PARAMETER: view},
        )


def show_folder_tile(windows_by_title, current_window, current_view, view, index):
    """A folder of the footer (D-286, D-533): a larger tile with its name inside, at the end of the menu. «Documentos
    del proyecto» stays lit while one of its documents is open."""
    window = WINDOW_OF_VIEW[view]
    active = window == current_window and (
        current_view == view or (view == PAGE_FOLDER and current_view in FOLDER_ORDER)
    )
    with st.container(key=f"nav_folder_tile_{index}" + ("_nav_current" if active else "")):
        st.page_link(
            windows_by_title[window],
            label=tr(view),
            help=tr(view),
            query_params=keep_context() | {VIEW_PARAMETER: view},
        )


def show_menu_block(windows_by_title, current_window, current_view, key, title, pages, open_key, is_open):
    """One section of the menu: its title, which folds it, and its pages."""
    with st.container(key=f"nav_group_{key}" + ("" if is_open else "_folded")):
        if st.button(tr(title), key=f"nav_toggle_{key}"):
            st.session_state[open_key] = not is_open
            st.rerun()
    tiles = [view for view in pages if view in DASHBOARD_TILES]
    if tiles:  # D-459: the dashboards under their own title, which stays with them when the section folds
        st.markdown(f'<p class="nav-subtitle">{html.escape(tr("Dashboards"))}</p>', unsafe_allow_html=True)
    for view in tiles:  # D-453: the dashboard tiles open the section and stay in sight when it folds (D-442)
        show_dashboard_tile(windows_by_title, current_window, current_view, view)
    if not is_open:
        return
    if pages is SOURCE_LINKS:
        # They leave the app (D-118): plain external links, not Streamlit pages.
        for index, (name, url) in enumerate(pages):
            with st.container(key=f"nav_child_{key}_{index}"):
                st.markdown(
                    f'<a class="nav-source-link" href="{html.escape(url, quote=True)}" '
                    f'target="_blank" rel="noopener noreferrer">{SOURCE_ICON_SVG}{html.escape(tr(name))}</a>',
                    unsafe_allow_html=True,
                )
        # D-286: opened at the end of the menu, the sources scroll into sight above the pinned footer.
        st.html(SHOW_SOURCES_SCRIPT, unsafe_allow_javascript=True)
        return
    for index, view in enumerate(pages):
        if view in DASHBOARD_TILES:
            continue
        window = WINDOW_OF_VIEW[view]
        # A document of the folder lights its folder (D-282).
        active = window == current_window and (
            view == current_view or (view == PAGE_FOLDER and current_view in FOLDER_ORDER)
        )
        with st.container(key=f"nav_child_{key}_{index}" + ("_nav_current" if active else "")):
            st.page_link(
                windows_by_title[window],
                label=tr(SIDEBAR_LABELS.get(view, view)),
                icon=SIDEBAR_ICONS.get(view, PAGE_ICONS.get(view)),
                query_params=keep_context() | {VIEW_PARAMETER: view},
            )


def build_sidebar_github_html(is_current):
    """GitHub's mark on a light pill in the sidebar footer (D-124): not a row of the
    list, where it read as one more section and its blue mark sank into the navy."""
    current = " sidebar-github-current" if is_current else ""
    return (
        f'<a class="sidebar-github{current}" href="{html.escape(build_page_address(PAGE_LINKS), quote=True)}" '
        f'target="_self" aria-label="{tr("GitHub del proyecto")}" title="{tr("GitHub del proyecto")}">'
        f'{build_github_icon_svg(20)}</a>'
    )


def show_profile_indicator():
    """D-373: right under the GreenOcean logo, before the menu, a visible button «Vista: Usuario · Cambiar» reopens
    «Elige tu vista» (D-353); choosing another view there closes the author's session."""
    if not get_profile():
        return
    with st.sidebar.container(key="profile_indicator_top"):
        if st.button(
            f"{tr('Vista')}: {current_view_name()} · {tr('Cambiar')}",
            key="profile_indicator",
            icon=":material/account_circle:",
            width="stretch",
            help=tr("Cambiar de vista: usuario, profesional o autor."),
        ):
            st.session_state[CHANGE_VIEW] = True
            st.rerun()


def show_sidebar_footer(current_window=None, folder=None):
    """The documents folder, then appearance, the GitHub mark (only for the Autor, D-500) and the language, always at
    the bottom, on every page."""
    with st.sidebar.container(key="sidebar_footer"):
        if folder:
            folder()
        with st.container(key="sidebar_tools", horizontal=True, vertical_alignment="center"):
            with st.container(key="sidebar_appearance"):
                show_theme_field()
            if is_author():
                st.markdown(build_sidebar_github_html(current_window == SECTION_RESOURCES), unsafe_allow_html=True)
            show_language_switch()


# D-172: Streamlit reloads this file on each run but keeps the imported bi/* modules
# as they were; on Streamlit Cloud a push then shows a new menu with old pages until
# someone reboots the app. Each run compares the modules' files with the time they
# were loaded and reloads the ones that changed, dependencies first.
# The times live on the bi package, which outlives the script runs: Streamlit
# re-executes this file on every run, so a global here would start empty each time.
MODULE_TIMES = vars(bi).setdefault("MODULE_TIMES", {})


def reload_changed_modules():
    """Reload every bi/* module whose file changed since it was loaded."""
    package = Path(__file__).resolve().parent
    changed = []
    for name, module in sorted(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if not name.startswith("bi.") or name == __name__ or not file or not file.startswith(str(package)):
            continue
        try:
            modified = os.stat(file).st_mtime_ns
        except OSError:
            continue
        if name not in MODULE_TIMES:
            MODULE_TIMES[name] = modified
        elif modified != MODULE_TIMES[name]:
            MODULE_TIMES[name] = modified
            changed.append(module)
    # brand_icons feeds devops: reload the ones without bi.* imports first.
    for module in sorted(
        changed,
        key=lambda module: sum(
            1 for value in vars(module).values() if getattr(value, "__name__", "").startswith("bi.")
        ),
    ):
        importlib.reload(module)
    return [module.__name__ for module in changed]


def main():
    """Theme, navigation with icons and the chosen page."""
    reload_changed_modules()
    st.set_page_config(
        page_title="Monitor de precios de alimentos",
        layout="wide",
        # A green tile with white bars: the Material glyph was dark and
        # nearly invisible on a dark browser tab.
        page_icon=str(Path(__file__).resolve().parent / "assets" / "favicon.png"),
    )
    problem = follow_published_database()
    if not queries.DATABASE_FILE.exists():
        st.error(
            "Falta la Base DuckDB etl/datos.duckdb y no se pudo descargar de GitHub"
            + (f" ({problem})" if problem else "")
            + ". En local: python bi/served_database.py"
        )
        return
    settle_theme()
    i18n.settle_language()
    i18n.install()
    settle_profile()
    restore_return_context()
    # «Ver como» left the menu (D-213); an old ?ver= address still opens, without it.
    st.query_params.pop("ver", None)
    profile = None
    order = order_windows()
    start = start_window(profile)
    windows_by_title = {}
    windows_by_title.update({window: build_window_page(window, order, start, windows_by_title) for window in order})
    redirects = [
        build_redirect_page(path, view, windows_by_title)
        for view, path in PAGE_PATHS.items()
        if path not in WINDOW_PATHS.values()
    ]
    redirects += [
        build_redirect_page(path, page, windows_by_title)
        for path, (page, _) in OLD_PATHS.items()
        if path not in WINDOW_PATHS.values() and path not in PAGE_PATHS.values()
    ]
    current_page = st.navigation(
        {
            "Recorrido": [windows_by_title[window] for window in ROUTE],
            "Referencias": [windows_by_title[SECTION_RESOURCES]],
            "Compatibilidad": [windows_by_title[SECTION_PROJECT], windows_by_title[SECTION_KPI]] + redirects,
        },
        position="hidden",
    )
    # Historical root links may request a project view. Keep that exact destination
    # when Dashboard becomes the root, rather than silently showing another view.
    # Views renamed since: old links open the new title (D-094).
    if st.query_params.get(VIEW_PARAMETER) in RETIRED_VIEWS:
        st.query_params[VIEW_PARAMETER] = RETIRED_VIEWS[st.query_params[VIEW_PARAMETER]]
    if st.query_params.get(VIEW_PARAMETER) in BA_TAB_OF_VIEW:  # D-456: the page is now a tab of «Análisis»
        st.query_params[BA_TAB_PARAMETER] = BA_TAB_OF_VIEW[st.query_params[VIEW_PARAMETER]]
        st.query_params[VIEW_PARAMETER] = PAGE_BA
    requested_view = user_view_page(st.query_params.get(VIEW_PARAMETER))  # D-502
    if requested_view != st.query_params.get(VIEW_PARAMETER):
        st.query_params[VIEW_PARAMETER] = requested_view
    requested_window = WINDOW_OF_VIEW.get(requested_view)
    if requested_window and requested_window != window_of_page(current_page):
        st.switch_page(windows_by_title[requested_window], query_params=st.query_params.to_dict())
    redirect_moved_tab(current_page, windows_by_title)
    current_window = window_of_page(current_page)
    if current_window not in WINDOWS:
        # An old address: it only switches to its window, before any menu is drawn.
        current_page.run()
        return
    WINDOW_PAGES.update(windows_by_title)
    expire_idle_author()
    follow_return(windows_by_title)
    open_profile_landing(windows_by_title)
    show_sidebar_navigation(windows_by_title, current_window, order)
    if get_profile() and not st.session_state.get(CHANGE_VIEW):
        record_page_visit(current_window)  # D-423: before the keeper, which carries the history across a reload
    keep_profile_across_app_reloads()
    if not get_profile() or st.session_state.get(CHANGE_VIEW):
        show_profile_dialog()
    else:
        reopen_run_window()
        show_quality_alert()
    current_page.run()


if __name__ == "__main__":
    main()
# endregion
