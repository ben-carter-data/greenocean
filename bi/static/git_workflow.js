
const D = JSON.parse(document.getElementById("data").textContent);
const S = D.stations, L = D.labels;
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
const map = document.getElementById("map");
const dr = document.getElementById("drawer"), sc = document.getElementById("scrim");
let cur = 0, last = null;
const colors = { a: "var(--l1)", b: "var(--l2)", c: "var(--l3)" };
function open(n) {
  const x = S[n - 1]; cur = n; dr.style.setProperty("--lc", colors[x.lane]); dr.replaceChildren();
  const close = el("button", "close", L.close); close.id = "cl"; close.onclick = shut; dr.append(close);
  dr.append(el("div", "who", L.station + " " + x.n + " · " + x.who + (x.optional ? " · " + L.optional : "") + (x.gate ? " · " + L.checkpoint : "")));
  const title = el("h2", "", x.title); title.id = "dt"; dr.append(title, el("p", "", x.what), el("h4", "", L.commands));
  const cl = el("div", "cl");
  x.commands.forEach((c) => { const row = el("div", "row"); const code = el("code", "", c); const btn = el("button", "", L.copy);
    btn.onclick = async () => { try { await navigator.clipboard.writeText(c); btn.textContent = L.copied; }
      catch (e) { const r = document.createRange(); r.selectNodeContents(code); const s = getSelection(); s.removeAllRanges(); s.addRange(r); btn.textContent = L.selected; }
      setTimeout(() => { btn.textContent = L.copy; }, 1400); };
    row.append(code, btn); cl.append(row); });
  dr.append(cl);
  if (x.fail) dr.append(el("h4", "", L.fails), el("p", "fail", x.fail));
  dr.append(el("h4", "", L.example), el("div", "ex", x.example), el("h4", "", L.register));
  if (!x.register.length) dr.append(el("p", "", L.none));
  x.register.forEach((o) => { const box = el("div", "occ");
    box.append(el("small", "", o.id + " · " + o.fecha + " · " + o.estado), el("b", "", o.ocurrencia));
    if (o.diagnostico) box.append(el("span", "", L.diagnosis + ": " + o.diagnostico));
    box.append(el("span", "", L.solution + ": " + o.solucion), el("span", "", o.comentario)); dr.append(box); });
  const nav = el("div", "nav"); const pv = el("button", "", L.previous), nx = el("button", "", L.next);
  pv.disabled = n === 1; nx.disabled = n === S.length; pv.onclick = () => open(n - 1); nx.onclick = () => open(n + 1); nav.append(pv, nx); dr.append(nav);
  dr.hidden = false; sc.hidden = false; close.focus();
}
function shut() { dr.hidden = true; sc.hidden = true; if (last) last.focus(); }
map.addEventListener("click", (e) => { const b = e.target.closest(".st"); if (b) { last = b; open(+b.dataset.n); } });
map.addEventListener("keydown", (e) => { const b = e.target.closest(".st");
  if (b && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); last = b; open(+b.dataset.n); } });
sc.onclick = shut;
document.addEventListener("keydown", (e) => { if (dr.hidden) return; if (e.key === "Escape") shut();
  if (e.key === "ArrowRight" && cur < S.length) open(cur + 1); if (e.key === "ArrowLeft" && cur > 1) open(cur - 1); });
