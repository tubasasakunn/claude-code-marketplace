// Hanasu App ID 編集ページの Sign In with Apple 行の状態を偵察する
import { chromium } from 'playwright-core';

const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p => /developer\.apple\.com/.test(p.url())) || await ctx.newPage();
await page.goto('https://developer.apple.com/account/resources/identifiers/bundleId/edit/WV6V37TTDY', { waitUntil: 'domcontentloaded', timeout: 45000 });
await page.waitForTimeout(8000);
console.log('URL:', page.url());

const info = await page.evaluate(() => {
  const res = { rows: [], buttons: [] };
  // capability 行を探す: "Sign In with Apple" テキストを含む行
  const nodes = [...document.querySelectorAll('*')].filter(e =>
    e.children.length === 0 && /sign in with apple/i.test(e.textContent || ''));
  for (const n of nodes.slice(0, 5)) {
    let row = n;
    for (let i = 0; i < 8 && row; i++) {
      const cb = row.querySelector && row.querySelector('input[type=checkbox]');
      if (cb) {
        const btns = [...row.querySelectorAll('button, a')].map(x => (x.innerText || '').trim()).filter(Boolean);
        res.rows.push({ text: (row.innerText || '').replace(/\s+/g, ' ').slice(0, 200), checked: cb.checked, disabled: cb.disabled, btns });
        break;
      }
      row = row.parentElement;
    }
  }
  res.buttons = [...document.querySelectorAll('button')].map(x => (x.innerText || '').trim()).filter(t => t && t.length < 30).slice(0, 30);
  return res;
});
console.log(JSON.stringify(info, null, 2));
await b.close();
