#!/usr/bin/env node
/**
 * 書き出した PNG を、App Store で見えるとおりの形にした HTML にする。
 *
 *   node tools/preview.mjs <out ディレクトリ> [...] -o preview.html
 *   node tools/preview.mjs portrait/out --label "手軽さ" -o preview.html
 *
 * 出力はそのまま Artifact として公開できる 1 枚の HTML。画像は data URI で
 * 埋め込むので外部参照は無い。
 *
 * 出すのは 2 つの見え方:
 *   検索結果       … 最初の 3 枚が並ぶ。大半のユーザーはここで続けるか決める
 *   プロダクトページ … 横スクロールのカルーセル。実際に指で送れる
 *
 * **確認は必ずこの形でやる。** 4 枚を平らに並べただけでは、縮小で読めなくなる
 * 見出しや、詳細ページで崩れるまたぎに気づけない。
 *
 * 複数セットを渡すと並べて比べられる（案の比較用）。
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const USAGE = `usage: node tools/preview.mjs <out ディレクトリ> [オプション] [...] [-o preview.html]

  --label <名前>   セットの見出し（既定: 親ディレクトリ名）
  --app   <名前>   アプリ名
  --sub   <文言>   サブタイトル
  --icon  <パス>   アプリアイコン
  -o      <パス>   出力先（既定: preview.html）

セットは複数渡せる。オプションは直前のセットに効く。

  node tools/preview.mjs a/out --label 案A b/out --label 案B -o compare.html`;

const args = process.argv.slice(2);
if (!args.length || args.includes('-h') || args.includes('--help')) {
  console.log(USAGE);
  process.exit(args.length ? 0 : 1);
}

const outIdx = args.findIndex((a) => a === '-o' || a === '--out');
const outFile = outIdx > -1 ? args[outIdx + 1] : 'preview.html';

const sets = [];
const opt = (key, val) => {
  if (!sets.length) { console.error(`${key} はディレクトリの後に置く\n\n${USAGE}`); process.exit(1); }
  sets[sets.length - 1][key] = val;
};
for (let i = 0; i < args.length; i++) {
  if (args[i] === '-o' || args[i] === '--out') { i++; continue; }
  if (args[i] === '--label') { opt('label', args[++i]); continue; }
  if (args[i] === '--app') { opt('app', args[++i]); continue; }
  if (args[i] === '--sub') { opt('sub', args[++i]); continue; }
  if (args[i] === '--icon') { opt('icon', args[++i]); continue; }
  if (args[i].startsWith('-')) { console.error(`知らないオプション: ${args[i]}\n\n${USAGE}`); process.exit(1); }
  const dir = args[i];
  if (!fs.existsSync(dir)) { console.error(`ディレクトリが無い: ${dir}`); process.exit(1); }
  sets.push({ dir, label: path.basename(path.dirname(path.resolve(dir))) });
}

if (!sets.length) { console.error(USAGE); process.exit(1); }

/** 表示用に縮小して data URI にする。原寸のままだと HTML が数十 MB になる。 */
function shrink(file, width) {
  const tmp = path.join(process.env.TMPDIR || '/tmp', `pv-${process.pid}-${path.basename(file)}.jpg`);
  execFileSync('sips', ['--resampleWidth', String(width), file,
    '--setProperty', 'format', 'jpeg', '--setProperty', 'formatOptions', '78',
    '--out', tmp], { stdio: 'ignore' });
  const b64 = fs.readFileSync(tmp).toString('base64');
  fs.unlinkSync(tmp);
  return `data:image/jpeg;base64,${b64}`;
}

function pngB64(file, width) {
  const tmp = path.join(process.env.TMPDIR || '/tmp', `pv-${process.pid}-icon.png`);
  execFileSync('sips', ['--resampleWidth', String(width), file, '--out', tmp], { stdio: 'ignore' });
  const b64 = fs.readFileSync(tmp).toString('base64');
  fs.unlinkSync(tmp);
  return `data:image/png;base64,${b64}`;
}

