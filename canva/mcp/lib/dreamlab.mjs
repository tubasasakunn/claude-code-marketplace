/**
 * Canva Dream Lab（旧 Magic Media）のブラウザ操作。
 *
 * Canva の AI 画像生成に公式 API は無いので、ログイン済み Chrome に CDP で接続して
 * 画面を操作する。UI が変われば壊れる前提の作りで、各ステップのスクショを残すのは
 * 復旧を速くするため。確定セレクタの根拠は skills/canva-image-gen/REFERENCE.md。
 *
 * ここがセレクタの正本。CLI（scripts/canva_magic_media.js）も MCP もこの層を通す。
 */
import { chromium } from "playwright-core";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { cdpUrl, DEFAULT_PORT, ensureTarget, isAlive } from "./chrome.mjs";

export const DREAM_LAB_URL = "https://www.canva.com/dream-lab/";
export const VALID_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "2:1"];

const PROMPT_PLACEHOLDER = "心に描いたイメージを教えてください";
const DOWNLOAD_BUTTON = "画像をダウンロード";
const COOKIE_BUTTONS = ["すべてのCookieを許可する", "Cookieを許可", "Accept all cookies", "Accept all"];
const WELCOME_TEXTS = ["おかえりなさい", "Welcome back"];
const CONTINUE_BUTTONS = ["続行", "Continue"];

function shotsDir() {
  return process.env.CANVA_MCP_SHOTS_DIR || path.join(os.tmpdir(), "canva-mcp-shots");
}

async function shot(page, name) {
  const dir = shotsDir();
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, `${name}.png`);
  await page.screenshot({ path: p }).catch(() => {});
  return p;
}

export function expandPath(p) {
  if (!p) return p;
  const expanded = p.startsWith("~") ? path.join(os.homedir(), p.slice(1)) : p;
  return path.resolve(expanded);
}

async function dismissCookie(page) {
  for (const name of COOKIE_BUTTONS) {
    try {
      await page.getByRole("button", { name, exact: false }).first().click({ timeout: 2000 });
      return true;
    } catch {
      // 出ていないのが正常。次の候補を試す
    }
  }
  return false;
}

/**
 * cookie が生きていても、Canva は久しぶりの接続に「おかえりなさい！→ 続行」を挟むことがある。
 * これが出ているあいだはプロンプト欄が存在しないので、先に通しておく。
 */
async function dismissWelcomeBack(page, log) {
  let seen = false;
  for (const t of WELCOME_TEXTS) {
    if (await page.getByText(t, { exact: false }).first().isVisible({ timeout: 2000 }).catch(() => false)) {
      seen = true;
      break;
    }
  }
  if (!seen) return false;

  log("セッション再開ダイアログを通す");
  for (const name of CONTINUE_BUTTONS) {
    try {
      await page.getByRole("button", { name, exact: true }).first().click({ timeout: 3000 });
      await page.waitForLoadState("domcontentloaded").catch(() => {});
      await page.waitForTimeout(3500);
      return true;
    } catch {
      // 次の言語ラベルを試す
    }
  }
  return false;
}

async function setRatio(page, ratio, log) {
  if (!VALID_RATIOS.includes(ratio)) {
    throw new Error(`未知の比率「${ratio}」。指定できるのは ${VALID_RATIOS.join(", ")}`);
  }
  log(`アスペクト比を ${ratio} に設定`);
  // 現在値を \d:\d で表示しているトグルを開く
  await page.locator("button", { hasText: /^\d+\s*:\s*\d+$/ }).first().click({ timeout: 6000 });
  await page.waitForTimeout(800);
  // 展開後の各比率は role=button ではなく role=option
  await page.getByRole("option", { name: ratio, exact: true }).first().click({ timeout: 5000 });
  await page.waitForTimeout(600);
}

