"""The DevOps and security section, only for the Autor (D-541): «Centro de operación» with the window of the weekly
load and «Ejecutar pipeline ahora», «GitHub Actions», «Configuración», the operation tabs and the security page.
"""

import html
import logging
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from bi import (
    actions_view,
    charts,
    compact_table,
    configuration,
    control,
    github_actions,
    i18n,
    live_flow,
    operation_center,
    quality_method,
    queries,
    run_monitor,
    security_map,
    weeks,
)
from bi.app_frame import (
    describe_late_sources,
    find_menu_page,
    get_mode,
    is_author,
    keep_context,
    leave_author,
    show_page_bar,
    show_view_tabs,
)
from bi.app_style import build_runs_css
from bi.constants import (
    ADMIN_UNLOCKED,
    GITHUB_CACHE_SECONDS,
    LIVE_SECONDS_WITH_TOKEN,
    LIVE_SECONDS_WITHOUT_TOKEN,
    NO_ACCESS,
    OPERATION_RECENT_RUNS,
    PAGE_ACTIONS,
    PAGE_CONFIG,
    PAGE_ICONS,
    PAGE_RUNS,
    PAGE_SECURITY,
    PROGRESS_POLL_SECONDS,
    RUN_WINDOW_OPEN,
    SECRET_GITHUB_TOKEN,
    SECRET_READ_TOKEN,
    SIDEBAR_ICONS,
    SIDEBAR_LABELS,
    VIEW_PARAMETER,
    WINDOW_OF_VIEW,
    WINDOW_PAGES,
)
from bi.data_access import (
    fetch_pipeline_runs,
    format_chile_time,
    get_database_version,
    get_last_github_answers,
    get_secret,
    parse_run_start,
    read_cached_token_expiration,
    read_flow_facts,
    read_latest_run,
    read_pipeline_runs,
    to_chile_time,
)
from bi.i18n import tr
from bi.page_engineering import show_cicd_tab, show_devops_tab, show_monitoring_tab
from etl import etl

# region Constants
RUN_WINDOW_KEY = "run_window"  # D-379: the fragment that holds the window's refreshing part


RUN_WINDOW_CLOSING = "run_window_closing"


RUN_PHASE_STATES = {
    run_monitor.STARTING: control.RUN_IN_PROGRESS,
    run_monitor.RUNNING: control.RUN_IN_PROGRESS,
    run_monitor.OK: control.RUN_OK,
}


RUN_FLOW_HEIGHT = 330


RELOADED_NOTICE = "panel_reloaded"


RUNS_VIEW_KEY = "runs_view"
# endregion


# region The window of the load
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


def reload_panel_data():
    """Read datos.db again (the weekly load or a manual run may have replaced it). D-421: only the Autor's session."""
    if not is_author():
        return
    st.cache_data.clear()
    st.session_state[RELOADED_NOTICE] = True


# endregion


# region The Autor's access and tokens
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


# endregion


# region «Centro de operación»
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


@st.cache_data(ttl=GITHUB_CACHE_SECONDS, show_spinner=False)
def fetch_run_step_details(run_id):
    """Steps of one run with their log addresses. A failure raises, and is not cached."""
    return control.list_run_step_details(run_id, get_secret(SECRET_GITHUB_TOKEN))


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


RUNS_VIEWS = {
    "Despliegue": lambda mode: show_devops_tab(mode),
    "Operación": lambda mode: show_runs_tab(mode),
    "CI/CD": lambda mode: show_cicd_tab(mode),
    "Monitoreo": lambda mode: show_monitoring_tab(mode),
}


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


# endregion


# region «GitHub Actions»
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


# endregion


# region «Configuración» and security
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


# endregion
