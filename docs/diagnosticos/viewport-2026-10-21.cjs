const { chromium } = require('playwright');
const fs = require('fs');
const views={'dashboard':'Dashboard','estacionalidad':'Contexto del precio','diagramas':'Pipeline y arquitectura','arquitectura':'Modelo de datos','operaciones':'Monitoreo','consultas-sql':'Consultas SQL','sad':'SAD · Arquitectura','ejecuciones':'Ejecuciones','mapa-de-seguridad':'Mapa de seguridad','plan-de-pruebas-de-seguridad':'Plan de pruebas de seguridad','stack-y-evidencia':'Stack y evidencia','prd':'PRD · Requisitos del producto','adr':'ADR · Decisiones de arquitectura','escalabilidad':'Escalabilidad','enlaces':'Enlaces'};const pages=['dashboard','estacionalidad','diagramas','arquitectura','operaciones','consultas-sql','sad','ejecuciones','mapa-de-seguridad','plan-de-pruebas-de-seguridad','stack-y-evidencia','prd','adr','escalabilidad','enlaces'];

// Read-only production diagnosis. Run with Playwright available through NODE_PATH.
const output = process.argv[2] || 'viewport-measurements.json';
const executable = process.env.CHROMIUM_EXECUTABLE || '/opt/pw-browsers/chromium';
const sizes = [[1440, 700], [1440, 900], [1920, 1080]];
const base = 'https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app/';

(async () => {
  const browser = await chromium.launch(fs.existsSync(executable)
    ? { executablePath: executable, headless: true }
    : { channel: 'chrome', headless: true });
  const rows = [];
  try {
    for (const theme of ['Vantablack', 'Blue Light']) {
      const page = await browser.newPage({ viewport: { width: 1440, height: 700 } });
      await page.goto(`${base}?tema=${encodeURIComponent(theme)}`, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => typeof window.__greenoceanFit === 'function');
      let frame;
      for (let attempt = 0; attempt < 120; attempt++) {
        for (const candidate of page.frames()) {
          if (await candidate.locator('[data-testid="stSidebar"] a').count().catch(() => 0) > 12) {
            frame = candidate;
          }
        }
        if (frame) break;
        await page.waitForTimeout(500);
      }
      if (!frame) throw new Error(`No app sidebar: ${theme}`);
      await page.waitForTimeout(6000);
      for (const path of pages) {
        const desired = views[path];
        let target;
        for (const anchor of await frame.locator('[data-testid="stSidebar"] a').all()) {
          const href = await anchor.getAttribute('href');
          if (new URL(href, frame.url()).searchParams.get('vista') === desired ||
              (path === 'enlaces' && href.startsWith('enlaces'))) {
            target = anchor;
            break;
          }
        }
        if (!target) throw new Error(`Missing navigation link: ${theme}, ${path}`);
        await target.click();
        await page.waitForTimeout(3500);
        for (const [w, h] of sizes) {
          await page.setViewportSize({ width: w, height: h });
          await page.waitForTimeout(1200);
          const measurement = await frame.evaluate(() => {
            const main = document.querySelector('[data-testid="stMain"]');
            const box = document.querySelector('[data-testid="stMainBlockContainer"]');
            return {
              url: location.href,
              scroll: main.scrollHeight,
              client: main.clientHeight,
              box: Math.round(box.getBoundingClientRect().height),
              zoom: getComputedStyle(box).zoom,
              fit: typeof window.__greenoceanFit,
              parentFit: typeof parent.__greenoceanFit,
              panel: [...box.querySelectorAll('[data-testid="stVerticalBlock"],iframe,[data-testid="stVegaLiteChart"],svg,[data-testid="stDataFrame"]')]
                .map(element => ({
                  tag: element.tagName,
                  id: element.getAttribute('data-testid'),
                  cls: element.className?.baseVal ?? element.className,
                  h: Math.round(element.getBoundingClientRect().height),
                  text: element.innerText?.slice(0, 110)
                })).sort((a, b) => b.h - a.h).slice(0, 10)
            };
          });
          rows.push({ theme, path, w, h, ...measurement });
          fs.writeFileSync(output, JSON.stringify(rows, null, 2) + '\n');
          console.log(theme, path, w, h, measurement.scroll, measurement.client);
        }
        await page.setViewportSize({ width: 1440, height: 700 });
      }
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
