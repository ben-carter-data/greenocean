"""D-510: «en vivo», the mark of a figure read from the base when the page opens.

A number read from the database looks the same as a number written by hand. The mark says which one it is: a green
dot that beats slowly beside the figures, with the words «en vivo · leído de la base al abrir» and, on hover, what was
read. A drawing that does not measure anything carries no mark, so the difference can be seen.
"""

import html

TEXT = "en vivo · leído de la base al abrir"
GREEN_DARK, GREEN_LIGHT = "#3dd68c", "#1f8f5f"


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
    return f"""
.live-mark {{ display:inline-flex; align-items:center; gap:6px; flex:none; font-size:11.5px; line-height:1.2;
  letter-spacing:.01em; color:{green}; white-space:nowrap; cursor:help; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
.live-mark i {{ width:7px; height:7px; border-radius:50%; background:{green}; box-shadow:0 0 0 0 {green};
  animation:live-mark-beat 1s ease-in-out infinite; }}
@keyframes live-mark-beat {{ 0%, 100% {{ opacity:1; box-shadow:0 0 0 0 {green}; }}
  50% {{ opacity:.45; box-shadow:0 0 0 4px color-mix(in srgb, {green} 25%, transparent); }} }}
@media (prefers-reduced-motion: reduce) {{ .live-mark i {{ animation:none; }} }}
"""
