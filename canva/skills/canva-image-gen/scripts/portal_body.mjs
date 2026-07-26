import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
let hdrs=null, body=null;
page.on('request', req=>{
  const u=req.url();
  if(/services-account\/v1\/bundleIds(\?|$)/i.test(u) && req.method()==='POST' && !body){
    hdrs=req.headers(); body=req.postData();
  }
});
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'networkidle',timeout:35000}).catch(()=>{});
await page.waitForTimeout(5000);
console.log('bundleIds POST body:', (body||'(none)').slice(0,400));
console.log('has csrf hdr:', !!(hdrs&&hdrs.csrf));
// 同じヘッダ・同じbodyの team指定でappGroupsを叩く
if(hdrs){
  const res = await page.evaluate(async ({h,bd})=>{
    const headers={'Content-Type':'application/vnd.api+json','X-HTTP-Method-Override':'GET','X-Requested-With':'XMLHttpRequest'};
    for(const k of Object.keys(h)){ if(/^csrf/i.test(k)) headers[k]=h[k]; }
    // bundleIds body から urlEncodedQueryParams / teamId 部分を流用
    let reqBody=bd;
    try{ const o=JSON.parse(bd); // teamId等を残しつつ対象をappGroupsに
      // urlEncodedQueryParams があればそれを使う
      reqBody=JSON.stringify(o);
    }catch{}
    const r=await fetch('https://developer.apple.com/services-account/v1/appGroups?limit=100',{method:'POST',headers,credentials:'include',body:reqBody});
    const t=await r.text(); let x; try{x=JSON.parse(t)}catch{x=t.slice(0,200)}
    return {status:r.status, count:(x.data?x.data.length:null), groups:(x.data?x.data.map(g=>({id:g.id,ident:g.attributes&&g.attributes.identifier})):(x.errors?x.errors[0].detail:x))};
  }, {h:hdrs, bd:body});
  console.log('appGroups retry:', JSON.stringify(res,null,2).slice(0,700));
}
await b.close().catch(()=>{});
