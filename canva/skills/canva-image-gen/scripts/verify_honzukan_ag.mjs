import { chromium } from 'playwright-core';
import fs from 'fs';
const TEAM='7NN5KD3TSU';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
let H=null;
page.on('request', req=>{ const u=req.url(); if(/services-account\/v1\//i.test(u)&&req.method()==='POST'&&!H){const h=req.headers(); if(h.csrf) H={csrf:h.csrf,csrf_ts:h.csrf_ts};} });
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'networkidle',timeout:35000}).catch(()=>{});
await page.waitForTimeout(3500);
if(!H){ console.log('NO_CSRF'); await b.close(); process.exit(0); }
const res = await page.evaluate(async ({TEAM,H})=>{
  const headers={'Content-Type':'application/vnd.api+json','X-HTTP-Method-Override':'GET','X-Requested-With':'XMLHttpRequest',csrf:H.csrf,csrf_ts:H.csrf_ts};
  const r=await fetch('https://developer.apple.com/services-account/v1/bundleIds/9AZ582Q782',{method:'POST',headers,credentials:'include',body:JSON.stringify({urlEncodedQueryParams:'include=bundleIdCapabilities',teamId:TEAM})});
  const t=await r.text(); let bd; try{bd=JSON.parse(t)}catch{return {s:r.status,raw:t.slice(0,200)}}
  const caps=(bd.included||[]).filter(x=>x.type==='bundleIdCapabilities');
  // App Groups らしき capability（settings に group id を含むもの）を探す
  const detail=caps.map(c=>({id:c.id, rel:c.relationships&&Object.keys(c.relationships), attrs:c.attributes}));
  return {s:r.status, capCount:caps.length, detail};
}, {TEAM,H});
console.log(JSON.stringify(res,null,1).slice(0,2500));
fs.writeFileSync('/tmp/honzukan_caps.json', JSON.stringify(res,null,2));
await b.close().catch(()=>{});
