"""D-504: the menu does not scroll towards a void; its logo, its fold button and its footer stay in sight."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts, dashboard  # noqa: E402

# region Constants
HEADER_HEIGHT = 72  # the logo's 52 px plus the 20 px of air under it, both owned by the sticky header
FOOTER_WRAPPER = (
    '[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"]\n'
    '        > [data-testid="stLayoutWrapper"]:has(> .st-key-sidebar_footer)'
)
# endregion


# region The menu does not scroll towards a void
def rule_of(css, selector):
    """The declarations of the first rule whose selector is exactly `selector`."""
    start = css.index(selector + " {")
    return css[start : css.index("}", start)]


@pytest.mark.parametrize("mode", sorted(charts.THEMES))
def test_d504_the_menu_column_is_the_window_and_no_padding_reserves_space_for_the_footer(mode):
    css = dashboard.build_sidebar_css(mode)
    assert "padding-bottom:140px" not in css and "100vh - 86px" not in css and "padding-bottom:116px" not in css
    column = rule_of(css, '[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"]')
    assert f"min-height:calc(100vh - {HEADER_HEIGHT}px)" in column and "padding-bottom:0" in column
    assert rule_of(css, '[data-testid="stSidebarUserContent"]').endswith("{padding:0 8px !important;")


@pytest.mark.parametrize("mode", sorted(charts.THEMES))
def test_d539_the_footer_is_a_column_of_icons_on_the_menus_left_edge(mode):
    """Like VS Code's activity bar: the footer leaves the end of the menu, which keeps the whole height of the window."""
    css = dashboard.build_sidebar_css(mode)
    bar = dashboard.ACTIVITY_BAR
    wrapper = rule_of(css, FOOTER_WRAPPER)
    assert "position:fixed !important; top:0 !important" in wrapper and f"width:{bar}px !important" in wrapper
    assert "sticky" not in wrapper and "margin:auto" not in wrapper
    footer = rule_of(css, ".st-key-sidebar_footer")
    assert "justify-content:space-between" in footer and "border-right:1px solid" in footer
    width = rule_of(css, '[data-testid="stSidebar"][data-collapsed="false"]')
    assert f"min-width:{232 + bar}px" in width  # the menu keeps its 232 px beside the bar (D-501)
    assert f"padding-left:{bar + 8}px !important" in css and f"padding-left:{bar + 16}px !important" in css
    assert '[data-collapsed="true"] .st-key-sidebar_footer {display:none !important;}' in css
    tile = rule_of(css, '[class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a, .st-key-sources_tile button')
    assert "width:34px !important; height:34px" in tile


@pytest.mark.parametrize("mode", sorted(charts.THEMES))
def test_d504_the_header_with_the_logo_and_the_fold_button_is_stuck_to_the_top(mode):
    css = dashboard.build_sidebar_css(mode)
    header = rule_of(css, '[data-testid="stSidebarHeader"]')
    assert f"height:{HEADER_HEIGHT}px" in header and "margin-bottom:0 !important" in header
    assert "position:sticky; top:0; z-index:6" in header
    assert f"background:{charts.get_palette(mode)['sidebar']}" in header
    assert "padding:12px 10px 26px 16px !important" in header  # the logo and the button keep their place (D-501)


def test_d504_the_turned_phone_grows_the_menu_column_with_its_sidebar():
    phone = dashboard.PHONE_LAYOUT_HTML
    landscape = phone[phone.index("@media (orientation:landscape) and (max-height:500px)") :]
    assert '[data-testid="stSidebar"] {height:161.3vh !important;' in landscape
    assert (
        '[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] '
        f"{{min-height:calc(161.3vh - {HEADER_HEIGHT}px) !important;}}"
    ) in landscape


def test_d504_the_menu_never_moves_its_nodes_with_a_script():
    """Streamlit owns the DOM (CLAUDE.md): the footer and the header are placed with CSS alone."""
    from tests import code_shape

    footer = code_shape.tree_of(dashboard.show_sidebar_footer)
    assert not code_shape.calls(footer, "st.html") and not code_shape.calls_named(footer, "html")  # no script runs here
    keys = {code_shape.keyword(call, "key") for call in code_shape.calls_named(footer, "container")}
    assert code_shape.normal('"sidebar_footer"') in keys


def test_d539_each_icon_of_the_bar_is_named_on_hover():
    from tests import code_shape  # R-004: the shape of the code, not its text

    links = code_shape.calls(code_shape.tree_of(dashboard.show_folder_tile), "st.page_link")
    assert "tr(view)" in {code_shape.keyword(call, "help") for call in links}
    popovers = code_shape.calls(code_shape.tree_of(dashboard.show_footer_tiles), "st.popover")
    assert code_shape.normal('tr("Fuentes de datos")') in {code_shape.keyword(call, "help") for call in popovers}


@pytest.mark.parametrize("mode", sorted(charts.THEMES))
def test_d540_every_button_of_the_bar_has_a_line_icon_in_one_tone(mode):
    from bi import activity_bar

    css = dashboard.build_sidebar_css(mode)
    # documents, study, sources, the KPI window (D-551) and the areas
    assert css.count(" mask:url(") == 4 + len(activity_bar.STACK_AREAS)
    for key, _, icon, _ in activity_bar.STACK_AREAS:
        assert f".st-key-stack_tile_{key} button::before" in css and icon in activity_bar.ICONS


def test_d540_the_stack_of_every_area_is_in_the_bar_for_every_view():
    from streamlit.testing.v1 import AppTest

    from bi import activity_bar

    assert [title for _, title, _, _ in activity_bar.STACK_AREAS] == [
        "Stack · Código",
        "Stack · Ingeniería de datos",
        "Stack · Calidad",
        "Stack · DevOps y seguridad",
        "Stack · Negocio · BA y BI",
    ]
    assert all(len(names) >= 7 and len(set(names)) == len(names) for _, _, _, names in activity_bar.STACK_AREAS)
    for profile in (dashboard.PROFILE_PUBLIC, dashboard.PROFILE_PROFESSIONAL):
        app = AppTest.from_file(str(Path(dashboard.__file__)), default_timeout=90)
        app.session_state[dashboard.PROFILE_STATE] = profile
        app.run()
        assert not app.exception
        labels = [popover.proto.popover.label for popover in app.sidebar.get("popover")]
        assert all(title in labels for _, title, _, _ in activity_bar.STACK_AREAS), (profile, labels)
        lists = [block.value for block in app.sidebar.markdown if 'class="stack-list"' in block.value]
        assert len(lists) == len(activity_bar.STACK_AREAS) and not any("<a " in block for block in lists)  # names only


# endregion
