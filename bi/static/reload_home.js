
(() => {
    if (document.documentElement.dataset.greenoceanReloadHandled === "true") return;
    document.documentElement.dataset.greenoceanReloadHandled = "true";
    // A reload just to sync the theme's base mode (D-099): stay on this page.
    try {
        if (sessionStorage.getItem("greenoceanThemeReload")) {
            sessionStorage.removeItem("greenoceanThemeReload");
            return;
        }
    } catch (_) {}
    const navigation = performance.getEntriesByType("navigation")[0];
    if (!navigation || navigation.type !== "reload") return;
    const current = new URL(window.location.href);
    const home = new URL("/", current);
    for (const name of ["tema"]) {
        if (current.searchParams.has(name)) home.searchParams.set(name, current.searchParams.get(name));
    }
    home.searchParams.set("vista", "__HOME__");
    try {
        const trail = JSON.parse(sessionStorage.getItem('greenoceanTrail') || '[]');
        const last = trail[trail.length - 1];
        if (last && last.filters && Object.keys(last.filters).length) {
            home.searchParams.set('_ctx', btoa(unescape(encodeURIComponent(JSON.stringify(last.filters)))));
        }
    } catch (_) {}
    if (current.pathname !== home.pathname || current.search !== home.search || current.hash) {
        window.location.replace(home.href);
    }
})();
