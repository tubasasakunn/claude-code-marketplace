/**
 * Canva Dream Lab（旧 Magic Media）の AI 画像生成をブラウザ操作で叩く CLI。
 *
 * 前提:
 *   - ./launch_chrome.sh で自動化用Chromeをデバッグ起動済み & Canvaログイン済み
 *   - npm install 済み（playwright-core）
 *
 * 使い方:
 *   node canva_magic_media.js "ネオン街を歩く柴犬, 写真風"
 *   node canva_magic_media.js "..." --ratio 1:1 --out ~/Pictures/canva
 *   node canva_magic_media.js "..." --ratio 9:16 --style 写真 --wait 120
 *
 * オプション:
 *   --ratio  <比率>   16:9 | 9:16 | 1:1 | 4:3 | 3:4 | 2:1   (既定: 変更しない)
 *   --style  <名前>   スタイルパネルに表示される日本語ラベル（例: 写真, アニメ）
 *   --out    <パス>   保存先ディレクトリ（既定: ./output）
 *   --wait   <秒>     生成完了の最大待ち秒数（既定: 75）
 */
const { chromium } = require("playwright-core");
const fs = require("fs");
const os = require("os");
const path = require("path");

const CDP_URL = `http://127.0.0.1:${process.env.CDP_PORT || "9222"}`;
const DREAM_LAB_URL = "https://www.canva.com/dream-lab/";
const SHOTS_DIR = path.join(__dirname, "shots");
const PROMPT_PLACEHOLDER = "心に描いたイメージを教えてください";
const VALID_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "2:1"];

// --- 簡易引数パーサ ---
function parseArgs(argv) {
  const opts = { ratio: null, style: null, out: path.join(__dirname, "output"), wait: 75 };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--ratio") opts.ratio = argv[++i];
    else if (a === "--style") opts.style = argv[++i];
    else if (a === "--out") opts.out = argv[++i];
    else if (a === "--wait") opts.wait = Number(argv[++i]);
    else positional.push(a);
  }
  opts.prompt = positional.join(" ");
  // ~ 展開
  if (opts.out.startsWith("~")) opts.out = path.join(os.homedir(), opts.out.slice(1));
  opts.out = path.resolve(opts.out);
  return opts;
}

async function shot(page, name) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  const p = path.join(SHOTS_DIR, `${name}.png`);
  await page.screenshot({ path: p });
}

async function dismissCookie(page) {
  for (const n of ["すべてのCookieを許可する", "Cookieを許可", "Accept all cookies", "Accept all"]) {
    try {
      await page.getByRole("button", { name: n, exact: false }).first().click({ timeout: 2000 });
      return;
    } catch (_) {}
  }
}

async function setRatio(page, ratio) {
  if (!VALID_RATIOS.includes(ratio)) {
    console.log(`  ⚠️ 未知の比率「${ratio}」。指定可: ${VALID_RATIOS.join(", ")} → スキップ`);
    return;
  }
  console.log(`→ アスペクト比を ${ratio} に設定`);
  // 比率セレクタ（role=combobox, aria=縦横比 / 現在値を \d:\d で表示）を開く
  const ratioBtn = page.locator("button", { hasText: /^\d+\s*:\s*\d+$/ }).first();
  await ratioBtn.click({ timeout: 6000 });
  await page.waitForTimeout(800);
  // メニュー内の該当比率（role=option）を選ぶ
  await page.getByRole("option", { name: ratio, exact: true }).first().click({ timeout: 5000 });
  await page.waitForTimeout(600);
}

