import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
// 既存のdeveloper.apple.comタブを再利用、無ければ新規
let page = ctx.pages().find(p => /developer\.apple\.com/.test(p.url()));
if (!page) page = await ctx.newPage();
await page.bringToFront().catch(()=>{});
await page.goto('https://developer.apple.com/account/resources/identifiers/list', { waitUntil:'domcontentloaded', timeout:30000 }).catch(e=>console.log('nav:',e.message));
await page.waitForTimeout(2500);
console.log('現在URL:', page.url());
console.log('→ この自動化用Chromeウィンドウでサインイン(2FA)してください');
await b.close().catch(()=>{});
