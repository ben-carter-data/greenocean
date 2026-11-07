
(() => {
  const maps = document.querySelectorAll(".am:not([data-ready])");
  maps.forEach((map) => {
    map.dataset.ready = "1";
    const ns = "http://www.w3.org/2000/svg";
    const main = map.querySelector(".am-main");
    const links = JSON.parse(main.dataset.links);
    const whats = Array.from(map.querySelectorAll(".am-whats span"), (item) => item.textContent);
    const prefix = "am" + Math.random().toString(36).slice(2, 8) + "-";
    const state = { hover: null, tour: null, pick: null, tip: null, story: null };
    const node = (stage, key) => stage.querySelector('[data-key="' + key + '"]');
    // D-441: orthogonal lines, as in an entity-relationship diagram. The stage becomes a grid of small cells; every
    // piece (logo, name, buttons) and every caption of the drawing is a wall. Each line takes the cheapest path: few
    // turns, around the walls, and away from the lanes the lines before it took, so two lines never run on top of each
    // other and cross only at right angles.
    const CELL = 6, TURN = 24, OVERLAP = 60, NEAR = 8, CROSS = 5, SOFT = 10, NAME = 14;
    const DX = [1, 0, -1, 0], DY = [0, 1, 0, -1];
    const route = (stage, pairs, only) => {
      const box = stage.getBoundingClientRect();
      // A scaled-down stage (a narrow window) is measured on screen and routed in its own units.
      const k = box.width / stage.offsetWidth || 1;
      const cols = Math.floor(stage.offsetWidth / CELL) + 1, rows = Math.floor(stage.offsetHeight / CELL) + 1;
      const size = cols * rows;
      const wall = new Uint8Array(size), lane = [new Uint8Array(size), new Uint8Array(size)];
      // Beside a lane: a line that runs alongside pays for it, so parallel lines keep two cells apart.
      const near = [new Uint8Array(size), new Uint8Array(size)];
      const clamp = (value, top) => Math.max(0, Math.min(top, value));
      const local = (element) => {
        const r = element.getBoundingClientRect();
        return { left: (r.left - box.left) / k, top: (r.top - box.top) / k, right: (r.right - box.left) / k,
          bottom: (r.bottom - box.top) / k };
      };
      const block = (r, pad, value) => {
        const c1 = clamp(Math.floor((r.left - pad) / CELL), cols - 1), c2 = clamp(Math.ceil((r.right + pad) / CELL), cols - 1);
        const r1 = clamp(Math.floor((r.top - pad) / CELL), rows - 1), r2 = clamp(Math.ceil((r.bottom + pad) / CELL), rows - 1);
        for (let row = r1; r2 >= row; row += 1) {
          for (let col = c1; c2 >= col; col += 1) {
            const cell = row * cols + col;
            // A hard wall (2) wins over a name (3), and a name over a caption line (1).
            wall[cell] = wall[cell] === 2 || value === 2 ? 2 : Math.max(wall[cell], value);
          }
        }
      };
      stage.querySelectorAll(":scope > .am-node").forEach((item) => {
        if (!item.offsetWidth) { return; }
        item.querySelectorAll(".am-logo, .am-rchip, .am-info, .am-lupa").forEach((part) => block(local(part), 2, 2));
        // A name is a soft wall: a line may pass behind it, at the price of a detour, and the name is drawn over it.
        item.querySelectorAll(".am-name, .am-sub").forEach((part) => block(local(part), 1, 3));
      });
      stage.querySelectorAll(":scope > .am-own span, :scope > .am-band span").forEach((part) => block(local(part), 1, 2));
      stage.querySelectorAll(":scope > .am-layer").forEach((part) => block(local(part), 0, 1));
      // The doors of a piece: five on each side of its logo and three over it, two cells out so that rounding never puts
      // a door inside the piece's own wall. None under the name: a head there would point at text, not at the piece.
      const ports = (item, inward) => {
        const logo = local(item.querySelector(".am-logo"));
        const cx = (logo.left + logo.right) / 2, cy = (logo.top + logo.bottom) / 2;
        const list = [];
        const add = (x, y, dir, rank) => {
          const col = clamp(Math.round(x / CELL), cols - 1), row = clamp(Math.round(y / CELL), rows - 1), cell = row * cols + col;
          if (wall[cell] === 2) { return; }
          const flat = dir % 2 === 0;
          const edge = dir === 0 ? logo.right : dir === 2 ? logo.left : dir === 3 ? logo.top : logo.bottom;
          list.push({
            cell, rank, side: dir, dir: inward ? (dir + 2) % 4 : dir,
            end: flat ? { x: edge, y: row * CELL } : { x: col * CELL, y: edge },
          });
        };
        [0, -1, 1, -2, 2].forEach((step, rank) => {
          add(logo.left - 2 - 2 * CELL, cy + step * CELL, 2, rank);
          add(logo.right + 2 + 2 * CELL, cy + step * CELL, 0, rank);
          if (2 > Math.abs(step)) { add(cx + step * CELL, logo.top - 2 - 2 * CELL, 3, rank + 1); }
        });
        return list;
      };
      const center = (item) => {
        const logo = local(item.querySelector(".am-logo"));
        return { x: (logo.left + logo.right) / 2, y: (logo.top + logo.bottom) / 2 };
      };
      const search = (starts, goals, target) => {
        const best = new Float64Array(size * 4).fill(Infinity), from = new Int32Array(size * 4).fill(-1);
        const goal = new Map(goals.map((port) => [port.cell, port])), opened = new Map();
        const tc = Math.round(target.x / CELL), tr = Math.round(target.y / CELL);
        const heap = [];
        const push = (entry) => {
          heap.push(entry);
          let i = heap.length - 1;
          while (i > 0) {
            const parent = (i - 1) >> 1;
            if (heap[i][0] >= heap[parent][0]) { break; }
            [heap[i], heap[parent]] = [heap[parent], heap[i]];
            i = parent;
          }
        };
        const pop = () => {
          const top = heap[0], last = heap.pop();
          if (heap.length) {
            heap[0] = last;
            let i = 0;
            for (;;) {
              const l = 2 * i + 1, r = l + 1;
              let small = i;
              if (heap.length > l && heap[small][0] > heap[l][0]) { small = l; }
              if (heap.length > r && heap[small][0] > heap[r][0]) { small = r; }
              if (small === i) { break; }
              [heap[i], heap[small]] = [heap[small], heap[i]];
              i = small;
            }
          }
          return top;
        };
        const guess = (cell) => {
          const col = cell % cols, row = (cell - col) / cols;
          return Math.max(0, Math.abs(col - tc) + Math.abs(row - tr) - 8);
        };
        starts.forEach((port) => {
          const id = port.cell * 4 + port.dir, g = port.rank * 2;
          if (best[id] > g) { best[id] = g; opened.set(id, port); push([g + guess(port.cell), g, id, 0]); }
        });
        let budget = size * 8;
        while (heap.length && budget > 0) {
          budget -= 1;
          const [, g, id, done] = pop();
          const cell = id >> 2, dir = id & 3;
          if (done) {
            const cells = [];
            let cursor = id, first = id;
            while (cursor !== -1) { cells.push(cursor >> 2); first = cursor; cursor = from[cursor]; }
            cells.reverse();
            return { cells, start: opened.get(first), end: goal.get(cell) };
          }
          if (g > best[id]) { continue; }
          if (goal.has(cell)) {
            const port = goal.get(cell);
            push([g + port.rank * 2 + (dir === port.dir ? 0 : TURN), g, id, 1]);
          }
          const col = cell % cols, row = (cell - col) / cols;
          for (let next = 0; 4 > next; next += 1) {
            if (next === (dir + 2) % 4) { continue; }
            const nc = col + DX[next], nr = row + DY[next];
            if (0 > nc || nc >= cols || 0 > nr || nr >= rows) { continue; }
            const n = nr * cols + nc;
            if (wall[n] === 2 && !goal.has(n)) { continue; }
            const axis = next % 2;
            const ng = g + 1 + (next === dir ? 0 : TURN) + (wall[n] === 1 ? SOFT : 0) + (wall[n] === 3 ? NAME : 0)
              + (lane[axis][n] ? OVERLAP : 0) + (near[axis][n] ? NEAR : 0) + (lane[1 - axis][n] ? CROSS : 0);
            const nid = n * 4 + next;
            if (best[nid] > ng) { best[nid] = ng; from[nid] = id; push([ng + guess(n), ng, nid, 0]); }
          }
        }
        return null;
      };
      // The first lines to be laid are the ones always drawn, then the shortest: they keep the straightest lanes.
      const spans = pairs.map(([a, b], index) => {
        if (only && !only.has(index)) { return 0; }
        const p = center(a), q = center(b);
        return Math.abs(p.x - q.x) + Math.abs(p.y - q.y);
      });
      const order = pairs.map((_, index) => index).filter((index) => !only || only.has(index)).sort((p, q) => (pairs[q][2] ? 1 : 0) - (pairs[p][2] ? 1 : 0) || spans[p] - spans[q]);
      const routes = [], sides = new Map();
      // A round trip (A to B, then B to A) leaves and arrives by other sides than its twin, so the two never share a lane.
      const apart = (list, side) => {
        const kept = list.filter((port) => port.side !== side);
        return kept.length ? kept : list;
      };
      order.forEach((index) => {
        const [a, b] = pairs[index];
        const twin = sides.get(b.dataset.key + ">" + a.dataset.key);
        let starts = ports(a, false), goals = ports(b, true);
        if (twin) { starts = apart(starts, twin.end); goals = apart(goals, twin.start); }
        const found = search(starts, goals, center(b));
        if (found) { sides.set(a.dataset.key + ">" + b.dataset.key, { start: found.start.side, end: found.end.side }); }
        let points;
        if (found) {
          const cells = found.cells;
          for (let i = 1; cells.length > i; i += 1) {
            const axis = (cells[i] - cells[i - 1]) % cols === 0 ? 1 : 0;
            [cells[i], cells[i - 1]].forEach((cell) => {
              lane[axis][cell] = 1;
              const side = axis === 0 ? cols : 1;
              [cell - side, cell + side].forEach((other) => { if (other >= 0 && size > other) { near[axis][other] = 1; } });
            });
          }
          points = [found.start.end].concat(cells.map((cell) => {
            const col = cell % cols;
            return { x: col * CELL, y: (cell - col) / cols * CELL };
          }), [found.end.end]);
        } else {
          const p = center(a), q = center(b);
          points = [p, { x: q.x, y: p.y }, q];
        }
        routes[index] = smooth(points);
      });
      return routes;
    };
    // A polyline with its straight runs joined and its corners slightly rounded.
    const smooth = (raw) => {
      const points = raw.filter((point, i) => {
        if (i === 0 || i === raw.length - 1) { return true; }
        const p = raw[i - 1], n = raw[i + 1];
        return !((p.x === point.x && point.x === n.x) || (p.y === point.y && point.y === n.y));
      });
      let d = "M" + points[0].x + " " + points[0].y;
      for (let i = 1; points.length - 1 > i; i += 1) {
        const p = points[i - 1], c = points[i], n = points[i + 1];
        const r = Math.min(5, Math.hypot(c.x - p.x, c.y - p.y) / 2, Math.hypot(n.x - c.x, n.y - c.y) / 2);
        const ux = Math.sign(c.x - p.x), uy = Math.sign(c.y - p.y), vx = Math.sign(n.x - c.x), vy = Math.sign(n.y - c.y);
        d += " L" + (c.x - ux * r) + " " + (c.y - uy * r) + " Q" + c.x + " " + c.y + " " + (c.x + vx * r) + " " + (c.y + vy * r);
      }
      const last = points[points.length - 1];
      return d + " L" + last.x + " " + last.y;
    };
    const layer = (stage) => {
      let svg = stage.querySelector(":scope > .am-lines");
      if (!svg) {
        svg = document.createElementNS(ns, "svg");
        svg.setAttribute("class", "am-lines");
        stage.prepend(svg);
      }
      while (svg.firstChild) { svg.removeChild(svg.firstChild); }
      return svg;
    };
    // D-441: a head at the end of every line, just before the logo it reaches, so its direction reads even still.
    const arrow = (svg, path) => {
      const length = path.getTotalLength();
      if (12 > length) { return null; }
      const tip = path.getPointAtLength(length - 1), back = path.getPointAtLength(length - 7);
      const angle = Math.atan2(tip.y - back.y, tip.x - back.x);
      const wing = (side) => (tip.x - 7 * Math.cos(angle + side * 0.5)) + " " + (tip.y - 7 * Math.sin(angle + side * 0.5));
      const head = document.createElementNS(ns, "path");
      head.setAttribute("d", "M" + wing(-1) + " L" + tip.x + " " + tip.y + " L" + wing(1));
      head.setAttribute("class", path.getAttribute("class") + " am-arrow");
      head.style.stroke = path.style.stroke;
      Object.assign(head.dataset, path.dataset);
      svg.appendChild(head);
      return head;
    };
    // The map draws its lines once per size; where they run is laid out again whenever the lines in view change (at
    // rest, a theme, a rhythm step, the walk or the piece under the cursor): only the lines in view are routed, so
    // they never go round lines that are hidden.
    const parts = [];
    let laid = "";
    // D-441: below a readable width the stages keep their layout and shrink as a whole, like a picture.
    const DESIGN = 820;
    const fit = (stage) => {
      // A little slack on the right: a caption or a label may reach past the last column.
      const aside = map.querySelector(".am-steps");
      const side = aside && aside.offsetWidth ? aside.offsetWidth + 16 : 0;  // D-471: the list takes its share
      const width = map.clientWidth - side - 12, mini = width > 0 && DESIGN > width + 12;
      map.classList.toggle("am-mini", !!mini);
      Object.assign(stage.style, mini
        ? { width: DESIGN + "px", transform: "scale(" + width / DESIGN + ")", transformOrigin: "0 0" }
        : { width: "", transform: "", transformOrigin: "" });
      stage.style.marginBottom = mini ? -(stage.offsetHeight * (1 - width / DESIGN)) + "px" : "";
    };
    const drawMain = () => {
      if (!main.offsetWidth) { return; }
      fit(main);
      const svg = layer(main);
      parts.length = 0;
      laid = "";
      links.forEach(([from, to, kind, themes, rhythm, base, color], index) => {
        const path = document.createElementNS(ns, "path");
        path.setAttribute("d", "M0 0");
        path.setAttribute("id", prefix + index);
        path.setAttribute("class", "am-line k-" + kind + (base ? " base" : ""));
        path.style.stroke = color;
        Object.assign(path.dataset, { from, to, index, rhythm, themes: themes.join(" "), base: base ? "1" : "" });
        svg.appendChild(path);
        const hit = document.createElementNS(ns, "path");
        hit.setAttribute("class", "am-hit");
        hit.dataset.index = index;
        // D-469: the map answers only to a click on an «i» or a magnifier: no line reacts to the cursor
        const label = document.createElementNS(ns, "text");
        svg.appendChild(hit);
        const dot = document.createElementNS(ns, "circle");
        dot.setAttribute("r", "3.6");
        dot.setAttribute("class", "am-msg k-" + kind);
        dot.style.fill = color;
        dot.dataset.index = index;
        const move = document.createElementNS(ns, "animateMotion");
        move.setAttribute("repeatCount", "indefinite");
        move.setAttribute("begin", "indefinite");
        const along = document.createElementNS(ns, "mpath");
        along.setAttribute("href", "#" + prefix + index);
        move.appendChild(along);
        dot.appendChild(move);
        svg.appendChild(dot);
        label.setAttribute("class", "am-label" + (base ? " base" : ""));
        label.textContent = whats[index];
        Object.assign(label.dataset, { from, to, index, rhythm, themes: themes.join(" ") });
        label.path = path;
        svg.appendChild(label);
        parts.push({ svg, path, hit, move, label, head: null });
      });
      refresh();
    };
    const layout = (wanted) => {
      const routes = route(main, links.map(([from, to, , , , base]) => [node(main, from), node(main, to), base]), wanted);
      parts.forEach((part, index) => {
        part.hit.classList.toggle("live", wanted.has(index));
        if (!wanted.has(index)) { return; }
        part.path.setAttribute("d", routes[index]);
        part.hit.setAttribute("d", routes[index]);
        part.move.setAttribute("dur", Math.max(1.6, part.path.getTotalLength() / 90).toFixed(2) + "s");
        if (part.head) { part.head.remove(); }
        part.head = arrow(part.svg, part.path);
      });
    };
    // The lines in view now: the walk's step, the one line a sequence is showing, or, at rest, the lines always drawn.
    const inView = () => {
      const theme = map.dataset.filter, rhythm = map.dataset.rhythm, pick = new Set();
      links.forEach(([, , , , , base], index) => {
        let show;
        if (state.tour) { show = state.tour.links.includes(String(index)); }
        else if (state.pick) { show = state.pick.has(index); }
        else if (state.hover || theme || rhythm) { show = false; }
        else { show = !!state.story && state.story[0] === index; }  // D-469: one line at a time, nothing else
        if (show) { pick.add(index); }
      });
      return pick;
    };
    const drawInside = (stage) => {
      if (!stage.offsetWidth) { return; }
      fit(stage);
      const svg = layer(stage);
      const specs = JSON.parse(stage.dataset.links);
      const names = Array.from(stage.parentElement.querySelectorAll(".am-ilabels span"), (item) => item.textContent);
      const routes = route(stage, specs.map(([from, to, , dash]) => [node(stage, from), node(stage, to), !dash]));
      specs.forEach(([, , , dash, color], index) => {
        const path = document.createElementNS(ns, "path");
        path.setAttribute("d", routes[index]);
        path.style.stroke = color;
        path.setAttribute("id", prefix + "in-" + index);
        path.setAttribute("class", "am-line k-flow" + (dash ? " dash" : ""));
        svg.appendChild(path);
        arrow(svg, path);
        // The same travelling message as on the map, so the order of the steps reads without arrows.
        const dot = document.createElementNS(ns, "circle");
        dot.setAttribute("r", "3.2");
        dot.setAttribute("class", "am-msg k-flow go");
        dot.style.fill = color;
        const move = document.createElementNS(ns, "animateMotion");
        move.setAttribute("dur", Math.max(1.6, path.getTotalLength() / 90).toFixed(2) + "s");
        move.setAttribute("repeatCount", "indefinite");
        const along = document.createElementNS(ns, "mpath");
        along.setAttribute("href", "#" + prefix + "in-" + index);
        move.appendChild(along);
        dot.appendChild(move);
        svg.appendChild(dot);
        if (names[index]) {
          const label = document.createElementNS(ns, "text");
          label.setAttribute("class", "am-label");
          const half = path.getTotalLength() / 2;
          const point = path.getPointAtLength(half), before = path.getPointAtLength(Math.max(0, half - 3));
          // Beside a line that runs down, above a line that runs across, so the label never covers a piece's text.
          const upright = Math.abs(point.y - before.y) > Math.abs(point.x - before.x);
          label.setAttribute("x", upright ? point.x + 6 : point.x);
          label.setAttribute("y", upright ? point.y + 4 : point.y - 5);
          label.setAttribute("text-anchor", upright ? "start" : "middle");
          label.textContent = names[index];
          svg.appendChild(label);
        }
      });
    };
    const lines = () => main.querySelectorAll(".am-line, .am-label");
    const dots = () => main.querySelectorAll(".am-msg");
    // Each visible label takes the place along its line that covers the least of the other labels and the nodes.
    const place = (labels) => {
      const box = main.getBoundingClientRect(), k = box.width / main.offsetWidth || 1;
      const rect = (item) => {
        const r = item.getBoundingClientRect();
        return {left: (r.left - box.left) / k, top: (r.top - box.top) / k, right: (r.right - box.left) / k,
          bottom: (r.bottom - box.top) / k};
      };
      const fixed = Array.from(main.querySelectorAll(
        ".am-logo, .am-name, .am-sub, .am-rchip, .am-info, .am-lupa, .am-layer, .am-own span, .am-band span"), rect);
      const placed = [];
      const overlap = (a, list) => list.reduce((sum, b) => sum + Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left))
        * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top)), 0);
      labels.forEach((label) => {
        const length = label.path.getTotalLength();
        let best = null;
        [0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74, 0.18, 0.82, 0.12, 0.88].forEach((share, rank) => {
          const point = label.path.getPointAtLength(length * share);
          // Over or under a line that runs across; beside, on either side, a line that runs down.
          [[0, -4, "middle"], [0, 13, "middle"], [6, 4, "start"], [-6, 4, "end"]].forEach(([dx, dy, anchor]) => {
            label.setAttribute("x", point.x + dx);
            label.setAttribute("y", point.y + dy);
            label.setAttribute("text-anchor", anchor);
            const r = label.getBBox();
            const area = {left: r.x - 4, top: r.y - 2, right: r.x + r.width + 4, bottom: r.y + r.height + 2};
            const clash = overlap(area, placed) * 10 + overlap(area, fixed);
            const score = clash + rank;
            if (!best || score > -1 && best.score > score) { best = {score, clash, x: point.x + dx, y: point.y + dy, anchor, area}; }
          });
        });
        label.setAttribute("x", best.x);
        label.setAttribute("y", best.y);
        label.setAttribute("text-anchor", best.anchor);
        // A label that cannot find a free place stays hidden: covering a piece or another label reads worse than none.
        // The cursor on its line, or its card, still tells what it carries.
        // With several lines in view (at rest) a label shows only where it touches no text, no logo and no other
        // label; otherwise its line's cursor or card tells it. Alone on screen it always shows.
        const tight = best.clash > 0 && labels.length > 1;
        label.classList.toggle("tight", tight);
        if (tight) { return; }
        placed.push(best.area);
      });
    };
    // Which lines show, which nodes dim and which dots travel, from the filter, the rhythm, the cursor or the walk.
    const refresh = () => {
      const theme = map.dataset.filter, rhythm = map.dataset.rhythm, step = state.tour;
      if (parts.length) {
        const wanted = inView(), key = Array.from(wanted).join(",");
        if (key !== laid) { laid = key; layout(wanted); }
      }
      main.querySelectorAll(".am-node").forEach((item) => {
        const dim = (!!theme && !item.dataset.themes.split(" ").includes(theme))
          || (!!rhythm && !item.dataset.rhythms.split(" ").includes(rhythm));
        item.classList.toggle("dim", dim);
        // In a sequence the two ends of the line in view stand out from the rest of the theme or the rhythm.
        const ends = !!state.pick && !state.hover && Array.from(state.pick).some((index) =>
          links[index][0] === item.dataset.key || links[index][1] === item.dataset.key);
        item.classList.toggle("end", ends);
        item.classList.toggle("tour", !!step && step.nodes.includes(item.dataset.key));
      });
      lines().forEach((line) => {
        const show = step ? step.links.includes(line.dataset.index)
          : !!state.pick && (!!theme || !!rhythm) && state.pick.has(Number(line.dataset.index));
        line.classList.toggle("show", show);
      });
      const atRest = !step && !state.pick && !state.hover && !theme && !rhythm;
      const told = atRest && state.story ? state.story : null;
      main.querySelectorAll(".am-node").forEach((item) => {
        const key = item.dataset.key;
        item.classList.toggle("lit", !!told && (told[2] === key
          || (told[0] >= 0 && (links[told[0]][0] === key || links[told[0]][1] === key))));
      });
      // D-468: the line in its turn blinks: a step of the walk, the line a sequence is on, or the story's line
      main.querySelectorAll(".am-line, .am-label").forEach((line) => {  // a head blinks with its line
        const index = Number(line.dataset.index);
        let on;
        if (step) { on = step.links.includes(line.dataset.index); }
        else if (state.pick) { on = state.pick.has(index); }
        else { on = !!told && told[0] === index; }
        if (line.classList.contains("am-line")) { line.classList.toggle("blink", on); }
        else { line.classList.toggle("story", !!told && told[0] === index); }
      });
      place(main.querySelectorAll(state.hover ? ".am-label.on" : step || theme || rhythm ? ".am-label.show"
        : ".am-label.base, .am-label.story"));
    };
    // The description of a node never covers the drawing when the side menu is open: it shows over the menu, where no
    // line runs. With the menu closed, it goes where it covers the fewest of the node's own lines and neighbours.
    const dodge = (item) => {
      const tip = item.querySelector(".am-tip");
      if (!tip || map.classList.contains("am-mini")) { return; }
      ["position", "left", "top", "right", "bottom", "transform", "width", "maxHeight", "gridAutoFlow", "zIndex", "fontSize"]
        .forEach((name) => { tip.style[name] = ""; });
      item.style.zIndex = "";
      const menu = document.querySelector('[data-testid="stSidebar"]');
      const side = menu ? menu.getBoundingClientRect() : null;
      const full = map.classList.contains("am-full");
      if (!full && side && side.width >= 240 && side.right > 0 && window.innerWidth > side.right + 600) {
        Object.assign(tip.style, {
          position: "fixed", left: (side.left + 10) + "px", top: "12px",
          width: (Math.max(side.right, main.getBoundingClientRect().left - 12) - side.left - 10) + "px",
          maxHeight: (window.innerHeight - 24) + "px", gridAutoFlow: "row", fontSize: "11.5px", transform: "none",
          right: "auto", bottom: "auto", zIndex: "1000001",
        });
        item.style.zIndex = "1000001";  // the menu is drawn above the page: the node rises with its description
        return;
      }
      // D-441: with the menu closed, or the map on the whole screen, the description is a narrow column: beside the
      // map when there is room, otherwise in the corner of the window that covers neither the piece nor any piece it
      // connects with, so every one of its lines stays in sight as they play.
      const box = main.getBoundingClientRect(), width = Math.min(330, window.innerWidth - 24);
      Object.assign(tip.style, {
        position: "fixed", left: "0px", top: "0px", right: "auto", bottom: "auto", transform: "none",
        width: width + "px", maxHeight: (window.innerHeight - 24) + "px", gridAutoFlow: "row", fontSize: "11.5px",
        zIndex: "1000001",
      });
      item.style.zIndex = "1000001";
      const h = Math.min(tip.getBoundingClientRect().height, window.innerHeight - 24);
      const key = item.dataset.key;
      const center = (element) => {
        const r = element.querySelector(".am-logo").getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
      };
      const ends = [center(item)].concat(links
        .filter(([from, to]) => from === key || to === key)
        .map(([from, to]) => node(main, from === key ? to : from)).filter(Boolean).map(center));
      const room = 12, bottom = window.innerHeight - h - room;
      const candidates = [];
      if (box.left - room * 2 >= width) { candidates.push([box.left - width - room, room]); }
      if (window.innerWidth - box.right - room * 2 >= width) { candidates.push([box.right + room, room]); }
      [[room, room], [window.innerWidth - width - room, room], [room, bottom], [window.innerWidth - width - room, bottom]]
        .forEach((place) => candidates.push(place));
      let best = null;
      candidates.forEach(([x, y], rank) => {
        const covered = ends.filter((p) => p.x >= x - 20 && x + width + 20 >= p.x && p.y >= y - 20 && y + h + 20 >= p.y);
        const score = covered.length * 100 + rank;
        if (!best || best.score > score) { best = { score, x, y }; }
      });
      Object.assign(tip.style, { left: best.x + "px", top: best.y + "px" });
    };
    // The cursor stops lighting a node's lines while a rhythm or the walk plays: the «Cada martes» chip sits inside
    // semanal.yml, so its click would otherwise leave all of that node's lines lit over the sequence.
    // D-441: several lines never show at once. The piece under the cursor, a theme or a rhythm plays its lines one at a
    // time, each with its own route and label, while the caption under the map names it: «3 / 13 · A → B: message».
    const seq = { list: [], at: 0, timer: null };
    const nameOf = (key) => {
      const item = node(main, key);
      return item ? item.getAttribute("aria-label") : key;
    };
    const stopSeq = () => {
      clearInterval(seq.timer);
      seq.timer = null;
      seq.list = [];
      state.pick = null;
      if (!state.tour) { caption.hidden = true; }
    };
    const playSeq = (list, before) => {
      stopSeq();
      if (!list.length) { return; }
      seq.list = list;
      seq.at = 0;
      const next = () => {
        const index = seq.list[seq.at];
        state.pick = new Set([index]);
        if (before) { before(index); }
        caption.hidden = false;
        caption.querySelector("b").textContent = (seq.at + 1) + " / " + seq.list.length;
        caption.querySelector("span").textContent =
          nameOf(links[index][0]) + " → " + nameOf(links[index][1]) + ": " + whats[index];
        refresh();
      };
      next();
      if (seq.list.length > 1) {
        seq.timer = setInterval(() => { seq.at = (seq.at + 1) % seq.list.length; next(); }, 1800);
      }
    };
    const unhover = () => {
      state.hover = null;
      map.classList.remove("has-focus");
      main.querySelectorAll(".on").forEach((element) => element.classList.remove("on"));
    };
    // D-469: a piece does nothing under the cursor nor on a click of its own: only its «i» and its magnifier act.
    // Cards: one at a time, closed with their button or Escape.
    const closeCards = () => {
      map.querySelectorAll(".am-card").forEach((card) => { card.hidden = true; });
      map.classList.remove("has-card");
    };
    const openCard = (selector) => {
      closeCards();
      const card = map.querySelector(".am-card" + selector);
      // The node under the cursor may have risen over the menu with its description: the card goes above it.
      main.querySelectorAll(".am-node").forEach((item) => { item.style.zIndex = ""; });
      if (card) { card.hidden = false; map.classList.add("has-card"); card.querySelector(".am-close").focus(); }
    };
    map.querySelectorAll(".am-close").forEach((button) => button.addEventListener("click", closeCards));
    map.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") { return; }
      if (state.tip) { closeTip(); return; }
      if (map.querySelector(".am-card:not([hidden])")) { closeCards(); }
      else if (map.classList.contains("am-full") && crumb.hidden) { map.classList.remove("am-full"); }
      else { back(); }
    });
    // The inside of a piece takes the place of the map; «Volver» brings the map back.
    const crumb = map.querySelector(".am-crumb"), bars = map.querySelector(".am-bars");
    const back = () => {
      map.querySelectorAll(".am-inside").forEach((inside) => { inside.hidden = true; });
      crumb.hidden = true;
      bars.hidden = false;
      main.hidden = false;
      drawMain();
    };
    crumb.querySelector("button").addEventListener("click", back);
    // D-467: the description of a piece opens with a click on its «i», never under the cursor, and while it is open
    // nothing moves; a click anywhere else or Escape closes it.
    const svgs = () => main.querySelectorAll("svg");
    const closeTip = () => {
      const open = main.querySelector(".am-node.tipped");
      if (open) { open.classList.remove("tipped"); open.style.zIndex = ""; }
      if (state.tip) {
        state.tip = null;
        svgs().forEach((svg) => { if (svg.unpauseAnimations) { svg.unpauseAnimations(); } });
      }
    };
    map.querySelectorAll(".am-info").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const item = button.closest(".am-node");
        const again = item.classList.contains("tipped");
        closeTip();
        if (again) { return; }
        state.tip = item.dataset.key;
        item.classList.add("tipped");
        dodge(item);
        clearInterval(seq.timer);  // the piece's lines stop on the one in view
        seq.timer = null;
        svgs().forEach((svg) => { if (svg.pauseAnimations) { svg.pauseAnimations(); } });
      });
    });
    map.addEventListener("click", (event) => { if (!event.target.closest(".am-info, .am-tip")) { closeTip(); } });
    map.querySelectorAll(".am-tipcard").forEach((button) => button.addEventListener("click", (event) => {
      event.stopPropagation();
      closeTip();
      openCard('[data-card="' + button.dataset.card + '"]');
    }));
    map.querySelectorAll(".am-zoom, .am-lupa").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const key = button.dataset.inside;
        const inside = map.querySelector('.am-inside[data-inside="' + key + '"]');
        if (!inside) { return; }
        stopTour();
        closeCards();
        main.hidden = true;
        bars.hidden = true;
        crumb.hidden = false;
        crumb.querySelector("b").textContent = node(main, key).getAttribute("aria-label");
        inside.hidden = false;
        drawInside(inside.querySelector(".am-view:not([hidden]) .am-istage"));
      });
    });
    // A tool's magnifier: how it works, or what it does in GreenOcean.
    map.querySelectorAll(".am-vbtn").forEach((button) => {
      button.addEventListener("click", () => {
        const inside = button.closest(".am-inside");
        inside.querySelectorAll(".am-vbtn").forEach((other) => other.classList.toggle("on", other === button));
        inside.querySelectorAll(".am-view").forEach((view) => { view.hidden = view.dataset.view !== button.dataset.view; });
        drawInside(inside.querySelector(".am-view:not([hidden]) .am-istage"));
      });
    });
    // Themes and rhythms: one at a time.
    map.querySelectorAll(".am-filter").forEach((button) => {
      button.addEventListener("click", () => {
        stopTour();
        const same = map.dataset.filter === button.dataset.theme;
        map.querySelectorAll(".am-filter, .am-rbtn").forEach((other) => other.classList.remove("on"));
        delete map.dataset.rhythm;
        if (same) { delete map.dataset.filter; refresh(); return; }
        const theme = button.dataset.theme;
        map.dataset.filter = theme;
        button.classList.add("on");
        playSeq(links.map((_, index) => index).filter((index) => links[index][3].includes(theme)));
      });
    });
    // A rhythm plays its lines one at a time; every Tuesday, in the order of the walk, so the load reads in sequence.
    const phases = JSON.parse(main.dataset.phases);
    const toggleRhythm = (rhythm) => {
      stopTour();
      const same = map.dataset.rhythm === rhythm;
      map.querySelectorAll(".am-filter, .am-rbtn").forEach((other) => other.classList.remove("on"));
      delete map.dataset.filter;
      if (same) { delete map.dataset.rhythm; }
      else {
        map.dataset.rhythm = rhythm;
        map.querySelectorAll('.am-rbtn[data-rhythm="' + rhythm + '"]').forEach((other) => other.classList.add("on"));
        unhover();
        const ordered = (phases[rhythm] || []).flat();
        playSeq(ordered.length ? ordered : links.map((_, index) => index).filter((index) => links[index][4] === rhythm));
        return;
      }
      refresh();
    };
    map.querySelectorAll(".am-rbtn, .am-rchip").forEach((button) => {
      button.addEventListener("click", (event) => { event.stopPropagation(); toggleRhythm(button.dataset.rhythm); });
    });
    // The Tuesday walk: one step every few seconds, with its line of explanation.
    const steps = Array.from(map.querySelectorAll(".am-tour span"), (item) => ({
      text: item.textContent, nodes: item.dataset.nodes.split(" "), links: item.dataset.links.split(" "),
    }));
    const tourButton = map.querySelector(".am-tourbtn"), caption = map.querySelector(".am-caption");
    let timer = null, at = 0;
    const show = () => {
      state.tour = steps[at];
      caption.querySelector("b").textContent = (at + 1) + " / " + steps.length;
      caption.querySelector("span").textContent = steps[at].text;
      refresh();
    };
    const stopTour = () => {
      stopSeq();
      if (timer) { clearInterval(timer); timer = null; }
      state.tour = null;
      map.classList.remove("touring");
      tourButton.classList.remove("on");
      caption.hidden = true;
      refresh();
    };
    tourButton.addEventListener("click", () => {
      if (timer) { stopTour(); return; }
      closeCards();
      map.querySelectorAll(".am-filter, .am-rbtn").forEach((other) => other.classList.remove("on"));
      delete map.dataset.filter;
      delete map.dataset.rhythm;
      stopSeq();
      at = 0;
      map.classList.add("touring");
      tourButton.classList.add("on");
      caption.hidden = false;
      show();
      timer = setInterval(() => {
        at += 1;
        if (at >= steps.length) { stopTour(); return; }
        show();
      }, 2800);
    });
    map.querySelector(".am-fullbtn").addEventListener("click", () => { map.classList.toggle("am-full"); });
    // Routing takes longer than a curve: a burst of resizes draws once, when it settles.
    const settle = (work) => {
      let timer = null;
      return () => { clearTimeout(timer); timer = setTimeout(work, 90); };
    };
    // D-467: at rest, the week's data travels its real way, one line at a time: from ODEPA and the INE through each stage
    // to the panel and the people; the story waits while a piece, a theme, the walk, a description or a card is in view.
    const story = JSON.parse(main.dataset.story || "[]");
    const tale = { at: 0, timer: null };
    const tell = () => {
      clearTimeout(tale.timer);
      if (!story.length) { return; }
      const resting = !state.tour && !state.pick && !state.hover && !state.tip && !map.dataset.filter
        && !map.dataset.rhythm && !main.hidden && !map.classList.contains("has-card");
      map.classList.toggle("telling", resting);
      if (!resting) {
        if (state.story) { state.story = null; }
        tale.timer = setTimeout(tell, 700);
        return;
      }
      const [index] = story[tale.at];
      state.story = story[tale.at];
      map.querySelectorAll(".am-step").forEach((item) => item.classList.toggle("now", Number(item.dataset.step) === tale.at));
      const now = map.querySelector('.am-step[data-step="' + tale.at + '"]'), list = map.querySelector(".am-steps-in");
      if (now && list && (now.offsetTop - list.scrollTop > list.clientHeight - 40 || 30 > now.offsetTop - list.scrollTop)) {
        list.scrollTop = now.offsetTop - list.clientHeight / 2;
      }
      refresh();
      caption.hidden = false;
      caption.querySelector("b").textContent = (tale.at + 1) + " / " + story.length;
      caption.querySelector("span").textContent =
        nameOf(links[index][0]) + " → " + nameOf(links[index][1]) + ": " + whats[index];
      tale.at = (tale.at + 1) % story.length;
      // D-469: the line shows, then goes, and only after a pause does the next one show
      tale.timer = setTimeout(() => {
        state.story = null;
        refresh();
        tale.timer = setTimeout(tell, tale.at === 0 ? 1600 : 450);
      }, 1500);
    };
    map.querySelectorAll(".am-step").forEach((item) => item.addEventListener("click", () => {
      tale.at = Number(item.dataset.step);
      state.story = null;
      tell();
    }));
    new ResizeObserver(settle(drawMain)).observe(map);
    map.querySelectorAll(".am-istage").forEach((stage) => new ResizeObserver(settle(() => drawInside(stage))).observe(stage));
    drawMain();
    tell();
  });
})();
