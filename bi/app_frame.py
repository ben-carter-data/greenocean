"""The frame of the panel (D-541): the theme and the profile of the visit, the author's access, the alerts only the author
sees, the addresses and windows of the pages with the history of «Volver», the header with its controls, and the
cards, links and texts every page draws. Every page module reads them from here.
"""

import contextvars
import html
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

import bi
from bi import (
    buttons,
    charts,
    configuration,
    control,
    home_mockup,
    i18n,
    lineage,
    live_mark,
    overview,
    page_bar,
    quality_method,
    quality_metrics,
    run_monitor,
)
from bi.app_style import (
    build_style_css,
    is_dark_surface,
)
from bi.constants import (
    ADMIN_UNLOCKED,
    ATTRIBUTION_TEXT,
    AUTHOR_ONLY_PAGES,
    BA_TAB_OF_VIEW,
    BA_TAB_PARAMETER,
    BRAND_GREEN_DARK,
    BRAND_GREEN_LIGHT,
    CHANNEL_PARAMETER,
    CHILE_TIME_ZONE,
    COMPACT_VIEW,
    DEFAULT_ROLE,
    DEFAULT_THEME,
    DOOR_PAGES,
    FOLDER_ORDER,
    FOLDER_TILES,
    HISTORY_LIMIT,
    HISTORY_STATE_KEYS,
    HOME_FAMILY_DONE,
    HOME_FLASH,
    HOME_LINK_PARAMETERS,
    HOME_PAGE,
    HOME_REGION_DONE,
    HOME_SEARCHED,
    HOME_STEP_PARAMETER,
    KPI_PARAMETER,
    KPI_PRESENTATION,
    LANDING_STATE,
    LATE_SOURCE_NAMES,
    MENU_BLOCK_OF_VIEW,
    MENU_BLOCKS,
    MENU_ORDER,
    PAGE_ACTIONS,
    PAGE_ADR,
    PAGE_ANALYSIS,
    PAGE_APP_MAP,
    PAGE_ARCHITECTURE,
    PAGE_BA,
    PAGE_CLOSURE,
    PAGE_CONFIG,
    PAGE_DECISION_INDEX,
    PAGE_DIAGRAMS,
    PAGE_DOCUMENTATION,
    PAGE_FOLDER,
    PAGE_GIT,
    PAGE_GLOSSARY,
    PAGE_HISTORY,
    PAGE_HOME,
    PAGE_INSIGHTS,
    PAGE_KPI,
    PAGE_MANUAL,
    PAGE_METHOD,
    PAGE_OPERATIONS,
    PAGE_PRD,
    PAGE_QUALITY_PLAN,
    PAGE_RULES,
    PAGE_RUNS,
    PAGE_SAD,
    PAGE_SEASONALITY,
    PAGE_SECURITY,
    PAGE_SOURCE_STUDY,
    PAGE_SQL,
    PAGE_STACK,
    PAGE_STAKEHOLDERS,
    PAGE_TEST_PLAN,
    PROFILE_PARAMETER,
    PROFILE_PROFESSIONAL,
    PROFILE_PUBLIC,
    PROFILE_STATE,
    PROFILES,
    PUBLIC_BLOCKS,
    REPORT_PARAMETER,
    REPORT_WINDOW,
    RETIRED_THEMES,
    RETIRED_VIEWS,
    RETURN_TARGET,
    ROLE_ORDER,
    ROLE_PARAMETER,
    ROLE_STATE,
    ROLES,
    RUN_WINDOW_OPEN,
    SECRET_CONTROL_CODE,
    SECRET_GITHUB_TOKEN,
    SECRET_READ_TOKEN,
    SIDEBAR_LABELS,
    SIDEBAR_TOP_LABELS,
    SOURCE_LINKS,
    TAB_PARAMETER,
    THEME_PARAMETER,
    THEME_STATE,
    VIEW_PARAMETER,
    WINDOW_OF_VIEW,
    WINDOW_PATHS,
    WINDOWS,
)
from bi.data_access import (
    format_chile_time,
    get_database_version,
    get_secret,
    parse_run_start,
    read_cached_token_expiration,
    read_latest_run,
    read_lineage,
    read_pipeline_runs,
    to_chile_time,
)
from bi.i18n import tr
from etl import etl
from bi import static_files

# region Constants
CHANGE_VIEW = "profile_change_open"


AUTHOR_SEEN = "author_seen_at"


AUTHOR_IDLE_SECONDS = 30 * 60


AUTHOR_CODE_ERROR = "profile_author_error"


AUTHOR_ENTERED = "profile_author_entered"  # D-350: a right key must close the window; a widget callback cannot rerun


# D-357: the page reloads by itself to change the native theme (D-070), to print (D-280) and when a document opens
# from the folder. D-430: every run keeps the view in the browser tab, so any reload of the tab finds it (an ordinary
# link, such as the report link of «Acción requerida», or F5): the view is chosen once per tab and only «Vista: … ·
# Cambiar» or the logo (D-373) open the window again; a new tab or a new visit asks. D-427: the Autor comes along too,
# with a ticket the server issued and checks and that expires with the Autor's session, so the tab never holds anything
# that opens the Autor's view by itself. D-428: Streamlit Community Cloud loads the page twice after a reload (the app
# frame, then the whole page), so each page reads the kept view once and leaves it for the second load. D-454: a session
# the server forgot (idle time, sleep, restart) reads it again, so the visit never asks twice for its view.
PROFILE_KEEPER_JS = static_files.read("profile_keeper.js")


AUTHOR_TICKET = "author_ticket"


LOAD_ALERT_SEEN = "load_alert_seen"


QUALITY_ALERT_SEEN = "quality_alert_seen"


OVERVIEW_CLASS_BY_VIEW = {
    PAGE_INSIGHTS: "overview-dashboard",
    PAGE_STAKEHOLDERS: "overview-dashboard",  # D-378: the section's main pages share one look, with no route footer
    PAGE_ANALYSIS: "overview-dashboard",
    PAGE_BA: "overview-dashboard",
    PAGE_HOME: "overview-dashboard",
    PAGE_SEASONALITY: "overview-history",
    PAGE_KPI: "overview-kpis",
    PAGE_DIAGRAMS: "overview-pipeline",
    PAGE_ARCHITECTURE: "overview-model",
}


