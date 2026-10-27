// Measures the dashboard in real browsers (D-323): load time of every page of the menu, WCAG 2.1 AA violations with
// axe-core, and the layout checks in Chromium, Firefox and WebKit at desktop sizes and a phone in landscape.
//
// Usage: NODE_PATH=<folder with playwright and axe-core> node tests/medicion/calidad.cjs http://localhost:8599 > out.json
// Prints one JSON object; it never changes the project.
const fs = require('fs');
const path = require('path');
const { chromium, firefox, webkit } = require('playwright');

const BASE = process.argv[2] || 'http://localhost:8599';
const AXE = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const SIZES = [[1440, 790], [1920, 1000], [844, 390]];
const BROWSERS = { chromium, firefox, webkit };
const START = '/dashboard?perfil=profesional&tema=Vantablack';

async function settle(page, timeout = 60000) {
  // Streamlit marks the app «notRunning» when the script has finished drawing the page.
  await page.waitForSelector('[data-testid="stApp"][data-test-script-state="notRunning"]', { timeout });
}

async function menuLinks(page) {
  return page.evaluate(() => [...document.querySelectorAll('[data-testid="stSidebar"] a[href]')].filter((a) => !a.closest('.st-key-assessment_line'))
    // The menu's icons are ligatures (grid_view, lock...): the name is the line that is not one.
    .map((a) => ({ name: a.innerText.split('\n').map((line) => line.trim()).filter((line) => line && !/^[a-z_]+$/.test(line)).pop() || '',
                   href: a.getAttribute('href') }))
    .filter((link) => link.name && !link.href.startsWith('http') && !link.href.includes('github.com'))
    .filter((link, index, all) => all.findIndex((other) => other.href === link.href) === index));
}

async function layout(page) {
  return page.evaluate(() => {
    const main = document.querySelector('[data-testid="stMain"]');
    return { error: !!document.querySelector('[data-testid="stException"]'),
             horizontal: document.documentElement.scrollWidth > window.innerWidth + 2,
             overflow: main ? main.scrollHeight - main.clientHeight : null };
  });
}

(async () => {
  const result = { base: BASE, pages: {}, browsers: {} };
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 790 } });
  await page.goto(BASE + START);
  await settle(page, 90000);
  const links = await menuLinks(page);
  for (const link of links) {
    const started = Date.now();
    await page.goto(new URL(link.href, BASE + '/').toString());
    await settle(page);
    const seconds = (Date.now() - started) / 1000;
    await page.waitForTimeout(600);  // let the last frames paint before the audit
    await page.addScriptTag({ content: AXE });
    const axe = await page.evaluate(async () => {
      const report = await window.axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] });
      return report.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length }));
    });
    result.pages[link.name] = { href: link.href, seconds, violations: axe.length,
                                nodes: axe.reduce((sum, v) => sum + v.nodes, 0), rules: axe };
  }
  await browser.close();
  if (process.argv.includes('--pages-only')) { process.stdout.write(JSON.stringify(result)); return; }
  for (const [name, engine] of Object.entries(BROWSERS)) {
    const checks = [];
    const instance = await engine.launch();
    for (const [width, height] of SIZES) {
      const context = await instance.newContext({ viewport: { width, height } });
      const tab = await context.newPage();
      await tab.goto(BASE + START);
      try { await settle(tab, 90000); } catch (error) { checks.push({ size: `${width}x${height}`, page: 'inicio', ok: false, why: 'no termina de cargar' }); await context.close(); continue; }
      for (const link of links) {
        await tab.goto(new URL(link.href, BASE + '/').toString());
        let state;
        try { await settle(tab); await tab.waitForTimeout(600); state = await layout(tab); } catch (error) { state = { error: true, why: 'tiempo agotado' }; }
        const ok = !state.error && !state.horizontal;
        checks.push({ size: `${width}x${height}`, page: link.name, ok, ...state });
      }
      await context.close();
    }
    await instance.close();
    result.browsers[name] = { checks: checks.length, passed: checks.filter((c) => c.ok).length,
                              failed: checks.filter((c) => !c.ok) };
  }
  process.stdout.write(JSON.stringify(result));
})().catch((error) => { console.error(error); process.exit(1); });
