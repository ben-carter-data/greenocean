// Layout measurement of the pages of the menu (read-only: it never changes the DOM).
//
// Needs Playwright from outside the project (no dependency is added to the repo):
//   NODE_PATH=/path/to/node_modules node tests/medicion/medir.cjs <out_dir>
// Environment: BASE (default http://localhost:8599/), CHROMIUM_EXECUTABLE (default: the
// installed Chrome channel), PAGES (comma list of indexes), THEMES, LANG_PANEL (en), SIZES ("1440x790,..."; the real viewport of a 1440 x 900 screen, D-274).
//
// Per page, theme and size it writes <out_dir>/medicion.json (one row each) and, at
// 1440 x 900, a viewport screenshot in <out_dir>/capturas/<theme>/<n>-<slug>.png.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const out = process.argv[2] || 'medicion-out';
const base = process.env.BASE || 'http://localhost:8599/';
const executable = process.env.CHROMIUM_EXECUTABLE;
const themes = (process.env.THEMES || 'Vantablack,Blue Light').split(',');
// D-284: LANG=en measures the panel in English (longer texts must still fit).
const lang = process.env.LANG_PANEL || '';
const sizes = (process.env.SIZES || '1440x790,1920x1000,1440x700,1920x1080,1024x768,768x1024,390x844,844x390')
  .split(',').map(s => s.split('x').map(Number));
const only = process.env.PAGES ? process.env.PAGES.split(',').map(Number) : null;
const SHOT_SIZE = [1440, 900];

// Sidebar order: the nth internal link, then the GitHub page (the last link, href enlaces).
// D-282: the documents live in their folder; the menu has ten pages and GitHub.
const SLUGS = ['resumen-semanal', 'precios-e-inflacion', 'pipeline-y-linaje', 'modelo-de-datos',
  'calidad-y-auditoria', 'consultas-sql', 'centro-de-operacion', 'mapa-de-seguridad', 'stack-y-evidencia',
  'documentos', 'github'];