# The pages whose only header is one thin bar (D-264, D-267).
BAR_VIEWS = {
    PAGE_INSIGHTS,
    PAGE_STAKEHOLDERS,
    PAGE_ANALYSIS,
    PAGE_BA,
    PAGE_HOME,
    PAGE_SEASONALITY,
    PAGE_DIAGRAMS,
    PAGE_ARCHITECTURE,
    PAGE_OPERATIONS,
    PAGE_SQL,
    PAGE_RULES,
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


# The project documents: no path row and no Volver (D-269); the folder's path leads back (D-282).
DOCUMENT_VIEWS = {
    PAGE_DOCUMENTATION,
    PAGE_PRD,
    PAGE_CLOSURE,
    PAGE_SAD,
    PAGE_ADR,
    PAGE_MANUAL,
    PAGE_GLOSSARY,
    PAGE_DECISION_INDEX,
    PAGE_TEST_PLAN,
    PAGE_QUALITY_PLAN,
}


COMPONENT_SYMBOLS = {
    "security": '<path d="M16 2 29 7v11c0 8-6 13-13 16C9 31 3 26 3 18V7Z"/><path d="m10 18 4 4 8-9"/>',
    "database": '<ellipse cx="16" cy="7" rx="12" ry="4"/><path d="M4 7v20c0 6 24 6 24 0V7M4 17c0 6 24 6 24 0"/>',
    "workflow": '<rect x="2" y="12" width="8" height="10" rx="2"/><rect x="22" y="12" width="8" height="10" rx="2"/><path d="M11 17h10m-4-4 4 4-4 4"/>',
    "document": '<path d="M7 2h13l7 7v23H7Z M20 2v8h7M11 16h12M11 21h12M11 26h8"/>',
    "code": '<rect x="2" y="4" width="28" height="26" rx="3"/><path d="M2 10h28m-19 6-5 4 5 4m10-8 5 4-5 4m-3-9-4 10"/>',
    "chart": '<path d="M4 4v26h26M9 24V14m8 10V8m8 16V3"/>',
    "person": '<circle cx="16" cy="10" r="6"/><path d="M4 32v-4c0-13 24-13 24 0v4"/>',
    "mission": '<circle cx="16" cy="17" r="13"/><circle cx="16" cy="17" r="7"/><path d="m16 17 14-14m-7 0h7v7"/>',
    "vision": '<path d="M1 17Q16-4 31 17 16 38 1 17Z"/><circle cx="16" cy="17" r="6"/>',
    "scope": '<path d="M11 3H3v9m18-9h8v9M3 22v9h8m18-9v9h-8M8 17h16"/>',
    "rule": '<path d="m9 3 14 0 8 14-8 14H9L1 17Z"/><path d="m9 17 5 5 10-11"/>',
    "alert": '<path d="M16 3 31 30H1Z M16 12v9m0 4v1"/>',
    "gap": '<path d="M3 10h26M3 26h26"/><circle cx="10" cy="10" r="4"/>'
    '<circle cx="23" cy="26" r="4"/><path d="M10 14v8m13-8v8"/>',
    "channels": '<circle cx="16" cy="6" r="4"/><circle cx="5" cy="29" r="4"/>'
    '<circle cx="16" cy="29" r="4"/><circle cx="27" cy="29" r="4"/>'
    '<path d="M16 10v8M5 18h22M5 18v7m11-7v7m11-7v7"/>',
    "region": '<path d="M16 34S5 23 5 14a11 11 0 0 1 22 0c0 9-11 20-11 20Z"/><circle cx="16" cy="14" r="4"/>',
    "calendar": '<rect x="3" y="6" width="26" height="26" rx="4"/>'
    '<path d="M3 14h26M9 2v8m14-8v8M9 20h4m6 0h4M9 26h4m6 0h4"/>',
    "lag": '<circle cx="16" cy="19" r="13"/><path d="M16 11v9l6 4M8 3 4 8h8"/>',
    "decision": '<path d="M16 2v10M5 31V19h22v12M16 12v7"/><circle cx="16" cy="4" r="3"/><circle cx="5" cy="30" r="3"/><circle cx="27" cy="30" r="3"/>',
}
# endregion


# region Variables
# D-427: the tickets that carry the Autor's view across a reload the app makes. They live in the server process (the
# bi package outlives the script runs); D-428: a ticket may be redeemed again until it expires, as long as the Autor's
# idle time, and leaving the Autor's view revokes it.
AUTHOR_TICKETS = vars(bi).setdefault("AUTHOR_TICKETS", {})


# D-456: the tab of «Análisis» being drawn, so the page it gathers draws only its own row under the tabs.
DRAWN_TAB = contextvars.ContextVar("drawn_tab", default="")
# endregion


# region Theme and profile
def get_mode():
    """Theme of the visit; Corporativo until the reader chooses another one."""
    theme = st.session_state.get(THEME_STATE)
    return theme if theme in charts.THEMES else DEFAULT_THEME


def settle_theme():
    """The address wins when it names a theme (a shared link); otherwise the session
    keeps the theme. Either way the address shows it."""
    requested = st.query_params.get(THEME_PARAMETER)
    requested = RETIRED_THEMES.get(requested, requested)
    if requested in charts.THEMES:
        st.session_state[THEME_STATE] = requested
    st.session_state[THEME_STATE] = get_mode()
    st.query_params[THEME_PARAMETER] = st.session_state[THEME_STATE]


def get_profile():
    """The profile of the visit, or None while the reader has not chosen it."""
    profile = st.session_state.get(PROFILE_STATE)
    return profile if profile in PROFILES else None


def get_role():
    role = st.session_state.get(ROLE_STATE)
    return role if role in ROLES else DEFAULT_ROLE


def settle_profile():
    """The profile belongs to the visit and is only ever chosen in the entry window (D-340): the address never picks
    it, so a new visit or a reload always asks. What the address says (?perfil=…&rol=…) is dropped until a profile
    is chosen, and written back afterwards only to show it."""
    for name, value in (
        (PROFILE_PARAMETER, get_profile()),
        (ROLE_PARAMETER, get_role() if get_profile() == PROFILE_PROFESSIONAL else None),
    ):
        if value:
            st.query_params[name] = value
        elif name in st.query_params:
            st.query_params.pop(name)  # a retired profile («Reclutamiento») or a role the view does not use


def current_view_name():
    """«Usuario», «Profesional» or «Autor»: the view the visit is in, for the indicator."""
    if is_public_profile():
        return tr("Usuario")
    return tr("Autor") if st.session_state.get(ADMIN_UNLOCKED) else tr("Profesional")


def reset_home_steps():
    """D-531: «Semanal» back to its initial state: every step waits again, in every channel, and the address names
    no region, week, family, alert or channel."""
    for key in list(st.session_state.keys()):
        if str(key).split('@')[0] in (HOME_REGION_DONE, HOME_FAMILY_DONE, HOME_FLASH, HOME_SEARCHED):
            st.session_state.pop(key, None)
    for name in (*HOME_LINK_PARAMETERS, HOME_STEP_PARAMETER):
        st.query_params.pop(name, None)


def choose_profile(profile, role=None):
    st.session_state.pop(CHANGE_VIEW, None)
    reset_home_steps()  # D-531: a new view starts the dashboard from the beginning
    st.session_state[PROFILE_STATE] = profile
    if role:
        st.session_state[ROLE_STATE] = role
    st.session_state[LANDING_STATE] = True  # D-371: the next run opens the Dashboard
    settle_profile()


def profile_parameters():
    if not get_profile():
        return {}
    return {PROFILE_PARAMETER: get_profile()} | (
        {ROLE_PARAMETER: get_role()} if get_profile() == PROFILE_PROFESSIONAL else {}
    )


def is_public_profile():
    return get_profile() == PROFILE_PUBLIC


def hide_author_pages(blocks):
    """D-339: a page only the author sees leaves the menu of everyone else. D-420: a section left with no page leaves
    too, so «DevOps y seguridad» does not exist for the user and the professional views."""
    if is_author():
        return blocks
    kept = [
        (key, title, pages if pages is SOURCE_LINKS else [view for view in pages if view not in AUTHOR_ONLY_PAGES])
        for key, title, pages in blocks
    ]
    return [block for block in kept if block[2] is SOURCE_LINKS or block[2]]


def visible_menu_blocks():
    """The sections of the menu this profile sees, in its order: the user view, only the business pages and the
    sources; the professional view, everything, led by the profile it puts forward. The author's pages only for the
    author."""
    return hide_author_pages(menu_blocks_of_profile())


def menu_blocks_of_profile():
    if is_public_profile():
        return [block for block in MENU_BLOCKS if block[0] in PUBLIC_BLOCKS]
    by_key = {block[0]: block for block in MENU_BLOCKS}
    order = ROLE_ORDER[get_role()] if get_profile() else [block[0] for block in MENU_BLOCKS]
    blocks = [by_key[key] for key in order]
    blocks += [block for block in MENU_BLOCKS if block not in blocks]
    if (
        get_profile() and get_role() == "seguridad"
    ):  # security first inside its own section (D-420: «Stack y evidencia»)
        blocks = [
            (key, title, sorted(pages, key=lambda view: view != PAGE_SECURITY) if key == "stack" else pages)
            for key, title, pages in blocks
        ]
    return blocks


def visible_menu_order():
    return [view for _, _, pages in visible_menu_blocks() if pages is not SOURCE_LINKS for view in pages]


def keep_profile_across_app_reloads():
    """D-357: the view the visit had before a reload the app itself made; D-427: the Autor too, through a ticket the
    server checks. D-373: a click on the logo asks for the view again."""
    keeper = st.components.v2.component("profile_keeper", js=PROFILE_KEEPER_JS)
    profile = get_profile()
    data = {
        "perfil": profile or "",
        "rol": get_role() if profile == PROFILE_PROFESSIONAL else "",
        "historial": st.session_state.get(PAGE_HISTORY, []),  # D-423: «Volver» survives the reload too
        "autor": issue_author_ticket(),
    }
    result = keeper(
        key="profile_keeper", data=data, on_keep_change=lambda: None, on_reopen_change=lambda: None, height=0
    )
    if result.reopen and profile:
        st.session_state[CHANGE_VIEW] = True  # D-373: the logo was clicked; the window opens in this same run
    kept = result.keep
    if not kept:
        return
    try:
        values = json.loads(kept)
    except (TypeError, ValueError):
        return
    restore_kept_history(values)  # D-423
    if profile:
        return
    if values.get("p") in PROFILES:
        st.session_state[PROFILE_STATE] = values["p"]
        if redeem_author_ticket(values.get("a")):  # D-427: the Autor's view, back without the key
            st.session_state[ADMIN_UNLOCKED] = True
            st.session_state[AUTHOR_SEEN] = datetime.now(timezone.utc).timestamp()
            st.session_state[QUALITY_ALERT_SEEN] = True  # the alert was already shown in this visit
        if values.get("r") in ROLES:
            st.session_state[ROLE_STATE] = values["r"]
        settle_profile()
        st.rerun()


def user_view_page(view):
    """D-502: the Usuario view holds only its two dashboards and the sources. Whatever view an address asks for, if
    this menu does not lead to it the visit stays in «Semanal»; checked on the server, never read from the address."""
    return PAGE_HOME if view and is_public_profile() and not can_open(view) else view


def open_profile_landing(windows_by_title):
    """D-371: right after a choice, the Dashboard, whatever page the window opened on; only a document the address
    opens («Abrir» or «PDF» of the folder) stays where it is."""
    if not st.session_state.pop(LANDING_STATE, False):
        return
    if st.query_params.get(VIEW_PARAMETER) in DOCUMENT_VIEWS - {PAGE_DOCUMENTATION}:
        return
    st.switch_page(
        windows_by_title[WINDOW_OF_VIEW[HOME_PAGE]], query_params=keep_context() | {VIEW_PARAMETER: HOME_PAGE}
    )


def keep_theme_from_field():
    """The theme field changed: keep it for the whole visit."""
    st.session_state[THEME_STATE] = st.session_state["theme_field"]
    st.query_params[THEME_PARAMETER] = st.session_state[THEME_STATE]


def build_base_mode_script(theme_or_base):
    """Keep native widgets on the same base as the project palette.

    Streamlit infers st.context.theme from the CSS background, so it cannot
    detect a native widget theme that disagrees with the overridden page color.
    The cached frontend choice is checked instead, with one reload per change.
    Streamlit keeps that choice per address, so it is written for every section at
    once: moving between sections never reloads the page, which would end the session
    and its filters (D-070).
    """
    theme = (
        theme_or_base
        if theme_or_base in charts.THEMES
        else (charts.MODE_DARK if theme_or_base == charts.BASE_DARK else charts.MODE_CORPORATE)
    )
    base = charts.get_palette(theme)["base"]
    value = json.dumps("Dark" if base == charts.BASE_DARK else "Light")
    selected_theme = json.dumps(theme)
    section_paths = json.dumps([""] + list(WINDOW_PATHS.values()))
    return static_files.script(
        "base_mode.js",
        {
            '__GO_VALUE__': value,
            '__GO_SECTION_PATHS__': section_paths,
            '__GO_SELECTED_THEME__': selected_theme,
        },
    )


def match_base_mode(theme):
    """Check the frontend cache, including after either direction of a theme switch."""
    components.html(build_base_mode_script(theme), height=0)


# endregion


# region Author access
def leave_author():
    """D-353: choosing the user or the professional view while the author's key is open closes that session; getting
    back in asks for the key again. The run being followed stays in GitHub and is forgotten here."""
    for key in (ADMIN_UNLOCKED, QUALITY_ALERT_SEEN, AUTHOR_CODE_ERROR, RUN_WINDOW_OPEN):
        st.session_state.pop(key, None)
    AUTHOR_TICKETS.pop(st.session_state.pop(AUTHOR_TICKET, None), None)  # D-427: no reload brings the Autor back
    st.session_state.pop(run_monitor.WATCH, None)


def expire_idle_author(now=None):
    """D-395: the Autor view closes after 30 minutes with nothing done in the page, as leaving it does (D-353); getting
    back in asks for the key. Only a full run counts as activity: the timer of the run window does not."""
    if not st.session_state.get(ADMIN_UNLOCKED):
        st.session_state.pop(AUTHOR_SEEN, None)
        return False
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    seen = st.session_state.get(AUTHOR_SEEN)
    if seen is not None and now - seen > AUTHOR_IDLE_SECONDS:
        leave_author()
        st.session_state.pop(AUTHOR_SEEN, None)
        st.toast(tr("La vista Autor se cerró tras 30 min sin actividad."), icon=":material/lock:")
        return True
    st.session_state[AUTHOR_SEEN] = now
    return False


def is_author():
    """D-420: the session is the Autor's. Kept on the server (the session), never read from the address: every page
    and every action of the Autor asks this before it draws or acts."""
    return bool(st.session_state.get(ADMIN_UNLOCKED))


def submit_author_code():
    """D-350: the author's door opens on Enter. A right key enters as the default professional view; a wrong one says
    so in place and empties the field, with no reload of the page."""
    ok, message = control.check_control_code(
        st.session_state.get("profile_author_code", ""), get_secret(SECRET_CONTROL_CODE), control.GATE
    )
    st.session_state["profile_author_code"] = ""
    if ok:
        st.session_state[AUTHOR_CODE_ERROR] = None
        st.session_state[ADMIN_UNLOCKED] = True
        st.session_state[AUTHOR_ENTERED] = True
        choose_profile(PROFILE_PROFESSIONAL, DEFAULT_ROLE)
    else:
        st.session_state[AUTHOR_CODE_ERROR] = message


def issue_author_ticket(now=None):
    """The ticket of this Autor session, renewed on each run: it expires when the session would (D-395)."""
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    for ticket, expiry in list(AUTHOR_TICKETS.items()):
        if expiry <= now:
            AUTHOR_TICKETS.pop(ticket, None)
    if not is_author():
        AUTHOR_TICKETS.pop(st.session_state.pop(AUTHOR_TICKET, None), None)
        return ""
    ticket = st.session_state.get(AUTHOR_TICKET)
    if ticket not in AUTHOR_TICKETS:
        ticket = st.session_state[AUTHOR_TICKET] = secrets.token_urlsafe(32)
    AUTHOR_TICKETS[ticket] = now + AUTHOR_IDLE_SECONDS
    return ticket


def redeem_author_ticket(ticket, now=None):
    """True for a ticket the server issued and that has not expired. D-428: the new session takes it over, because
    Streamlit Community Cloud loads the page twice and the second load needs it too; leaving the Autor revokes it."""
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    if not isinstance(ticket, str):
        return False
    expiry = AUTHOR_TICKETS.get(ticket)
    if not (expiry and expiry > now):
        AUTHOR_TICKETS.pop(ticket, None)
        return False
    st.session_state[AUTHOR_TICKET] = ticket
    return True


@st.dialog("GreenOcean", width="small", dismissible=False)
def show_profile_dialog():
    """The first screen of a visit (D-295): the brand, «Elige tu vista» and two pills; under «Profesional», the profiles
    it can put forward. Nothing else. The page waits behind."""
    st.markdown(
        f'<div class="profile-brand"><span class="profile-logo">waves</span>GreenOcean</div>'
        f'<p class="profile-ask">{html.escape(tr("Elige tu vista"))}</p>',
        unsafe_allow_html=True,
    )
    with st.container(horizontal=True, gap="small", key="profile_choices"):
        with st.container(key="profile_side_profesional"):
            name, icon = PROFILES[PROFILE_PROFESSIONAL]
            if st.button(tr("Profesional"), key=f"profile_choose_{PROFILE_PROFESSIONAL}", icon=icon, width="stretch"):
                leave_author()
                choose_profile(PROFILE_PROFESSIONAL, DEFAULT_ROLE)
                st.rerun()
            # The profiles it can put forward, right under its pill.
            with st.container(horizontal=True, gap=None, key="profile_roles"):
                for role, label in ROLES.items():
                    if st.button(tr(label), key=f"profile_role_{role}", type="tertiary"):
                        leave_author()
                        choose_profile(PROFILE_PROFESSIONAL, role)
                        st.rerun()
        with st.container(key="profile_side_consulta"):
            name, icon = PROFILES[PROFILE_PUBLIC]
            if st.button(tr("Usuario"), key=f"profile_choose_{PROFILE_PUBLIC}", icon=icon, width="stretch"):
                leave_author()
                choose_profile(PROFILE_PUBLIC)
                st.rerun()
    if get_profile():  # D-353: the window was reopened from the menu; the current view can be kept
        if st.button(tr("Mantener esta vista"), key="profile_keep", type="tertiary"):
            st.session_state.pop(CHANGE_VIEW, None)
            st.rerun()
    # D-369: the author's door is no longer a third choice: a small link in the window's corner, with its key field
    # on click. D-335: the same key as «Acceso del autor» of the Operations center; nobody else sees the alerts.
    with st.container(key="profile_author_corner"):
        with st.popover(tr("Acceso del autor"), icon=":material/lock:", type="tertiary"):
            # D-350: Enter sends the key (on a phone, the keyboard's «Ir» is the same event); no button.
            st.text_input(
                tr("Clave"),
                key="profile_author_code",
                type="password",
                label_visibility="collapsed",
                placeholder=tr("Clave"),
                on_change=submit_author_code,
            )
            if st.session_state.pop(AUTHOR_ENTERED, False):
                st.rerun()  # the window is a fragment: only a full rerun closes it once the key was right
            if st.session_state.get(AUTHOR_CODE_ERROR):
                st.error(tr(st.session_state[AUTHOR_CODE_ERROR]))


# endregion


# region Alerts for the author
@st.dialog("Acción requerida", width="large")
def show_quality_alert_dialog():
    """D-335, only for the author: what is out of its acceptable in the latest report, the critical first; D-410: before
    it, each token at 15 days or fewer from its expiry. «Entendido» closes it; it comes back with the next visit while the
    condition lasts. It reads the report and the tokens' dates; it computes nothing else."""
    reports, goals, policy = quality_method.read_page()
    nonconformities = quality_metrics.read(quality_metrics.FOLDER / "no_conformidades.json").get("registros", [])
    runs, _ = read_pipeline_runs()
    failed = control.latest_load_failure(runs)
    day = failed["started_at"].astimezone(ZoneInfo(CHILE_TIME_ZONE)).strftime("%d-%m") if failed else None
    address = build_page_address(PAGE_METHOD)
    incidents = quality_metrics.read(quality_metrics.FOLDER / "incidentes_externos.json").get("registros", [])
    body = quality_method.build_alert(
        reports,
        goals,
        policy,
        nonconformities,
        lambda report: f"{address}&{REPORT_PARAMETER}={quality_metrics.report_ref(report)}",
        day,
        incidents=incidents,
    )
    tokens = configuration.build_token_alerts_html(read_token_alerts())  # D-410: the tokens first, then the report
    st.markdown(quality_method.build_css(charts.get_palette(get_mode())) + tokens + body, unsafe_allow_html=True)
    if st.button(tr("Entendido"), key="quality_alert_close", type="primary"):
        st.rerun()


def read_token_alerts():
    """D-410: each token at 15 days or fewer from its expiry, or expired, from the date GitHub gives (asked at most once
    an hour). A token missing or that cannot be read is not here: «Configuración» shows it."""
    now = datetime.now(timezone.utc)
    alerts = []
    for name in (SECRET_GITHUB_TOKEN, SECRET_READ_TOKEN):
        token = get_secret(name)
        if not token:
            continue
        try:
            expiration = read_cached_token_expiration(token)
        except Exception:  # GitHub unreachable or the token refused: the page says it, the alert does not guess
            continue
        alert = configuration.token_alert(configuration.token_label(name), expiration, now)
        if alert:
            alerts.append(alert)
    return alerts


def show_quality_alert():
    """The author's alert, once per visit and only when something is out of its acceptable (D-335) or a token is at 15
    days or fewer from its expiry (D-410)."""
    if not st.session_state.get(ADMIN_UNLOCKED) or st.session_state.get(QUALITY_ALERT_SEEN):
        return
    reports, goals, policy = quality_method.read_page()
    nonconformities = quality_metrics.read(quality_metrics.FOLDER / "no_conformidades.json").get("registros", [])
    out = bool(reports) and bool(
        quality_method.open_rows(reports[-1], nonconformities)
    )  # D-419: a resolved one raises nothing
    if not out and not read_token_alerts():
        return
    st.session_state[QUALITY_ALERT_SEEN] = True
    show_quality_alert_dialog()


def show_load_alert(windows_by_title):
    """D-298: when the last weekly load failed, every page says so at once, in the menu, with a way to the Operations
    center; the first page of the visit also raises a notice. The panel keeps showing the last valid load."""
    if not st.session_state.get(ADMIN_UNLOCKED):
        return  # a failure is for the operator: only whoever typed the author's key sees it
    runs, _ = read_pipeline_runs()
    failed = control.latest_load_failure(runs)
    if not failed:
        return
    day = failed["started_at"].astimezone(ZoneInfo(CHILE_TIME_ZONE)).strftime("%d-%m")
    with st.sidebar.container(key="load_alert"):
        st.markdown(
            f'<p class="load-alert-title">{html.escape(tr("La carga del {} falló").format(day))}</p>'
            f'<p class="load-alert-note">{html.escape(tr("El panel muestra la última carga válida."))}</p>',
            unsafe_allow_html=True,
        )
        st.page_link(
            windows_by_title[WINDOW_OF_VIEW[PAGE_RUNS]],
            label=tr("Ver qué paso falló"),
            icon=":material/arrow_forward:",
            query_params=keep_context() | {VIEW_PARAMETER: PAGE_RUNS},
        )
    if st.session_state.get(LOAD_ALERT_SEEN) != failed["id"]:
        st.session_state[LOAD_ALERT_SEEN] = failed["id"]
        st.toast(
            tr("La carga del {} falló: el panel muestra la última carga válida.").format(day), icon=":material/error:"
        )


# endregion


# region Addresses, windows and return
def build_page_address(page_title, tab=None, kpi=None):
    """Relative address of a page, one of its tabs or a KPI card."""
    page_title = RETIRED_VIEWS.get(page_title, page_title)
    ba_tab = BA_TAB_OF_VIEW.get(page_title)  # D-456: a page that became a tab opens its tab
    if ba_tab:
        page_title = PAGE_BA
    parameters = {}
    theme = st.session_state.get(THEME_STATE)
    if theme in charts.THEMES:
        parameters[THEME_PARAMETER] = theme
    parameters.update(i18n.address_parameters())
    parameters.update(profile_parameters())
    if tab:
        parameters[TAB_PARAMETER] = tab
    if kpi:
        parameters[KPI_PARAMETER] = kpi
    if ba_tab:
        parameters[BA_TAB_PARAMETER] = ba_tab
    window = WINDOW_OF_VIEW.get(page_title, page_title)
    if page_title in WINDOW_OF_VIEW and page_title != read_window_views(window)[0]:
        parameters[VIEW_PARAMETER] = page_title
    query = f"?{urlencode(parameters)}" if parameters else ""
    # The first window is the home page: Streamlit serves it at the root of the app.
    path = "./" if window == start_window() else WINDOW_PATHS[window]
    return path + query


def keep_context():
    """The address of the next page keeps the theme and the profile (filters and choices
    stay in the session)."""
    context = {}
    if st.session_state.get(THEME_STATE) in charts.THEMES:
        context[THEME_PARAMETER] = st.session_state[THEME_STATE]
    context.update(i18n.address_parameters())
    context.update(profile_parameters())
    return context


def read_window_views(window, profile=None):
    """One stable order for every visitor."""
    return list(WINDOWS[window])


def start_window(profile=None):
    """A single public entry point; legacy profile arguments are ignored."""
    return REPORT_WINDOW


def window_view_key(window):
    """Session key of the view chosen in one window."""
    return f"view_{WINDOW_PATHS[window]}"


def read_current_view(window):
    """The view drawn in a window: the address first, then the last choice."""
    views = read_window_views(window)
    view = st.query_params.get(VIEW_PARAMETER, st.session_state.get(window_view_key(window), views[0]))
    return view if view in views else views[0]


def request_return():
    """«Volver» (on click, before the run): this page leaves the history and the one before comes back with its state.
    With no page before, the visit goes back to «Elige tu vista»."""
    history = st.session_state.get(PAGE_HISTORY, [])
    if history:
        history.pop()
    if not history:
        st.session_state[CHANGE_VIEW] = True
        return
    previous = history[-1]
    for key in [key for key in st.session_state if str(key).split("@")[0] in HISTORY_STATE_KEYS]:
        if key not in previous["state"]:
            del st.session_state[key]
    for key, value in previous["state"].items():
        st.session_state[key] = value
    st.session_state[RETURN_TARGET] = previous


def restore_kept_history(kept):
    """D-357, D-423: a reload the app makes (a channel card, a document) carries the history with the view. The steps
    kept go first; the page the reload opened, already recorded in this new session, follows them."""
    history = kept.get("h") if isinstance(kept, dict) else None
    if not isinstance(history, list):
        return
    steps = [
        step
        for step in history[-HISTORY_LIMIT:]
        if isinstance(step, dict)
        and isinstance(step.get("window"), str)
        and isinstance(step.get("params"), dict)
        and isinstance(step.get("state"), dict)
        and all(str(key).split("@")[0] in HISTORY_STATE_KEYS for key in step["state"])
    ]
    for step in st.session_state.get(PAGE_HISTORY, []):
        if not steps or (steps[-1]["window"], steps[-1]["params"]) != (step["window"], step["params"]):
            steps.append(step)
    st.session_state[PAGE_HISTORY] = steps[-HISTORY_LIMIT:]


def can_open(view):
    """D-376: whether this view's menu leads to a page: one of its own, or one that opens from a page of its own."""
    order = visible_menu_order()
    return view in order or DOOR_PAGES.get(view) in order or (view in BA_TAB_OF_VIEW and PAGE_BA in order)


def build_view_path(window, view):
    """«Section › Page», with the same names as the menu (D-250)."""
    window_label = tr(SIDEBAR_TOP_LABELS.get(window, window))
    label = tr(SIDEBAR_LABELS.get(view, view))
    path = window_label if len(read_window_views(window)) == 1 else f"{window_label} › {label}"
    if view in MENU_BLOCK_OF_VIEW:
        block = tr(MENU_BLOCK_OF_VIEW[view])
        path = label if block == label else f"{block} › {label}"
    if view in FOLDER_TILES:  # D-533: a folder of the footer is its own path
        path = label
    if view in FOLDER_ORDER:
        path = f"{tr(PAGE_FOLDER)} › {label}"
    if view in DOOR_PAGES:  # D-391: a page opened from a button sits in the menu section of the page it opens from
        path = f"{tr(MENU_BLOCK_OF_VIEW[DOOR_PAGES[view]])} › {label}"
    return path


# endregion


# region Header and controls
def apply_style(mode):
    """Add the dashboard CSS to the page."""
    palette = charts.get_palette(mode)
    # The shared finish is optional: without the file the base style still applies.
    finish_file = Path(__file__).with_name("premium.css")
    finish = finish_file.read_text() if finish_file.exists() else ""
    for token, key in {
        "CARD": "card",
        "BORDER": "card_border",
        "INK": "strong_text",
        "ACCENT": "accent",
        "BG": "background",
    }.items():
        finish = finish.replace("__" + token + "__", palette[key])
    st.markdown(f"<style>{build_style_css(mode)}{finish}{buttons.build_icon_css()}</style>", unsafe_allow_html=True)
    # D-505: the styles of «Semanal» travel here, in the first element of every page. Drawn inside the page, the
    # browser lost them for one frame while Streamlit swapped the pages, and the old content flashed as plain text.
    st.markdown(home_mockup.style(mode, palette), unsafe_allow_html=True)


def build_greenocean_logo(mode, sidebar=False):
    """Transparent wordmark, displayed by Streamlit outside the navigation links."""
    background = charts.get_palette(mode)["sidebar" if sidebar else "background"]
    dark = is_dark_surface(background)
    green, ocean = (BRAND_GREEN_DARK, "#80baff") if dark else (BRAND_GREEN_LIGHT, "#185ca8")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="190" height="36" viewBox="0 0 190 36">'
        '<title>GreenOcean</title>'
        '<text x="0" y="27" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" '
        'font-size="28" font-weight="500" letter-spacing="-.8">'
        f'<tspan fill="{green}">Green</tspan><tspan fill="{ocean}">Ocean</tspan></text></svg>'
    )


