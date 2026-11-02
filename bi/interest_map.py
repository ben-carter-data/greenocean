"""The interest map of «Interesados» (D-444): three rings around GreenOcean and each stakeholder on its ring, read from
the PRD (3.4). D-455: the page and the PRD draw it from this one module, so the two never differ."""

import html
import math

from bi import charts

# Each ring (high, medium, low) is an ellipse around GreenOcean, a tilted disc; each stakeholder sits on its ring at its
# own angle (degrees, 0 to the right, 90 down), so no two names meet.
RINGS = [(0.21, "Interés alto"), (0.335, "Interés medio"), (0.445, "Interés bajo")]
ANGLES = [[160, 20, 90], [212, 328], [163, 17]]
TILT = 0.44  # the vertical radius of a ring over its horizontal one, on screen: the disc seen from above
RATIO = 1.85  # the stage's width over its height
COLORS = ["#5fd39b", "#5aa9ea", "#b49cff"]
CRITERION = "Cada anillo dice cuánto depende su decisión de estos datos y con qué frecuencia los usa."


def place(level, order):
    """Where a stakeholder sits, in % of the stage: on its ring, at its angle."""
    radius = RINGS[level][0]
    angle = math.radians(ANGLES[level][order])
    return 50 + radius * 100 * math.cos(angle), 50 + radius * 100 * RATIO * TILT * math.sin(angle)


def build_map_html(rows, palette, link_of, translate=lambda text: text):
    """The rings, GreenOcean in the middle and each stakeholder as an icon and its name, nothing else; the cursor or the
    keyboard grows the icon and shows why it is on its ring. link_of(row) gives (address, note): with an address the
    stakeholder opens its page, without one it is not a link and the note follows its reason."""
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
        f'<p class="im-criterion">{html.escape(translate(CRITERION))}</p></div>'
    )


def build_css(palette, fit_height=True):
    """The stage keeps its proportions at any width, like a picture; letters and icons scale with it (cqw). On its page
    it is never taller than the window; in a document it takes the document's width."""
    ink, text, muted, background = palette["strong_text"], palette["text"], palette["reference"], palette["background"]
    width = f"min(100%, calc((100vh - 190px) * {RATIO}))" if fit_height else "100%"
    return f"""<style>
    .im-wrap {{ container-type:inline-size; width:{width}; margin:0 auto; }}
    .im-stage {{ position:relative; width:100%; aspect-ratio:{RATIO} / 1; }}
    .im-ring {{ position:absolute; border-radius:50%; border:1.5px solid color-mix(in srgb, var(--ring) 70%, transparent);
        background:radial-gradient(ellipse at 50% 35%, color-mix(in srgb, var(--ring) 9%, transparent),
        color-mix(in srgb, var(--ring) 2%, transparent) 70%);
        box-shadow:0 1.2cqw 2.4cqw -1.6cqw color-mix(in srgb, var(--ring) 45%, transparent); pointer-events:none; }}
    .im-level {{ position:absolute; left:50%; transform:translate(-50%, -50%); padding:0 .8cqw; font-size:max(9px, 1.05cqw);
        font-weight:700; letter-spacing:.09em; text-transform:uppercase; background:{background}; border-radius:1cqw;
        white-space:nowrap; pointer-events:none; }}
    .im-center {{ position:absolute; left:50%; top:50%; transform:translate(-50%, -50%); display:flex; flex-direction:column;
        align-items:center; gap:.3cqw; color:{ink}; font-size:max(11px, 1.5cqw); pointer-events:none; }}
    .im-logo {{ font-family:"Material Symbols Rounded"; font-feature-settings:"liga"; font-size:max(22px, 3.4cqw);
        color:#5aa9ea; line-height:1; }}
    .im-node {{ position:absolute; transform:translate(-50%, -32%); display:flex; flex-direction:column; align-items:center;
        width:15cqw; gap:.35cqw; text-align:center; text-decoration:none !important; color:{ink} !important; outline:none;
        z-index:1; }}
    .im-node:hover, .im-node:focus-visible {{ z-index:3; }}
    .im-icon {{ font-family:"Material Symbols Rounded"; font-feature-settings:"liga";
        font-variation-settings:"FILL" 0, "wght" 300, "GRAD" 0, "opsz" 48; font-size:max(22px, 3.3cqw); line-height:1;
        transition:transform .18s ease; }}
    .im-node:hover .im-icon, .im-node:focus-visible .im-icon {{ transform:scale(1.35); }}
    .im-name {{ font-size:max(10px, 1.3cqw); font-weight:600; line-height:1.25; color:{ink};
        text-shadow:0 0 3px {background}, 0 0 3px {background}, 0 0 6px {background}; }}
    .im-node:focus-visible .im-name {{ text-decoration:underline; text-underline-offset:3px; }}
    .im-why {{ max-height:0; overflow:hidden; opacity:0; font-size:max(9.5px, 1.02cqw); line-height:1.35; color:{text};
        background:{background}; border-radius:.6cqw; padding:0 .6cqw; transition:opacity .18s ease, max-height .18s ease; }}
    .im-node:hover .im-why, .im-node:focus-visible .im-why {{ max-height:12cqw; opacity:1; }}
    .im-criterion {{ margin:.4rem 0 0; text-align:center; font-size:13px; color:{charts.legible(muted, background)}; }}
    </style>"""