async function setStyle(page, style) {
  console.log(`→ スタイルを「${style}」に設定`);
  await page.getByRole("button", { name: "スタイル", exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(1200);
  try {
    await page.getByText(style, { exact: true }).first().click({ timeout: 4000 });
  } catch (e) {
    await shot(page, "style_not_found");
    console.log(`  ⚠️ スタイル「${style}」が見つからず。shots/style_not_found.png を確認 → スキップ`);
  }
  // パネルを閉じる
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(500);
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (!opts.prompt) {
    console.error('使い方: node canva_magic_media.js "プロンプト" [--ratio 1:1] [--style 写真] [--out <dir>] [--wait 90]');
    process.exit(1);
  }

  const browser = await chromium.connectOverCDP(CDP_URL);
  const context = browser.contexts()[0];
  const page = await context.newPage();

  console.log("→ Dream Lab を開く");
  await page.goto(DREAM_LAB_URL, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  await dismissCookie(page);
  await page.waitForTimeout(500);
  await shot(page, "01_dreamlab");

  const dlBtn = page.getByRole("button", { name: "画像をダウンロード" });
  const beforeCount = await dlBtn.count();
  console.log(`  既存の生成済み画像: ${beforeCount}`);

  // オプション適用
  if (opts.ratio) {
    try { await setRatio(page, opts.ratio); }
    catch (e) { console.log(`  ⚠️ 比率設定失敗: ${e.message} → 既定のまま続行`); }
  }
  if (opts.style) {
    try { await setStyle(page, opts.style); }
    catch (e) { console.log(`  ⚠️ スタイル設定失敗: ${e.message} → 既定のまま続行`); }
  }

  console.log(`→ プロンプト入力: ${opts.prompt}`);
  const box = page.getByPlaceholder(PROMPT_PLACEHOLDER, { exact: false }).first();
  await box.waitFor({ state: "visible", timeout: 8000 });
  await box.click();
  await box.fill(opts.prompt);
  await shot(page, "02_filled");

  console.log("→ 生成を実行（Enter送信）");
  await box.press("Enter");
  await page.waitForTimeout(2500);

  console.log(`→ 生成完了を待つ（最大 ${opts.wait}s）`);
  const deadline = Date.now() + opts.wait * 1000;
  let done = false;
  while (Date.now() < deadline) {
    await page.waitForTimeout(4000);
    const now = await dlBtn.count();
    process.stdout.write(`  ダウンロード可能画像: ${now}\r`);
    if (now > beforeCount) { console.log(`\n  ✅ 新しい画像を検知（${beforeCount} → ${now}）`); done = true; break; }
  }
  console.log("");
  await shot(page, "04_result");

  if (!done) {
    console.log("⚠️ 時間内に新規画像を検知できず。shots/04_result.png を確認。--wait を増やして再試行を。");
    await browser.close();
    return;
  }

  const afterCount = await dlBtn.count();
  const newN = afterCount - beforeCount;
  console.log(`→ 新規 ${newN} 枚を ${opts.out} にダウンロード`);
  fs.mkdirSync(opts.out, { recursive: true });

  let saved = 0;
  for (let i = 0; i < newN; i++) {
    const btn = dlBtn.nth(i);
    try {
      await btn.scrollIntoViewIfNeeded();
      await btn.hover();
      const [download] = await Promise.all([
        page.waitForEvent("download", { timeout: 15000 }),
        btn.click(),
      ]);
      const raw = (download.suggestedFilename() || `image_${i}.jpg`).replace(/[/\\]/g, "_");
      // Canva はプロンプト全文をファイル名に使うため ENAMETOOLONG になる。
      // 拡張子を保ったままスラグを短く切り詰める。
      const ext = path.extname(raw) || ".jpg";
      const stem = path.basename(raw, ext).slice(0, 60).trim();
      const base = `${stem}${ext}`;
      const fn = path.join(opts.out, `${String(i + 1).padStart(2, "0")}_${base}`);
      await download.saveAs(fn);
      console.log(`  ✅ ${fn} (${fs.statSync(fn).size} B)`);
      saved++;
      await page.waitForTimeout(800);
    } catch (e) {
      console.log(`  ✗ ${i + 1} 枚目失敗: ${e.message}`);
    }
  }
  console.log(`→ 完了: ${saved}/${newN} 枚を ${opts.out} に保存`);

  await page.waitForTimeout(500);
  await browser.close();
}

main().catch((e) => { console.error(e); process.exit(1); });
