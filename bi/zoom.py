"""Zoom and pan inside a diagram frame, on phones and computers (T-59).

By default a diagram fits the width of its frame and shows whole. Two fingers
zoom in (pinch), one finger or the mouse drags it, and three discreet buttons
under the frame zoom in, zoom out and reset. Only the frame moves; the page does not.

Zooming widens the diagram itself instead of enlarging a picture of it, so the
browser draws the SVG again at its new size: it stays sharp at any zoom. The
shape never changes. No library: one script for the whole page.
"""

from bi import static_files

# region Constants
ZOOM_STEP = 1.5
MAXIMUM_ZOOM = 6
# endregion

# region Variables
ZOOM_SCRIPT = (  # D-543: the script lives in bi/static/zoom.js; its two numbers come from here
    "<script>"
    + static_files.read("zoom.js")
    .replace("__ZOOM_STEP__", str(ZOOM_STEP))
    .replace("__MAXIMUM_ZOOM__", str(MAXIMUM_ZOOM))
    + "</script>"
)
# Every piece of a diagram that carries an SVG <title> explains itself in a card that
# opens at once on hover and stays open on a click or a tap; a second click, Escape or
# a click elsewhere closes it. The native browser tooltip came late, only on hover and
# never on a phone. The <title> text moves to data-tip, so both never show together.
TIP_SCRIPT = static_files.script("diagram_tips.js")
# endregion


# region Zoom and pan inside a diagram frame, on phones and computers
def build_zoom_frame_html(inner_html, css_class="", style=""):
    """A frame the zoom script turns into a zoomable view of inner_html."""
    style_attribute = f' style="{style}"' if style else ""
    return (
        f'<div class="zoom-frame {css_class}"{style_attribute}><div class="zoom-viewport">'
        f'<div class="zoom-content">{inner_html}</div></div></div>'
    )


def build_zoom_css(palette):
    """Frame, viewport and buttons in the colors of the active theme."""
    return static_files.fill(
        "zoom.css",
        {
            'var(--go-card)': palette["card"],
            'var(--go-strong-text)': palette["strong_text"],
            'var(--go-card-border)': palette["card_border"],
            'var(--go-accent)': palette["accent"],
        },
    )


# endregion
