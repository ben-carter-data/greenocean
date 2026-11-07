
(() => {
  if (window.__documentPrinted) return;
  window.__documentPrinted = true;
  window.addEventListener("afterprint", () => {
    const url = new URL(window.location.href);
    url.searchParams.set("tema", url.searchParams.get("imprimir"));
    url.searchParams.delete("imprimir");
    if (window.__goRemember) window.__goRemember();
    window.location.replace(url.toString());
  }, { once: true });
  // D-427: print only the document: wait until «Elige tu vista» is gone (the view comes back a moment after the load).
  let tries = 0;
  const ready = () => {
    if (!document.querySelector(".profile-ask")) { window.print(); return; }
    tries += 1;
    if (tries > 40) return;  // after 20 s with the window still open, nothing is printed (no less-than sign: D-280)
    setTimeout(ready, 500);
  };
  setTimeout(ready, 3000);
})();
