(() => {
    if (window.greenoceanIdleBound) { return; }
    window.greenoceanIdleBound = true;
    const IDLE_MS = 20000;
    let timer = null;
    const setPaused = (paused) => {
        document.documentElement.classList.toggle('greenocean-idle', paused);
        document.querySelectorAll('svg').forEach((svg) => {
            try { paused ? svg.pauseAnimations() : svg.unpauseAnimations(); } catch (_) {}
        });
    };
    const wake = () => {
        if (document.documentElement.classList.contains('greenocean-idle')) { setPaused(false); }
        clearTimeout(timer);
        timer = setTimeout(() => setPaused(true), IDLE_MS);
    };
    ['mousemove', 'pointerdown', 'keydown', 'wheel', 'touchstart', 'scroll'].forEach((name) =>
        window.addEventListener(name, wake, { passive: true, capture: true }));
    wake();
})();