async function setStyle(page, style, log) {
  log(`スタイルを「${style}」に設定`);
  await page.getByRole("button", { name: "スタイル", exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(1200);
  try {
    await page.getByText(style, { exact: true }).first().click({ timeout: 4000 });
  } catch {
    const p = await shot(page, "style_not_found");
    throw new Error(`スタイル「${style}」が見つかりません。パネルの実際のラベルを ${p} で確認してください。`);
  }
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(500);
}

/** CDP 越しに Canva のログイン cookie が生きているかを見る。 */
export async function checkLogin({ port = DEFAULT_PORT } = {}) {
  const version = await isAlive(port);
  if (!version) {
    return { chrome: false, loggedIn: false, cookies: 0, message: `ポート ${port} で Chrome が待ち受けていません。` };
  }
  await ensureTarget(port);
  const browser = await chromium.connectOverCDP(cdpUrl(port));
  try {
    const context = browser.contexts()[0];
    const cookies = await context.cookies("https://www.canva.com");
    const loggedIn = cookies.length > 0;
    return {
      chrome: true,
      browser: version["Browser"] ?? null,
      loggedIn,
      cookies: cookies.length,
      message: loggedIn
        ? `Chrome は待ち受け中、Canva の cookie を ${cookies.length} 個保持しています。`
        : "Chrome は待ち受け中ですが、Canva の cookie がありません。普段の Chrome でログインし直して canva_setup_profile をやり直してください。",
    };
  } finally {
    await browser.close();
  }
}

/**
 * 自動化用 Chrome で Dream Lab を開き、人がログインし終えるのを待つ。
 *
 * 普段使いプロファイルのコピーだけでは足りないことがある。cookie の行は引き継げても、
 * Chrome の cookie 暗号化が強化されて別プロファイルでは復号できず、Canva 側は
 * ログイン画面（/login?redirect=/dream-lab/）を出す。「おかえりなさい → 続行」を押しても
 * 戻らないときがこれで、そのときは自動化用プロファイルで一度だけ人が入り直すしかない。
 *
 * 開いたページは閉じない。人がそこで操作するため。
 */
export async function waitForLogin({ port = DEFAULT_PORT, timeoutSec = 300, log = () => {} } = {}) {
  if (!(await isAlive(port))) {
    throw new Error(`ポート ${port} で Chrome が待ち受けていません。先に canva_launch_chrome を実行してください。`);
  }
  await ensureTarget(port);
  const browser = await chromium.connectOverCDP(cdpUrl(port));
  const started = Date.now();
  try {
    const page = await browser.contexts()[0].newPage();
    await page.bringToFront().catch(() => {});
    await page.goto(DREAM_LAB_URL, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await dismissCookie(page);
    await dismissWelcomeBack(page, log);

    const deadline = started + timeoutSec * 1000;
    while (Date.now() < deadline) {
      const ready = await page
        .getByPlaceholder(PROMPT_PLACEHOLDER, { exact: false })
        .count()
        .catch(() => 0);
      if (ready > 0) {
        const sec = Math.round((Date.now() - started) / 1000);
        log(`ログインを確認しました（${sec}s）`);
        return { loggedIn: true, seconds: sec, url: page.url() };
      }
      await page.waitForTimeout(5000);
    }
    return { loggedIn: false, seconds: timeoutSec, url: page.url() };
  } finally {
    // 接続を切るだけ。Chrome とページはそのまま残す
    await browser.close().catch(() => {});
  }
}

/**
 * プロンプトから画像を生成し、保存先ディレクトリへダウンロードする。
 *
 * 1 プロンプトにつき 4 枚生成される。完了判定は「画像をダウンロード」ボタンの
 * 個数が増えたかどうかで見る（生成の進捗を示す明示的な要素が無いため）。
 */
export async function generate({
  prompt,
  ratio = null,
  style = null,
  out,
  waitSec = 75,
  port = DEFAULT_PORT,
  log = () => {},
} = {}) {
  if (!prompt || !prompt.trim()) throw new Error("prompt が空です。");
  const outDir = expandPath(out || path.join(os.homedir(), "Pictures/canva"));
  const warnings = [];

  if (!(await isAlive(port))) {
    throw new Error(
      `ポート ${port} で Chrome が待ち受けていません。先に canva_launch_chrome を実行してください。`,
    );
  }

  await ensureTarget(port);
  const browser = await chromium.connectOverCDP(cdpUrl(port));
  const context = browser.contexts()[0];
  const page = await context.newPage();

  try {
    log("Dream Lab を開く");
    await page.goto(DREAM_LAB_URL, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    await dismissCookie(page);
    await page.waitForTimeout(500);
    if (await dismissWelcomeBack(page, log)) {
      // 「続行」の着地先が Dream Lab とは限らないので、離れていたら戻す
      if (!page.url().includes("/dream-lab")) {
        await page.goto(DREAM_LAB_URL, { waitUntil: "domcontentloaded" });
        await page.waitForTimeout(3500);
      }
    }
    await shot(page, "01_dreamlab");

    const dlBtn = page.getByRole("button", { name: DOWNLOAD_BUTTON });
    const before = await dlBtn.count();
    log(`既存の生成済み画像: ${before}`);

    if (ratio) {
      try {
        await setRatio(page, ratio, log);
      } catch (e) {
        warnings.push(`比率の設定に失敗（既定のまま続行）: ${e.message}`);
      }
    }
    if (style) {
      try {
        await setStyle(page, style, log);
      } catch (e) {
        warnings.push(`スタイルの設定に失敗（既定のまま続行）: ${e.message}`);
      }
    }

    log(`プロンプト入力: ${prompt}`);
    const box = page.getByPlaceholder(PROMPT_PLACEHOLDER, { exact: false }).first();
    try {
      await box.waitFor({ state: "visible", timeout: 8000 });
    } catch {
      const p = await shot(page, "prompt_not_found");
      throw new Error(
        `プロンプト入力欄が見つかりません。UI が変わった可能性があります。${p} を見て placeholder を確認してください。`,
      );
    }
    await box.click();
    await box.fill(prompt);
    await shot(page, "02_filled");

    log("生成を実行");
    await box.press("Enter");
    await page.waitForTimeout(2500);

    log(`生成完了を待つ（最大 ${waitSec}s）`);
    const deadline = Date.now() + waitSec * 1000;
    let done = false;
    while (Date.now() < deadline) {
      await page.waitForTimeout(4000);
      if ((await dlBtn.count()) > before) {
        done = true;
        break;
      }
    }
    const resultShot = await shot(page, "04_result");

    if (!done) {
      throw new Error(
        `${waitSec} 秒以内に新しい画像を検知できませんでした。${resultShot} を確認し、wait_sec を増やして再試行してください。`,
      );
    }

    const after = await dlBtn.count();
    const expected = after - before;
    log(`新規 ${expected} 枚を ${outDir} へ保存`);
    fs.mkdirSync(outDir, { recursive: true });

    const saved = [];
    for (let i = 0; i < expected; i++) {
      const btn = dlBtn.nth(i);
      try {
        await btn.scrollIntoViewIfNeeded();
        await btn.hover();
        const [download] = await Promise.all([
          page.waitForEvent("download", { timeout: 15000 }),
          btn.click(),
        ]);
        const raw = (download.suggestedFilename() || `image_${i}.jpg`).replace(/[/\\]/g, "_");
        // Canva はプロンプト全文をファイル名に使うので、そのままだと ENAMETOOLONG になる。
        // 拡張子を保ったままスラグを切り詰める。
        const ext = path.extname(raw) || ".jpg";
        const stem = path.basename(raw, ext).slice(0, 60).trim();
        const file = path.join(outDir, `${String(i + 1).padStart(2, "0")}_${stem}${ext}`);
        await download.saveAs(file);
        saved.push({ path: file, bytes: fs.statSync(file).size });
        log(`保存: ${file}`);
        await page.waitForTimeout(800);
      } catch (e) {
        warnings.push(`${i + 1} 枚目のダウンロードに失敗: ${e.message}`);
      }
    }

    return { prompt, ratio, style, outDir, expected, saved, warnings, shotsDir: shotsDir() };
  } finally {
    await page.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}
