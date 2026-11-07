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
    return f"""
    .zoom-viewport {{ overflow: hidden; touch-action: pan-y; border-radius: 12px; }}
    .zoom-frame.zoomed .zoom-viewport {{ touch-action: none; cursor: grab; }}
    .zoom-content {{ width: 100%; }}
    /* Only the diagram itself: a logo nested inside it keeps its own size. */
    .zoom-content > img, .zoom-content > svg {{ display: block; width: 100%; height: auto; }}
    .zoom-content .has-tooltip {{ cursor: help; }}
    /* A row under the frame, aligned right: the buttons never cover the diagram. */
    .zoom-buttons {{ display: flex; justify-content: flex-end; gap: 4px; margin-top: 6px;
                     opacity: 0.75; }}
    .zoom-buttons:hover, .zoom-buttons:focus-within {{ opacity: 1; }}
    .zoom-buttons button {{ width: 32px; height: 32px; padding: 0; border-radius: 8px;
                            cursor: pointer; font-size: 16px; line-height: 1;
                            background: {palette["card"]}; color: {palette["strong_text"]};
                            border: 1px solid {palette["card_border"]}; }}
    .zoom-buttons button:hover {{ color: {palette["accent"]};
                                  border-color: {palette["accent"]}; }}
    @media (max-width: 640px) {{
        .zoom-buttons button {{ width: 28px; height: 28px; font-size: 14px; }}
    }}
    """


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
TIP_SCRIPT = r"""<script>
(() => {
if (window.diagramTipsReady) { return; }
window.diagramTipsReady = true;
const AREAS = ".zoom-content svg, .lineage-frame svg, .doc-diagram svg";
const card = document.createElement("div");
card.className = "diagram-tip";
card.setAttribute("role", "tooltip");
Object.assign(card.style, {position: "fixed", zIndex: 10000, maxWidth: "340px", display: "none",
    padding: "10px 13px", borderRadius: "12px", background: "rgba(15,23,42,.97)", color: "#e2e8f0",
    border: "1px solid rgba(148,163,184,.35)", boxShadow: "0 18px 36px -12px rgba(0,0,0,.55)",
    font: "13px/1.45 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif", pointerEvents: "none"});
document.body.appendChild(card);
let pinned = null;

// The card is built node by node, never from an HTML string.
const line = (parent, text, style) => {
    const node = document.createElement("div");
    node.textContent = text;
    Object.assign(node.style, style || {});
    parent.appendChild(node);
};
// «Nombre (Sigla) — qué es. Aquí: su papel.»: the name in bold, the role on its own line.
const render = (text) => {
    card.replaceChildren();
    for (const entry of text.split("\n").filter(Boolean)) {
        const block = document.createElement("div");
        block.style.margin = "2px 0 7px";
        const parts = entry.split(" — ");
        const head = parts.length > 1 ? parts.shift() : "";
        const [what, role] = parts.join(" — ").split(/\s*(?:Aquí|Here):\s*/);  // D-443: both languages
        if (head) { line(block, head, {fontWeight: "700", color: "#fff"}); }
        line(block, what);
        if (role) { line(block, "En este proyecto:" + " " + role, {color: "#bae6fd", marginTop: "3px"}); }
        card.appendChild(block);
    }
};

const prepare = () => document.querySelectorAll(AREAS).forEach((svg) => {
    svg.querySelectorAll("title").forEach((title) => {
        const owner = title.parentElement;
        if (!owner || owner.tagName.toLowerCase() === "svg" || !title.textContent.trim()) { return; }
        owner.dataset.tip = title.textContent.trim();
        owner.style.cursor = "help";
        // Emptied, never removed: React owns these nodes and removes them itself later.
        title.textContent = "";
    });
});

const place = (x, y) => {
    const box = card.getBoundingClientRect();
    let left = x + 14, top = y + 16;
    if (left + box.width > innerWidth - 8) { left = x - box.width - 14; }
    if (top + box.height > innerHeight - 8) { top = y - box.height - 16; }
    card.style.left = Math.max(8, left) + "px";
    card.style.top = Math.max(8, top) + "px";
};
const show = (owner, x, y) => {
    render(owner.dataset.tip);
    card.style.display = "block";
    place(x, y);
};
const hide = () => { card.style.display = "none"; pinned = null; };
const ownerOf = (event) => event.target.closest && event.target.closest("[data-tip]");

document.addEventListener("pointerover", (event) => {
    const owner = ownerOf(event);
    if (owner && !pinned && event.pointerType === "mouse") { show(owner, event.clientX, event.clientY); }
});
document.addEventListener("pointermove", (event) => {
    if (!pinned && card.style.display === "block" && event.pointerType === "mouse") {
        ownerOf(event) ? place(event.clientX, event.clientY) : hide();
    }
});
document.addEventListener("click", (event) => {
    const owner = ownerOf(event);
    if (!owner) { if (pinned) { hide(); } return; }
    if (pinned === owner) { hide(); return; }
    show(owner, event.clientX, event.clientY);
    pinned = owner;
});
document.addEventListener("keydown", (event) => { if (event.key === "Escape") { hide(); } });
addEventListener("scroll", () => { if (!pinned) { card.style.display = "none"; } }, true);

prepare();
new MutationObserver(prepare).observe(document.body, {childList: true, subtree: true});
})();
</script>"""
# endregion
