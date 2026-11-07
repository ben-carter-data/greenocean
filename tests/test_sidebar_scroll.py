"""D-504: the menu does not scroll towards a void; its logo, its fold button and its footer stay in sight."""

import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from bi import charts, dashboard  # noqa: E402

HEADER_HEIGHT = 72  # the logo's 52 px plus the 20 px of air under it, both owned by the sticky header
FOOTER_WRAPPER = (
    '[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"]\n'
    '        > [data-testid="stLayoutWrapper"]:has(> .st-key-sidebar_footer)'
)


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
    source = Path(dashboard.__file__).read_text(encoding="utf-8")
    footer = source[source.index("def show_sidebar_footer") :]
    footer = footer[: footer.index("\ndef ")]
    assert "st.html(" not in footer and "<script" not in footer and 'container(key="sidebar_footer")' in footer


def test_d539_each_icon_of_the_bar_is_named_on_hover():
    source = Path(dashboard.__file__).read_text(encoding="utf-8")
    tiles = source[source.index("def show_folder_tile") :]
    assert "help=tr(view)" in tiles[: tiles.index("\ndef ")]
    sources = source[source.index("def show_footer_tiles") :]
    assert 'help=tr("Fuentes de datos")' in sources[: sources.index("\ndef ")]
