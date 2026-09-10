#!/usr/bin/env node
/**
 * テンプレートの index.html を開き、`.shot` 要素を 1 枚ずつ PNG に書き出す。
 *
 *   node template/_lib/render.mjs template/bold-breakout
 *   node template/_lib/render.mjs template/bold-breakout --only 2,3
 *
 * ページ全体ではなく要素単位で撮るので、ビューポートの大きさに関係なく
 * `.shot` の CSS 実寸（既定 1320×2868）がそのまま出力サイズになる。
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const tplDir = process.argv[2];
if (!tplDir) {
  console.error('usage: node render.mjs <テンプレートディレクトリ> [--only 1,3]');
  process.exit(1);
}

const root = path.resolve(tplDir);
const indexPath = path.join(root, 'index.html');
if (!fs.existsSync(indexPath)) {
  console.error(`index.html が無い: ${indexPath}`);
  process.exit(1);
}

const onlyArg = process.argv.indexOf('--only');
const only = onlyArg > -1
  ? new Set(process.argv[onlyArg + 1].split(',').map((n) => Number(n.trim())))
  : null;

const outDir = path.join(root, 'out');
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1320, height: 1200 },
  deviceScaleFactor: 1,
});

// file:// なので画像の読み込み完了を networkidle では待てない。個別に待つ。
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));

await page.goto(pathToFileURL(indexPath).href, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => Promise.all(
  [...document.images]
    .filter((img) => !img.complete)
    .map((img) => new Promise((res) => { img.onload = img.onerror = res; })),
));

// モックアップ合成や切り出しは非同期。テンプレートが window.__ready を出していれば待つ。
await page.evaluate(() => window.__ready || null);

if (errors.length) {
  console.error('ページ内でエラー:\n  ' + errors.join('\n  '));
  await browser.close();
  process.exit(1);
}

// 読めなかった画像はここで落とす。ストア素材に穴が空いたまま出すより早く気づく方がよい。
const broken = await page.evaluate(() =>
  [...document.images].filter((i) => !i.naturalWidth).map((i) => i.getAttribute('src')));
if (broken.length) {
  console.error('画像が読めない:\n  ' + broken.join('\n  '));
  await browser.close();
  process.exit(1);
}

const shots = await page.$$('.shot');
if (!shots.length) {
  console.error('.shot 要素が 1 つも無い');
  await browser.close();
  process.exit(1);
}

for (const [i, el] of shots.entries()) {
  const n = i + 1;
  if (only && !only.has(n)) continue;
  const file = path.join(outDir, `${String(n).padStart(2, '0')}.png`);
  await el.screenshot({ path: file });
  const { width, height } = await el.boundingBox();
  console.log(`${path.relative(process.cwd(), file)}  ${width}×${height}`);
}

await browser.close();
