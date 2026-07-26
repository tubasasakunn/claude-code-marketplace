import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
const pages = ctx.pages();
console.log('現在のタブ:');
for(const p of pages) console.log('  -', p.url().slice(0,90));
// idmsa/appleauth のページを探す
let page = pages.find(p=>/idmsa\.apple\.com/.test(p.url()));
if(!page){ 
  // 認証済みか？ developer.apple.com が見えるなら既にログイン済み
  const dev = pages.find(p=>/developer\.apple\.com\/account\/resources/.test(p.url()));
  console.log('idmsaタブ無し。developer.apple.com authed tab:', dev? dev.url():'なし');
  console.log('STATE: likely_logged_in');
  await b.close(); process.exit(0);
}
await page.bringToFront().catch(()=>{});
const frame = page.frames().find(f=>/appleauth\/auth\/signin/.test(f.url()));
if(!frame){ console.log('auth frame無し（画面遷移中?） url=',page.url()); await b.close(); process.exit(0);}
const pw = frame.locator('#password_text_field');
const vis = await pw.isVisible().catch(()=>false);
const accVal = await frame.locator('#account_name_text_field').inputValue().catch(()=>'?');
console.log('account欄value:', accVal, '| password欄visible:', vis);
if(vis){
  await pw.click({timeout:6000}).catch(e=>console.log('click err',e.message));
  await pw.focus().catch(()=>{});
  console.log('→ password欄をフォーカス/選択しました。スマホで入力できます');
} else {
  console.log('password欄が見えない（別ステップ表示中の可能性）');
}
await b.close().catch(()=>{});
