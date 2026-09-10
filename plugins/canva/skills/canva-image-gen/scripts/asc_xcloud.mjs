import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/appstoreconnect\.apple\.com/.test(p.url())) || await ctx.newPage();
// seiza アプリの Xcode Cloud ページ
await page.goto('https://appstoreconnect.apple.com/apps/6790113283/ci',{waitUntil:'networkidle',timeout:35000}).catch(e=>console.log('nav',e.message));
await page.waitForTimeout(5000);
console.log('url:', page.url());
console.log('title:', await page.title().catch(()=>'?'));
// ページ内の主要ボタン・見出しを拾う
const info = await page.evaluate(()=>{
  const btns=[...document.querySelectorAll('button,a')].map(b=>(b.innerText||'').trim()).filter(t=>t && t.length<40 && /start|get|workflow|cloud|connect|xcode|作成|接続|始め|設定/i.test(t));
  const heads=[...document.querySelectorAll('h1,h2,h3')].map(h=>(h.innerText||'').trim()).filter(Boolean).slice(0,6);
  return {buttons:[...new Set(btns)].slice(0,12), heads, bodyStart:(document.body.innerText||'').replace(/\s+/g,' ').slice(0,300)};
});
console.log('=== headings ==='); console.log(JSON.stringify(info.heads));
console.log('=== buttons ==='); console.log(JSON.stringify(info.buttons));
console.log('=== body ==='); console.log(info.bodyStart);
await b.close().catch(()=>{});
