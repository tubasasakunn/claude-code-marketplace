import { chromium } from 'playwright-core';
const TEAM='7NN5KD3TSU';
const TARGETS={yamazukan:'FRNH9X78QP', honzukan:'9AZ582Q782', mamezukan:'4J6QLFC8G6'};
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
let H=null;
page.on('request', req=>{ const u=req.url(); if(/services-account\/v1\//i.test(u)&&req.method()==='POST'&&!H){const h=req.headers(); if(h.csrf) H={csrf:h.csrf,csrf_ts:h.csrf_ts};} });
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'networkidle',timeout:35000}).catch(()=>{});
await page.waitForTimeout(3500);
if(!H){ console.log('NO_CSRF'); await b.close(); process.exit(0); }
const res = await page.evaluate(async ({TEAM,H,TARGETS})=>{
  async function pget(resource, params){
    const headers={'Content-Type':'application/vnd.api+json','X-HTTP-Method-Override':'GET','X-Requested-With':'XMLHttpRequest',csrf:H.csrf,csrf_ts:H.csrf_ts};
    const r=await fetch('https://developer.apple.com/services-account/v1/'+resource,{method:'POST',headers,credentials:'include',body:JSON.stringify({urlEncodedQueryParams:params||'',teamId:TEAM})});
    const t=await r.text(); try{return {s:r.status,b:JSON.parse(t)}}catch{return {s:r.status,b:t.slice(0,150)}}
  }
  const out={};
  for(const [nm,id] of Object.entries(TARGETS)){
    // 方法A: include=appGroups
    const a=await pget('bundleIds/'+id,'include=appGroups');
    let mA='n/a';
    if(a.s===200){ const inc=(a.b.included||[]).filter(x=>x.type==='appGroups'); mA=inc.map(x=>x.attributes&&x.attributes.identifier); }
    // 方法B: capabilities のtype全部
    const c=await pget('bundleIds/'+id,'include=bundleIdCapabilities');
    let caps='n/a';
    if(c.s===200){ caps=(c.b.included||[]).filter(x=>x.type==='bundleIdCapabilities').map(x=>x.attributes.capabilityType); }
    out[nm]={includeAppGroups:mA, capTypes:caps, aStatus:a.s};
  }
  return out;
}, {TEAM,H,TARGETS});
for(const [nm,v] of Object.entries(res)) console.log(nm.padEnd(12), JSON.stringify(v));
await b.close().catch(()=>{});
