
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
function block(parent, title, text, className) {
  if (!text) { return; }
  const box = element("div", "block " + (className || ""));
  box.append(element("h3", "", title), element("p", "", text));
  parent.append(box);
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
      const head = element("div", "group");
      head.append(element("span", "", rule.layerName));
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
  detail.append(element("h2", "", `${rule.n} · ${rule.title}`), element("p", "kicker", `${labels.where}: ${rule.layerName}`));
  block(detail, labels.problem, rule.problem);
  block(detail, labels.without, rule.without);
  block(detail, labels.example, rule.example);
  block(detail, labels.inference, rule.inference, "inference");
  if (rule.uses === true) { block(detail, labels.uses, labels.sameRule, "uses"); }
  if (rule.uses === false) { block(detail, labels.notUses, rule.whyNot, "plain"); }
  const backing = element("p", "backing");
  backing.append(`${labels.backing}: `);
  rule.backing.forEach((code) => { backing.append(`${code} · `); });
  rule.code.forEach((reference, index) => {
    const code = element("code");
    code.textContent = reference.text;
    if (reference.href) {
      const link = element("a");
      link.href = reference.href;
      link.target = "_blank";
      link.rel = "noopener";
      link.append(code);
      backing.append(link);
    } else {
      backing.append(code);
    }
    if (index < rule.code.length - 1) { backing.append(" · "); }
  });
  detail.append(backing);
  panel.querySelectorAll(".dot").forEach((dot) => dot.classList.toggle("on", Number(dot.dataset.rule) === chosen.rule));
  panel.querySelectorAll(".layer").forEach((layer) => layer.classList.toggle("on", layer.dataset.layer === chosen.layer));
}
function activate(node, action) {
  node.addEventListener("click", action);
  node.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); action(); }
  });
}
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
