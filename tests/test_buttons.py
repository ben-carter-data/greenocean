"""D-281: one button and link component for the whole panel (bi/buttons.py, styled once in bi/premium.css)."""
import re
from pathlib import Path

import pytest

from bi import buttons, charts, page_bar

BI_DIR = Path(buttons.__file__).parent
FINISH = (BI_DIR / "premium.css").read_text(encoding="utf-8")


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]


def contrast(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + .05) / (low + .05)


def test_d281_the_component_is_styled_once_and_no_old_link_style_is_left():
    assert FINISH.count(".stApp .go-btn,") == 1 and ".go-btn--primary" in FINISH and ".go-btn--text" in FINISH
    assert ".go-btn--compact" in FINISH and ":focus-visible" in FINISH
    for path in BI_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\.go-btn[\w-]* ?\{", text), path.name  # the look lives only in premium.css
        assert ".doc-print {" not in text and ".page-bar-link" not in text, path.name


@pytest.mark.parametrize("variant", buttons.VARIANTS)
@pytest.mark.parametrize("size", buttons.SIZES)
def test_d281_every_variant_and_size_writes_the_component(variant, size):
    link = buttons.build_link_html("Abrir", "https://example.org", icon="github", variant=variant, size=size,
                                   external=True)
    assert f'class="go-btn go-btn--{variant} go-btn--{size}"' in link and 'class="go-icon go-icon-github"' in link
    assert "<svg" not in link  # st.html drops inline SVG: the icon is a mask
    assert 'target="_blank" rel="noopener noreferrer"' in link and "↗" in link
    button = buttons.build_button_html("Imprimir", icon="print", variant=variant, size=size, extra="doc-print")
    assert button.startswith(f'<button class="go-btn go-btn--{variant} go-btn--{size} doc-print" type="button">')


def test_d281_the_bars_the_documents_and_the_print_use_the_component():
    from bi import dashboard
    assert page_bar.build_link_html("Plan", "/plan", "nota").startswith('<a class="go-btn go-btn--secondary go-btn--compact"')
    assert dashboard.PRINT_BUTTON_HTML.startswith('<button class="go-btn go-btn--primary go-btn--normal doc-print"')
    assert 'class="go-btn go-btn--text' in dashboard.build_external_link_html("Ver en GitHub", "https://github.com")
    assert 'class="go-btn go-btn--secondary' in dashboard.build_external_link_html("x en GitHub", "https://github.com",
                                                                                     "secondary")


@pytest.mark.parametrize("theme", charts.THEMES)
def test_d281_the_component_reads_with_aa_contrast_in_every_theme(theme):
    palette = charts.get_palette(theme)
    for surface in (palette["background"], palette["card"]):
        assert contrast(palette["strong_text"], surface) >= 4.5, (theme, surface)  # the label
        assert contrast(palette["accent"], surface) >= 4.5, (theme, surface)  # the text variant and the halo
        assert contrast(palette["accent"], surface) >= 3  # the border on hover, a non-text element


def test_d281_every_icon_has_its_mask():
    css = buttons.build_icon_css()
    for name in buttons.ICONS:
        assert f".stApp .go-icon-{name} {{-webkit-mask-image:url(\"data:image/svg+xml," in css, name
