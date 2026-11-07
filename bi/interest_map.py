"""The interest map of «Interesados» (D-444): three rings around GreenOcean and each stakeholder on its ring, read from
the PRD (3.4). D-455: the page and the PRD draw it from this one module, so the two never differ."""

import html
import math

from bi import charts, static_files

# region Constants
# Each ring (high, medium, low) is an ellipse around GreenOcean, a tilted disc; each stakeholder sits on its ring at its
# own angle (degrees, 0 to the right, 90 down), so no two names meet.
RINGS = [(0.21, "Interés alto"), (0.335, "Interés medio"), (0.445, "Interés bajo")]
ANGLES = [[160, 20, 90], [212, 328], [163, 17]]
TILT = 0.44  # the vertical radius of a ring over its horizontal one, on screen: the disc seen from above
RATIO = 1.85  # the stage's width over its height
COLORS = ["#5fd39b", "#5aa9ea", "#b49cff"]
CRITERION = "Cada anillo dice cuánto depende su decisión de estos datos y con qué frecuencia los usa."
# endregion


# region The interest map of «Interesados»
def place(level, order):
    """Where a stakeholder sits, in % of the stage: on its ring, at its angle."""
    radius = RINGS[level][0]
    angle = math.radians(ANGLES[level][order])
    return 50 + radius * 100 * math.cos(angle), 50 + radius * 100 * RATIO * TILT * math.sin(angle)


def build_map_html(rows, palette, link_of, translate=lambda text: text, criterion=True):
    """The rings, GreenOcean in the middle and each stakeholder as an icon and its name, nothing else; the cursor or the
    keyboard grows the icon and shows why it is on its ring. link_of(row) gives (address, note): with an address the
    stakeholder opens its page, without one it is not a link and the note follows its reason. criterion: the rule of
    the rings under the map; the tab says it in its green panel instead (D-458)."""
    background = palette["background"]
    colors = [charts.legible(color, background, 3) for color in COLORS]
    rings = []
    for level, (radius, label) in enumerate(RINGS):
        height = radius * 100 * RATIO * TILT
        rings.append(
            f'<span class="im-ring r{level}" style="left:{50 - radius * 100:.2f}%;width:{radius * 200:.2f}%;'
            f'top:{50 - height:.2f}%;height:{height * 2:.2f}%;--ring:{colors[level]}"></span>'
            f'<span class="im-level" style="top:{50 - height:.2f}%;color:{colors[level]}">'
            f"{html.escape(translate(label))}</span>"
        )
    nodes = []
    seen = [0, 0, 0]
    for row in rows:
        level = row["level"]
        x, y = place(level, seen[level])
        seen[level] += 1
        address, note = link_of(row)
        why = row["why"] + "." + (f" {note}" if note else "")
        inner = (
            f'<span class="im-icon" aria-hidden="true" style="color:{colors[level]}">{row["icon"]}</span>'
            f'<span class="im-name">{html.escape(row["name"])}</span>'
        )
        if address:
            nodes.append(
                f'<a class="im-node" href="{html.escape(address, quote=True)}" target="_self" '
                f'style="left:{x:.2f}%;top:{y:.2f}%">{inner}<span class="im-why">{html.escape(why)}</span></a>'
            )
        else:
            nodes.append(
                f'<span class="im-node" tabindex="0" style="left:{x:.2f}%;top:{y:.2f}%">{inner}'
                f'<span class="im-why">{html.escape(why)}</span></span>'
            )
    return (
        f'<div class="im-wrap"><div class="im-stage" role="img" aria-label="{html.escape(translate("Mapa de interés"))}">'
        f'{"".join(rings)}<span class="im-center"><span class="im-logo" aria-hidden="true">waves</span>'
        f'<b>GreenOcean</b></span>{"".join(nodes)}</div>'
        + (f'<p class="im-criterion">{html.escape(translate(CRITERION))}</p>' if criterion else "")
        + "</div>"
    )


def build_css(palette, fit_height=True, reserved=190):
    """The stage keeps its proportions at any width, like a picture; letters and icons scale with it (cqw). On its page
    it is never taller than the window less the reserved height above and below it; in a document it takes the
    document's width."""
    ink, text, muted, background = palette["strong_text"], palette["text"], palette["reference"], palette["background"]
    width = f"min(100%, calc((100vh - {reserved}px) * {RATIO}))" if fit_height else "100%"
    return static_files.style(
        "interest_map.css",
        {
            'var(--go-width)': width,
            'var(--go-ratio)': RATIO,
            'var(--go-background)': background,
            'var(--go-ink)': ink,
            'var(--go-text)': text,
            'var(--go-charts-legible-muted-background)': charts.legible(muted, background),
        },
    )


# endregion
