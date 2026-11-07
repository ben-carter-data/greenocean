
export default function(component) {
    const { setTriggerValue } = component;
    const handler = (event) => {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey
            || event.shiftKey || event.altKey) return;
        const link = event.target.closest && event.target.closest('.greenocean-mockup a[href]');
        if (!link) return;
        const url = new URL(link.getAttribute('href'), window.location.href);
        if (url.origin !== window.location.origin || url.pathname !== window.location.pathname) return;
        // Only the map and family links: a product's «Contexto del precio» link
        // carries a view and a product key, and must navigate (D-123b).
        const params = url.searchParams;
        // D-406, D-494: «Semanal» links to itself, whatever its channel (step 2); another view navigates.
        const here = new URLSearchParams(window.location.search);
        const samePage = params.get('vista') === here.get('vista');
        if (!params.has('_home_region') || params.has('_home_key') || (params.has('vista') && !samePage)) return;
        event.preventDefault();
        setTriggerValue('link', url.search);
    };
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
}
