
    const page = window.parent;
    const attempt = "project-base-request-" + page.location.pathname;
    const key = "stActiveTheme-" + page.location.pathname + "-v2";
    const wanted = __GO_VALUE__;
    // The app may live under a folder: the sections share the current page's folder.
    const folder = page.location.pathname.replace(/[^/]*$/, "");
    try {
        const current = JSON.parse(page.localStorage.getItem(key) || "null");
        const requested = page.sessionStorage.getItem(attempt);
        // Stored preference can already match while React still uses the old base.
        const ink = page.getComputedStyle(page.document.body).color.match(/[0-9.]+/g);
        const brightInk = ink && (Number(ink[0]) * .2126 + Number(ink[1]) * .7152 + Number(ink[2]) * .0722) > 128;
        const baseMatches = ink && (wanted === "Dark" ? brightInk : !brightInk);
        if (baseMatches) { page.sessionStorage.removeItem(attempt); }
        for (const path of __GO_SECTION_PATHS__) {
            page.localStorage.setItem("stActiveTheme-" + folder + path + "-v2",
                                      JSON.stringify(wanted));
        }
        if (!baseMatches && requested !== wanted) {
            page.sessionStorage.setItem(attempt, wanted);
            // The address keeps the chosen palette across the reload.
            const address = new URL(page.location.href);
            address.searchParams.set("tema", __GO_SELECTED_THEME__);
            page.history.replaceState(null, "", address.toString());
            // This reload only syncs Streamlit's native-widget base mode; it is not
            // a real page refresh, so it must not send the reader back home (D-099).
            page.sessionStorage.setItem("greenoceanThemeReload", "1");
            if (page.__goRemember) { page.__goRemember(); }  // D-357: this reload is the app's own
            page.location.reload();
        }
    } catch (error) { /* CSS remains usable when browser storage is unavailable. */ }
    