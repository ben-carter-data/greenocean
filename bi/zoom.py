"""Zoom and pan inside a diagram frame, on phones and computers (T-59).

By default a diagram fits the width of its frame and shows whole. Two fingers
zoom in (pinch), one finger or the mouse drags it, and three discreet buttons
under the frame zoom in, zoom out and reset. Only the frame moves; the page does not.

Zooming widens the diagram itself instead of enlarging a picture of it, so the
browser draws the SVG again at its new size: it stays sharp at any zoom. The
shape never changes. No library: one script for the whole page.
"""

ZOOM_STEP = 1.5
MAXIMUM_ZOOM = 6


def build_zoom_frame_html(inner_html, css_class=""):
    """A frame the zoom script turns into a zoomable view of inner_html."""
    return (f'<div class="zoom-frame {css_class}"><div class="zoom-viewport">'
            f'<div class="zoom-content">{inner_html}</div></div></div>')


def build_zoom_css(palette):
    """Frame, viewport and buttons in the colors of the active theme."""
    return f"""
    .zoom-viewport {{ overflow: hidden; touch-action: pan-y; border-radius: 12px; }}
    .zoom-frame.zoomed .zoom-viewport {{ touch-action: none; cursor: grab; }}
    .zoom-content {{ width: 100%; }}
    .zoom-content img, .zoom-content svg {{ display: block; width: 100%; height: auto; }}
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


ZOOM_SCRIPT = f"""<script>
(() => {{
if (window.diagramZoomReady) {{ return; }}
window.diagramZoomReady = true;
const STEP = {ZOOM_STEP};
const MAXIMUM = {MAXIMUM_ZOOM};

// Widen the diagram to scale times the frame, keeping the point (x, y) of the
// frame still. The frame keeps its height while zoomed, so the page below
// does not jump.
const setZoom = (frame, scale, x, y) => {{
    const viewport = frame.querySelector(".zoom-viewport");
    const content = frame.querySelector(".zoom-content");
    const previous = Number(frame.dataset.zoom || 1);
    scale = Math.min(MAXIMUM, Math.max(1, scale));
    if (previous === 1 && scale > 1) {{
        viewport.style.height = viewport.clientHeight + "px";
    }}
    const focusX = x ?? viewport.clientWidth / 2;
    const focusY = y ?? viewport.clientHeight / 2;
    const left = (viewport.scrollLeft + focusX) * scale / previous - focusX;
    const top = (viewport.scrollTop + focusY) * scale / previous - focusY;
    content.style.width = scale * 100 + "%";
    frame.dataset.zoom = scale;
    frame.classList.toggle("zoomed", scale > 1);
    if (scale === 1) {{ viewport.style.height = ""; }}
    viewport.scrollLeft = left;
    viewport.scrollTop = top;
}};

const addButtons = (frame) => {{
    const buttons = document.createElement("div");
    buttons.className = "zoom-buttons";
    const actions = [["＋", "Acercar", () => STEP], ["－", "Alejar", () => 1 / STEP],
                     ["⟲", "Volver al tamaño original", null]];
    for (const [text, label, factor] of actions) {{
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = text;
        button.title = label;
        button.setAttribute("aria-label", label);
        button.addEventListener("click", () => {{
            const scale = Number(frame.dataset.zoom || 1);
            setZoom(frame, factor ? scale * factor() : 1);
        }});
        buttons.appendChild(button);
    }}
    frame.appendChild(buttons);
}};

// Two fingers: zoom around their middle point. One finger or the mouse, while
// zoomed: drag the diagram inside its frame.
const listenToPointers = (frame) => {{
    const viewport = frame.querySelector(".zoom-viewport");
    const pointers = new Map();
    let pinch = null;
    const pointInFrame = (event) => {{
        const box = viewport.getBoundingClientRect();
        return [event.clientX - box.left, event.clientY - box.top];
    }};
    viewport.addEventListener("pointerdown", (event) => {{
        pointers.set(event.pointerId, pointInFrame(event));
        if (pointers.size === 2) {{
            const [a, b] = [...pointers.values()];
            pinch = {{distance: Math.hypot(a[0] - b[0], a[1] - b[1]),
                      scale: Number(frame.dataset.zoom || 1)}};
        }}
    }});
    viewport.addEventListener("pointermove", (event) => {{
        if (!pointers.has(event.pointerId)) {{ return; }}
        const [lastX, lastY] = pointers.get(event.pointerId);
        const [x, y] = pointInFrame(event);
        pointers.set(event.pointerId, [x, y]);
        if (pointers.size === 2 && pinch) {{
            const [a, b] = [...pointers.values()];
            const distance = Math.hypot(a[0] - b[0], a[1] - b[1]);
            setZoom(frame, pinch.scale * distance / pinch.distance,
                    (a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
        }} else if (pointers.size === 1 && frame.classList.contains("zoomed")) {{
            viewport.scrollLeft -= x - lastX;
            viewport.scrollTop -= y - lastY;
        }}
    }});
    const release = (event) => {{
        pointers.delete(event.pointerId);
        if (pointers.size < 2) {{ pinch = null; }}
    }};
    for (const name of ["pointerup", "pointercancel", "pointerleave"]) {{
        viewport.addEventListener(name, release);
    }}
}};

const prepare = (frame) => {{
    if (frame.dataset.zoomReady) {{ return; }}
    frame.dataset.zoomReady = "yes";
    addButtons(frame);
    listenToPointers(frame);
}};

// Streamlit draws the page in steps: frames that appear later are prepared too.
const prepareAll = () => document.querySelectorAll(".zoom-frame").forEach(prepare);
prepareAll();
new MutationObserver(prepareAll).observe(document.body, {{childList: true, subtree: true}});
}})();
</script>"""
