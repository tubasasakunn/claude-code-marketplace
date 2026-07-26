import { chromium } from 'playwright-core';
const TEAM='7NN5KD3TSU';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'domcontentloaded',timeout:30000}).catch(()=>{});
await page.waitForTimeout(2500);
const res = await page.evaluate(async (TEAM)=>{
  async function j(url){ try{ const r=await fetch(url,{headers:{'Accept':'application/vnd.api+json'},credentials:'include'}); const t=await r.text(); let b; try{b=JSON.parse(t)}catch{b=t.slice(0,300)} return {status:r.status,b}; }catch(e){return {err:e.message}} }
  const out={};
  // teamId をクエリで
  out.ag = await j('https://developer.apple.com/services-account/v1/appGroups?teamId='+TEAM+'&limit=50');
  return out;
}, TEAM);
// App Group 一覧を整形
const ag=res.ag;
console.log('appGroups status:', ag.status);
if(ag.b && ag.b.data){
  for(const g of ag.b.data){ console.log('  ', g.id, '|', g.attributes && (g.attributes.identifier||g.attributes.name)); }
} else {
  console.log('body:', JSON.stringify(ag.b).slice(0,500));
}
await b.close().catch(()=>{});