def build_greenocean_icon(mode):
    """The folded menu's mark: the wordmark's own colors in a small monogram, so nothing
    sits over the page route (D-231)."""
    dark = is_dark_surface(charts.get_palette(mode)["background"])
    green, ocean = (BRAND_GREEN_DARK, "#80baff") if dark else (BRAND_GREEN_LIGHT, "#185ca8")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="36" viewBox="0 0 40 36">'
        '<title>GreenOcean</title>'
        '<text x="1" y="27" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" '
        'font-size="28" font-weight="600" letter-spacing="-1">'
        f'<tspan fill="{green}">G</tspan><tspan fill="{ocean}">O</tspan></text></svg>'
    )


def show_app_header(window):
    """Shared, sober graphic navigation, followed by preferences and location."""
    palette = charts.get_palette(get_mode())
    st.logo(build_greenocean_logo(get_mode(), sidebar=True), icon_image=build_greenocean_icon(get_mode()), size="large")
    st.markdown(
        static_files.style(
            "app_header.css",
            {
                'var(--go-text)': palette['text'],
                'var(--go-card-border)': palette['card_border'],
                'var(--go-strong-text)': palette['strong_text'],
            },
        ),
        unsafe_allow_html=True,
    )
    view = read_current_view(window)
    # The Resumen (D-264) and the main pages (D-267) draw the path and Volver in their own bar. The documents have
    # neither (D-269): the menu, always in sight, already says where the reader is and takes them anywhere.
    if view not in BAR_VIEWS | DOCUMENT_VIEWS:
        with st.container(key="app_header", horizontal=True, vertical_alignment="center"):
            st.markdown(
                f'<div class="app-brand" aria-label="Página actual">{html.escape(build_view_path(window, view))}</div>',
                unsafe_allow_html=True,
            )
            with st.container(key="header_preferences", horizontal=True):
                show_return_button()
    theme = get_mode()
    match_base_mode(theme)
    return theme


