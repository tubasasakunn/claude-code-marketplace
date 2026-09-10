import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url()));
if(!page){ page = ctx.pages().find(p=>/developer\.apple\.com/.test(p.url())) || await ctx.newPage(); }
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'domcontentloaded',timeout:30000});
await page.waitForTimeout(4000);
console.log('page url:', page.url());
// 認証済みページ文脈で内部APIを叩く（cookie付き・CSRFはページが持つ）
const res = await page.evaluate(async ()=>{
  const out={};
  // CSRF トークンをmetaやwindowから探す
  const csrf = (document.querySelector('meta[name=csrf]')||{}).content || window.csrf || null;
  out.csrfFound = !!csrf;
  async function tryGet(url, extraHeaders){
    try{
      const r = await fetch(url, {headers: Object.assign({'Accept':'application/vnd.api+json, application/json'}, extraHeaders||{}), credentials:'include'});
      const t = await r.text();
      return {status:r.status, body:t.slice(0,600)};
    }catch(e){ return {err:e.message}; }
  }
  out.appGroups_v1 = await tryGet('https://developer.apple.com/services-account/v1/appGroups?limit=50');
  out.appGroups_qh = await tryGet('https://developer.apple.com/services-account/QH65B2/account/ios/identifiers/listApplicationGroups.action');
  return out;
});
console.log(JSON.stringify(res,null,2).slice(0,1800));
await b.close().catch(()=>{});
