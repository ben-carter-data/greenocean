// D-248: each document page printed to PDF by Chrome, and the print checked against the page and its Markdown.
// For every document: the section titles and the diagrams visible in print media are the same, in the same order,
// as on screen and as in the .md file; nothing of the document is hidden or cut. Writes <out>/<doc>.pdf.
//   NODE_PATH=/path/to/node_modules node tests/medicion/imprimir.cjs <out_dir> [theme]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const out = process.argv[2] || 'impresion';
const theme = process.argv[3] || 'Vantablack';
const base = process.env.BASE || 'http://localhost:8599/';
const DOCS = [['PRD', 'PRD.md'], ['SAD', 'SAD.md'], ['ADR', 'ADR.md'], ['Plan de pruebas de seguridad', 'SEGURIDAD.md'],
              ['Escalabilidad', null]];

function markdownOutline(file) {
  if (!file) return null;
  const text = fs.readFileSync(path.join(__dirname, '..', '..', 'docs', file), 'utf8');
  const titles = [...text.matchAll(/^## (.+)$/gm)].map(m => m[1].trim());
  const diagrams = [...text.matchAll(/^\[\[diagrama:(\w+)\]\]\s*$/gm)].length;
  return { titles, diagrams };
}

function outline() {
  const doc = document.querySelector('.st-key-project_document');
  const visible = e => { const s = getComputedStyle(e); const r = e.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
  const titles = [...doc.querySelectorAll('h2')].filter(visible).map(h => h.innerText.trim());
  const diagrams = [...doc.querySelectorAll('[data-testid="stIFrame"], .doc-diagram')].filter(visible).length;
  const sidebar = document.querySelector('[data-testid="stSidebar"]');
  return { titles, diagrams, sidebarShown: !!sidebar && visible(sidebar), docHeight: Math.round(doc.getBoundingClientRect().height) };
}

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`${base}?tema=${encodeURIComponent(theme)}`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('[data-testid="stSidebar"] a', { timeout: 90000 });
  await page.waitForTimeout(3000);
  let failures = 0;
  for (const [label, file] of DOCS) {
    await page.emulateMedia({ media: 'screen' });
    await page.locator('[data-testid="stSidebar"] a', { hasText: label }).first().click();
    await page.waitForTimeout(6000);
    const screen = await page.evaluate(outline);
    await page.emulateMedia({ media: 'print' });
    await page.waitForTimeout(800);
    const print = await page.evaluate(outline);
    const md = markdownOutline(file);
    const name = (file || 'Escalabilidad').replace('.md', '');
    await page.pdf({ path: path.join(out, `${name}.pdf`), format: 'A4', printBackground: true });
    const pdfPages = (fs.readFileSync(path.join(out, `${name}.pdf`), 'latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
    const same = JSON.stringify(screen.titles) === JSON.stringify(print.titles) && screen.diagrams === print.diagrams;
    const matchesMd = !md || (JSON.stringify(md.titles) === JSON.stringify(print.titles) && md.diagrams === print.diagrams);
    const ok = same && matchesMd && !print.sidebarShown;
    if (!ok) failures += 1;
    console.log(`${ok ? 'OK ' : 'MAL'} ${name}: ${print.titles.length} títulos, ${print.diagrams} diagramas, ${pdfPages} páginas PDF` +
                (md ? ` · .md: ${md.titles.length} títulos, ${md.diagrams} diagramas` : '') +
                (same ? '' : ` · pantalla ${JSON.stringify(screen)}`) + (print.sidebarShown ? ' · el menú se imprime' : ''));
  }
  await browser.close();
  process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
