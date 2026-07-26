import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account\/resources/.test(p.url())) || await ctx.newPage();
await page.bringToFront().catch(()=>{});
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'domcontentloaded',timeout:30000});
await page.waitForTimeout(4000);
console.log('list url:', page.url());
// Honzukan 行のリンクを探す
const link = await page.evaluate(()=>{
  const as=[...document.querySelectorAll('a')];
  for(const a of as){ const t=(a.innerText||'').trim(); if(/honzukan/i.test(t) && /identifiers\/bundleId\/edit/.test(a.href)) return a.href; }
  // テキストにcom.basaapp.honzukanを含む行の近くのeditリンク
  for(const a of as){ if(/identifiers\/bundleId\/edit/.test(a.href)){ const row=a.closest('tr')||a.parentElement; if(row && /honzukan/i.test(row.innerText||'')) return a.href; } }
  return null;
});
console.log('Honzukan edit link:', link);
if(!link){ 
  const rows = await page.evaluate(()=>[...document.querySelectorAll('tr,a')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/honzukan|basaapp/i.test(t)).slice(0,10));
  console.log('rows:', JSON.stringify(rows));
  await b.close(); process.exit(0);
}
await page.goto(link,{waitUntil:'domcontentloaded',timeout:30000});
await page.waitForTimeout(4000);
console.log('edit url:', page.url());
// App Groups 関連UIを探索
const ag = await page.evaluate(()=>{
  const res={appGroupsChecked:null, configureBtns:[], labels:[]};
  // capability行: label "App Groups"
  const all=[...document.querySelectorAll('*')];
  for(const el of all){
    const t=(el.innerText||'').trim();
    if(/^App Groups$/i.test(t) && el.children.length<3){ 
      // 近傍のcheckbox/button
      const box=el.closest('div,tr,li')||el.parentElement;
      const cb=box?box.querySelector('input[type=checkbox]'):null;
      res.appGroupsChecked = cb? cb.checked : 'no-checkbox';
      const btns=box?[...box.querySelectorAll('button,a')].map(b=>(b.innerText||'').trim()).filter(Boolean):[];
      res.labels.push('AppGroups box btns: '+JSON.stringify(btns));
    }
  }
  res.configureBtns=[...document.querySelectorAll('button,a')].map(b=>(b.innerText||'').trim()).filter(t=>/configure|edit|assign|設定|編集/i.test(t)).slice(0,10);
  return res;
});
console.log('AppGroups state:', JSON.stringify(ag,null,2));
await b.close().catch(()=>{});
