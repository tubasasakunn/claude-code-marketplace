import { chromium } from 'playwright-core';
// CDP Chrome の apple.com タブを見て、idmsa/signin を抜けて developer.apple.com の
// 認証済みページ（identifiers 等）に到達したら LOGGED_IN を出す。最大 ~15分。
for (let i=0;i<90;i++){
  try {
    const b = await chromium.connectOverCDP('http://localhost:9222');
    const ctx = b.contexts()[0];
    const pages = ctx.pages();
    let signedIn=false, urls=[];
    for (const p of pages){
      const u = p.url(); urls.push(u);
      if (/developer\.apple\.com\/account\/resources/.test(u) && !/idmsa|signin|auth/.test(u)) signedIn=true;
    }
    await b.close().catch(()=>{});
    if (signedIn){ console.log('LOGGED_IN', JSON.stringify(urls)); process.exit(0); }
    if (i%6===0) console.log('['+i+'] waiting... urls=', JSON.stringify(urls.filter(u=>/apple/.test(u))));
  } catch(e){ if(i%6===0) console.log('['+i+'] probe err', e.message); }
  await new Promise(r=>setTimeout(r,10000));
}
console.log('TIMEOUT_NOT_LOGGED_IN');