for (const set of sets) {
  const dir = path.resolve(set.dir);
  const files = fs.readdirSync(dir).filter((f) => /\.png$/i.test(f)).sort();
  if (!files.length) { console.error(`PNG が無い: ${dir}`); process.exit(1); }

  // 1 枚目の縦横比で向きを判定する。横向きは検索結果に 1 枚しか出ない。
  const probe = execFileSync('sips', ['-g', 'pixelWidth', '-g', 'pixelHeight', path.join(dir, files[0])])
    .toString();
  const w = Number(probe.match(/pixelWidth:\s*(\d+)/)[1]);
  const h = Number(probe.match(/pixelHeight:\s*(\d+)/)[1]);
  set.landscape = w > h;
  set.size = `${w}×${h}`;
  set.shots = files.map((f) => shrink(path.join(dir, f), set.landscape ? 720 : 520));
  set.icon = set.icon ? pngB64(set.icon, 160) : null;
  console.log(`${set.label}  ${files.length} 枚  ${set.size}${set.landscape ? '（横向き）' : ''}`);
}

const IOS_FONT = `-apple-system, "SF Pro Text", BlinkMacSystemFont, "Hiragino Sans", sans-serif`;

const statusbar = `
  <div class="statusbar"><span>9:41</span>
    <svg width="72" height="12" viewBox="0 0 72 12" fill="#000" aria-hidden="true">
      <rect x="0" y="7" width="3" height="5" rx="1"/><rect x="5" y="5" width="3" height="7" rx="1"/>
      <rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="1" width="3" height="11" rx="1"/>
      <path d="M28 4.2a8 8 0 0 1 10 0l-1.2 1.5a6.1 6.1 0 0 0-7.6 0zm2.4 2.9a4.3 4.3 0 0 1 5.2 0L33 10.6z"/>
      <rect x="50" y="1.5" width="18" height="9" rx="2.6" fill="none" stroke="#000" stroke-opacity=".38"/>
      <rect x="51.6" y="3.1" width="13" height="5.8" rx="1.5"/>
      <path d="M69.4 4.6v3.4a1.9 1.9 0 0 0 0-3.4z" fill-opacity=".38"/>
    </svg>
  </div>`;

const icon = (src, cls) => src
  ? `<img class="app-icon ${cls}" src="${src}" alt="">`
  : `<span class="app-icon ${cls}"></span>`;

const section = (s) => `
  <section class="set">
    <div class="set-head">
      <h2>${s.label}</h2>
      <span class="meta">${s.shots.length} 枚 ・ ${s.size}${s.landscape ? ' ・ 横向き' : ''}</span>
    </div>

    <div class="stalls">
      <div class="stall">
        <h3>検索結果</h3>
        <p>一覧に並んだ状態。大半の人はここで続けるか離れるかを決める。</p>
        <div class="phone"><div class="screen">
          <div class="island"></div>
          ${statusbar}
          <div class="searchbar"><div class="searchfield">${s.app || s.label}</div></div>
          <article class="result">
            <div class="result-head">
              ${icon(s.icon, 'sm')}
              <div class="result-meta">
                <h4>${s.app || 'App'}</h4>
                <p class="sub">${s.sub || ''}</p>
              </div>
              <span class="get">入手</span>
            </div>
            <div class="triptych ${s.landscape ? 'land' : ''}">
              ${s.shots.slice(0, s.landscape ? 1 : 3).map((x) => `<img src="${x}" alt="">`).join('')}
            </div>
          </article>
          <div class="divider"></div>
          <article class="result peek" aria-hidden="true">
            <div class="result-head">
              <span class="app-icon sm"></span>
              <div class="result-meta"><div class="bar"></div><div class="bar sub2"></div></div>
              <span class="get ghost">入手</span>
            </div>
            <div class="triptych ${s.landscape ? 'land' : ''}">
              ${Array(s.landscape ? 1 : 3).fill('<span class="skel"></span>').join('')}
            </div>
          </article>
          <div class="home"></div>
        </div></div>
        <p class="note">${s.landscape
          ? '<b>横向きなので 1 枚しか出ない。</b>縦なら 3 枚並ぶ。'
          : '出るのは<b>最初の 3 枚だけ</b>。4 枚目以降は一覧に現れない。'}</p>
      </div>

      <div class="stall">
        <h3>プロダクトページ</h3>
        <p>タップして開いた先。スクリーンショットは横スクロールになる。</p>
        <div class="phone"><div class="screen">
          <div class="island"></div>
          ${statusbar}
          <div class="product-head">
            ${icon(s.icon, 'lg')}
            <div class="product-title">
              <h4>${s.app || 'App'}</h4>
              <p class="sub">${s.sub || ''}</p>
              <div class="cta"><span class="get">入手</span></div>
            </div>
          </div>
          <p class="preview-label">プレビュー</p>
          <div class="carousel ${s.landscape ? 'land' : ''}" tabindex="0" aria-label="スクリーンショット">
            ${s.shots.map((x) => `<img src="${x}" alt="">`).join('')}
          </div>
          <div class="home"></div>
        </div></div>
        <p class="note">枚の間に<b>余白が入り</b>、送れば組み合わせも変わる。
          <b>各枚が単体でも成立</b>している必要がある。</p>
      </div>
    </div>
  </section>`;

