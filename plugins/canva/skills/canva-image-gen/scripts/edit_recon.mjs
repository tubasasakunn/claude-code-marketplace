import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9222');
const ctx = b.contexts()[0];
let page = ctx.pages().find(p=>/developer\.apple\.com\/account/.test(p.url()) && !/idmsa|signin/.test(p.url())) || await ctx.newPage();
const editUrl='https://developer.apple.com/account/resources/identifiers/bundleId/edit/9AZ582Q782';
await page.goto(editUrl,{waitUntil:'networkidle',timeout:35000}).catch(e=>console.log('nav',e.message));
await page.waitForTimeout(5000);
console.log('url:', page.url());
console.log('title:', await page.title().catch(()=>'?'));
// App Groups 行を探す
const info = await page.evaluate(()=>{
  const res={appGroupsRow:null, editButtons:[], checkboxNear:null};
  const all=[...document.querySelectorAll('*')];
  for(const el of all){
    const t=(el.textContent||'').trim();
    if(t==='App Groups' && el.children.length===0){
      let box=el; for(let k=0;k<6 && box;k++){ box=box.parentElement; if(box && box.querySelector('input,button')) break; }
      if(box){
        const cb=box.querySelector('input[type=checkbox]');
        const btns=[...box.querySelectorAll('button')].map(b=>({t:(b.innerText||'').trim(),dis:b.disabled}));
        res.appGroupsRow={checked: cb?cb.checked:'no-cb', buttons:btns};
      }
      break;
    }
  }
  res.allEditBtns=[...document.querySelectorAll('button')].map(b=>(b.innerText||'').trim()).filter(t=>/edit|configure|設定|編集|save|続ける|assign/i.test(t)).slice(0,12);
  return res;
});
console.log('AppGroups recon:', JSON.stringify(info,null,2).slice(0,1000));
await b.close().catch(()=>{});