// Runs inside every frame (page and iframes). Self-contained on purpose.
function measureFrame(isChild) {
  const R = e => e.getBoundingClientRect();
  const vis = e => {
    const s = getComputedStyle(e), r = R(e);
    return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > 0 && r.width > 0 && r.height > 0;
  };
  const root = document.querySelector('[data-testid="stMainBlockContainer"]') || document.body;
  const main = document.querySelector('[data-testid="stMain"]');
  const vw = window.innerWidth, vh = window.innerHeight;
  const short = e => {
    const cls = (typeof e.className === 'string' ? e.className : (e.className && e.className.baseVal) || '')
      .split(/\s+/).filter(c => /^st-key-|^[a-z]+[-_][a-z0-9_-]+$/.test(c) && !/^(st-|e[0-9a-z]{6,})/.test(c) || /^st-key-/.test(c)).slice(0, 2).join('.');
    return e.tagName.toLowerCase() + (e.getAttribute('data-testid') ? '[' + e.getAttribute('data-testid') + ']' : '') + (cls ? '.' + cls : '') + (e.id ? '#' + e.id : '');
  };
  const inScope = e => root.contains(e) || root === document.body;
  const hiddenByAncestor = e => {
    for (let a = e; a && a !== document.body; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return true;
    }
    return false;
  };

  // Text lines: one rect per line of every text node that is visible.
  const lines = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.nodeValue.replace(/\s+/g, ' ').trim();
    const el = n.parentElement;
    if (!t || !el || /^(SCRIPT|STYLE|NOSCRIPT|TITLE)$/.test(el.tagName)) continue;
    if (hiddenByAncestor(el)) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    const isSvg = el instanceof SVGElement;
    let size = parseFloat(getComputedStyle(el).fontSize);
    if (isSvg) {
      const owner = el.closest('text') || el;
      const m = owner.getScreenCTM && owner.getScreenCTM();
      if (m) size = size * Math.hypot(m.a, m.b);
    } else if (el.offsetWidth > 0) {
      size = size * (R(el).width / el.offsetWidth || 1);
    }
    for (const r of range.getClientRects()) {
      if (r.width < 2 || r.height < 2) continue;
      lines.push({ el, t: t.slice(0, 40), l: r.left, r: r.right, top: r.top, b: r.bottom, size });
    }
  }
  const sr = e => e.matches && e.matches('[class*="sr-only"],[aria-hidden="true"][tabindex="-1"]');

  // Small texts (< 11 px rendered).
  const small = lines.filter(x => x.size < 10.95 && x.l < vw && x.r > 0)
    .map(x => ({ t: x.t, px: +x.size.toFixed(1), at: short(x.el) }));
  const smallUnique = [...new Map(small.map(s => [s.t + s.px, s])).values()];

  // Overlap text over text (different elements, 30% of the smaller box).
  const overlapText = [];
  for (let i = 0; i < lines.length; i++) {
    for (let j = i + 1; j < lines.length; j++) {
      const a = lines[i], b = lines[j];
      if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const w = Math.min(a.r, b.r) - Math.max(a.l, b.l), h = Math.min(a.b, b.b) - Math.max(a.top, b.top);
      if (w <= 1 || h <= 1) continue;
      const area = w * h, small_ = Math.min((a.r - a.l) * (a.b - a.top), (b.r - b.l) * (b.b - b.top));
      if (area / small_ >= 0.3 && a.l < vw && b.l < vw) overlapText.push({ a: a.t, b: b.t, pct: Math.round(100 * area / small_) });
    }
  }

  // Icons: img, svg <image>, material icons and small stand-alone svg.
  const icons = [];
  for (const e of root.querySelectorAll('img, image, [data-testid="stIconMaterial"], svg')) {
    if (!vis(e) || hiddenByAncestor(e)) continue;
    const r = R(e);
    if (e.tagName.toLowerCase() === 'svg') {
      if (e.querySelector('text') || r.width > 90 || r.height > 90) continue;
    }
    icons.push({ e, l: r.left, r: r.right, top: r.top, b: r.bottom, name: short(e) });
  }
  const overlapIcon = [];
  for (const x of lines) {
    for (const ic of icons) {
      if (ic.e.contains(x.el) || x.el.contains(ic.e)) continue;
      const w = Math.min(x.r, ic.r) - Math.max(x.l, ic.l), h = Math.min(x.b, ic.b) - Math.max(x.top, ic.top);
      if (w <= 1 || h <= 1) continue;
      const pct = 100 * w * h / ((x.r - x.l) * (x.b - x.top));
      if (pct >= 15) overlapIcon.push({ t: x.t, icon: ic.name, pct: Math.round(pct) });
    }
  }

  // Clipped text: the line leaves the box of an ancestor that hides its overflow.
  const clipped = [];
  for (const x of lines) {
    for (let a = x.el.parentElement; a && a !== document.body && a !== main; a = a.parentElement) {
      const s = getComputedStyle(a);
      const hides = v => v === 'hidden' || v === 'clip';
      if (!(hides(s.overflowX) || hides(s.overflowY))) continue;
      const r = R(a);
      const cutX = hides(s.overflowX) && (x.l < r.left - 2 || x.r > r.right + 2);
      const cutY = hides(s.overflowY) && (x.top < r.top - 2 || x.b > r.bottom + 2);
      if ((cutX || cutY) && r.width > 0 && r.height > 0) { clipped.push({ t: x.t, by: short(a), axis: (cutX ? 'x' : '') + (cutY ? 'y' : '') }); break; }
    }
  }

  // Content bottom, empty space under it and the tallest blocks (what makes the page grow).
  let bottom = 0;
  const bottoms = lines.filter(x => !sr(x.el)).map(x => x.b);
  for (const e of root.querySelectorAll('svg, img, iframe, canvas, button, input, textarea, [data-testid="stDataFrame"], [data-testid="stImage"]')) {
    if (vis(e) && !hiddenByAncestor(e)) bottoms.push(R(e).bottom);
  }
  bottom = bottoms.length ? Math.max(...bottoms) : 0;
  const mainRect = main ? R(main) : { top: 0, bottom: vh, height: vh };
  const blockRect = R(root);
  const tall = [...root.querySelectorAll('[data-testid="stVerticalBlock"], [data-testid="stIFrame"], iframe, [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"], svg, table, [class*="st-key-"]')]
    .filter(vis).map(e => ({ el: short(e), h: Math.round(R(e).height), w: Math.round(R(e).width) }))
    .sort((a, b) => b.h - a.h).slice(0, 6);

  // Diagrams and tables present and visible.
  const big = [...root.querySelectorAll('svg, canvas, [data-testid="stDataFrame"], table, img')]
    .filter(e => vis(e) && !hiddenByAncestor(e)).map(e => ({ el: short(e), w: Math.round(R(e).width), h: Math.round(R(e).height), l: Math.round(R(e).left), r: Math.round(R(e).right) }))
    .filter(b => b.w >= 200 && b.h >= 100);
  const svgs = [...root.querySelectorAll('svg')].filter(e => vis(e) && R(e).width >= 200 && R(e).height >= 100);
  const svgCut = svgs.filter(e => R(e).right > vw + 1 || R(e).left < -1).map(e => short(e));

  // Frames: each iframe, its box and the scroll of its own document when readable.
  const frames = [...root.querySelectorAll('iframe')].filter(vis).map(f => {
    let inner = null;
    try { inner = { sh: f.contentDocument.documentElement.scrollHeight, sw: f.contentDocument.documentElement.scrollWidth }; } catch (e) { inner = 'opaque'; }
    return { title: f.title || f.getAttribute('data-testid') || '', w: Math.round(R(f).width), h: Math.round(R(f).height), inner };
  });

  return {
    isChild,
    url: location.href.slice(0, 120),
    main: main ? { scroll: main.scrollHeight, client: main.clientHeight, scrollX: main.scrollWidth, clientW: main.clientWidth } : null,
    doc: { scroll: document.documentElement.scrollHeight, inner: vh, scrollX: document.documentElement.scrollWidth, innerW: vw },
    block: { h: Math.round(blockRect.height), w: Math.round(blockRect.width) },
    contentBottom: Math.round(bottom),
    emptyBelow: Math.round(mainRect.bottom - bottom),
    emptyPct: Math.round(100 * (mainRect.bottom - bottom) / (mainRect.height || vh)),
    nLines: lines.length,
    small: smallUnique.slice(0, 12), nSmall: smallUnique.length,
    overlapText: overlapText.slice(0, 10), nOverlapText: overlapText.length,
    overlapIcon: overlapIcon.slice(0, 10), nOverlapIcon: overlapIcon.length,
    clipped: clipped.slice(0, 10), nClipped: clipped.length,
    tall, big: big.slice(0, 12), nBig: big.length, svgCut, frames,
  };
}