def show_return_button():
    """Volver: back to the previous page of this visit, with its selection (D-423); without one, «Elige tu vista»."""
    st.button(
        tr("Volver"),
        icon=":material/arrow_back:",
        key="return_to_previous",
        help=tr("Volver al punto anterior del proyecto, con su selección."),
        on_click=request_return,
    )


def show_theme_field():
    """A compact appearance icon; four named choices remain accessible."""
    st.session_state["theme_field"] = get_mode()
    icon = ":material/dark_mode:" if charts.get_palette(get_mode())["base"] == "dark" else ":material/light_mode:"
    with st.popover(
        tr("Apariencia"), icon=icon, help=tr("Cambiar los colores: Corporativo, Vantablack, Blue Light o Dark Grey.")
    ):
        st.radio(tr("Apariencia del panel"), charts.THEMES, key="theme_field", on_change=keep_theme_from_field)


def show_language_switch():
    """ES · EN (D-283): the language of the panel and of the documents, next to the appearance, kept in the address."""
    with st.container(key="language_switch", horizontal=True, gap="small"):
        for language in i18n.LANGUAGES:
            if st.button(
                language.upper(),
                key=f"language_{language}",
                type="primary" if language == i18n.get_language() else "secondary",
                help=f"{i18n.LANGUAGE_NAMES[language]} · {tr('Cambiar el idioma del panel y de los documentos.')}",
            ):
                i18n.choose_language(language)
                st.rerun()


