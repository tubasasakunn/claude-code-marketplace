import { chromium } from 'playwright-core';
const TEAM='7NN5KD3TSU';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
let hdrs=null;
page.on('request', req=>{ const u=req.url(); if(/services-account\/v1\//i.test(u)&&req.method()==='POST'&&!hdrs){const h=req.headers(); if(h.csrf) hdrs={csrf:h.csrf,csrf_ts:h.csrf_ts};} });
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'networkidle',timeout:35000}).catch(()=>{});
await page.waitForTimeout(4000);
if(!hdrs){ console.log('NO_CSRF'); await b.close(); process.exit(0); }
const out = await page.evaluate(async ({TEAM,H})=>{
  async function pget(resource, params){
    const headers={'Content-Type':'application/vnd.api+json','X-HTTP-Method-Override':'GET','X-Requested-With':'XMLHttpRequest',csrf:H.csrf,csrf_ts:H.csrf_ts};
    const r=await fetch('https://developer.apple.com/services-account/v1/'+resource,{method:'POST',headers,credentials:'include',body:JSON.stringify({urlEncodedQueryParams:params||'',teamId:TEAM})});
    const t=await r.text(); try{return {s:r.status,b:JSON.parse(t)}}catch{return {s:r.status,b:t.slice(0,200)}}
  }
  const res={};
  const ag=await pget('appGroups','limit=200');
  res.appGroups = ag.s===200 ? ag.b.data.map(g=>({id:g.id,ident:g.attributes.identifier,name:g.attributes.name})) : ag;
  // bundleIds 全部
  const bi=await pget('bundleIds','limit=1000&filter[platform]=IOS,MACOS');
  res.bundleIds = bi.s===200 ? bi.b.data.filter(x=>/com\.basaapp/.test(x.attributes.identifier)).map(x=>({id:x.id,ident:x.attributes.identifier})) : bi;
  return res;
}, {TEAM, H:hdrs});
console.log('=== App Groups ===');
console.log(JSON.stringify(out.appGroups,null,1).slice(0,600));
console.log('=== com.basaapp bundleIds (portal internal id) ===');
console.log(JSON.stringify(out.bundleIds,null,0).slice(0,900));
// 保存
import('fs').then(fs=>fs.writeFileSync('/tmp/portal_survey.json', JSON.stringify({hdrs, out},null,2)));
await b.close().catch(()=>{});
