"""A 3D icon of its own for each sales channel of ODEPA (D-453), each in its own colours, for the cards of «Último dato
por canal». Every icon is a standalone SVG with its gradients, shown as an image so Streamlit's markdown keeps it whole."""

import base64

# region Constants
# Shared pieces: a soft floor shadow and the gradient helper.
SHADOW = '<ellipse cx="32" cy="58" rx="22" ry="4" fill="#000" opacity=".22"/>'
# endregion


# region Channel icons
def gradient(name, top, bottom, vertical=True):
    direction = 'x1="0" y1="0" x2="0" y2="1"' if vertical else 'x1="0" y1="0" x2="1" y2="0"'
    return f'<linearGradient id="{name}" {direction}><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>'


ICONS = {
    # Wholesale: a stack of crates, orange and brown.
    "Mayorista": (
        gradient("t", "#ffc46b", "#f29d38") + gradient("l", "#e08a2e", "#b8661c") + gradient("r", "#c2701f", "#8f4d12"),
        SHADOW + '<path d="M10 40l12-6 12 6-12 6z" fill="url(#t)"/><path d="M10 40v12l12 6V46z" fill="url(#l)"/>'
        '<path d="M34 40v12l-12 6V46z" fill="url(#r)"/>'
        '<path d="M30 40l12-6 12 6-12 6z" fill="url(#t)"/><path d="M30 40v12l12 6V46z" fill="url(#l)"/>'
        '<path d="M54 40v12l-12 6V46z" fill="url(#r)"/>'
        '<path d="M20 25l12-6 12 6-12 6z" fill="url(#t)"/><path d="M20 25v12l12 6V31z" fill="url(#l)"/>'
        '<path d="M44 25v12l-12 6V31z" fill="url(#r)"/>'
        '<path d="M14 45l6 3M38 30l6-3M24 31l6 3" stroke="#7a3f0c" stroke-width="1.2" opacity=".5"/>',
    ),
    # Supermarket: a shopping cart, blue.
    "Supermercado": (
        gradient("b", "#7cc4ff", "#2f7fe0") + gradient("h", "#b9e0ff", "#5aa9ea"),
        SHADOW
        + '<path d="M6 14h8l7 27h28l6-20H17" fill="none" stroke="url(#h)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M18 21h37l-6 20H23z" fill="url(#b)"/><path d="M24 26h26M26 32h21M28 37h17" stroke="#d8eeff" stroke-width="1.6" opacity=".7"/>'
        '<circle cx="26" cy="50" r="5" fill="#1d4f9a"/><circle cx="26" cy="50" r="2" fill="#b9e0ff"/>'
        '<circle cx="46" cy="50" r="5" fill="#1d4f9a"/><circle cx="46" cy="50" r="2" fill="#b9e0ff"/>',
    ),
    # Street market: a stall with a striped awning over fruit, red and green.
    "Feria libre": (
        gradient("w", "#ff6b6b", "#d93a3a") + gradient("c", "#6fd38a", "#2f9c55") + gradient("p", "#a9744a", "#7a4f2c"),
        SHADOW + '<path d="M12 22h4v34h-4zM48 22h4v34h-4z" fill="url(#p)"/>'
        '<path d="M6 22l6-12h40l6 12z" fill="#fff"/>'
        '<path d="M12 10l-6 12h8l4-12zM26 10l-2 12h8l0-12zM40 10l2 12h8l-4-12z" fill="url(#w)"/>'
        '<path d="M6 22h52v4H6z" fill="#b82f2f"/>'
        '<path d="M10 40h44l-3 8H13z" fill="url(#c)"/>'
        '<circle cx="20" cy="37" r="4.5" fill="#ff8a3d"/><circle cx="30" cy="36" r="4.5" fill="#ffd23f"/>'
        '<circle cx="40" cy="37" r="4.5" fill="#e8463e"/><circle cx="25" cy="33" r="3.5" fill="#8bd450"/>'
        '<circle cx="36" cy="32" r="3.5" fill="#ff8a3d"/>',
    ),
    # Butcher: a marbled steak on a wooden board, crimson.
    "Carnicería": (
        gradient("m", "#ff6f7f", "#c42a45") + gradient("d", "#d9a066", "#9c6a3a"),
        SHADOW
        + '<path d="M6 46l26-10 26 10-26 10z" fill="url(#d)"/><path d="M6 46v3l26 10v-3zM58 46v3L32 59v-3z" fill="#7d5130"/>'
        '<path d="M16 30c0-10 10-16 22-14s16 10 12 18-12 12-22 10-12-6-12-14z" fill="url(#m)"/>'
        '<path d="M16 30c0 8 4 12 12 14 10 2 18-2 22-10" fill="none" stroke="#fff4ec" stroke-width="3" opacity=".9"/>'
        '<path d="M26 24c4 2 8 1 11-2M30 32c3 1 7 0 9-3" stroke="#ffd0d6" stroke-width="1.6" fill="none" opacity=".8"/>'
        '<circle cx="40" cy="27" r="3.4" fill="#fff4ec"/>',
    ),
    # Online supermarket: a phone with a cart on its screen, violet.
    "Supermercado en Línea": (
        gradient("f", "#a98bff", "#6a3fe0") + gradient("s", "#e9e2ff", "#c3b3ff"),
        SHADOW
        + '<rect x="18" y="6" width="28" height="50" rx="6" fill="url(#f)"/><rect x="21" y="11" width="22" height="38" rx="2" fill="url(#s)"/>'
        '<circle cx="32" cy="52.5" r="1.8" fill="#e9e2ff"/>'
        '<path d="M24 22h3l3 12h10l3-9H28" fill="none" stroke="#5a32c8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
        '<circle cx="31" cy="38" r="1.8" fill="#5a32c8"/><circle cx="39" cy="38" r="1.8" fill="#5a32c8"/>'
        '<path d="M46 16l8-4M48 24l9 0" stroke="#a98bff" stroke-width="2.4" stroke-linecap="round"/>',
    ),
    # Retail market: a small shopfront with a teal awning.
    "Mercado Minorista": (
        gradient("a", "#4fe0d0", "#14a596")
        + gradient("wl", "#f4f1ea", "#d6cfc0")
        + gradient("g", "#bfe9ff", "#7cc4ef"),
        SHADOW + '<path d="M10 24h44v32H10z" fill="url(#wl)"/>'
        '<path d="M6 14h52l-4 12H10z" fill="url(#a)"/>'
        '<path d="M10 26c0 3 3 5 6 5s6-2 6-5c0 3 3 5 6 5s6-2 6-5c0 3 3 5 6 5s6-2 6-5c0 3 3 5 6 5s6-2 6-5" fill="#0f8679"/>'
        '<rect x="15" y="36" width="14" height="12" rx="1.5" fill="url(#g)"/><rect x="35" y="36" width="12" height="20" rx="1.5" fill="#0f8679"/>'
        '<circle cx="44" cy="46" r="1.2" fill="#e8fffb"/>',
    ),
    # Bakery: a golden loaf with its scores.
    "Panadería": (
        gradient("br", "#ffd27a", "#d9932b") + gradient("bs", "#c47a1e", "#8f5412"),
        SHADOW + '<path d="M8 40c0-14 12-22 24-22s24 8 24 22c0 6-4 10-10 10H18c-6 0-10-4-10-10z" fill="url(#bs)"/>'
        '<path d="M9 37c0-12 11-19 23-19s23 7 23 19c0 4-4 6-8 6H17c-4 0-8-2-8-6z" fill="url(#br)"/>'
        '<path d="M20 26l5 9M30 23l4 11M41 25l3 9" stroke="#fff1cf" stroke-width="2.6" stroke-linecap="round" opacity=".85"/>'
        '<path d="M14 33c4-8 12-12 18-12" stroke="#fff6dd" stroke-width="2" fill="none" opacity=".6"/>',
    ),
    # Wholesale market: a delivery truck, indigo with a gold cargo stripe.
    "Mercado Mayorista": (
        gradient("k", "#8a94ff", "#4a52d6") + gradient("cb", "#c7ccff", "#8a94ff"),
        SHADOW + '<rect x="4" y="18" width="34" height="28" rx="3" fill="url(#k)"/>'
        '<path d="M8 30h26" stroke="#ffc94a" stroke-width="3"/>'
        '<path d="M38 26h10l8 9v11H38z" fill="url(#cb)"/><path d="M41 29h6l5 6H41z" fill="#e8ebff"/>'
        '<circle cx="15" cy="49" r="5.5" fill="#262a6b"/><circle cx="15" cy="49" r="2.2" fill="#c7ccff"/>'
        '<circle cx="46" cy="49" r="5.5" fill="#262a6b"/><circle cx="46" cy="49" r="2.2" fill="#c7ccff"/>',
    ),
}
# A channel the data adds later still gets a mark: a neutral 3D tag.
FALLBACK = (
    gradient("n", "#c3cad6", "#7d8796"),
    SHADOW + '<path d="M12 14h24l16 16-20 20-20-20z" fill="url(#n)"/><circle cx="24" cy="24" r="4" fill="#eef2f7"/>',
)


def svg(channel):
    """The channel's icon as one SVG document; each is its own image, so two icons' gradient names never clash."""
    defs, body = ICONS.get(channel, FALLBACK)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs>{defs}</defs>{body}</svg>'


def image(channel, size=44):
    """The icon as an image tag; an image keeps its gradients where markdown would strip them."""
    data = base64.b64encode(svg(channel).encode()).decode()
    return (
        f'<img class="ch-icon" src="data:image/svg+xml;base64,{data}" width="{size}" height="{size}" alt="" '
        'aria-hidden="true">'
    )


# endregion
