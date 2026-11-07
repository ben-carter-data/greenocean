
export default function(component) {
    const { setTriggerValue, data } = component;
    const KEY = "go-keep-profile";
    const store = window.sessionStorage;
    const remember = () => {
        if (!data || !data.perfil) return;
        try {
            store.setItem(KEY, JSON.stringify({
                p: data.perfil, r: data.rol || "", h: data.historial || [], a: data.autor || "", t: Date.now()
            }));
        } catch (e) {}
    };
    window.__goRemember = remember;
    remember();  // D-430: each run, so a reload of this tab never asks for the view again
    // D-423: read even when the address already names the view, because the history of «Volver» comes along too.
    // D-428: once per page, and the kept view stays for the second load Streamlit Community Cloud makes.
    // D-454: and again whenever the server comes without a view while this tab has one: after a long idle time (or a
    // sleep, or a restart) the server forgets the session and the page reconnects in place, without a reload.
    try {
        const lost = !(data && data.perfil);
        const raw = window.__goKeptRead && !lost ? null : store.getItem(KEY);
        window.__goKeptRead = true;
        if (raw) setTriggerValue("keep", raw);
    } catch (e) {}
    const handler = (event) => {
        // D-406: a channel card is a reload the app makes too, like a document of the folder
        const link = event.target.closest && event.target.closest(".df-actions a, .doc-path a, .doc-print, a.im-node");
        if (link) remember();
        // D-373: the GreenOcean logo reopens «Elige tu vista» instead of going to the first page.
        const logo = event.target.closest && event.target.closest(
            '[data-testid="stSidebarLogo"], [data-testid="stHeaderLogo"], [data-testid="stLogoLink"]'
        );
        if (logo && data && data.perfil) {
            event.preventDefault();
            event.stopPropagation();
            setTriggerValue("reopen", String(Date.now()));
        }
    };
    document.addEventListener("click", handler, true);
    return () => document.removeEventListener("click", handler, true);
}
