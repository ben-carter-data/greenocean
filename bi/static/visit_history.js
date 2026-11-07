(() => {
    try {
        if (!document.documentElement.dataset.greenoceanLinksBound) {
            document.documentElement.dataset.greenoceanLinksBound = 'true';
            document.addEventListener('click', event => {
                if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
                const anchor = event.target.closest && event.target.closest('a[href]');
                if (!anchor || anchor.hasAttribute('download')) return;
                // Only internal navigation forces the same tab (D-113): this app may run
                // behind an iframe wrapper, where forcing target=_self on an external
                // link (GitHub, ODEPA…) makes the destination refuse to be framed.
                if (anchor.hostname === location.hostname) anchor.target = '_self';
            }, true);
        }
        const url = new URL(location.href); url.searchParams.delete('_ctx');
        const identity = url.pathname + '|' + ['vista','kpi','consulta'].map(k => url.searchParams.get(k) || '').join('|');
        const pending = sessionStorage.getItem('greenoceanReturning');
        if (pending && pending !== identity) return;
        if (pending) sessionStorage.removeItem('greenoceanReturning');
        const rows = JSON.parse(sessionStorage.getItem('greenoceanTrail') || '[]');
        const record = {url:url.pathname + url.search, identity, filters:__FILTERS__};
        if (rows.length && rows[rows.length-1].identity === identity) rows[rows.length-1] = record;
        else rows.push(record);
        sessionStorage.setItem('greenoceanTrail', JSON.stringify(rows.slice(-30)));
    } catch (_) {}
    })();