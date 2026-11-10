
(() => {
// D-166, D-573: a phone turned sideways shows the computer layout, menu included. Streamlit
// folded the menu when the page opened upright, so it opens again on turning.
const phoneSideways = () => Boolean(window.greenoceanPhoneSideways && window.greenoceanPhoneSideways());
// D-473: Streamlit marks the menu with data-collapsed; older versions, with aria-expanded.
const isOpen = (sidebar) => sidebar.dataset.collapsed === "false" || sidebar.getAttribute("aria-expanded") === "true";
const openMenu = () => {
    let attempts = 0;
    const open = () => {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const button = document.querySelector('[data-testid="stExpandSidebarButton"]');
        if (sidebar && isOpen(sidebar)) { return; }
        if (button) { button.click(); } else if (attempts++ < 40) { setTimeout(open, 100); }
    };
    open();
};
if (!window.greenoceanPhoneTurnBound) {
    window.greenoceanPhoneTurnBound = true;
    window.addEventListener("greenocean-phone-sideways", openMenu);
    if (phoneSideways()) { openMenu(); }
}
if (phoneSideways()) { return; }
if (window.innerWidth >= __GO_NARROW_SCREEN_WIDTH__) { return; }
try { if (sessionStorage.getItem("sidebarFolded")) { return; } } catch (error) { return; }
let tries = 0;
const fold = () => {
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    const button = document.querySelector('[data-testid="stSidebarCollapseButton"] button');
    if (sidebar && button && isOpen(sidebar)) {
        button.click();
        try { sessionStorage.setItem("sidebarFolded", "yes"); } catch (error) {}
    } else if (sidebar && !isOpen(sidebar)) {
        try { sessionStorage.setItem("sidebarFolded", "yes"); } catch (error) {}
    } else if (tries++ < 40) {
        setTimeout(fold, 100);
    }
};
fold();
})();
