/**
 * Gemini（gemini.google.com）のブラウザ操作。
 *
 * Gemini には公式 API があるが、こちらが相手にするのは **アプリ側にしか無い機能**
 * （Nano Banana の画像生成、Deep Research、Canvas など）。テキスト生成だけで足りるなら
 * 公式 API のほうが速く、壊れず、規約上も素直なので、そちらを使うこと。
 *
 * ここがセレクタの正本。UI が変われば壊れる前提の作りで、各ステップのスクショを残すのは
 * 復旧を速くするため。実測で判明した事故は skills/gemini-browser/REFERENCE.md にある。
 */
import { chromium } from "playwright-core";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { cdpUrl, DEFAULT_PORT, ensureTarget, isAlive } from "./chrome.mjs";

export const GEMINI_URL = "https://gemini.google.com/app";

// 実測で確定したロケータ（2026-08 時点）
const PROMPT_BOX = 'rich-textarea [contenteditable="true"]';
const TOOLS_BUTTON = "アップロードとツール";
const MORE_TOOLS = "その他のツール";
// getByRole ではクリックが通らないので CSS で当てる
const MODEL_BUTTON = 'button[aria-label*="モード選択ツール"]';
// モデルメニューは Angular Material ではなく独自要素（gem-menu > gem-menu-item）。
// role は menuitemradio ではなく menuitem で、.cdk-overlay-container にも入らない。
const MENU_ITEM = 'gem-menu [role="menuitem"]';
const SIDEBAR_BUTTON = "サイドバーを開く";
const START_RESEARCH = /リサーチを開始|Start research/;
// 開始直後に「リサーチが完了したらお知らせします」が出るので、日本語で判定してはいけない。
// 完了メッセージは日本語 UI でも英文で出る。
const RESEARCH_DONE = /completed your research/i;
// 進行中に出る表示。これが見えているあいだは完了ではない
const RESEARCH_BUSY = /件のウェブサイトをリサーチ|リサーチしています|Researching \d+/;
// レポートがこの長さに満たないうちは、まだ書き終えていないとみなす
const REPORT_MIN = 2000;
const RESPONSE = "model-response";
// Deep Research のレポートは model-response ではなくイマーシブパネルに出る
const IMMERSIVE = "[class*=immersive]";
// model-response の innerText には見出しが混ざる
const RESPONSE_HEADING = /^(Gemini の回答|Gemini's response)\s*/;
const CONVERSATION = '[data-test-id="conversation"], .conversation-title';

export const TOOLS = ["画像を作成", "動画を作成", "音楽を作成", "Canvas", "Deep Research",
                      "ガイド付き学習", "パーソナル インテリジェンス"];
// 「その他のツール」の奥に隠れているもの
const NESTED_TOOLS = new Set(["Deep Research", "ガイド付き学習", "パーソナル インテリジェンス", "Labs"]);

function shotsDir() {
  return process.env.GEMINI_MCP_SHOTS_DIR || path.join(os.tmpdir(), "gemini-mcp-shots");
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

async function connect(port) {
  if (!(await isAlive(port))) {
    throw new Error(`ポート ${port} で Chrome が待ち受けていません。先に gemini_launch_chrome を実行してください。`);
  }
  await ensureTarget(port);
  return chromium.connectOverCDP(cdpUrl(port));
}

async function openApp(browser) {
  const page = await browser.contexts()[0].newPage();
  await page.goto(GEMINI_URL, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  return page;
}

/** ログイン中の Google アカウント。メールを含む aria-label だけを見る（ヘルプリンクを拾わないため）。 */
async function whoami(page) {
  for (const sel of ['a[aria-label*="@"]', 'button[aria-label*="@"]']) {
    const el = page.locator(sel).first();
    if (await el.count().catch(() => 0)) {
      const label = await el.getAttribute("aria-label").catch(() => null);
      if (label && label.includes("@")) return label.replace(/\s+/g, " ").trim();
    }
  }
  return null;
}

async function currentModel(page) {
  const btn = page.locator(MODEL_BUTTON).first();
  if (!(await btn.count().catch(() => 0))) return null;
  const label = await btn.getAttribute("aria-label").catch(() => null);
  const m = label && /現在のモデル:\s*([^)）]+)/.exec(label);
  return m ? m[1] : label;
}

/** プロンプト欄が出ているか。ログイン済みかどうかの判定はこれで行う（cookie 数では判定しない）。 */
async function promptReady(page) {
  return (await page.locator(PROMPT_BOX).count().catch(() => 0)) > 0;
}

async function selectModel(page, model, log) {
  log(`モデルを「${model}」に切り替える`);
  await page.locator(MODEL_BUTTON).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
  try {
    await page.locator(MENU_ITEM).filter({ hasText: model }).first().click({ timeout: 5000 });
    await page.waitForTimeout(1500);
  } catch {
    await page.keyboard.press("Escape").catch(() => {});
    throw new Error(`モデル「${model}」が見つかりません。gemini_check で選べる一覧を確認してください。`);
  }
}

async function selectTool(page, tool, log) {
  log(`ツール「${tool}」を選ぶ`);
  await page.getByRole("button", { name: TOOLS_BUTTON }).click({ timeout: 6000 });
  await page.waitForTimeout(1500);
  if (NESTED_TOOLS.has(tool)) {
    await page.getByText(MORE_TOOLS, { exact: true }).first().click({ timeout: 5000 });
    await page.waitForTimeout(1500);
  }
  try {
    await page.getByText(tool, { exact: true }).first().click({ timeout: 5000 });
    await page.waitForTimeout(1500);
  } catch {
    const p = await shot(page, "tool_not_found");
    throw new Error(`ツール「${tool}」が見つかりません。${p} を確認してください。`);
  }
}

async function send(page, prompt) {
  const box = page.locator(PROMPT_BOX).first();
  await box.waitFor({ state: "visible", timeout: 10000 });
  await box.click();
  // fill は contenteditable に効かないので、キー入力で流し込む
  await page.keyboard.insertText(prompt);
  await page.waitForTimeout(800);
  await page.keyboard.press("Enter");
}

/** 応答テキストが伸びなくなるまで待つ。明示的な完了シグナルが無いのでこれで見る。 */
async function waitForStableResponse(page, { waitSec, log }) {
  const deadline = Date.now() + waitSec * 1000;
  let last = "";
  let stable = 0;
  while (Date.now() < deadline) {
    await page.waitForTimeout(2500);
    const t = (await page.locator(RESPONSE).last().innerText().catch(() => ""))
      .replace(RESPONSE_HEADING, "").trim();
    if (t && t === last) {
      if (++stable >= 2) return t;
    } else {
      stable = 0;
      last = t;
    }
  }
  log(`${waitSec} 秒で打ち切り（応答が伸び続けている）`);
  return last;
}

/** 接続と、Gemini が使える状態かを見る。 */
export async function check({ port = DEFAULT_PORT } = {}) {
  const version = await isAlive(port);
  if (!version) {
    return { chrome: false, ready: false, message: `ポート ${port} で Chrome が待ち受けていません。` };
  }
  const browser = await connect(port);
  try {
    const page = await openApp(browser);
    const [account, model, ready] = await Promise.all([whoami(page), currentModel(page), promptReady(page)]);
    const upgrade = await page.getByText(/アップグレード|Upgrade/).count().catch(() => 0);
    let models = [];
    if (ready) {
      await page.locator(MODEL_BUTTON).first().click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(2200);
      const raw = await page.locator(MENU_ITEM).allInnerTexts().catch(() => []);
      // 各項目は「名前\n説明\nNew」の形なので 1 行目だけ採る
      models = raw.map((t) => t.split("\n")[0].trim()).filter(Boolean);
      await page.keyboard.press("Escape").catch(() => {});
    }
    await page.close().catch(() => {});
    return {
      chrome: true,
      browser: version["Browser"] ?? null,
      ready,
      account,
      model,
      paid: upgrade === 0,
      models,
      message: ready
        ? `Gemini を使えます（${account ?? "アカウント不明"} / モデル ${model ?? "?"}）。`
        : "Chrome は動いていますが、Gemini のプロンプト欄が出ていません。ログインを確認してください。",
    };
  } finally {
    await browser.close().catch(() => {});
  }
}

/** 普通に 1 往復する。 */
export async function ask({ prompt, model = null, waitSec = 120, port = DEFAULT_PORT, log = () => {} } = {}) {
  if (!prompt?.trim()) throw new Error("prompt が空です。");
  const browser = await connect(port);
  const page = await openApp(browser);
  try {
    if (!(await promptReady(page))) {
      const p = await shot(page, "not_logged_in");
      throw new Error(`Gemini のプロンプト欄がありません。ログインが切れている可能性があります（${p}）。`);
    }
    if (model) await selectModel(page, model, log);
    log(`送信: ${prompt.slice(0, 60)}`);
    await send(page, prompt);
    const text = await waitForStableResponse(page, { waitSec, log });
    await shot(page, "ask_result");
    return { prompt, model: model ?? (await currentModel(page)), text, shotsDir: shotsDir() };
  } finally {
    await page.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

/**
 * 画像を生成して保存する（Nano Banana）。
 *
 * 取り出しはダウンロードボタンを使わない。押しても出るのはスナックバー通知で、
 * download イベントも発火せず、blob: の fetch も revoke 済みで失敗する。
 * 描画済みの img を canvas に写して dataURL にするのが唯一通る道。
 */
export async function generateImage({
  prompt, out, waitSec = 180, port = DEFAULT_PORT, log = () => {},
} = {}) {
  if (!prompt?.trim()) throw new Error("prompt が空です。");
  const outDir = expandPath(out || path.join(os.homedir(), "Pictures/gemini"));
  const browser = await connect(port);
  const page = await openApp(browser);
  try {
    if (!(await promptReady(page))) throw new Error("Gemini のプロンプト欄がありません。ログインを確認してください。");
    await selectTool(page, "画像を作成", log);
    log(`送信: ${prompt.slice(0, 60)}`);
    await send(page, prompt);

    const imgs = page.locator(`${RESPONSE} img, message-content img`);
    const deadline = Date.now() + waitSec * 1000;
    let found = 0;
    while (Date.now() < deadline) {
      await page.waitForTimeout(4000);
      found = await imgs.count().catch(() => 0);
      if (found > 0) break;
    }
    if (!found) {
      const p = await shot(page, "image_timeout");
      throw new Error(`${waitSec} 秒以内に画像を検知できませんでした。${p} を確認してください。`);
    }
    await page.waitForTimeout(2500);

    fs.mkdirSync(outDir, { recursive: true });
    const saved = [];
    const warnings = [];
    const n = await imgs.count();
    for (let i = 0; i < n; i++) {
      const el = imgs.nth(i);
      const dataUrl = await el
        .evaluate((img) => {
          const c = document.createElement("canvas");
          c.width = img.naturalWidth;
          c.height = img.naturalHeight;
          c.getContext("2d").drawImage(img, 0, 0);
          return c.toDataURL("image/png");
        })
        .catch((e) => {
          warnings.push(`${i + 1} 枚目を canvas から取れず: ${e.message.split("\n")[0]}`);
          return null;
        });
      if (!dataUrl) continue;
      const m = /^data:image\/png;base64,(.*)$/s.exec(dataUrl);
      if (!m) continue;
      const file = path.join(outDir, `${String(i + 1).padStart(2, "0")}_gemini.png`);
      fs.writeFileSync(file, Buffer.from(m[1], "base64"));
      const size = await el.evaluate((e) => `${e.naturalWidth}x${e.naturalHeight}`).catch(() => "?");
      saved.push({ path: file, bytes: fs.statSync(file).size, size });
      log(`保存: ${file} (${size})`);
    }
    await shot(page, "image_result");
    return { prompt, outDir, saved, warnings, shotsDir: shotsDir() };
  } finally {
    await page.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

/** イマーシブパネルからレポート本文を取る。model-response には要約しか入らない。 */
async function readReport(page) {
  const panel = page.locator(IMMERSIVE);
  if (!(await panel.count().catch(() => 0))) return "";
  return (await panel.last().innerText().catch(() => "")).trim();
}

/**
 * Deep Research を回す。
 *
 * 2 段構えである点に注意。プロンプトを送るとまずリサーチ計画が出て、
 * 「リサーチを開始」を押さないと本番が始まらない。完了の合図は
 * 「I've completed your research.」で、本文はイマーシブパネルに出る。
 */
export async function deepResearch({
  prompt, out = null, waitSec = 900, port = DEFAULT_PORT, log = () => {},
} = {}) {
  if (!prompt?.trim()) throw new Error("prompt が空です。");
  const browser = await connect(port);
  const page = await openApp(browser);
  try {
    if (!(await promptReady(page))) throw new Error("Gemini のプロンプト欄がありません。ログインを確認してください。");
    await selectTool(page, "Deep Research", log);
    log(`テーマ: ${prompt.slice(0, 60)}`);
    await send(page, prompt);

    const t0 = Date.now();
    const deadline = t0 + waitSec * 1000;
    let started = false;
    let done = false;
    while (Date.now() < deadline) {
      await page.waitForTimeout(10000);
      if (!started) {
        const go = page.getByRole("button", { name: START_RESEARCH }).first();
        if (await go.count().catch(() => 0)) {
          await go.click({ timeout: 8000 }).catch(() => {});
          started = true;
          log(`リサーチを開始（${Math.round((Date.now() - t0) / 1000)}s）`);
          continue;
        }
      }
      if (!started) continue;

      // 完了の判定は 3 つ揃ってから。文言だけだと開始直後の案内に引っかかる
      const [sign, busy] = await Promise.all([
        page.getByText(RESEARCH_DONE).count().catch(() => 0),
        page.getByText(RESEARCH_BUSY).count().catch(() => 0),
      ]);
      const len = (await readReport(page)).length;
      log(`経過 ${Math.round((Date.now() - t0) / 1000)}s / レポート ${len} 文字 / 完了サイン ${sign} / 進行中 ${busy}`);
      if (sign && !busy && len >= REPORT_MIN) {
        done = true;
        break;
      }
    }

    const seconds = Math.round((Date.now() - t0) / 1000);
    if (!done) {
      const p = await shot(page, "research_timeout");
      return {
        prompt, started, done: false, seconds, report: "", path: null, shotsDir: shotsDir(),
        message: `${seconds} 秒では終わりませんでした（${p}）。Gemini 側では続いているので、` +
                 "しばらく待って gemini_deep_research_result で取り出してください。",
      };
    }

    await page.waitForTimeout(4000);
    const report = await readReport(page);
    let file = null;
    if (out && report) {
      file = expandPath(out);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, report);
      log(`保存: ${file}`);
    }
    await shot(page, "research_result");
    return { prompt, started, done: true, seconds, report, path: file, shotsDir: shotsDir() };
  } finally {
    await page.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

/**
 * 会話履歴からレポートを持つものを探して取り出す。
 *
 * 「直近の会話」が Deep Research とは限らない（画像生成を挟めばそちらが最新になる）ので、
 * 上から順に開いてイマーシブパネルの中身を見る。title を渡せばその会話に絞る。
 */
export async function latestReport({ out = null, title = null, maxScan = 5, port = DEFAULT_PORT, log = () => {} } = {}) {
  const browser = await connect(port);
  const page = await openApp(browser);
  try {
    const titles = [];
    for (let i = 0; i < maxScan; i++) {
      await page.getByRole("button", { name: SIDEBAR_BUTTON }).click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(2500);
      const convs = page.locator(CONVERSATION);
      const n = await convs.count().catch(() => 0);
      if (i >= n) break;

      const label = (await convs.nth(i).innerText().catch(() => "")).replace(/\s+/g, " ").trim();
      if (i === 0 && n === 0) throw new Error("会話履歴が見つかりません。");
      titles.push(label);
      if (title && !label.includes(title)) continue;

      log(`会話を開く: ${label.slice(0, 40)}`);
      await convs.nth(i).click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(7000);

      const report = await readReport(page);
      if (report.length > 500) {
        const done = (await page.getByText(RESEARCH_DONE).count().catch(() => 0)) > 0;
        let file = null;
        if (out) {
          file = expandPath(out);
          fs.mkdirSync(path.dirname(file), { recursive: true });
          fs.writeFileSync(file, report);
          log(`保存: ${file}`);
        }
        return { done, report, path: file, title: label, titles, shotsDir: shotsDir() };
      }
    }
    return { done: false, report: "", path: null, title: null, titles, shotsDir: shotsDir() };
  } finally {
    await page.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}
