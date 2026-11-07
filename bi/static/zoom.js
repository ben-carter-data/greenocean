
(() => {
if (window.diagramZoomReady) { return; }
window.diagramZoomReady = true;
const STEP = __ZOOM_STEP__;
const MAXIMUM = __MAXIMUM_ZOOM__;

// Widen the diagram to scale times the frame, keeping the point (x, y) of the
// frame still. The frame keeps its height while zoomed, so the page below
// does not jump.
const setZoom = (frame, scale, x, y) => {
    const viewport = frame.querySelector(".zoom-viewport");
    const content = frame.querySelector(".zoom-content");
    const previous = Number(frame.dataset.zoom || 1);
    scale = Math.min(MAXIMUM, Math.max(1, scale));
    if (previous === 1 && scale > 1) {
        viewport.style.height = viewport.clientHeight + "px";
    }
    const focusX = x ?? viewport.clientWidth / 2;
    const focusY = y ?? viewport.clientHeight / 2;
    const left = (viewport.scrollLeft + focusX) * scale / previous - focusX;
    const top = (viewport.scrollTop + focusY) * scale / previous - focusY;
    content.style.width = scale * 100 + "%";
    frame.dataset.zoom = scale;
    frame.classList.toggle("zoomed", scale > 1);
    if (scale === 1) { viewport.style.height = ""; }
    viewport.scrollLeft = left;
    viewport.scrollTop = top;
};

const addButtons = (frame) => {
    const buttons = document.createElement("div");
    buttons.className = "zoom-buttons";
    // D-443: each name on its own, so the English layer reads it whole (a one-character string beside it misleads it).
    const zoomIn = "Acercar";
    const zoomOut = "Alejar";
    const reset = "Volver al tamaño original";
    const actions = [["＋", zoomIn, () => STEP], ["－", zoomOut, () => 1 / STEP], ["⟲", reset, null]];
    for (const [text, label, factor] of actions) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = text;
        button.title = label;
        button.setAttribute("aria-label", label);
        button.addEventListener("click", () => {
            const scale = Number(frame.dataset.zoom || 1);
            setZoom(frame, factor ? scale * factor() : 1);
        });
        buttons.appendChild(button);
    }
    frame.appendChild(buttons);
};

// Two fingers: zoom around their middle point. One finger or the mouse, while
// zoomed: drag the diagram inside its frame.
const listenToPointers = (frame) => {
    const viewport = frame.querySelector(".zoom-viewport");
    const pointers = new Map();
    let pinch = null;
    const pointInFrame = (event) => {
        const box = viewport.getBoundingClientRect();
        return [event.clientX - box.left, event.clientY - box.top];
    };
    viewport.addEventListener("pointerdown", (event) => {
        pointers.set(event.pointerId, pointInFrame(event));
        if (pointers.size === 2) {
            const [a, b] = [...pointers.values()];
            pinch = {distance: Math.hypot(a[0] - b[0], a[1] - b[1]),
                      scale: Number(frame.dataset.zoom || 1)};
        }
    });
    viewport.addEventListener("pointermove", (event) => {
        if (!pointers.has(event.pointerId)) { return; }
        const [lastX, lastY] = pointers.get(event.pointerId);
        const [x, y] = pointInFrame(event);
        pointers.set(event.pointerId, [x, y]);
        if (pointers.size === 2 && pinch) {
            const [a, b] = [...pointers.values()];
            const distance = Math.hypot(a[0] - b[0], a[1] - b[1]);
            setZoom(frame, pinch.scale * distance / pinch.distance,
                    (a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
        } else if (pointers.size === 1 && frame.classList.contains("zoomed")) {
            viewport.scrollLeft -= x - lastX;
            viewport.scrollTop -= y - lastY;
        }
    });
    const release = (event) => {
        pointers.delete(event.pointerId);
        if (pointers.size < 2) { pinch = null; }
    };
    for (const name of ["pointerup", "pointercancel", "pointerleave"]) {
        viewport.addEventListener(name, release);
    }
};

const prepare = (frame) => {
    if (frame.dataset.zoomReady) { return; }
    frame.dataset.zoomReady = "yes";
    addButtons(frame);
    listenToPointers(frame);
};

// Streamlit draws the page in steps: frames that appear later are prepared too.
const prepareAll = () => document.querySelectorAll(".zoom-frame").forEach(prepare);
prepareAll();
new MutationObserver(prepareAll).observe(document.body, {childList: true, subtree: true});
})();
