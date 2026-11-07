
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