# endregion


# region Cards, links and texts
def open_card(key, title=None, caption=None, hint=None, kpi=None):
    """A rounded card; use it with 'with'. The key must be unique on the page.

    hint, when given, is a short explanation in plain words that appears when
    the mouse passes over the ⓘ next to the title. kpi is only the internal
    destination identifier; visitors see a plain «Cómo se calcula» link.
    """
    card = st.container(key=f"card_{key}")
    hint_icon = build_hint_icon(hint) if hint else ""
    if kpi:
        definition = {
            "K1": "brecha entre consumidor y mayorista",
            "K2": "brecha entre canales",
            "K3": "índice de precio regional",
            "K4": "estacionalidad de precios",
            "K5": "rezago descriptivo",
            "K6": "variaciones y alertas",
            "K7": "cobertura de productos comparables",
            "K8": "filas rechazadas",
        }
        hint = (hint + " " if hint else "") + (
            "Este cálculo corresponde a " + definition.get(kpi, "un indicador del proyecto") + "."
        )
        hint_icon = build_hint_icon(hint)
    kpi_link = build_kpi_link(kpi) if kpi else ""
    if title or hint:
        # One line: the title shortens with «…» (whole on hover); ⓘ and the link stay whole.
        card.markdown(
            f'<div class="card-title">{build_component_symbol(component_kind(key, title))}'
            f'<span class="card-title-text" title="{html.escape(title or "")}">'
            f'{html.escape(title or "")}</span>{hint_icon}{kpi_link}</div>',
            unsafe_allow_html=True,
        )
    if caption:
        card.caption(caption)
    return card


