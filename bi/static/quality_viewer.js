
const slides=[...document.querySelectorAll('.slide')];let at=0;
const pos=document.getElementById('pos');
const thumbs=document.getElementById('thumbs'),stage=document.getElementById('stage'),canvas=document.getElementById('canvas');
let tiles=[];
function show(i){at=Math.max(0,Math.min(slides.length-1,i));slides.forEach((s,k)=>s.classList.toggle('active',k===at));
tiles.forEach((t,k)=>t.classList.toggle('current',k===at));
if(tiles[at])tiles[at].scrollIntoView({block:'nearest',inline:'nearest'});
pos.textContent=(at+1)+' / '+slides.length;}
function fit(){const s=Math.min(stage.clientWidth/960,stage.clientHeight/540);canvas.style.transform='scale('+s+')';
tiles.forEach(t=>{t.firstChild.style.transform='scale('+(t.clientWidth/960)+')';});}
document.getElementById('prev').onclick=()=>show(at-1);document.getElementById('next').onclick=()=>show(at+1);
document.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='PageDown')show(at+1);
if(e.key==='ArrowLeft'||e.key==='PageUp')show(at-1);if(e.key==='Home')show(0);if(e.key==='End')show(slides.length-1);});
const full=document.getElementById('full');
if(!document.fullscreenEnabled){full.style.display='none';}
full.onclick=()=>{document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();};
document.getElementById('print').onclick=()=>window.print();
const places=v=>{const r=Math.round(v*1e6)/1e6;return Number.isInteger(r)?0:Math.abs(r)<1?2:1;};
const fmt=v=>v.toLocaleString(DATA.lang,{minimumFractionDigits:places(v),maximumFractionDigits:places(v)});
const unit=u=>u?' '+(DATA.units[u]||u):'';
const a=document.getElementById('cmp-a'),b=document.getElementById('cmp-b'),out=document.getElementById('cmp');
a.value=DATA.a;b.value=DATA.b;
function compare(){const ra=DATA.reports.find(r=>r.n==a.value),rb=DATA.reports.find(r=>r.n==b.value);
const top=Math.max(1,...ra.rows.concat(rb.rows).map(r=>r[1]||0));
const t=document.createElement('table');const head=document.createElement('tr');
[DATA.head[0],DATA.codes[ra.n],DATA.codes[rb.n],DATA.head[3]].forEach(h=>{const th=document.createElement('th');th.textContent=h;head.appendChild(th);});
const thead=document.createElement('thead');thead.appendChild(head);t.appendChild(thead);const body=document.createElement('tbody');
const keys=r=>r.rows.filter(x=>x[1]!==null).map(x=>x[3]).sort().join();const warn=document.getElementById('cmp-warn');
warn.hidden=keys(ra)===keys(rb);warn.textContent=DATA.warn;
rb.rows.filter(row=>ra.rows.some(x=>x[3]===row[3])).forEach(row=>{const old=ra.rows.find(x=>x[3]===row[3]);const before=old[1];const tr=document.createElement('tr');
const name=document.createElement('td');const strong=document.createElement('b');strong.textContent=row[0];name.appendChild(strong);
const bars=document.createElement('div');bars.className='pair';
[[before,'__GO_BEFORE__'],[row[1],'__GO_SKY__']].forEach(([v,c])=>{const i=document.createElement('i');i.style.background=c;
i.style.width=(v===null||v===undefined?0:Math.max(2,v/top*100))+'%';bars.appendChild(i);});name.appendChild(bars);
const ca=document.createElement('td');ca.className='num';ca.textContent=old[4];
const cb=document.createElement('td');cb.className='num';cb.textContent=row[4];
const d=document.createElement('td');d.className='num';
if(before===null||before===undefined||row[1]===null){d.textContent='—';}else{const diff=row[1]-before;
d.textContent=(diff>0?'+':'')+fmt(diff)+unit(row[2]);d.className='num '+(diff>0?'up':diff<0?'down':'');}
[name,ca,cb,d].forEach(c=>tr.appendChild(c));body.appendChild(tr);});t.appendChild(body);out.replaceChildren(t);}
a.onchange=compare;b.onchange=compare;compare();
slides.forEach((s,k)=>{const tile=document.createElement('button');tile.className='thumb';tile.setAttribute('aria-label',(k+1)+' / '+slides.length);
const mini=document.createElement('div');mini.className='mini';const copy=s.cloneNode(true);
copy.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));copy.setAttribute('aria-hidden','true');copy.classList.add('active');
mini.appendChild(copy);const number=document.createElement('i');number.textContent=k+1;tile.append(mini,number);
tile.onclick=()=>show(k);thumbs.appendChild(tile);tiles.push(tile);});
new ResizeObserver(fit).observe(stage);new ResizeObserver(fit).observe(thumbs);fit();show(0);
