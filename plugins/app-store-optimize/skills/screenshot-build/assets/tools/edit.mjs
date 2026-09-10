#!/usr/bin/env node
/**
 * レイアウトエディタをブラウザで開く。
 *
 *   node tools/edit.mjs template/bold-breakout
 *
 * 画面で位置を合わせて「保存」を押すと、そのテンプレートの layout.js に書き出す。
 * build（compose.js）が content.js の値にこれを被せるので、次に書き出す PNG へ
 * そのまま効く。
 *
 * file:// で直接開いても編集はできるが、保存だけはできない（ブラウザからファイルを
 * 書けないため）。その場合は「コピー」で JSON を取り出す。
 */
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { spawn } from 'node:child_process';

const tpl = process.argv[2];
if (!tpl || tpl.startsWith('--')) {
  console.error('usage: node tools/edit.mjs <テンプレートディレクトリ> [--root <配信の基点>]');
  process.exit(1);
}

/**
 * 配信の基点。
 *
 * content.js の画像は作業ディレクトリの外（`../../../apps/<slug>/material/...` など）を
 * 指していることが多い。file:// なら実ファイルを辿れるが、HTTP ではルートより上に出られず
 * 画像が全滅する。localhost 限定なので、素材が入る範囲まで基点を上げておく。
 * 足りなければ `--root <パス>` で指定する。
 */
const rootArg = process.argv.indexOf('--root');
const up = path.resolve(process.cwd(), '../../..');
const SERVE_ROOT = rootArg > -1
  ? path.resolve(process.argv[rootArg + 1])
  : (fs.existsSync(up) ? up : process.cwd());
const tplDir = path.resolve(tpl);
const layoutFile = path.join(tplDir, 'layout.js');
if (!fs.existsSync(path.join(tplDir, 'index.html'))) {
  console.error(`index.html が無い: ${tplDir}`);
  process.exit(1);
}

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');

  if (req.method === 'POST' && url.pathname.endsWith('/__save')) {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        fs.writeFileSync(layoutFile,
          '// エディタ（tools/edit.mjs）が書き出す位置の上書き。手で編集してもよい。\n'
          + '// content.js の値に被さる。固まったら content.js へ写してこのファイルを消す。\n'
          + `window.LAYOUT = ${JSON.stringify(data, null, 2)};\n`, 'utf8');
        console.log(`保存 → ${path.relative(SERVE_ROOT, layoutFile)}  (${Object.keys(data).length} 件)`);
        for (const [k, v] of Object.entries(data)) console.log(`  ${k}  ${JSON.stringify(v)}`);
        res.writeHead(200).end('ok');
      } catch (e) {
        res.writeHead(400).end(String(e));
      }
    });
    return;
  }

  let rel = decodeURIComponent(url.pathname).replace(/^\/+/, '');
  if (rel === '') rel = path.relative(SERVE_ROOT, path.join(tplDir, 'index.html'));
  const file = path.resolve(SERVE_ROOT, rel);
  if (!file.startsWith(SERVE_ROOT + path.sep)) { res.writeHead(403).end(); return; }
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404).end(); return; }

  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

server.listen(0, () => {
  const { port } = server.address();
  const rel = path.relative(SERVE_ROOT, path.join(tplDir, 'index.html'));
  const url = `http://localhost:${port}/${rel}?edit=1`;
  console.log(`エディタ: ${url}`);
  console.log('位置を合わせて「保存」。閉じるときは Ctrl-C。\n');
  spawn('open', [url], { stdio: 'ignore', detached: true }).unref();
});
