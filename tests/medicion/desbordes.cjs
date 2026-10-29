// Finds text that sticks out of its box or of its card, or is cut without an ellipsis (D-324). Read-only: it never
// changes the project. For every page of the menu (and each of its tabs, and the enlarged products table) it lists the
// elements whose own text is wider than their box, or that leave the card or the window that holds them.
//
// Usage: NODE_PATH=<folder with playwright> node tests/medicion/desbordes.cjs http://localhost:8501 > out.json
// Environment: THEMES (default Corporativo,Vantablack), LANGS (default es,en), SIZES (default "1440x790,1920x1000,1280x720,
// 1024x768,844x390"), PAGES (comma list of menu positions, to look at a few).
const { chromium } = require('playwright');

const BASE = process.argv[2] || 'http://localhost:8501';
const THEMES = (process.env.THEMES || 'Corporativo,Vantablack').split(',');
const LANGS = (process.env.LANGS || 'es,en').split(',');
const SIZES = (process.env.SIZES || '1440x790,1920x1000,1280x720,1024x768,844x390').split(',').map((s) => s.split('x').map(Number));
const ONLY = process.env.PAGES ? process.env.PAGES.split(',').map(Number) : null;

// Runs inside every frame: self-contained on purpose.
function findOverflows() {
  const found = [];
  const clip = (value) => value === 'hidden' || value === 'clip' || value === 'auto' || value === 'scroll';
  const visible = (e) => {
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > 0 && r.width > 1 && r.height > 1;
  };
  const label = (e) => {
    const test = e.getAttribute('data-testid');
    const classes = typeof e.className === 'string'
      ? e.className.trim().split(/\s+/).filter((c) => c && !/^st-emotion|^e[0-9a-z]{6,}$|^st-[a-z]{1,3}$/.test(c)).slice(0, 3)
      : [];
    return e.tagName.toLowerCase() + (test ? `[${test}]` : '') + (classes.length ? '.' + classes.join('.') : '');
  };
  const ownText = (e) => [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
  const boxed = (s) => parseFloat(s.borderRightWidth) > 0 || parseFloat(s.borderLeftWidth) > 0 || (s.backgroundColor && s.backgroundColor !== 'rgba(0, 0, 0, 0)');
  const vw = document.documentElement.clientWidth;
  for (const e of document.querySelectorAll('body *')) {
    if (['SCRIPT', 'STYLE', 'SVG', 'PATH', 'TEMPLATE', 'OPTION'].includes(e.tagName.toUpperCase())) continue;
    const text = ownText(e);
    if (!text && !['BUTTON', 'INPUT'].includes(e.tagName)) continue;
    if (!visible(e)) continue;
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    if (s.position === 'fixed') continue;
    if (e.closest('[role="tooltip"], [data-baseweb="popover"], .stTooltipContent, [aria-hidden="true"], .sr-only')) continue;
    // What a closed details holds is not drawn for the reader: only its summary is (D-327).
    const folded = e.closest('details:not([open])');
    if (folded && !e.closest('summary')) continue;
    // 1) the element's own text is wider (or taller) than its box; the width is the text's own, not a hidden child's
    if (s.display !== 'inline' && e.clientWidth > 0 && !(e instanceof SVGElement)) {
      let textRight = -Infinity;
      for (const node of e.childNodes) {
        if (node.nodeType !== 3 || !node.textContent.trim()) continue;
        const range = document.createRange(); range.selectNodeContents(node);
        for (const rect of range.getClientRects()) textRight = Math.max(textRight, rect.right);
      }
      const k = e.offsetWidth ? r.width / e.offsetWidth : 1;  // the phone in landscape draws the page scaled
      const room = r.right - (parseFloat(s.paddingRight) + parseFloat(s.borderRightWidth)) * k;
      const wider = Math.round(textRight - room);
      if (textRight > -Infinity && wider > 2) {
        if ((s.overflowX === 'hidden' || s.overflowX === 'clip') && s.textOverflow !== 'ellipsis') found.push({ kind: 'recortado', by: wider, el: label(e), text: text.slice(0, 60) });
        else if (s.overflowX === 'visible') found.push({ kind: 'texto más ancho que su caja', by: wider, el: label(e), text: text.slice(0, 60) });
      }
      const taller = e.scrollHeight - e.clientHeight;
      if (taller > 2 && (s.overflowY === 'hidden' || s.overflowY === 'clip') && !(s.webkitLineClamp && s.webkitLineClamp !== 'none')) {
        found.push({ kind: 'recortado en alto', by: taller, el: label(e), text: text.slice(0, 60) });
      }
    }
    // 2) the element leaves the card (or the window) that holds it, with nothing that scrolls or clips in between
    let parent = e.parentElement, contained = false;
    while (parent && parent !== document.body) {
      const ps = getComputedStyle(parent);
      if (clip(ps.overflowX)) { contained = true; break; }
      if (boxed(ps) && ps.display !== 'inline') {
        const pr = parent.getBoundingClientRect();
        if (pr.width > 1 && (r.right > pr.right + 1.5 || r.left < pr.left - 1.5)) {
          found.push({ kind: 'fuera de su tarjeta', by: Math.round(Math.max(r.right - pr.right, pr.left - r.left)), el: label(e), text: text.slice(0, 60), card: label(parent) });
        }
        break;
      }
      parent = parent.parentElement;
    }
    if (!contained && (r.right > vw + 1.5 || r.left < -1.5) && !e.closest('[data-testid="stSidebar"]')) {
      found.push({ kind: 'fuera de la ventana', by: Math.round(Math.max(r.right - vw, -r.left)), el: label(e), text: text.slice(0, 60) });
    }
  }
  return found;
}

async function audit(page) {
  const all = [];
  for (const frame of page.frames()) {
    try {
      const rows = await frame.evaluate(findOverflows);
      all.push(...rows.map((row) => ({ ...row, frame: frame === page.mainFrame() ? 'página' : 'iframe' })));
    } catch (error) { if (!/detached|destroyed|closed/i.test(String(error))) console.error('frame:', String(error).slice(0, 200)); }
  }
  return all;
}

async function settle(page, timeout = 60000) {
  await page.waitForSelector('[data-testid="stApp"][data-test-script-state="notRunning"]', { timeout });
  await page.waitForTimeout(700);
}

(async () => {
  const browser = await chromium.launch();
  const result = [];
  const seen = new Set();
  const record = (where, rows) => {
    for (const row of rows) {
      const key = [where.page, where.theme, where.lang, where.size, row.kind, row.el, row.text].join('|');
      if (!seen.has(key)) { seen.add(key); result.push({ ...where, ...row }); }
    }
  };
  for (const lang of LANGS) for (const theme of THEMES) for (const [width, height] of SIZES) {
    const context = await browser.newContext({ viewport: { width, height } });
    const page = await context.newPage();
    const start = `${BASE}/?perfil=profesional&tema=${theme}${lang === 'en' ? '&lang=en' : ''}`;
    await page.goto(start);
    try { await settle(page, 90000); } catch (error) { continue; }
    const links = await page.evaluate(() => [...document.querySelectorAll('[data-testid="stSidebar"] a[href]')].filter((a) => !a.closest('.st-key-assessment_line'))
      .map((a) => ({ name: a.innerText.split('\n').map((l) => l.trim()).filter((l) => l && !/^[a-z_]+$/.test(l)).pop() || '', href: a.getAttribute('href') }))
      .filter((l) => l.name && !l.href.startsWith('http') && !l.href.includes('github.com'))
      .filter((l, i, all) => all.findIndex((o) => o.href === l.href) === i));
    for (const [index, link] of links.entries()) {
      if (ONLY && !ONLY.includes(index)) continue;
      const where = { page: link.name, theme, lang, size: `${width}x${height}` };
      const address = new URL(link.href, BASE + '/');
      address.searchParams.set('perfil', 'profesional'); address.searchParams.set('tema', theme);
      if (lang === 'en') address.searchParams.set('lang', 'en');
      await page.goto(address.toString());
      try { await settle(page); } catch (error) { record(where, [{ kind: 'no termina de cargar', by: 0, el: '', text: '', frame: 'página' }]); continue; }
      record(where, await audit(page));
      const tabs = page.locator('[role="tab"]:visible');
      const count = Math.min(await tabs.count(), 12);
      for (let t = 0; t < count; t++) {
        try {
          const name = ((await tabs.nth(t).innerText()) || '').trim().slice(0, 30);
          await tabs.nth(t).click(); await page.waitForTimeout(900);
          record({ ...where, page: `${link.name} › ${name}` }, await audit(page));
        } catch (error) { /* the tab went away */ }
      }
      if (link.name.startsWith('Panorama')) {
        const enlarge = page.locator('.st-key-home_products_enlarge button').first();
        if (await enlarge.count()) {
          await enlarge.click(); await page.waitForTimeout(1800);
          record({ ...where, page: 'Panorama › tabla ampliada' }, await audit(page));
          await page.keyboard.press('Escape'); await page.waitForTimeout(500);
        }
      }
    }
    await context.close();
  }
  await browser.close();
  process.stdout.write(JSON.stringify(result));
})().catch((error) => { console.error(error); process.exit(1); });
