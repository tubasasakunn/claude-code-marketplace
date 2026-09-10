import { chromium } from 'playwright-core';
for(let i=0;i<100;i++){
  try{
    const b=await chromium.connectOverCDP('http://localhost:9222');
    const ctx=b.contexts()[0];
    const pages=ctx.pages();
    // idmsaタブが消え/認証済みになり、developer.apple.com が resources に居るか
    const idmsa=pages.find(p=>/idmsa\.apple\.com.*signin/.test(p.url()));
    const dev=pages.find(p=>/developer\.apple\.com\/account\/resources/.test(p.url()) && !/idmsa|signin/.test(p.url()));
    // idmsaタブ内でまだpassword画面か確認
    let idmsaStillLogin=false;
    if(idmsa){ const fr=idmsa.frames().find(f=>/appleauth\/auth\/signin/.test(f.url())); if(fr){ idmsaStillLogin= await fr.locator('#password_text_field').isVisible().catch(()=>false); } }
    await b.close().catch(()=>{});
    if(dev && !idmsaStillLogin){ console.log('LOGIN_DONE'); process.exit(0); }
    if(i%6===0) console.log('['+i+'] idmsaLoginVisible='+idmsaStillLogin+' devAuthed='+!!dev);
  }catch(e){ if(i%6===0) console.log('['+i+'] err',e.message); }
  await new Promise(r=>setTimeout(r,9000));
}
console.log('TIMEOUT');