async function settle(page) {
  // Streamlit marks the stale elements while it reruns.
  // The first load redirects to the first page's address; an evaluation cut by it counts as busy.
  for (let i = 0; i < 80; i++) {
    const busy = await page.evaluate(() => !!document.querySelector('[data-stale="true"], [data-testid="stStatusWidget"]'))
      .catch(() => true);
    if (!busy) break;
    await page.waitForTimeout(250);
  }
  await page.waitForTimeout(1800);
}

async function measureAll(page) {
  const parts = [];
  for (const frame of page.frames()) {
    try {
      const isChild = frame !== page.mainFrame();
      const m = await frame.evaluate(measureFrame, isChild);
      if (isChild && m.nLines === 0 && m.nBig === 0) continue;
      m.frameName = frame.name() || frame.url().slice(0, 40);
      parts.push(m);
    } catch (e) { /* detached frame */ }
  }
  return parts;
}

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch(executable
    ? { executablePath: executable, headless: true } : { channel: 'chrome', headless: true });
  const rows = [];
  const file = path.join(out, 'medicion.json');
  try {
    for (const theme of themes) {
      const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
      await page.goto(`${base}?tema=${encodeURIComponent(theme)}${lang ? `&lang=${lang}` : ''}`, { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('[data-testid="stSidebar"] a', { timeout: 90000 });
      await settle(page);
      const hrefs = await page.$$eval('[data-testid="stSidebar"] a', as => as.map(a => a.getAttribute('href')));
      const internal = hrefs.filter(h => h && !h.startsWith('http'));
      // The view links, then GitHub (href enlaces).
      const order = [...internal.filter(h => !h.startsWith('enlaces')), ...internal.filter(h => h.startsWith('enlaces'))];
      for (let i = 0; i < SLUGS.length; i++) {
        if (only && !only.includes(i)) continue;
        await page.setViewportSize({ width: 1440, height: 900 });
        const href = order[i];
        await page.locator(`[data-testid="stSidebar"] a[href="${href}"]`).first().click();
        await settle(page);
        for (const [w, h] of sizes) {
          await page.setViewportSize({ width: w, height: h });
          await page.waitForTimeout(1500);
          await settle(page);
          const parts = await measureAll(page);
          rows.push({ theme, n: i + 1, slug: SLUGS[i], w, h, parts });
          fs.writeFileSync(file, JSON.stringify(rows, null, 1) + '\n');
          if (w === SHOT_SIZE[0] && h === SHOT_SIZE[1]) {
            const dir = path.join(out, 'capturas', theme.replace(/\s+/g, '-'));
            fs.mkdirSync(dir, { recursive: true });
            await page.screenshot({ path: path.join(dir, `${String(i + 1).padStart(2, '0')}-${SLUGS[i]}.png`) });
          }
          const m = parts[0];
          console.log(theme, SLUGS[i], `${w}x${h}`, 'scroll', m.main && m.main.scroll, '/', m.main && m.main.client,
            'vacío', m.emptyPct + '%', 'peq', parts.reduce((s, p) => s + p.nSmall, 0),
            'txt×txt', parts.reduce((s, p) => s + p.nOverlapText, 0), 'txt×ico', parts.reduce((s, p) => s + p.nOverlapIcon, 0));
        }
      }
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
