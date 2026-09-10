import { chromium } from 'playwright-core';
import fs from 'fs';
const id='K37MFBXS5Y', nm='michinoekizukan';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
await page.goto('https://developer.apple.com/account/resources/identifiers/bundleId/edit/'+id,{waitUntil:'networkidle',timeout:40000}).catch(()=>{});
// App Groups ラベルが現れるまで待つ
for(let i=0;i<12;i++){ const ok=await page.evaluate(()=>[...document.querySelectorAll('*')].some(e=>e.children.length===0&&(e.textContent||'').trim()==='App Groups')); if(ok) break; await page.waitForTimeout(1500); }
await page.waitForTimeout(1500);
const chk=await page.evaluate(()=>{ const els=[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&(e.textContent||'').trim()==='App Groups'); for(const el of els){ let box=el; for(let k=0;k<8&&box;k++){ box=box.parentElement; if(box){ const cb=box.querySelector('input[type=checkbox]'); if(cb){ if(!cb.checked) cb.click(); return 'cb='+cb.checked; } } } } return 'no-label'; });
await page.waitForTimeout(1500);
const cfg=await page.evaluate(()=>{ const els=[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&(e.textContent||'').trim()==='App Groups'); for(const el of els){ let box=el; for(let k=0;k<8&&box;k++){ box=box.parentElement; if(box){ const c=[...box.querySelectorAll('button')].find(b=>/configure/i.test(b.innerText||'')); if(c){c.click(); return 'ok';} } } } return 'no-cfg'; });
await page.waitForTimeout(3200);
const pick=await page.evaluate(()=>{ const rows=[...document.querySelectorAll('*')].filter(e=>/group\.com\.basaapp\.liferesult/.test(e.textContent||'')); let t=null; for(const e of rows){ if(e.children.length<=2) t=e; } if(!t) return 'no-group'; let box=t,cb=null; for(let k=0;k<6&&box;k++){ cb=box.querySelector&&box.querySelector('input[type=checkbox]'); if(cb) break; box=box.parentElement; } if(!cb) return 'no-cb'; if(!cb.checked) cb.click(); return 'checked='+cb.checked; });
await page.waitForTimeout(1000);
await page.evaluate(()=>{ const c=[...document.querySelectorAll('button')].find(b=>/^continue$/i.test((b.innerText||'').trim())); if(c) c.click(); });
await page.waitForTimeout(2200);
const sv=await page.evaluate(()=>{ const s=[...document.querySelectorAll('button')].find(b=>/^save$/i.test((b.innerText||'').trim())&&!b.disabled); if(s){s.click(); return 'save';} return 'no-save'; });
await page.waitForTimeout(2500);
await page.evaluate(()=>{ const c=[...document.querySelectorAll('button')].find(b=>/^(confirm|modify)$/i.test((b.innerText||'').trim())); if(c) c.click(); });
await page.waitForTimeout(4000);
console.log(nm,'chk='+chk,'cfg='+cfg,'pick='+pick,sv,'url:',page.url().includes('/list')?'LIST(ok)':'still-edit');
await b.close().catch(()=>{});
