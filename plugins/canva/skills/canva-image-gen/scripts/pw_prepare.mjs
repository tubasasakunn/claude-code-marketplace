import { chromium } from 'playwright-core';
const EMAIL='bassa.application@gmail.com';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/idmsa\.apple\.com/.test(p.url()));
if(!page){ console.log('idmsaタブ無し（既にログイン済みの可能性）'); await b.close(); process.exit(0);}
await page.bringToFront().catch(()=>{});
const frame = page.frames().find(f=>/appleauth\/auth\/signin/.test(f.url()));
if(!frame){ console.log('auth frame無し url=',page.url()); await b.close(); process.exit(0);}
// account が空なら再入力
const acc = frame.locator('#account_name_text_field');
const cur = await acc.inputValue().catch(()=>'');
if(!cur){ await acc.fill(EMAIL).catch(async()=>{ await acc.click({force:true}).catch(()=>{}); await acc.type(EMAIL,{delay:40}); }); console.log('email 再入力:', await acc.inputValue().catch(()=>'?')); }
else console.log('email 既存:', cur);
// password 欄を JS で直接フォーカス（オーバーレイ回避）
const r = await frame.evaluate(()=>{
  const pw=document.querySelector('#password_text_field');
  if(!pw) return 'no-pw';
  pw.removeAttribute('tabindex');
  pw.focus();
  return document.activeElement===pw ? 'FOCUSED' : ('active='+(document.activeElement&&document.activeElement.id));
});
console.log('password focus:', r);
console.log('→ スマホ側でパスワードを入力→続ける→2FA を進めてください');
await b.close().catch(()=>{});
