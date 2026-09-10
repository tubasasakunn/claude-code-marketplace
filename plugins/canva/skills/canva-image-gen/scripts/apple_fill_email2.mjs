import { chromium } from 'playwright-core';
const EMAIL='bassa.application@gmail.com';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/idmsa\.apple\.com/.test(p.url()));
if(!page){ console.log('NO_APPLE_PAGE'); await b.close(); process.exit(0);}
await page.bringToFront().catch(()=>{});
const frame = page.frames().find(f=>/appleauth\/auth\/signin/.test(f.url()));
if(!frame){ console.log('NO_AUTH_FRAME'); await b.close(); process.exit(0);}
try{
  const acc = frame.locator('#account_name_text_field');
  await acc.click({timeout:8000});
  await acc.fill('');
  await acc.type(EMAIL, {delay:40});
  await page.waitForTimeout(600);
  const val = await acc.inputValue().catch(()=>'?');
  console.log('email入力後 value:', val);
  // 続けるボタン or Enter でパスワード段へ
  const btns = await frame.evaluate(()=>[...document.querySelectorAll('button')].map(b=>({t:(b.innerText||'').trim().slice(0,20),id:b.id,vis:!!b.offsetParent})).filter(x=>x.vis));
  console.log('buttons:', JSON.stringify(btns));
  // Apple は email 入力→continueで password 表示。password欄が既に見えているか確認
  const pwVisible = await frame.locator('#password_text_field').isVisible().catch(()=>false);
  console.log('password欄 visible(現時点):', pwVisible);
  if(!pwVisible){
    // continueを押す（id: sign-in ではなく矢印。Enterで代替）
    await acc.press('Enter');
    await page.waitForTimeout(2500);
    const pw2 = await frame.locator('#password_text_field').isVisible().catch(()=>false);
    console.log('Enter後 password欄 visible:', pw2);
  }
}catch(e){ console.log('ERR:', e.message); }
await b.close().catch(()=>{});
