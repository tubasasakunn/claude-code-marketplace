import { chromium } from 'playwright-core';
const TEAM='7NN5KD3TSU';
const FAM={honzukan:'9AZ582Q782',mamezukan:'4J6QLFC8G6',yamazukan:'FRNH9X78QP',sakezukan:'5Z6N5CT278',sushizukan:'2X647T52W7',eigazukan:'D795U57L3Z',seizazukan:'K37M93393X',michinoekizukan:'K37MFBXS5Y'};
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
let H=null;
page.on('request', req=>{ const u=req.url(); if(/services-account\/v1\//i.test(u)&&req.method()==='POST'&&!H){const h=req.headers(); if(h.csrf) H={csrf:h.csrf,csrf_ts:h.csrf_ts};} });
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'networkidle',timeout:35000}).catch(()=>{});
await page.waitForTimeout(3500);
if(!H){ console.log('NO_CSRF'); await b.close(); process.exit(0); }
const res = await page.evaluate(async ({TEAM,H,FAM})=>{
  async function pget(res,params){ const headers={'Content-Type':'application/vnd.api+json','X-HTTP-Method-Override':'GET','X-Requested-With':'XMLHttpRequest',csrf:H.csrf,csrf_ts:H.csrf_ts}; const r=await fetch('https://developer.apple.com/services-account/v1/'+res,{method:'POST',headers,credentials:'include',body:JSON.stringify({urlEncodedQueryParams:params||'',teamId:TEAM})}); const t=await r.text(); try{return {s:r.status,b:JSON.parse(t)}}catch{return{s:r.status}} }
  const out={};
  for(const [nm,id] of Object.entries(FAM)){
    const r=await pget('bundleIds/'+id,'include=bundleIdCapabilities');
    if(r.s!==200){ out[nm]={err:r.s}; continue; }
    const caps=(r.b.included||[]).filter(x=>x.type==='bundleIdCapabilities');
    const ag=caps.find(c=>/_APP_GROUPS$/.test(c.id));
    out[nm]={hasAGcap:!!ag, enabled: ag?ag.attributes.enabled:false};
  }
  return out;
}, {TEAM,H,FAM});
for(const [nm,v] of Object.entries(res)) console.log(nm.padEnd(16), JSON.stringify(v));
await b.close().catch(()=>{});
