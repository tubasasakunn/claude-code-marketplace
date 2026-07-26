// Hanasu App ID の Sign In with Apple capability を GUI でトグルする
// 使い方: node siwa_toggle.mjs off   → チェックを外して Save+Confirm
//         node siwa_toggle.mjs on    → チェックを入れて Save+Confirm
import { chromium } from 'playwright-core';

const mode = process.argv[2];
if (!['on', 'off'].includes(mode)) { console.log('usage: siwa_toggle.mjs on|off'); process.exit(1); }
const want = mode === 'on';

const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p => /developer\.apple\.com/.test(p.url())) || await ctx.newPage();
await page.goto('https://developer.apple.com/account/resources/identifiers/bundleId/edit/WV6V37TTDY', { waitUntil: 'domcontentloaded', timeout: 45000 });
await page.waitForTimeout(8000);

// SIWA 行のチェックボックスを特定してクリック（他の行には触らない）
const row = page.locator('div,tr,li').filter({ hasText: /^\s*Sign In with Apple/i }).filter({ has: page.locator('input[type=checkbox]') }).last();
const cb = row.locator('input[type=checkbox]').first();
const before = await cb.isChecked();
console.log('before checked =', before, '→ want', want);
if (before !== want) {
  // input が視覚的に隠れているUIがあるので force で label ごと押す
  await cb.click({ force: true, timeout: 10000 });
  await page.waitForTimeout(1500);
  console.log('after click checked =', await cb.isChecked());
} else {
  console.log('already in desired state; no click');
}

// Save
const save = page.locator('button', { hasText: /^Save$/ }).first();
if (await save.isEnabled().catch(() => false)) {
  await save.click();
  await page.waitForTimeout(2500);
  // 確認ダイアログ（Modify App Capabilities）
  const dlgBtns = await page.evaluate(() => [...document.querySelectorAll('button')].map(x => (x.innerText || '').trim()).filter(Boolean));
  console.log('dialog buttons:', JSON.stringify(dlgBtns.slice(0, 15)));
  const confirm = page.locator('button', { hasText: /^(Confirm|Continue)$/ }).first();
  if (await confirm.isVisible().catch(() => false)) {
    await confirm.click();
    console.log('confirmed');
  } else {
    console.log('no confirm dialog visible');
  }
  await page.waitForTimeout(6000);
} else {
  console.log('Save button not enabled');
}
console.log('final URL:', page.url());
await b.close();
