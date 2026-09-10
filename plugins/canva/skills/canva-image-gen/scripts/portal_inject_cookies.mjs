// asc CLI の web セッション Cookie を CDP Chrome に注入し、Developer Portal へログイン状態で入る
import { chromium } from 'playwright-core';
import { readFileSync } from 'fs';
import { globSync } from 'glob';

const files = globSync('/Users/tubasasakun/.asc/web/session-*.json');
if (!files.length) { console.log('NO_SESSION_FILE'); process.exit(1); }
const sess = JSON.parse(readFileSync(files[0], 'utf8'));

const cookies = [];
const seen = new Set();
for (const [origin, jar] of Object.entries(sess.cookies)) {
  const host = new URL(origin).hostname;
  for (const c of jar) {
    // myacinfo 等の共通クッキーは .apple.com、idmsa 固有(aasp/DES*)はそのホストへ
    const shared = ['myacinfo', 'dslang', 'site', 'itctx', 'itcdq'].includes(c.name);
    const domain = shared ? '.apple.com' : host;
    const key = c.name + '|' + domain;
    if (seen.has(key)) continue;
    seen.add(key);
    cookies.push({ name: c.name, value: c.value, domain, path: '/', secure: true });
  }
}
console.log('injecting', cookies.length, 'cookies:', cookies.map(c => c.name + '@' + c.domain).join(', '));

const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
await ctx.addCookies(cookies);
let page = ctx.pages().find(p => /apple\.com/.test(p.url())) || await ctx.newPage();
await page.goto('https://developer.apple.com/account/resources/identifiers/list', { waitUntil: 'domcontentloaded', timeout: 45000 });
await page.waitForTimeout(8000);
console.log('URL:', page.url());
console.log('TITLE:', await page.title());
console.log(/idmsa|signin/i.test(page.url()) ? 'LOGIN: FAILED' : 'LOGIN: OK');
await b.close();
