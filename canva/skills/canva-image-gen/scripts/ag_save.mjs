import { chromium } from 'playwright-core';
import fs from 'fs';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account\/resources\/identifiers\/bundleId\/edit/.test(p.url())) || ctx.pages().find(p=>/developer\.apple\.com/.test(p.url()));
if(!page){ console.log('NO_EDIT_PAGE'); await b.close(); process.exit(0); }
const writes=[];
page.on('request', req=>{ const u=req.url(); const ov=(req.headers()['x-http-method-override']||'').toUpperCase();
  if(/services-account\/v1\//i.test(u) && (req.method()==='POST'||req.method()==='PATCH') && ov!=='GET'){ writes.push({m:req.method(),ov,u:u.replace('https://developer.apple.com','').slice(0,70),body:(req.postData()||'').slice(0,500)}); }
});
async function shot(n){ try{ fs.writeFileSync('/tmp/ag_'+n+'.png', await page.screenshot()); }catch{} }
// 1) モーダルの Continue
let r = await page.evaluate(()=>{ const btns=[...document.querySelectorAll('button')]; const c=btns.find(b=>/^continue$/i.test((b.innerText||'').trim())); if(c){c.click(); return 'continue clicked';} return 'no continue'; });
console.log('modal:', r); await page.waitForTimeout(2500); await shot('05_afterContinue');
// 2) Save
r = await page.evaluate(()=>{ const btns=[...document.querySelectorAll('button')]; const s=btns.find(b=>/^save$/i.test((b.innerText||'').trim()) && !b.disabled); if(s){s.click(); return 'save clicked';} return 'no enabled Save (disabled='+String(btns.some(b=>/^save$/i.test((b.innerText||'').trim())))+')'; });
console.log('save:', r); await page.waitForTimeout(2500); await shot('06_afterSave');
// 3) 確認ダイアログ（Modify App Capabilities → Confirm）
r = await page.evaluate(()=>{ const btns=[...document.querySelectorAll('button')]; const c=btns.find(b=>/^(confirm|modify|続ける|変更)$/i.test((b.innerText||'').trim())); const labels=btns.map(b=>(b.innerText||'').trim()).filter(Boolean); if(c){c.click(); return 'confirm clicked ('+c.innerText.trim()+')';} return 'no confirm. buttons='+JSON.stringify(labels.slice(0,10)); });
console.log('confirm:', r); await page.waitForTimeout(3500); await shot('07_afterConfirm');
console.log('url now:', page.url());
console.log('=== WRITE calls captured ==='); writes.forEach(w=>console.log(JSON.stringify(w)));
await b.close().catch(()=>{});
