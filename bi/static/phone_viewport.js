(() => {
// D-573: a phone turned sideways lays the panel out __GO_PHONE_LAYOUT_WIDTH__ px wide, like a computer, so every width
// rule of the panel sees the computer layout; held upright it keeps its own width and shows «Gira tu teléfono».
// Shrinking the page afterwards (D-166) left the rules seeing the phone's width: the steps of «Semanal» stacked.
const COMPUTER = "width=__GO_PHONE_LAYOUT_WIDTH__";
const OWN = "width=device-width, initial-scale=1, shrink-to-fit=no";
const phone = Math.min(screen.width, screen.height) <= 500;
const sideways = () => {
    if (screen.orientation && screen.orientation.type) { return screen.orientation.type.startsWith("landscape"); }
    if (typeof window.orientation === "number") { return Math.abs(window.orientation) === 90; }
    return screen.width > screen.height;
};
window.greenoceanPhoneSideways = () => phone && sideways();
const apply = () => {
    const meta = document.querySelector('meta[name="viewport"]');
    const wanted = window.greenoceanPhoneSideways() ? COMPUTER : OWN;
    if (meta && meta.content !== wanted) {
        meta.content = wanted;
        if (wanted === COMPUTER) { window.dispatchEvent(new Event("greenocean-phone-sideways")); }
    }
};
if (!phone) { return; }
apply();
if (!window.greenoceanViewportBound) {
    window.greenoceanViewportBound = true;
    window.addEventListener("orientationchange", () => setTimeout(apply, 50));
    if (screen.orientation) { screen.orientation.addEventListener("change", apply); }
}
})();