def build_hint_icon(hint):
    """An ⓘ that shows a short explanation when the mouse passes over it, or when
    it is tapped on a phone (tabindex makes it focusable)."""
    # Explain identifiers inline, so a visitor never needs to guess an acronym.
    terms = {
        "KPI": "indicador clave de desempeño",
        "SQL": "lenguaje de consultas",
        "BI": "inteligencia de negocios",
        "BA": "análisis de negocio",
    }
    plain = hint.replace("**", "")
    used = [f"{term}: {meaning}" for term, meaning in terms.items() if re.search(rf"\b{term}\b", plain)]
    if used:
        plain += " · " + "; ".join(used) + "."
    plain_hint = html.escape(plain, quote=True)
    return f'<span class="hint" tabindex="0" role="button" aria-label="{plain_hint}" data-hint="{plain_hint}">ⓘ</span>'


def build_link_html(text, address):
    """A link that opens in the same tab, with already-escaped text."""
    return f'<a href="{html.escape(address)}" target="_self">{html.escape(text)}</a>'


def build_kpi_code_html(name):
    """«K6 · Alertas de precio» as a link to its step-by-step calculation, or a dash for a KPI only the panel computes."""
    code = overview.KPI_CODES.get(name)
    if not code:
        return "—"
    label = f"{code} · {i18n.translate_text(KPI_PRESENTATION[code][0])}"
    return build_link_html(label, build_page_address(PAGE_KPI, kpi=code))


