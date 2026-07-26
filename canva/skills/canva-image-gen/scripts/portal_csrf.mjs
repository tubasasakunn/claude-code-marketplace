import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
let cap=null;
page.on('request', req=>{
  const u=req.url();
  if(/services-account\/v1\/bundleIds/i.test(u) && !cap){
    const h=req.headers();
    cap={url:u, method:req.method(), headers:h};
  }
});
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'networkidle',timeout:35000}).catch(()=>{});
await page.waitForTimeout(5000);
if(!cap){ console.log('NO_CAPTURE'); await b.close(); process.exit(0); }
// csrf関連ヘッダだけ抜く（値は長さ表示・存在確認）
const h=cap.headers;
const keys=Object.keys(h).filter(k=>/csrf|override|team|x-/i.test(k));
console.log('captured', cap.method, cap.url.slice(0,80));
for(const k of keys) console.log('  hdr', k, '=', (h[k]||'').slice(0,50));
// この csrf を使って appGroups を読む
const res = await page.evaluate(async (hh)=>{
  const headers={'Content-Type':'application/vnd.api+json','X-HTTP-Method-Override':'GET'};
  for(const k of Object.keys(hh)){ if(/^csrf/i.test(k)) headers[k]=hh[k]; }
  try{
    const r=await fetch('https://developer.apple.com/services-account/v1/appGroups?limit=100',{method:'POST',headers,credentials:'include',body:JSON.stringify({})});
    const t=await r.text(); let bd; try{bd=JSON.parse(t)}catch{bd=t.slice(0,300)}
    return {status:r.status, count:(bd.data?bd.data.length:null), groups:(bd.data?bd.data.map(g=>({id:g.id,ident:g.attributes&&g.attributes.identifier})):bd)};
  }catch(e){return {err:e.message}}
}, h);
console.log('appGroups via override:', JSON.stringify(res,null,2).slice(0,800));
await b.close().catch(()=>{});
