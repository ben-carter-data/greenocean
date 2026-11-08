"""GreenOcean's panel: its entry point, its navigation and its menu.

Run it with:  streamlit run bi/dashboard.py

Streamlit runs this file on every visit and every click. It keeps what decides which page to show: the windows and
pages of the menu, the footers that lead from one page to the next, the history of «Volver», the menu with its
activity bar, and main(). The rest of the panel lives in the modules it imports (D-541):

- bi/constants.py: the fixed names. bi/data_access.py: what is read from the Base DuckDB and from GitHub.
- bi/app_style.py: the global stylesheets. bi/app_frame.py: theme, profile, the Autor's access, header, shared parts.
- bi/page_weekly.py, page_analysis.py, page_engineering.py, page_quality.py, page_devops.py, page_documents.py:
  the pages, each family in its own file.

Texts shown to the reader are in Spanish (bi/i18n.py gives their English); code and comments are in English.
"""

import functools
import ast
import base64
import hashlib
import html
import importlib
import json
import os
import sys
from pathlib import Path

import streamlit as st

# Streamlit runs this file as a script, so the project folder is added to the
# import path to reach the other modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bi  # noqa: E402
from bi import (
    activity_bar,
    overview,  # noqa: F401  read by the tests through this module
    architecture,  # noqa: F401  read by the tests through this module
    buttons,
    charts,  # noqa: F401  read by the tests through this module
    i18n,
    doc_diagrams,  # noqa: F401  read by the tests through this module
    lineage,
    sql_explorer,
    static_files,
    project,  # noqa: F401  read by the tests through this module
    queries,
)
from etl import etl  # noqa: E402, F401  read by the tests through this module
from bi.page_documents import (  # noqa: E402
    show_documents_folder,
    show_project_document,
    show_source_study,
    build_github_icon_svg,
    show_links_page,
    PROJECT_DOCUMENTS,  # noqa: F401  read by the tests through this module
    FOLDER_VIEW_KEY,  # noqa: F401  read by the tests through this module
    PRINT_DOCUMENT_CSS,  # noqa: F401  read by the tests through this module
    PRINT_THEME,  # noqa: F401  read by the tests through this module
    PRINT_BUTTON_HTML,  # noqa: F401  read by the tests through this module
    AUTO_PRINT_SCRIPT,  # noqa: F401  read by the tests through this module
    build_print_address,  # noqa: F401  read by the tests through this module
    read_folder_files,  # noqa: F401  read by the tests through this module
    heading_anchor,  # noqa: F401  read by the tests through this module
    link_document_views,  # noqa: F401  read by the tests through this module
    build_print_button_html,  # noqa: F401  read by the tests through this module
)
from bi.page_devops import (  # noqa: E402
    RUNS_VIEWS,  # noqa: F401  read by the tests through this module
    show_run_indicator,
    reopen_run_window,
    show_runs_page,
    show_actions_page,
    show_configuration_page,
    show_security_page,
    RUN_WINDOW_KEY,  # noqa: F401  read by the tests through this module
    RUN_WINDOW_CLOSING,  # noqa: F401  read by the tests through this module
    RELOADED_NOTICE,  # noqa: F401  read by the tests through this module
    RUNS_VIEW_KEY,  # noqa: F401  read by the tests through this module
    render_run_window,  # noqa: F401  read by the tests through this module
    request_run_window_close,  # noqa: F401  read by the tests through this module
    minimize_run_window,  # noqa: F401  read by the tests through this module
    close_run_window,  # noqa: F401  read by the tests through this module
    show_run_window_shell,  # noqa: F401  read by the tests through this module
    show_run_now_dialog,  # noqa: F401  read by the tests through this module
    reload_panel_data,  # noqa: F401  read by the tests through this module
)
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
    show_kpi_window,
    FAMILY_FOCUS_KEY,  # noqa: F401  read by the tests through this module
    OVERVIEW_WEEK_KEY,  # noqa: F401  read by the tests through this module
    BA_TAB_KEY,  # noqa: F401  read by the tests through this module
    SYSTEM_DECISION_PAGES,  # noqa: F401  read by the tests through this module
    read_ba_history,  # noqa: F401  read by the tests through this module
    read_family_inflation,  # noqa: F401  read by the tests through this module
)
from bi.app_diagrams import format_file_size, read_store_sizes  # noqa: E402, F401  read by the tests through this module
from bi.page_engineering import (  # noqa: E402
    show_diagrams_page,
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
    show_stack_page,
    show_rules_page,
    show_app_map_page,
    read_flow_model,  # noqa: F401  read by the tests through this module
)
from bi.page_quality import (  # noqa: E402
    show_operations_page,
    QUALITY_OPEN_KEY,  # noqa: F401  read by the tests through this module
    build_rejected_rows_table,  # noqa: F401  read by the tests through this module
    show_quality_tab,  # noqa: F401  read by the tests through this module
    show_method_page,
    show_git_page,
    filter_reports,  # noqa: F401  read by the tests through this module
    show_quality_report_dialog,  # noqa: F401  read by the tests through this module
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
    leave_author,  # noqa: F401  read by the tests through this module
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
    build_external_link_html,  # noqa: F401  read by the tests through this module
    build_repository_link_html,  # noqa: F401  read by the tests through this module
    find_menu_page,  # noqa: F401  read by the tests through this module
    is_dark_theme,  # noqa: F401  read by the tests through this module
    describe_state_source,  # noqa: F401  read by the tests through this module
    describe_late_sources,  # noqa: F401  read by the tests through this module
    show_attribution,
)
from bi.app_style import (  # noqa: E402
    is_dark_surface,  # noqa: F401  read by the tests through this module
    build_sidebar_css,
    MENU_INK,  # noqa: F401  read by the tests through this module
    ACTIVITY_BAR,  # noqa: F401  read by the tests through this module
    build_theme_css,  # noqa: F401  read by the tests through this module
    build_section_colors_css,  # noqa: F401  read by the tests through this module
    build_runs_css,  # noqa: F401  read by the tests through this module
)
from bi.data_access import (  # noqa: E402
    follow_published_database,
    get_database_version,
    read_latest_week,  # noqa: F401  read by the tests through this module
    current_channel,  # noqa: F401  read by the tests through this module
    scoped,  # noqa: F401  read by the tests through this module
    read_price_alerts,  # noqa: F401  read by the tests through this module
    read_place_alerts,  # noqa: F401  read by the tests through this module
    read_latest_run,  # noqa: F401  read by the tests through this module
    read_latest_by_source,  # noqa: F401  read by the tests through this module
    read_cached_all_variations,  # noqa: F401  read by the tests through this module
    NATIONAL_KEY,  # noqa: F401  read by the tests through this module
    read_channel_national_prices,  # noqa: F401  read by the tests through this module
    describe_product,  # noqa: F401  read by the tests through this module
    get_secret,  # noqa: F401  read by the tests through this module
    get_last_github_answers,  # noqa: F401  read by the tests through this module
    fetch_pipeline_runs,  # noqa: F401  read by the tests through this module
    read_lineage,
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
    ALL_VALUES,  # noqa: F401  read by the tests through this module
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
    REPORT_PARAMETER,  # noqa: F401  read by the tests through this module
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
    ADMIN_UNLOCKED,  # noqa: F401  read by the tests through this module
    FOLDER_DOCUMENTS,  # noqa: F401  read by the tests through this module
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

# region Constants
# D-283: every text a reader sees goes through tr, which gives its English when the reader chose English.
tr = i18n.tr
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
IDLE_ANIMATION_SCRIPT = static_files.script("idle_animation.js")

FOLD_SIDEBAR_SCRIPT = static_files.script(
    "fold_sidebar.js",
    {
        '__GO_NARROW_SCREEN_WIDTH__': NARROW_SCREEN_WIDTH,
    },
)

# D-462: a dashboard opens with the menu folded, so its charts get the width; the button that unfolds it beats in the
# green of GreenOcean (D-450), so it is seen. It folds once per page opened: a menu the reader opens stays open while
# the reader works on that page. A phone turned sideways keeps its menu open (D-166).
DASHBOARD_FOLD_SCRIPT = static_files.script("dashboard_fold.js")

# D-166: the panel is read in landscape. A phone held upright sees one screen asking to
# turn it (no page can rotate a phone: only the reader can); turned, the phone gets
# the computer layout in miniature, every page whole, and no empty band on top.
# Tablets and computers never match these queries. Plain fills only: st.html strips
# SVG gradients.
PHONE_LAYOUT_HTML = static_files.read("phone_layout.html")

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

# The parameters every address carries (theme, language, view) never make a new step.
CONTEXT_PARAMETERS = {THEME_PARAMETER, i18n.LANGUAGE_PARAMETER, PROFILE_PARAMETER, ROLE_PARAMETER, "_ctx"}

RELOAD_HOME_SCRIPT = static_files.script("reload_home.js").replace("__HOME__", PAGE_HOME)

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

SHOW_SOURCES_SCRIPT = static_files.script("show_sources.js")
# endregion


# region Variables
# D-172: Streamlit reloads this file on each run but keeps the imported bi/* modules
# as they were; on Streamlit Cloud a push then shows a new menu with old pages until
# someone reboots the app. Each run compares the modules' files with the time they
# were loaded and reloads the ones that changed, dependencies first.
# The times live on the bi package, which outlives the script runs: Streamlit
# re-executes this file on every run, so a global here would start empty each time.
MODULE_TIMES = vars(bi).setdefault("MODULE_TIMES", {})
# endregion


# region Windows and pages
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
    redirect = functools.partial(redirect_to_view, view, windows_by_title)
    return st.Page(redirect, title=view, url_path=url_path, visibility="hidden")


def redirect_to_view(view, windows_by_title):
    """What a hidden page at an old address does: it opens its window on the same view, with the same parameters."""
    parameters = {key: value for key, value in st.query_params.to_dict().items()}
    window = WINDOW_OF_VIEW[view]
    if view != read_window_views(window)[0]:
        parameters[VIEW_PARAMETER] = view
    st.switch_page(windows_by_title[window], query_params=parameters)


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


# endregion


# region Footers of the pages
def show_dashboard_menu_fold(view, mode):
    """D-462, D-463, D-466: on going to a dashboard or a page of diagrams the menu folds and its button beats in green;
    elsewhere it stays. Each load of the app, its entry, opens it."""
    is_dashboard = view in FOLD_MENU_VIEWS
    if is_dashboard:
        green = ba_green(mode)
        st.markdown(
            static_files.style(
                "menu_fold.css",
                {
                    'var(--go-green)': green,
                },
            ),
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


# endregion


# region History of «Volver»
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


def build_visit_history_script():
    snapshot = {key: st.session_state[key] for key in RETURN_CONTEXT_KEYS if key in st.session_state}
    encoded = json.dumps(snapshot, ensure_ascii=True, default=str).replace("<", "\\u003c")
    return static_files.script("visit_history.js").replace("__FILTERS__", encoded)


# endregion


# region The menu and its activity bar
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
        # D-551: the KPIs of the panel, in one window, for every view.
        with st.container(key="stack_tile_kpi"):
            title = i18n.translate_text("Los KPI del panel")
            if st.button(tr("KPI"), key="kpi_window", help=title):
                st.dialog(title, width="large")(show_kpi_window)(get_mode())
        with st.container(key="sources_tile"):
            with st.popover(tr("Fuentes"), help=tr("Fuentes de datos")):
                st.markdown(f"**{tr('Fuentes de datos')}**")
                for name, url in SOURCE_LINKS:
                    st.markdown(
                        buttons.build_link_html(tr(name), url, icon="external", variant="text", external=True),
                        unsafe_allow_html=True,
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


# endregion


# region Start
def read_bi_imports(file):
    """D-541: the bi modules a module imports, read from its source, wherever the import sits."""
    names = set()
    for node in ast.walk(ast.parse(Path(file).read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module == "bi":
            names |= {f"bi.{alias.name}" for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("bi."):
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names if alias.name.startswith("bi.")}
    return names


def order_reloads(changed, imports):
    """D-541: the changed modules and every module that imports one of them, directly or not, dependencies first.
    Since the panel was split, a page holds the functions it imported from the frame: reloading only the frame would
    leave the page with the old ones, so the pages that import it reload after it."""
    stale = set(changed)
    grew = True
    while grew:
        grew = False
        for name, uses in imports.items():
            if name not in stale and uses & stale:
                stale.add(name)
                grew = True
    ordered = []
    remaining = set(stale)
    while remaining:
        ready = sorted(name for name in remaining if not (imports.get(name, set()) & (remaining - {name})))
        for name in ready or sorted(remaining):  # a cycle has no first module: a fixed order then
            ordered.append(name)
            remaining.discard(name)
    return ordered


def reload_changed_modules():
    """Reload every bi/* module whose file changed since it was loaded, and the ones that import it (D-541)."""
    package = Path(__file__).resolve().parent
    loaded, changed = {}, []
    for name, module in sorted(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if not name.startswith("bi.") or name == __name__ or not file or not file.startswith(str(package)):
            continue
        try:
            modified = os.stat(file).st_mtime_ns
        except OSError:
            continue
        loaded[name] = module
        if name not in MODULE_TIMES:
            MODULE_TIMES[name] = modified
        elif modified != MODULE_TIMES[name]:
            MODULE_TIMES[name] = modified
            changed.append(name)
    if not changed:
        return []
    imports = {name: read_bi_imports(module.__file__) & set(loaded) for name, module in loaded.items()}
    ordered = order_reloads(changed, imports)
    for name in ordered:
        importlib.reload(loaded[name])
    return ordered


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