def build_kpi_link(kpi):
    """Open an indicator's explanation without exposing its internal K-code."""
    address = build_page_address(PAGE_KPI, kpi=kpi)
    if st.session_state.get(COMPACT_VIEW):
        return (
            f'<span class="kpi-link" title="Abrir la explicación del cálculo">'
            f'{build_link_html("Cómo se calcula →", address)}</span>'
        )
    return f'<span class="kpi-link">{build_link_html("¿Cómo se calcula?", address)}</span>'


def build_chip(text, kind, hover_text=None):
    """A small colored label: kind is ok, failed, running, neutral, rise or fall.

    hover_text, when given, appears when the mouse passes over the label.
    """
    if not hover_text:
        return f'<span class="chip chip-{kind}">{html.escape(text)}</span>'
    escaped_hover_text = html.escape(hover_text, quote=True)
    return (
        f'<span class="chip chip-{kind} hint-chip" tabindex="0" '
        f'title="{escaped_hover_text}" data-hint="{escaped_hover_text}">'
        f'{html.escape(text)}</span>'
    )


def show_chart(chart):
    """Draw an Altair chart with its own colors (not Streamlit's chart theme)."""
    st.altair_chart(chart, use_container_width=True, theme=None)


def format_inline(text):
    """Escaped text with the two marks the documents use: **bold** and `code`."""
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)


def show_section_intro(title, lead, is_subsection=False):
    """A section title and one sentence that says what the section is for."""
    title_class = "subsection-title" if is_subsection else "section-title"
    st.markdown(
        f'<div class="section-head"><div class="{title_class}">{html.escape(title)}'
        f'</div><div class="section-lead">{format_inline(lead)}</div></div>',
        unsafe_allow_html=True,
    )


def capitalize_first(text):
    """A text that may come from the middle of a sentence, starting in upper case."""
    return text[:1].upper() + text[1:]


def component_kind(*texts):
    """A visual vocabulary based on the object's function, rather than uniform boxes."""
    text = " ".join(str(value or "") for value in texts).lower()
    for kind, pattern in [
        ("security", r"seguridad|secret|clave|token|permiso|administraci|acceso"),
        ("mission", r"misi[oó]n|objetivo"),
        ("vision", r"visi[oó]n"),
        ("scope", r"alcance|cobertura"),
        ("decision", r"decisi|d-\d"),
        ("alert", r"alerta|rechaz|falla|riesgo|l[ií]mite"),
        ("rule", r"regla|rn-\d|validaci|control de|calidad"),
        ("workflow", r"descarga|agente|pipeline|workflow|journey|recorrido|devops|ejecuci|prueba|cron|cach[eé]"),
        ("code", r"c[oó]digo|python|sql|quer[yi]|consulta"),
        ("database", r"tabla|base|datos\.db|raw\.db|modelo|dimensi[oó]n|fuente|registro|etl_run"),
        ("person", r"stakeholder|geren|analista|equipo|usuario|qui[eé]n"),
        ("region", r"regional_map|d[oó]nde es m[aá]s caro"),
        ("chart", r"precio|variaci|brecha|calendario|[ií]ndice|k[1-8]|indicador|tendencia|evolucion|usable_data"),
    ]:
        if re.search(pattern, text):
            return kind
    return "document"


def build_component_symbol(kind):
    shape = COMPONENT_SYMBOLS.get(kind, COMPONENT_SYMBOLS["document"])
    return (
        f'<span class="component-symbol" data-kind="{kind}" aria-hidden="true">'
        '<svg viewBox="-3 -3 40 44" fill="none" stroke="currentColor" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<g transform="translate(1.2 2)" opacity=".24" stroke-width="3.3">' + shape + '</g>'
        '<g fill="currentColor" fill-opacity=".13">' + shape + '</g>'
        '<g transform="translate(-.45 -.55)" stroke="white" opacity=".65" stroke-width=".65">'
        + shape
        + '</g></svg></span>'
    )


def build_info_card_html(
    title, text, label=None, note=None, link=None, is_warning=False, body_html="", is_highlight=False, component=None
):
    """One card: an optional label, a title, a short text, more content right under it
    (body_html), a note and a named link at the bottom."""
    text = capitalize_first(text)
    semantic = component or component_kind(title, label)
    parts = [
        build_component_symbol(semantic),
        f'<div class="info-label">{html.escape(label)}</div>' if label else "",
        f'<div class="info-title">{format_inline(title)}</div>',
        f'<div class="info-text">{format_inline(text)}</div>',
        body_html,
        f'<div class="info-note">{format_inline(note)}</div>' if note else "",
        f'<div class="info-link">{link}</div>' if link else "",
    ]
    kind = " is-warning" if is_warning else " is-highlight" if is_highlight else ""
    return f'<div class="info-card{kind}" data-component-kind="{semantic}">{"".join(parts)}</div>'


