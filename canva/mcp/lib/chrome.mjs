/**
 * 自動化用 Chrome の面倒を見る層。
 *
 * Chrome 136+ は既定の user-data-dir に対して --remote-debugging-port を無効化する
 * （Cookie 窃取対策）。そのため普段使いプロファイルを別ディレクトリへコピーし、
 * そのコピーをデバッグ起動する。コピー時点のログイン状態は Keychain 経由で復号できるので
 * そのまま引き継がれる。詳細は skills/canva-image-gen/REFERENCE.md。
 */
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const execFileAsync = promisify(execFile);

export const DEFAULT_PORT = Number(process.env.CDP_PORT || 9222);
export const CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
export const SRC_ROOT = path.join(os.homedir(), "Library/Application Support/Google/Chrome");
export const DST_ROOT = path.join(os.homedir(), "Library/Application Support/Google/Chrome-automation");

// 引き継ぎたいのは cookie と設定だけ。キャッシュ類は要らないうえ、普段使いの Chrome が
// 動いていると転送中に消えて rsync を落とすので、まとめて除外する。
const RSYNC_EXCLUDES = [
  "Cache", "Code Cache", "GPUCache",
  "Service Worker/CacheStorage", "Service Worker/ScriptCache",
  "DawnGraphiteCache", "DawnWebGPUCache", "GraphiteDawnCache", "Application Cache",
  "WebStorage", "blob_storage", "Crashpad", "component_crx_cache",
  "optimization_guide_model_store", "Storage/ext", "shared_proto_db",
];

/** rsync の 24 は「転送中に元ファイルが消えた」。キャッシュを除外しても起きうるので通す。 */
const RSYNC_TOLERATED_CODES = new Set([24]);

/** Cookies(SQLite) の canva.com ホストの件数を数える。掴まれている DB を避けて複製してから読む。 */
async function countCanvaCookies(cookiesPath) {
  if (!fs.existsSync(cookiesPath)) return 0;
  const tmp = path.join(os.tmpdir(), `canva-mcp-count-${process.pid}.db`);
  try {
    fs.copyFileSync(cookiesPath, tmp);
    const { stdout } = await execFileAsync("sqlite3", [
      tmp,
      "SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%canva.com%';",
    ]);
    return Number(stdout.trim()) || 0;
  } catch {
    return 0;
  } finally {
    fs.rmSync(tmp, { force: true });
  }
}

export function cdpUrl(port = DEFAULT_PORT) {
  return `http://127.0.0.1:${port}`;
}

