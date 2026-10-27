"""The one button and link component of the panel (D-281).

Its look lives once, in bi/premium.css (`.go-btn`): a 1 px border, soft corners, an almost transparent glass fill, a
thin icon on the left and, on hover or keyboard focus, the accent of the theme on the border with a halo. The same
rule dresses the page links Streamlit draws for «Anterior / Siguiente». This module writes the markup.
"""

import html
from urllib.parse import quote

VARIANTS = ("primary", "secondary", "text")
SIZES = ("compact", "normal")
# Thin line icons, 24-unit grid, drawn with the text color.
ICONS = {
    "github": '<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 '
    '4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 '
    '4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>',
    "print": '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 14h12v7H6z"/>',
    "external": '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>',
    "arrow": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "document": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'
    '<path d="M9 13h6M9 17h6"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "language": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18"/>',
}


def build_icon_html(name):
    """An icon as a span: st.html drops inline SVG, so the drawing travels as a CSS mask (build_icon_css)."""
    return f'<span class="go-icon go-icon-{name}" aria-hidden="true"></span>'


def build_icon_css():
    """One mask per icon, painted with the text color of the component."""
    rules = []
    for name, body in ICONS.items():
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
        )
        address = f'url("data:image/svg+xml,{quote(svg)}")'
        rules.append(f".stApp .go-icon-{name} {{-webkit-mask-image:{address};mask-image:{address};}}")
    return "\n".join(rules)


def build_class(variant="secondary", size="normal", extra=""):
    assert variant in VARIANTS and size in SIZES, (variant, size)
    return " ".join(part for part in ("go-btn", f"go-btn--{variant}", f"go-btn--{size}", extra) if part)


def build_link_html(text, address, *, icon=None, variant="secondary", size="normal", external=False, note=""):
    """A link drawn as the component; an external one opens a new tab and says so with ↗."""
    target = ' target="_blank" rel="noopener noreferrer"' if external else ' target="_self"'
    title = f' title="{html.escape(note, quote=True)}"' if note else ""
    mark = build_icon_html(icon) if icon else ""
    return (
        f'<a class="{build_class(variant, size)}" href="{html.escape(address, quote=True)}"{target}{title}>'
        f'{mark}<span>{html.escape(text)}{" ↗" if external else ""}</span></a>'
    )


def build_button_html(text, *, icon=None, variant="secondary", size="normal", extra=""):
    """A button drawn as the component; its behaviour is attached by the caller's script, by its class."""
    mark = build_icon_html(icon) if icon else ""
    return f'<button class="{build_class(variant, size, extra)}" type="button">{mark}<span>{html.escape(text)}</span></button>'
