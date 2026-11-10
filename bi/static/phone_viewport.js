(() => {
// D-573: a phone turned sideways lays the panel out __GO_PHONE_LAYOUT_WIDTH__ px wide, like a computer, so every width
// rule of the panel sees the computer layout; held upright it keeps its own width and shows «Gira tu teléfono».
// Shrinking the page afterwards (D-166) left the rules seeing the phone's width: the steps of «Semanal» stacked.
// Streamlit Community Cloud draws the panel in a frame of the same site: the phone obeys the viewport of the page around
// it, so both are set; each keeps its own original value for the phone held upright.
const COMPUTER = "width=__GO_PHONE_LAYOUT_WIDTH__";
const phone = Math.min(screen.width, screen.height) <= 500;
const sideways = () => {
    if (screen.orientation && screen.orientation.type) { return screen.orientation.type.startsWith("landscape"); }
    if (typeof window.orientation === "number") { return Math.abs(window.orientation) === 90; }
    return screen.width > screen.height;
};
window.greenoceanPhoneSideways = () => phone && sideways();
const viewports = () => {
    const found = [document.querySelector('meta[name="viewport"]')];
    try { if (window.top !== window) { found.push(window.top.document.querySelector('meta[name="viewport"]')); } } catch (error) {}
    return found.filter(Boolean);
};
const apply = () => {
    const turned = window.greenoceanPhoneSideways();
    let changed = false;
    viewports().forEach((meta) => {
        if (meta.dataset.goOwn === undefined) { meta.dataset.goOwn = meta.content; }
        const wanted = turned ? COMPUTER : meta.dataset.goOwn;
        if (meta.content !== wanted) { meta.content = wanted; changed = true; }
    });
    if (changed && turned) { window.dispatchEvent(new Event("greenocean-phone-sideways")); }
};
if (!phone) { return; }
apply();
if (!window.greenoceanViewportBound) {
    window.greenoceanViewportBound = true;
    window.addEventListener("orientationchange", () => setTimeout(apply, 50));
    if (screen.orientation) { screen.orientation.addEventListener("change", apply); }
}
})();