/** デバッグポートが待ち受けているか。Chrome の生死判定はこれ一本で足りる。 */
export async function isAlive(port = DEFAULT_PORT) {
  try {
    const res = await fetch(`${cdpUrl(port)}/json/version`, {
      signal: AbortSignal.timeout(1500),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export function profileExists() {
  return fs.existsSync(path.join(DST_ROOT, "Default"));
}

/** 自動化用プロファイルを掴んでいる Chrome を落とす。普段使いの Chrome は別ディレクトリなので巻き込まない。 */
export async function killAutomationChrome() {
  await execFileAsync("pkill", ["-f", `user-data-dir=${DST_ROOT}`]).catch(() => {});
  await new Promise((r) => setTimeout(r, 1200));
}

/**
 * ページが 1 枚も無い Chrome には connectOverCDP できない
 * （Browser.setDownloadBehavior が "Browser context management is not supported" で落ちる）。
 * 起動しっぱなしの Chrome は全タブを閉じられてこの状態になるので、繋ぐ前に空タブを 1 枚用意する。
 */
export async function ensureTarget(port = DEFAULT_PORT) {
  let pages = [];
  try {
    const list = await fetch(`${cdpUrl(port)}/json/list`, { signal: AbortSignal.timeout(2000) });
    pages = (await list.json()).filter((t) => t.type === "page");
  } catch {
    return 0;
  }
  if (pages.length) return pages.length;

  // Chrome 111+ の /json/new は PUT でないと 405 を返す
  await fetch(`${cdpUrl(port)}/json/new?about:blank`, {
    method: "PUT",
    signal: AbortSignal.timeout(4000),
  }).catch(() => {});
  await new Promise((r) => setTimeout(r, 600));
  return 1;
}

/**
 * どのプロファイルに Canva のログインがあるかを Cookies(SQLite) の件数で推定する。
 * Chrome が掴んでいるファイルを直接開くとロックに当たるので、tmp へ複製してから読む。
 */
export async function detectCanvaProfile() {
  if (!fs.existsSync(SRC_ROOT)) return [];
  const names = fs
    .readdirSync(SRC_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory() && (d.name === "Default" || /^Profile \d+$/.test(d.name)))
    .map((d) => d.name);

  let labels = {};
  try {
    const localState = JSON.parse(fs.readFileSync(path.join(SRC_ROOT, "Local State"), "utf8"));
    labels = localState?.profile?.info_cache ?? {};
  } catch {
    // Local State が読めなくても件数だけで判断できる
  }

  const results = [];
  for (const name of names) {
    const src = path.join(SRC_ROOT, name, "Cookies");
    if (!fs.existsSync(src)) continue;
    const tmp = path.join(os.tmpdir(), `canva-mcp-cookies-${name.replace(/\s/g, "_")}.db`);
    try {
      fs.copyFileSync(src, tmp);
      const { stdout } = await execFileAsync("sqlite3", [
        tmp,
        "SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%canva.com%';",
      ]);
      results.push({
        profile: name,
        label: labels[name]?.name ?? null,
        canvaCookies: Number(stdout.trim()) || 0,
      });
    } catch {
      // sqlite3 が無い / 壊れた DB は候補から外すだけでよい
    } finally {
      fs.rmSync(tmp, { force: true });
    }
  }
  return results.sort((a, b) => b.canvaCookies - a.canvaCookies);
}

/**
 * 普段使いプロファイルを自動化用ディレクトリへコピーする。
 * 初回と、Canva のログインが切れて普段の Chrome で入り直したときに実行する。
 */
export async function setupProfile({ srcProfile = process.env.SRC_PROFILE || "Profile 1", log = () => {} } = {}) {
  const src = path.join(SRC_ROOT, srcProfile);
  if (!fs.existsSync(src)) {
    throw new Error(`コピー元プロファイルがありません: ${src}`);
  }
  // コピー先を作り直すので、そこを掴んでいる Chrome は先に落とす。
  // 生きたまま消すと、以後その Chrome は壊れた状態のまま CDP に応答しなくなる。
  await killAutomationChrome();
  log(`コピー元: ${src}`);
  log(`コピー先: ${path.join(DST_ROOT, "Default")}`);

  fs.rmSync(DST_ROOT, { recursive: true, force: true });
  fs.mkdirSync(DST_ROOT, { recursive: true });
  for (const f of ["Local State", "First Run"]) {
    try {
      fs.copyFileSync(path.join(SRC_ROOT, f), path.join(DST_ROOT, f));
    } catch {
      // First Run は無いことがある
    }
  }

  const dst = path.join(DST_ROOT, "Default");
  const args = ["-a"];
  for (const e of RSYNC_EXCLUDES) args.push("--exclude", e);
  args.push(`${src}/`, `${dst}/`);
  try {
    await execFileAsync("rsync", args, { maxBuffer: 32 * 1024 * 1024 });
  } catch (e) {
    if (!RSYNC_TOLERATED_CODES.has(e.code)) throw e;
    log(`rsync が一部ファイルを取りこぼしました（コード ${e.code}）。cookie が揃っていれば問題ありません。`);
  }

  // コピーできたかどうかは転送の成否ではなく、Canva の cookie が入ったかで判定する
  const cookies = await countCanvaCookies(path.join(dst, "Cookies"));
  if (cookies === 0) {
    throw new Error(
      `コピーはできましたが、${srcProfile} から Canva の cookie を引き継げませんでした。` +
        "普段使いの Chrome で Canva にログインしているプロファイルを src_profile に指定してください。",
    );
  }

  const { stdout } = await execFileAsync("du", ["-sh", DST_ROOT]);
  const size = stdout.split("\t")[0]?.trim() ?? "?";
  log(`コピー完了: ${size} / Canva cookie ${cookies} 個`);
  return { srcProfile, dst, size, cookies };
}

/** 自動化用プロファイルをデバッグ起動する。既に待ち受けていれば何もしない。 */
export async function launchChrome({ port = DEFAULT_PORT, timeoutMs = 16000, log = () => {} } = {}) {
  const already = await isAlive(port);
  if (already) {
    log(`既にポート ${port} で待ち受け中`);
    return { started: false, port, version: already };
  }
  if (!profileExists()) {
    throw new Error("自動化用プロファイルがありません。先に canva_setup_profile を実行してください。");
  }
  if (!fs.existsSync(CHROME_BIN)) {
    throw new Error(`Google Chrome が見つかりません: ${CHROME_BIN}`);
  }

  // 同じ user-data-dir を掴んだままの古いプロセスが残っているとポートを開けない
  await killAutomationChrome();

  log(`デバッグ起動（ポート ${port}）`);
  const child = spawn(
    CHROME_BIN,
    [
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${DST_ROOT}`,
      "--profile-directory=Default",
      "--no-first-run",
      "--no-default-browser-check",
      "about:blank",
    ],
    { detached: true, stdio: "ignore" },
  );
  child.unref();

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const v = await isAlive(port);
    if (v) {
      log(`起動完了。${cdpUrl(port)} で接続できる`);
      return { started: true, port, version: v };
    }
    await new Promise((r) => setTimeout(r, 400));
  }
  throw new Error(`デバッグポート ${port} の待ち受けを確認できませんでした。`);
}
