const data = JSON.parse(document.getElementById("data").textContent);
const labels = data.labels;
function write(parent, text) {
  text.split("`").forEach((piece, index) => {
    if (!piece) { return; }
    if (index % 2) { const code = document.createElement("code"); code.textContent = piece; parent.append(code); }
    else { parent.append(piece); }
  });
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) { node.className = className; }
  if (text) { write(node, text); }
  return node;
}
// D-552: one row of the rule's table: its name on the left, its content on the right.
function row(table, title, content, className) {
  if (!content) { return; }
  const line = element("tr", className || "");
  const cell = element("td");
  if (typeof content === "string") { write(cell, content); } else { cell.append(content); }
  line.append(element("th", "", title), cell);
  table.append(line);
}
function backing(rule) {
  const cell = element("span", "backing");
  rule.backing.forEach((code) => { cell.append(`${code} · `); });
  rule.code.forEach((reference, index) => {
    const code = element("code");
    code.textContent = reference.text;
    if (reference.href) {
      const link = element("a");
      link.href = reference.href;
      link.target = "_blank";
      link.rel = "noopener";
      link.append(code);
      cell.append(link);
    } else {
      cell.append(code);
    }
    if (index < rule.code.length - 1) { cell.append(" · "); }
  });
  return cell;
}
const state = {};
function draw(tab) {
  const panel = document.querySelector(`section[data-tab="${tab}"]`);
  const list = panel.querySelector(".list");
  const chosen = state[tab];
  list.replaceChildren();
  let group = null;
  data.rules.filter((rule) => rule.tab === tab && (!chosen.layer || rule.layer === chosen.layer)).forEach((rule) => {
    if (group !== rule.layer) {
      group = rule.layer;
      // D-552: each stage opens its own band, with what happens there, apart from the one before
      const head = element("div", "group");
      head.append(element("strong", "", data.layers[rule.layer].name), element("span", "summary", data.layers[rule.layer].summary));
      if (chosen.layer) {
        const all = element("button", "", labels.all);
        all.type = "button";
        all.addEventListener("click", () => { chosen.layer = null; draw(tab); });
        head.append(all);
      }
      list.append(head);
    }
    const item = element("button", "item");
    item.type = "button";
    item.dataset.rule = rule.n;
    item.setAttribute("aria-current", String(rule.n === chosen.rule));
    item.append(element("span", "n", String(rule.n)), element("span", "t", rule.title));
    if (rule.inference) { item.append(element("span", "m inferred", "◆")); }
    if (rule.uses === true) { item.append(element("span", "m uses", "●")); }
    if (rule.uses === false) { item.append(element("span", "m plain", "○")); }
    item.addEventListener("click", () => { chosen.rule = rule.n; draw(tab); });
    list.append(item);
  });
  const current = list.querySelector('[aria-current="true"]');
  if (current) { current.scrollIntoView({ block: "nearest" }); }
  const rule = data.rules.find((one) => one.n === chosen.rule);
  const detail = panel.querySelector(".detail");
  detail.replaceChildren();
  detail.scrollTop = 0;
  const table = element("table", "facts");
  row(table, labels.stage, `${rule.layerName} · ${data.layers[rule.layer].summary}`);
  row(table, labels.kpi, rule.kpi, "kpi");
  row(table, labels.problem, rule.problem);
  row(table, labels.without, rule.without);
  row(table, labels.example, rule.example);
  row(table, labels.inference, rule.inference, "inference");
  if (rule.uses === true) { row(table, labels.samePackage, `${labels.yes}. ${labels.sameRule}`, "uses"); }
  if (rule.uses === false) { row(table, labels.samePackage, `${labels.no}. ${rule.whyNot}`, "plain"); }
  row(table, labels.backing, backing(rule));
  detail.append(element("h2", "", `${rule.n} · ${rule.title}`), table);
  panel.querySelectorAll(".dot").forEach((dot) => dot.classList.toggle("on", Number(dot.dataset.rule) === chosen.rule));
  panel.querySelectorAll(".layer").forEach((layer) => layer.classList.toggle("on", layer.dataset.layer === chosen.layer));
}
function activate(node, action) {
  node.addEventListener("click", action);
  node.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); action(); }
  });
}
// D-552: what each piece of the drawing is, on hover or with the keyboard: «Name — what it is. Aquí: what it does here».
const tip = element("div", "tip");
tip.setAttribute("role", "tooltip");
tip.hidden = true;
document.body.append(tip);
function showTip(node) {
  const parts = node.dataset.tip.split(" — ");
  const [what, here] = parts.slice(1).join(" — ").split(/\s*(?:Aquí|Here):\s*/);
  tip.replaceChildren(element("b", "", parts[0]), element("div", "", what));
  if (here) {
    const line = element("div", "here");
    line.append(element("i", "", labels.here), ` ${here}`);
    tip.append(line);
  }
  tip.hidden = false;
  const box = node.getBoundingClientRect();
  const width = tip.offsetWidth;
  const height = tip.offsetHeight;
  const left = Math.min(Math.max(8, box.left + box.width / 2 - width / 2), window.innerWidth - width - 8);
  const below = box.bottom + 8;
  tip.style.left = `${left}px`;
  tip.style.top = `${below + height > window.innerHeight - 8 ? Math.max(8, box.top - height - 8) : below}px`;
}
document.querySelectorAll(".map [data-tip]").forEach((node) => {
  node.addEventListener("mouseenter", () => showTip(node));
  node.addEventListener("focus", () => showTip(node));
  node.addEventListener("mouseleave", () => { tip.hidden = true; });
  node.addEventListener("blur", () => { tip.hidden = true; });
});
document.querySelectorAll("section[data-tab]").forEach((panel) => {
  const tab = panel.dataset.tab;
  state[tab] = { layer: null, rule: data.rules.find((rule) => rule.tab === tab).n };
  panel.querySelectorAll(".dot").forEach((dot) => activate(dot, () => {
    const rule = data.rules.find((one) => one.n === Number(dot.dataset.rule));
    state[tab].rule = rule.n;
    if (state[tab].layer && state[tab].layer !== rule.layer) { state[tab].layer = rule.layer; }
    draw(tab);
  }));
  panel.querySelectorAll(".layer").forEach((layer) => activate(layer, () => {
    const key = layer.dataset.layer;
    state[tab].layer = state[tab].layer === key ? null : key;
    if (state[tab].layer) { state[tab].rule = data.rules.find((rule) => rule.layer === key).n; }
    draw(tab);
  }));
  draw(tab);
});
document.querySelectorAll(".tabs button").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".tabs button").forEach((other) => other.setAttribute("aria-selected", String(other === button)));
  document.querySelectorAll("section[data-tab]").forEach((panel) => { panel.hidden = panel.dataset.tab !== button.dataset.tab; });
}));
