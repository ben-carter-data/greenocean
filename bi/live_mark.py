"""D-510: «en vivo», the mark of a figure read from the base when the page opens.

A number read from the database looks the same as a number written by hand. The mark says which one it is: a green
dot that beats slowly beside the figures, with the words «en vivo · leído de la base al abrir» and, on hover, what was
read. A drawing that does not measure anything carries no mark, so the difference can be seen.
"""

import html
from bi import static_files

# region Constants
TEXT = "en vivo · leído de la base al abrir"
GREEN_DARK, GREEN_LIGHT = "#3dd68c", "#1f8f5f"
# endregion


# region «en vivo», the mark of a figure read from the base
def build_html(what, extra=""):
    """The mark: a dot that beats and the words; «what» is what was read, shown on hover."""
    classes = "live-mark" + (f" {extra}" if extra else "")
    return (
        f'<span class="{classes}" title="{html.escape(str(what), quote=True)}"><i aria-hidden="true"></i>{TEXT}</span>'
    )


def build_css(dark):
    """The style of the mark, for the page and for a drawing in its own frame. One beat per second; still when the
    reader asked for less motion."""
    green = GREEN_DARK if dark else GREEN_LIGHT
    return static_files.fill(
        "live_mark.css",
        {
            'var(--go-green)': green,
        },
    )


# endregion
