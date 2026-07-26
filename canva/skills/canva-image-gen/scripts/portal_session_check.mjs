import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://localhost:9222');
const ctx = browser.contexts()[0];
const page = await ctx.newPage();
await page.goto('https://developer.apple.com/account/resources/identifiers/list', { waitUntil: 'domcontentloaded', timeout: 45000 });
await page.waitForTimeout(6000);
const url = page.url();
console.log('URL:', url);
console.log('TITLE:', await page.title());
console.log(/idmsa|signin|\/auth/i.test(url) ? 'SESSION: EXPIRED' : 'SESSION: ALIVE');
await page.close();
await browser.close();
