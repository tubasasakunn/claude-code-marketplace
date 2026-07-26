import { chromium } from 'playwright-core';
import fs from 'fs';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
const writes=[];
page.on('request', req=>{ const u=req.url(); const m=req.method(); const ov=(req.headers()['x-http-method-override']||'').toUpperCase();
  if(/services-account\/v1\//i.test(u) && (m==='POST'||m==='PATCH'||m==='PUT') && ov!=='GET'){ writes.push({m,ov,u:u.slice(0,90),body:(req.postData()||'').slice(0,400)}); }
});
await page.goto('https://developer.apple.com/account/resources/identifiers/bundleId/edit/9AZ582Q782',{waitUntil:'networkidle',timeout:35000}).catch(()=>{});
await page.waitForTimeout(4000);
async function shot(n){ try{ const buf=await page.screenshot(); fs.writeFileSync('/tmp/ag_'+n+'.png', buf);}catch{} }
await shot('01_edit');
// App Groups 行を特定して checkbox 有効化 + Configure
const step = await page.evaluate(()=>{
  function findRow(labelText){
    const els=[...document.querySelectorAll('*')].filter(e=>e.children.length===0 && (e.textContent||'').trim()===labelText);
    for(const el of els){ let box=el; for(let k=0;k<8&&box;k++){ box=box.parentElement; if(box){ const cb=box.querySelector('input[type=checkbox]'); const cfg=[...box.querySelectorAll('button')].find(b=>/configure/i.test(b.innerText||'')); if(cb||cfg) return {box,cb,cfg}; } } }
    return null;
  }
  const r=findRow('App Groups');
  if(!r) return {err:'no App Groups row'};
  const info={hadCheckbox:!!r.cb, checked:r.cb?r.cb.checked:null, hasConfigure:!!r.cfg};
  if(r.cb && !r.cb.checked){ r.cb.click(); info.clickedCheckbox=true; }
  return info;
});
console.log('checkbox step:', JSON.stringify(step));
await page.waitForTimeout(1500); await shot('02_checked');
// Configure をクリック（App Groups行の）
const cfg = await page.evaluate(()=>{
  const els=[...document.querySelectorAll('*')].filter(e=>e.children.length===0 && (e.textContent||'').trim()==='App Groups');
  for(const el of els){ let box=el; for(let k=0;k<8&&box;k++){ box=box.parentElement; if(box){ const c=[...box.querySelectorAll('button')].find(b=>/configure/i.test(b.innerText||'')); if(c){ c.click(); return 'clicked Configure'; } } } }
  return 'no Configure in row';
});
console.log('configure:', cfg);
await page.waitForTimeout(3000); await shot('03_modal');
// モーダル内: liferesult グループの checkbox をチェック
const pick = await page.evaluate(()=>{
  // モーダル内の group 行
  const rows=[...document.querySelectorAll('*')].filter(e=>/group\.com\.basaapp\.liferesult/.test(e.textContent||'') );
  // 最深要素
  let target=null; for(const e of rows){ if(e.children.length<=2){ target=e; } }
  if(!target) return {err:'liferesult not in modal', modalText:(document.body.innerText||'').slice(0,300)};
  let box=target; let cb=null; for(let k=0;k<6&&box;k++){ cb=box.querySelector&&box.querySelector('input[type=checkbox]'); if(cb) break; box=box.parentElement; }
  if(!cb) return {err:'no checkbox for liferesult'};
  const was=cb.checked; if(!cb.checked) cb.click();
  return {was, nowChecked:cb.checked};
});
console.log('pick liferesult:', JSON.stringify(pick));
await page.waitForTimeout(1200); await shot('04_picked');
console.log('=== writes so far ==='); writes.forEach(w=>console.log(' ', JSON.stringify(w)));
console.log('NOTE: まだ Save/Confirm は押していない（安全確認のため）');
await b.close().catch(()=>{});
