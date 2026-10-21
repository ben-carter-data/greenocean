/* Run with Playwright available in NODE_PATH; no production dependency is added. */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
function codeHash(){
 const root=path.join(__dirname,'..','bi');
 const hash=crypto.createHash('sha256');
 for(const file of fs.readdirSync(root).filter(f=>/\.(py|css)$/.test(f)).sort())hash.update(file).update(fs.readFileSync(path.join(root,file)));
 return hash.digest('hex');
}
const url = process.env.APP_URL || 'http://localhost:8511/';
const output = process.env.VIEWPORT_OUTPUT || 'work/viewport';
const sizes = [[1440,700],[1440,900],[1920,1080]];
const views = ['Dashboard','Contexto del precio','Pipeline y arquitectura','Modelo de datos','Monitoreo','Consultas SQL',
 'SAD · Arquitectura','Ejecuciones','Mapa de seguridad','Plan de pruebas de seguridad','Stack y evidencia',
 'PRD · Requisitos del producto','ADR · Decisiones de arquitectura','Escalabilidad','Enlaces'];

async function audit(frame, selector = 'body') {
 return frame.evaluate(selector => {
  const root = document.querySelector(selector);
  if (!root) return {missing:true};
  const main = document.querySelector('[data-testid="stMain"]');
  const clipped=[], small=[], labels=[];
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  for(let node;node=walker.nextNode();) {
   const text=node.textContent.trim(), el=node.parentElement;
   if(!text||!el||el.closest('style,script,[aria-hidden="true"],.sqlx-hl,.stTooltipContent,[role="tooltip"]'))continue;
   if(!el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;
   const style=getComputedStyle(el);
   if(/Material|Symbols/.test(style.fontFamily))continue;
   const range=document.createRange();range.selectNodeContents(node);
   let rects=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0);
   if(!rects.length)continue;
   let visible=true;
   for(let a=el;a&&a!==root.parentElement;a=a.parentElement) {
    const s=getComputedStyle(a), r=a.getBoundingClientRect();
    if(s.opacity==='0'||s.visibility==='hidden'||s.display==='none'){visible=false;break;}
    const scrolls=/(auto|scroll)/.test(s.overflowX+' '+s.overflowY);
    if(scrolls) {rects=rects.map(t=>({top:Math.max(t.top,r.top),bottom:Math.min(t.bottom,r.bottom),left:Math.max(t.left,r.left),right:Math.min(t.right,r.right)})).filter(t=>t.bottom-t.top>1&&t.right-t.left>1);break;}
    if(/hidden|clip/.test(s.overflowX+' '+s.overflowY)&&r.width&&r.height) {
     for(const t of rects)if(t.left<r.left-2||t.right>r.right+2||t.top<r.top-2||t.bottom>r.bottom+2) {
      clipped.push({text:text.slice(0,70),ancestor:a.className?.baseVal??a.className});break;
     }
    }
   }
   if(!visible||!rects.length)continue;
   let font=parseFloat(style.fontSize);
   if(el instanceof SVGElement&&el.getScreenCTM){const m=el.getScreenCTM();if(m)font*=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));}
   if(font<10.95)small.push({text:text.slice(0,60),font:+font.toFixed(2),tag:el.tagName});
   for(const r of rects)if(r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth)labels.push({text:text.slice(0,60),el,r});
  }
  const overlaps=[];
  for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){
   const a=labels[i],b=labels[j];if(a.el===b.el||a.el.contains(b.el)||b.el.contains(a.el))continue;
   const width=Math.min(a.r.right,b.r.right)-Math.max(a.r.left,b.r.left);
   const height=Math.min(a.r.bottom,b.r.bottom)-Math.max(a.r.top,b.r.top);
   if(width>4&&height>3)overlaps.push([a.text,b.text]);
  }
  const diagrams=[...root.querySelectorAll('svg[viewBox]')].filter(e=>e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&e.getBoundingClientRect().height>30).length;
  const graphicOverlaps=[];
  for(const phase of root.querySelectorAll('.oc-phase'))for(const logo of root.querySelectorAll('.oc-logo')){
   const a=phase.getBoundingClientRect(),b=logo.getBoundingClientRect();
   if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>2&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2)graphicOverlaps.push(phase.textContent);
  }
  const box=document.querySelector('[data-testid="stMainBlockContainer"]');
  return {scroll:main?.scrollHeight??document.documentElement.scrollHeight,
   client:main?.clientHeight??innerHeight,width:innerWidth,height:innerHeight,
   diagrams,zoom:box?getComputedStyle(box).zoom:'1',clipped,small,overlaps,graphicOverlaps};
 },selector);
}
async function settle(frame, view) {
 await frame.locator(`[data-viewport-ready=${JSON.stringify(view)}]`).waitFor({state:'attached',timeout:60000});
 await frame.waitForFunction(()=>!document.querySelector('[data-testid="stMain"] [data-stale="true"]'));
 await (typeof frame.page==="function"?frame.page():frame).waitForTimeout(700);
 const exception=await frame.locator('[data-testid="stException"]').allTextContents();
 if(exception.length)throw new Error(exception.join('\n'));
}
module.exports={audit,settle};
if(require.main===module)(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const executable=process.env.CHROMIUM_EXECUTABLE||'/opt/pw-browsers/chromium';
 const browser=await chromium.launch(fs.existsSync(executable)?{executablePath:executable,headless:true}:{channel:'chrome',headless:true});
 const results=[];
 const initialHash=codeHash();
 fs.writeFileSync(path.join(output,'metadata.json'),JSON.stringify({appUrl:url,cloudWrapper:process.env.CLOUD_WRAPPER==='1',browser:browser.version(),codeSha256:initialHash,startedAt:new Date().toISOString()},null,2)+'\n');
 try{
  for(const theme of (process.env.ONE_THEME?[process.env.ONE_THEME]:['Vantablack','Blue Light'])){
   const page=await browser.newPage({viewport:{width:1440,height:700}});
   // Model the same-origin Cloud wrapper; fit must work with no stMain in the parent.
   let frame;
   if(process.env.CLOUD_WRAPPER==='1'){
    await page.route('**/__viewport_wrapper__',route=>route.fulfill({contentType:'text/html',body:`<!doctype html><style>html,body{margin:0;height:100%;}iframe{display:block;width:100%;height:100%;border:0;}</style><iframe src="${url}?tema=${encodeURIComponent(theme)}"></iframe>`}));
    await page.goto(new URL('__viewport_wrapper__',url).href);
    frame=await (await page.waitForSelector('iframe')).contentFrame();
   }else{
    await page.goto(`${url}?tema=${encodeURIComponent(theme)}`);frame=page;
    await page.waitForFunction(()=>document.querySelector('[data-viewport-ready],iframe[title="streamlitApp"]'));
    const cloud=await page.locator('iframe[title="streamlitApp"]').elementHandle();
    if(cloud)frame=await cloud.contentFrame();
   }
   await settle(frame,'Dashboard');
   for(const view of views.filter(v=>!process.env.ONLY_VIEWS||process.env.ONLY_VIEWS.split("|").includes(v))){
    let link;
    for(const a of await frame.locator('[data-testid="stSidebar"] a').all()){
     const href=await a.getAttribute('href');
     if(new URL(href,frame.url()).searchParams.get('vista')===view||(view==='Enlaces'&&href.startsWith('enlaces'))){link=a;break;}
    }
    if(!link)throw new Error(`Missing link: ${view}`);
    await link.click();await settle(frame,view);
    const cases=[['default',null]];
    if(process.env.VIEWPORT_VARIANTS==='1'){
     const button=name=>async()=>{await frame.getByText(name,{exact:true}).click()};
     if(view==='Pipeline y arquitectura')cases.push(['linaje',button('Linaje dbt')]);
     if(view==='Modelo de datos')for(const label of ['Modelo estrella','Entidad-relación','Cruces entre bases'])cases.push([label,button(label)]);
     if(view==='Contexto del precio'){
      cases.push(['sin-inflacion',button('Sin inflación')]);
      cases.push(['ampliar',async()=>{await frame.getByRole('button',{name:'Ampliar',exact:true}).first().click()}]);
     }
     if(view==='Consultas SQL')cases.push(['resultado',async()=>{
      await frame.locator('textarea').fill('SELECT * FROM main.weekly_price LIMIT 5000'+ '\n-- consulta extensa'.repeat(70));
      await frame.locator('.st-key-sqlx_run button').first().click();
      await frame.locator('[data-testid="stDataFrame"]').waitFor({state:'attached'});
     }]);
     if(view==='Ejecuciones')cases.push(['plataforma',async()=>{await frame.getByRole('tab',{name:'Plataforma',exact:true}).click()}]);
    }
    for(const [scenario, action] of cases){
     if(action){await action();await page.waitForTimeout(600);await settle(frame,view);}
    for(const [width,height]of sizes){
     await page.setViewportSize({width,height});await page.waitForTimeout(800);
     const main=await audit(frame,'.st-key-app_canvas');
     const embeds=[];
     for(const iframe of await frame.locator('.st-key-app_canvas iframe.stIFrame').all()){
      const rect=await iframe.boundingBox();if(!rect||rect.height<5)continue;
      const child=await (await iframe.elementHandle()).contentFrame();if(child)embeds.push(await audit(child));
     }
     const expectedEmbed=['Monitoreo','Mapa de seguridad','Plan de pruebas de seguridad','PRD · Requisitos del producto','Enlaces'].includes(view)||(view==='Modelo de datos'&&['default','Cruces entre bases'].includes(scenario))||(view==='Ejecuciones'&&scenario==='default');
     if(expectedEmbed&&!embeds.length)throw new Error(`Missing content iframe: ${view}`);
     if(['Contexto del precio','Pipeline y arquitectura'].includes(view)&&scenario!=='linaje'&&!main.diagrams)throw new Error(`Missing chart/diagram: ${view}`);
     const row={theme,view,scenario,width,height,...main,embeds};results.push(row);
     console.log(theme,view,scenario,width,height,main.scroll,main.client,'clip',main.clipped.length,'small',main.small.length,'overlap',main.overlaps.length,'embedded',embeds.map(e=>[e.scroll,e.client,e.clipped.length,e.small.length,e.overlaps.length]));
     fs.writeFileSync(path.join(output,'measurements.json'),JSON.stringify(results,null,2)+'\n');
     if(height===700)await page.screenshot({path:path.join(output,`${theme}-${views.indexOf(view)}-${scenario}.png`)});
    }
    await page.setViewportSize({width:1440,height:700});
    }
   }
   await page.close();
  }
 }finally{await browser.close();}
 if(codeHash()!==initialHash)throw new Error('Application source changed during the measurement run');
 const failures=results.filter(r=>r.scroll>r.client||r.zoom!=='1'||r.clipped.length||r.small.length||r.overlaps.length||r.graphicOverlaps.length||r.embeds.some(e=>e.scroll>e.client||e.clipped.length||e.small.length||e.overlaps.length||e.graphicOverlaps.length));
 console.log(`${results.length} measurements; ${failures.length} need attention`);
 if(failures.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
