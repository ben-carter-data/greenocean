
(() => {
if (window.lineageReady) { return; }
window.lineageReady = true;
const GRAPH = 'svg[aria-label="Linaje dbt: de bronce a marts"]';
const split = (text) => (text || "").split(" ").filter(Boolean);

// The graph of one drawing, read once from its data attributes.
const graphOf = (svg) => {
    if (svg.lineageGraph) { return svg.lineageGraph; }
    const up = new Map();
    const down = new Map();
    svg.querySelectorAll("[data-node]").forEach((node) => {
        up.set(node.dataset.node, split(node.dataset.up));
        down.set(node.dataset.node, split(node.dataset.down));
    });
    svg.lineageGraph = {up, down};
    return svg.lineageGraph;
};
// Every node reachable from start along links (transitive inputs or outputs).
const reach = (start, links) => {
    const seen = new Set([start]);
    const queue = [start];
    while (queue.length) {
        for (const next of links.get(queue.pop()) || []) {
            if (!seen.has(next)) { seen.add(next); queue.push(next); }
        }
    }
    return seen;
};

const light = (svg, id) => {
    const graph = graphOf(svg);
    const before = reach(id, graph.up);
    const after = reach(id, graph.down);
    svg.classList.add("lin-active");
    svg.querySelectorAll("[data-node]").forEach((node) => {
        const name = node.dataset.node;
        node.classList.toggle("lin-on", before.has(name) || after.has(name));
        node.classList.toggle("lin-focus", name === id);
    });
    const lit = [];
    svg.querySelectorAll("[data-from]").forEach((part) => {
        const from = part.dataset.from;
        const to = part.dataset.to;
        const on = (before.has(from) && before.has(to)) || (after.has(from) && after.has(to));
        part.classList.toggle("lin-on", on);
        if (on && part.classList.contains("lin-edge")) { lit.push(part); }
    });
    // Lit links over the dimmed ones that share their buses.
    // Nodes never move: Streamlit (React) owns this markup and must find it where it left it.
};
const clear = (svg) => {
    svg.classList.remove("lin-active");
    svg.querySelectorAll(".lin-on, .lin-focus").forEach((part) => part.classList.remove("lin-on", "lin-focus"));
};
const nodeOf = (element) => (element && element.closest ? element.closest("[data-node]") : null);
const graphAround = (element) => (element && element.closest ? element.closest(GRAPH) : null);

document.addEventListener("pointerover", (event) => {
    const node = nodeOf(event.target);
    const svg = graphAround(node);
    if (svg && !svg.dataset.lineagePinned) { light(svg, node.dataset.node); }
});
document.addEventListener("pointerout", (event) => {
    const node = nodeOf(event.target);
    const svg = graphAround(node);
    if (!svg || svg.dataset.lineagePinned) { return; }
    const next = nodeOf(event.relatedTarget);
    if (next && svg.contains(next)) { return; }
    clear(svg);
});
document.addEventListener("click", (event) => {
    const svg = graphAround(event.target);
    if (!svg) { return; }
    const node = nodeOf(event.target);
    if (!node) {
        delete svg.dataset.lineagePinned;
        clear(svg);
    } else if (svg.dataset.lineagePinned === node.dataset.node) {
        delete svg.dataset.lineagePinned;
        light(svg, node.dataset.node);
    } else {
        svg.dataset.lineagePinned = node.dataset.node;
        light(svg, node.dataset.node);
    }
});
// The keyboard: Tab onto a model lights it, Enter pins it, Escape clears.
document.addEventListener("focusin", (event) => {
    const node = nodeOf(event.target);
    const svg = graphAround(node);
    if (svg && !svg.dataset.lineagePinned) { light(svg, node.dataset.node); }
});
document.addEventListener("focusout", (event) => {
    const svg = graphAround(nodeOf(event.target));
    if (svg && !svg.dataset.lineagePinned) { clear(svg); }
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        const node = nodeOf(event.target);
        const svg = graphAround(node);
        if (svg) { svg.dataset.lineagePinned = node.dataset.node; light(svg, node.dataset.node); }
    }
    if (event.key === "Escape") {
        document.querySelectorAll(GRAPH).forEach((svg) => { delete svg.dataset.lineagePinned; clear(svg); });
    }
});

// Streamlit draws the page in steps and redraws it on every rerun: a new drawing
// starts unselected, and its graph is read again on first use.
const prepare = () => document.querySelectorAll(GRAPH).forEach((svg) => {
    if (svg.dataset.lineageReady) { return; }
    svg.dataset.lineageReady = "yes";
    delete svg.lineageGraph;
    clear(svg);
});
prepare();
new MutationObserver(prepare).observe(document.body, {childList: true, subtree: true});
})();
