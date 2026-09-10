import { chromium } from 'playwright-core';
const EMAIL='bassa.application@gmail.com';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/idmsa\.apple\.com|apple\.com.*(signin|auth)/.test(p.url())) || ctx.pages().find(p=>/apple\.com/.test(p.url()));
if(!page){ console.log('NO_APPLE_PAGE', ctx.pages().map(p=>p.url())); await b.close(); process.exit(0);}
console.log('page url:', page.url());
await page.bringToFront().catch(()=>{});
await page.waitForTimeout(1500);
// フレーム含めて account/email 入力欄を探索
async function probe(frame,label){
  const fields = await frame.evaluate(()=>{
    const els=[...document.querySelectorAll('input')];
    return els.map((e,i)=>({i,type:e.type,id:e.id,name:e.name,ph:e.placeholder,vis:!!(e.offsetParent),ac:e.autocomplete})).filter(f=>f.type!=='hidden');
  }).catch(()=>[]);
  if(fields.length) console.log('FRAME',label,JSON.stringify(fields));
  return fields;
}
const frames=page.frames();
console.log('frames:', frames.map(f=>f.url().slice(0,60)));
for(let k=0;k<frames.length;k++){ await probe(frames[k], k+':'+frames[k].url().slice(0,40)); }
await b.close().catch(()=>{});
