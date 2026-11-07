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
def test_d504_the_footer_lives_in_the_flow_pushed_to_the_end_and_stuck_to_the_bottom(mode):
    css = dashboard.build_sidebar_css(mode)
    footer = rule_of(css, ".st-key-sidebar_footer")
    assert "position:fixed" not in footer and "bottom:0" not in footer and "width:232px" not in footer
    assert f"background:{charts.get_palette(mode)['sidebar']}" in footer and "border-top:1px solid" in footer
    wrapper = rule_of(css, FOOTER_WRAPPER)
    assert "margin:auto -8px 0" in wrapper and "width:calc(100% + 16px)" in wrapper and "max-width:none" in wrapper
    assert "position:sticky; bottom:0; z-index:5" in wrapper


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


@pytest.mark.parametrize("mode", sorted(charts.THEMES))
def test_d538_the_two_folders_and_the_sources_share_one_compact_row(mode):
    """The footer's three tiles sit side by side in one row of 62 px, so «Calidad» is in sight when the app opens."""
    css = dashboard.build_sidebar_css(mode)
    tile = rule_of(css, '[class*="st-key-nav_folder_tile"] [data-testid="stPageLink"] a, .st-key-sources_tile button')
    assert "height:62px" in tile and "sidebar_sources_row" not in css
    source = Path(dashboard.__file__).read_text(encoding="utf-8")
    tiles = source[source.index("def show_footer_tiles") :]
    lines = tiles[: tiles.index("\ndef ")].splitlines()
    row = next(line for line in lines if 'container(key="sidebar_tiles"' in line)
    sources = next(line for line in lines if 'container(key="sources_tile")' in line)
    indent = len(row) - len(row.lstrip())
    assert len(sources) - len(sources.lstrip()) == indent + 4  # the sources tile lives inside the row
