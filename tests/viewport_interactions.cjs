const {chromium}=require('playwright');
const {settle}=require('./viewport.cjs');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  for(const theme of ['Vantablack','Blue Light'])for(const [width,height]of [[1440,700],[1440,900],[1920,1080]]){
   const p=await browser.newPage({viewport:{width,height}});
   await p.goto(`http://localhost:8511/?tema=${encodeURIComponent(theme)}`);await settle(p,'Dashboard');
   const table=p.locator('.mock-products-table');
   const product=await table.evaluate(e=>{e.scrollTop=e.scrollHeight;return [e.scrollHeight,e.clientHeight,e.scrollTop]});
   if(product[2]<=0)throw Error('Product list cannot scroll');
   if(await p.locator('[data-testid="stMain"]').evaluate(e=>e.scrollTop))throw Error('Product scrolling moved stMain');
   const link=p.locator('[data-testid="stSidebar"] a').filter({hasText:'SAD · Arquitectura'});await link.click();await settle(p,'SAD · Arquitectura');
   await p.locator('.st-key-document_index a').nth(1).click();await p.waitForTimeout(500);
   const doc=await p.locator('.st-key-project_document').evaluate(e=>[e.scrollHeight,e.clientHeight,e.scrollTop]);
   const main=await p.locator('[data-testid="stMain"]').evaluate(e=>[e.scrollHeight,e.clientHeight,e.scrollTop]);
   if(doc[2]<=0||main[2]!==0||main[0]>main[1])throw Error(`Index failed: ${JSON.stringify({doc,main})}`);
   console.log(theme,width,height,'products',product,'document',doc,'main',main);
   await p.close();
  }
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
