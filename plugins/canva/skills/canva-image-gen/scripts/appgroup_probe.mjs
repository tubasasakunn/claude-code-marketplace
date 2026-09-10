import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
const page = await ctx.newPage();
try {
  await page.goto('https://developer.apple.com/account/resources/identifiers/list', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(5000);
  const url = page.url();
  console.log('URL:', url);
  const loggedIn = !/signin|auth|idmsa\.apple/.test(url);
  console.log('loggedIn:', loggedIn);
  if (!loggedIn) { console.log('NOT_LOGGED_IN'); process.exit(0); }
  const rows = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('a,tr,td,span').forEach(el => {
      const t = (el.innerText||'').trim();
      if (/honzukan|com\.basaapp/i.test(t)) out.push(t.replace(/\s+/g,' ').slice(0,90));
    });
    return [...new Set(out)].slice(0,20);
  });
  console.log('matches:', JSON.stringify(rows, null, 2));
} catch(e) { console.log('ERR:', e.message); }
finally { await page.close().catch(()=>{}); await b.close().catch(()=>{}); }