def show_info_cards(cards_html, is_compact=False):
    """Cards in a grid: side by side when they fit, stacked on narrow screens. Compact
    cards keep their own height instead of the tallest one of their row."""
    kind = " is-compact" if is_compact else ""
    st.markdown(f'<div class="info-grid{kind}">{"".join(cards_html)}</div>', unsafe_allow_html=True)


# endregion


# region Page bar, tabs and shared helpers
def show_page_bar(view, title, description, chips=(), side=None, terms=(), live=None):
    """The header of a page (D-267, D-398): only «Volver», the path (the description on hover) and the time of the
    data. What the page says (its question when it is not just its name, its figures as chips, what it measures) and
    what it does (side: a button, a switch) go in a row of the content right under the bar. Links to other pages live
    in the menu, never here. D-456: a page drawn as a tab of «Análisis» keeps only that row, under the tabs. D-510: «live»
    names what the page's figures were read from, and the mark that beats goes beside them."""
    tab = DRAWN_TAB.get()
    if tab:
        show_title = tr(title) != tr(tab)
    else:
        latest = read_latest_run()
        path = build_view_path(WINDOW_OF_VIEW.get(view, view), view)
        st.markdown(page_bar.build_css(charts.get_palette(get_mode())), unsafe_allow_html=True)
        with st.container(key="page_bar", horizontal=True, vertical_alignment="center"):
            show_return_button()
            st.markdown(page_bar.build_bar_html(path, tr(description)), unsafe_allow_html=True, width="stretch")
            st.markdown(
                page_bar.build_updated_html(format_load_time(latest), latest["status"] == etl.STATUS_LOADED),
                unsafe_allow_html=True,
                width="content",
            )
            show_title = tr(title) != path.rpartition(" › ")[2]
            if live and not (show_title or chips or side or terms):
                # D-510: a page with no row of its own (its tabs draw theirs) carries the mark in the bar itself
                st.markdown(live_mark.build_html(tr(live)), unsafe_allow_html=True, width="content")
    if not (show_title or chips or side or terms):
        return
    with st.container(key="page_info", horizontal=True, vertical_alignment="center"):
        st.markdown(
            page_bar.build_info_html(tr(title), tr(description), chips, show_title, tr(live) if live else None),
            unsafe_allow_html=True,
            width="stretch",
        )
        if terms:
            st.markdown(page_bar.build_terms_html(terms), unsafe_allow_html=True, width="content")
        if side:
            side()


def show_compact_page_header(title, description):
    """A one-line header, like the Dashboard's: title and freshness together; the
    description shows on hover instead of taking a line of its own."""
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = tr("Carga correcta") if run_kind == "ok" else tr("Última carga con falla")
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
    st.markdown(
        f'<div class="compact-header"><h1 title="{html.escape(tr(description), quote=True)}">'
        f'{html.escape(tr(title))}</h1><span class="page-freshness">{tr("Datos al")} '
        f'{freshness} {build_chip(run_text, run_kind)}</span></div>',
        unsafe_allow_html=True,
    )


def format_load_time(latest):
    """«20 oct · 12:54»: the time of a load, short, as the Resumen's bar shows it (D-264)."""
    stamp = to_chile_time(parse_run_start(latest["started_at"]))
    month = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"][stamp.month - 1]
    return f"{stamp.day} {month} · {stamp:%H:%M}"


def build_external_link_html(text, address, variant="text"):
    """A link that leaves the app, drawn as the shared component (D-281): it says where it goes and opens a new tab (↗)."""
    return buttons.build_link_html(
        text, address, icon="github" if "GitHub" in text else "external", variant=variant, external=True
    )


def build_repository_link_html(text, address, variant="text"):
    """D-500: a link to the author's repository exists only for the Autor (D-420): anyone else gets nothing, from the
    server, whatever the page."""
    return build_external_link_html(text, address, variant) if is_author() else ""


def show_view_tabs(key, labels, palette):
    """D-360: tabs that draw only the one chosen. st.tabs draws every tab on each run (four diagrams at once in the
    Operations center); this selector looks like tabs and draws only what is in sight. Returns the chosen label."""
    if st.session_state.get(key) not in labels:
        st.session_state[key] = labels[0]
    ink, muted, line, accent = palette["strong_text"], palette["reference"], palette["card_border"], palette["accent"]
    st.markdown(
        static_files.style(
            "view_tabs.css",
            {
                'var(--go-key)': key,
                'var(--go-line)': line,
                'var(--go-charts-legible-muted-palette-background)': charts.legible(muted, palette["background"]),
                'var(--go-accent)': accent,
                'var(--go-ink)': ink,
            },
        ),
        unsafe_allow_html=True,
    )
    choice = st.segmented_control(
        tr("Vista"), labels, key=key, format_func=tr, required=True, label_visibility="collapsed", width="content"
    )
    return choice or labels[0]


def find_menu_page(label):
    """The page whose label in the menu, in the documents folder or on a page's door (D-376: «Precios e inflación»)
    is `label`, or None."""
    for view in MENU_ORDER + FOLDER_ORDER + list(DOOR_PAGES) + list(BA_TAB_OF_VIEW):  # D-456: and the tabs
        name = SIDEBAR_LABELS.get(view, view)
        if label in (name, i18n.EN.get(name), i18n.PAGES.get(name)):  # D-444: a page label from either dictionary
            return view
    return None


def is_dark_theme(mode):
    return charts.get_palette(mode)["base"] == charts.BASE_DARK


def channel_address(channel):
    address = build_page_address(PAGE_HOME)  # D-494: a channel is step 2 of «Semanal»
    return address + ("&" if "?" in address else "?") + urlencode({CHANNEL_PARAMETER: channel})


def describe_state_source(error_text, step_states, latest_load):
    """Where the states come from when GitHub did not answer, and why it did not."""
    if step_states:
        source = tr("se muestra la última respuesta guardada")
    else:
        loaded_at = format_chile_time(parse_run_start(latest_load["started_at"]))
        source = tr("los estados salen de la última carga guardada en la base ({})").format(loaded_at)
    return tr("GitHub no respondió ({}); {}.").format(error_text, source)


def describe_late_sources(message):
    """D-356: «ODEPA aún no publica la semana 19–25 oct (mayorista)», from the notice the load left in its run; the week
    as its range (D-374)."""
    if not message or not str(message).startswith(etl.NOTICE_SOURCE_LATE):
        return ""
    parts = []
    for item in str(message).split(":", 1)[1].split(","):
        source, _, week = item.strip().partition(" ")
        if week:
            parts.append(
                tr("ODEPA aún no publica la semana {} ({})").format(
                    i18n.tr_week(week), tr(LATE_SOURCE_NAMES.get(source, source))
                )
            )
    return " · ".join(parts)


def show_attribution():
    """Footer of every page: the data source. The project links live only in
    Operaciones (D-056)."""
    st.divider()
    summary = lineage.summarize_build(*read_lineage(get_database_version()))
    st.markdown(f'<div class="page-lineage">{lineage.build_badge_html(summary)}</div>', unsafe_allow_html=True)
    st.caption(tr(ATTRIBUTION_TEXT))


# endregion
