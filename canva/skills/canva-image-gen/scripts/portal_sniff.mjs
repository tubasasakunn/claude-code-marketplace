import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
const seen=[];
page.on('request', req=>{
  const u=req.url();
  if(/services-account|account\/.*\.action|appGroups|bundleIds/i.test(u)){
    const h=req.headers();
    seen.push({m:req.method(), u:u.slice(0,120), team:h['x-team-id']||h['teamid']||h['x-http-method-override']||null, ct:h['content-type']||null, csrf:h['csrf']?'y':(h['x-csrf-token']?'y':'n')});
  }
});
// 一覧を再ロードしてXHRを誘発
await page.goto('https://developer.apple.com/account/resources/identifiers/list',{waitUntil:'networkidle',timeout:35000}).catch(e=>console.log('nav',e.message));
await page.waitForTimeout(5000);
console.log('captured services-account requests:');
for(const s of seen.slice(0,15)) console.log(' ', JSON.stringify(s));
// ついでにページが持つ全リクエストヘッダの一例（identifiers系）を1件フル表示
await b.close().catch(()=>{});