const html = `<title>ストア画像プレビュー</title>
<style>
  :root {
    --paper:#F7F4F0; --raised:#FFF; --ink:#2A2520; --muted:#877A70;
    --accent:#C25A33; --rule:#E4DCD3; --shadow:24px 60px rgba(58,30,16,.13);
  }
  @media (prefers-color-scheme: dark) {
    :root { --paper:#16120F; --raised:#1F1A16; --ink:#F1EAE3; --muted:#9C8D81;
            --accent:#E68A5E; --rule:#322A24; --shadow:24px 60px rgba(0,0,0,.5); }
  }
  :root[data-theme="light"] { --paper:#F7F4F0; --raised:#FFF; --ink:#2A2520; --muted:#877A70;
    --accent:#C25A33; --rule:#E4DCD3; --shadow:24px 60px rgba(58,30,16,.13); }
  :root[data-theme="dark"] { --paper:#16120F; --raised:#1F1A16; --ink:#F1EAE3; --muted:#9C8D81;
    --accent:#E68A5E; --rule:#322A24; --shadow:24px 60px rgba(0,0,0,.5); }

  * { box-sizing:border-box; }
  body {
    margin:0; padding:clamp(30px,5vw,64px) clamp(18px,4vw,44px) 90px;
    background:var(--paper); color:var(--ink); line-height:1.75;
    font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",system-ui,sans-serif;
    font-feature-settings:"palt" 1; -webkit-font-smoothing:antialiased;
  }
  .wrap { max-width:980px; margin:0 auto; display:flex; flex-direction:column; gap:64px; }
  header { display:flex; flex-direction:column; gap:12px; }
  .eyebrow { margin:0; font-size:12px; font-weight:700; letter-spacing:.16em; color:var(--accent); }
  h1 { margin:0; font-size:clamp(26px,4vw,38px); font-weight:800; letter-spacing:-.035em; line-height:1.3; }
  .lede { margin:0; max-width:62ch; color:var(--muted); font-size:15px; }

  .set { display:flex; flex-direction:column; gap:20px; }
  .set-head { display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;
              padding-bottom:12px; border-bottom:1px solid var(--rule); }
  .set-head h2 { margin:0; font-size:21px; font-weight:800; letter-spacing:-.03em; }
  .set-head .meta { font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:12px; color:var(--muted); }

  .stalls { display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:44px 36px; justify-items:center; }
  .stall { display:flex; flex-direction:column; gap:12px; max-width:412px; }
  .stall h3 { margin:0; font-size:17px; font-weight:700; letter-spacing:-.02em; }
  .stall > p { margin:0; font-size:13.5px; color:var(--muted); min-height:44px; }

  .note { margin:0; padding:12px 15px; border-left:2px solid var(--accent); background:var(--raised);
          border-radius:0 8px 8px 0; font-size:12.5px; line-height:1.7; color:var(--muted); min-height:auto !important; }
  .note b { color:var(--ink); font-weight:600; }

  .phone { width:390px; max-width:100%; padding:11px; border-radius:56px;
           background:linear-gradient(150deg,#55525a,#232227 42%,#3d3b42);
           box-shadow:0 var(--shadow),0 2px 6px rgba(0,0,0,.3); }
  /* 実機の画面は中身の量に関係なく同じ高さ。並べる以上ここを揃えないと嘘になる。 */
  .screen { position:relative; min-height:844px; display:flex; flex-direction:column;
            border-radius:46px; overflow:hidden; background:#fff; color:#000;
            font-family:${IOS_FONT}; line-height:1.4; }
  .screen > * { flex:none; }
  .island { position:absolute; top:11px; left:50%; width:118px; height:34px; margin-left:-59px;
            border-radius:20px; background:#000; z-index:3; }
  .statusbar { display:flex; align-items:center; justify-content:space-between; padding:17px 30px 6px;
               font-size:15px; font-weight:600; letter-spacing:-.02em; font-variant-numeric:tabular-nums; }
  .home { width:140px; height:5px; margin:auto auto 9px; border-radius:3px; background:#000; opacity:.85; }

  .app-icon { border-radius:22.5%; display:block; background:#e9e6e2; flex:none; }
  .app-icon.sm { width:62px; height:62px; }
  .app-icon.lg { width:108px; height:108px; }
  .get { padding:5px 20px; border-radius:999px; background:#f2f2f7; color:#007aff;
         font-size:15px; font-weight:700; }
  .get.ghost { color:#c7c7cc; }
  .sub { color:#8a8a8e; font-size:13px; margin:1px 0 0; }

  .searchbar { padding:6px 16px 12px; }
  .searchfield { padding:8px 12px; border-radius:11px; background:#e9e9ec; color:#3c3c43; font-size:16px; }
  .result { padding:14px 16px 18px; }
  .result-head { display:flex; align-items:center; gap:12px; }
  .result-meta { flex:1; min-width:0; }
  .result-meta h4 { margin:0; font-size:16px; font-weight:600; letter-spacing:-.02em;
                    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .triptych { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:14px; }
  .triptych.land { grid-template-columns:1fr; }
  .triptych img { width:100%; display:block; border-radius:9px; border:.5px solid rgba(0,0,0,.09); }
  .skel { display:block; aspect-ratio:1320/2868; border-radius:9px; background:#f0edea; }
  .triptych.land .skel { aspect-ratio:2868/1320; }
  .divider { height:.5px; background:#d8d8dc; margin-left:90px; }
  .peek { opacity:.45; }
  .bar { height:15px; border-radius:4px; background:#e6e2de; width:46%; }
  .bar.sub2 { height:12px; margin-top:6px; background:#efece9; width:70%; }

  .product-head { display:flex; gap:15px; padding:14px 20px 0; }
  .product-title { display:flex; flex-direction:column; gap:4px; padding-top:2px; min-width:0; }
  .product-title h4 { margin:0; font-size:21px; font-weight:600; letter-spacing:-.03em; line-height:1.25; }
  .cta { margin-top:auto; }
  .preview-label { margin:24px 20px 10px; font-size:21px; font-weight:700; letter-spacing:-.03em; }
  .carousel { display:flex; gap:10px; padding:0 20px 22px; overflow-x:auto;
              scroll-snap-type:x mandatory; scrollbar-width:none; }
  .carousel::-webkit-scrollbar { display:none; }
  .carousel img { width:232px; flex:none; display:block; border-radius:13px;
                  border:.5px solid rgba(0,0,0,.09); scroll-snap-align:start; }
  .carousel.land img { width:330px; }

  @media (prefers-reduced-motion: reduce) { * { scroll-behavior:auto !important; } }
</style>
<div class="wrap">
  <header>
    <p class="eyebrow">ストア画像プレビュー</p>
    <h1>App Store でどう見えるか</h1>
    <p class="lede">書き出した PNG を、実際の 2 つの見え方に流し込んだもの。
      Apple のページではなく手元のプレビューで、入手ボタンは押しても何も起きない。
      右のカルーセルは横に送れる。</p>
  </header>
  ${sets.map(section).join('\n')}
</div>
`;

fs.writeFileSync(outFile, html);
console.log(`\n${outFile}  ${(html.length / 1024 / 1024).toFixed(2)} MB`);
