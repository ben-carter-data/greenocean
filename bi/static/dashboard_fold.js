
(() => {
    const view = "__VIEW__";
    const fold = "__FOLD__" === "yes";
    // D-573: a turned phone is laid out as a computer, so its dashboards fold the menu as a computer's do
    const wide = window.innerWidth >= __WIDE__;
    // D-466: the page before in this load of the app; each load (an address typed, a reload) is an entry and opens the menu
    const last = window.__goMenuView === undefined ? null : window.__goMenuView;
    window.__goMenuView = view;
    if (last === view) return;
    // Streamlit marks the menu with data-collapsed (aria-expanded in older versions)
    const isOpen = (sidebar) => sidebar.dataset.collapsed === "false" || sidebar.getAttribute("aria-expanded") === "true";
    let tries = 0;
    const act = () => {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const button = last === null
            ? document.querySelector('[data-testid="stExpandSidebarButton"]')
            : document.querySelector('[data-testid="stSidebarCollapseButton"] button');
        if (sidebar && button && (last === null) !== isOpen(sidebar)) { button.click(); return; }
        if (sidebar && (last === null) === isOpen(sidebar)) return;
        if (tries++ < 40) setTimeout(act, 100);
    };
    if (last === null ? wide : fold && wide) act();
})();
