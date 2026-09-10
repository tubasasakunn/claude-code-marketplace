/**
 * 自動化用 Chrome の面倒を見る層。
 *
 * Chrome 136+ は既定の user-data-dir に対して --remote-debugging-port を無効化する
 * （Cookie 窃取対策）。そのため普段使いプロファイルを別ディレクトリへコピーし、
 * そのコピーをデバッグ起動する。
 *
 * **canva プラグインの mcp/lib/chrome.mjs とほぼ同じ実装**（プラグインを独立して
 * 配れるようにするため、共有せず複製している）。Chrome まわりの事故 —— タブ 0 枚、
 * プロファイルを生きたまま作り直す、rsync が生きたキャッシュで落ちる —— の対処は
 * 両方に等しく効くので、**片方を直したらもう片方も見ること**。
 *
 * Canva 用（既定 9222）と Gemini 用（既定 9223）は複製先もポートも別なので、並走できる。
 */
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const execFileAsync = promisify(execFile);

export const DEFAULT_PORT = Number(process.env.GEMINI_CDP_PORT || 9223);
export const CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
export const SRC_ROOT = path.join(os.homedir(), "Library/Application Support/Google/Chrome");
export const DST_ROOT = path.join(os.homedir(), "Library/Application Support/Google/Chrome-gemini");

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

/** Cookies(SQLite) の指定ホストの件数を数える。掴まれている DB を避けて複製してから読む。 */
async function countCookies(cookiesPath, hostLike = "%google.com%") {
  if (!fs.existsSync(cookiesPath)) return 0;
  const tmp = path.join(os.tmpdir(), `gemini-mcp-count-${process.pid}.db`);
  try {
    fs.copyFileSync(cookiesPath, tmp);
    const { stdout } = await execFileAsync("sqlite3", [
      tmp,
      `SELECT COUNT(*) FROM cookies WHERE host_key LIKE '${hostLike}';`,
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

export function profileExists(dstRoot = DST_ROOT) {
  return fs.existsSync(path.join(dstRoot, "Default"));
}

/**
 * 指定した自動化用プロファイルを掴んでいる Chrome を落とす。
 * 普段使いの Chrome は別ディレクトリなので巻き込まない。
 * dstRoot を変えれば、用途ごとに別プロファイル・別ポートで並走させられる
 * （例: Canva 用は 9222、別サービス用は 9223）。
 */
export async function killAutomationChrome(dstRoot = DST_ROOT) {
  await execFileAsync("pkill", ["-f", `user-data-dir=${dstRoot}`]).catch(() => {});
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
 * 普段使い Chrome のプロファイルを列挙し、表示名とログイン中の Google アカウントを返す。
 * どれを複製すればよいかは人にしか決められないので、判断材料を出すところまでをやる。
 */
export async function detectProfiles() {
  if (!fs.existsSync(SRC_ROOT)) return [];
  const names = fs
    .readdirSync(SRC_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory() && (d.name === "Default" || /^Profile \d+$/.test(d.name)))
    .map((d) => d.name);

  let info = {};
  try {
    const localState = JSON.parse(fs.readFileSync(path.join(SRC_ROOT, "Local State"), "utf8"));
    info = localState?.profile?.info_cache ?? {};
  } catch {
    // Local State が読めなければ、ディレクトリ名だけで案内する
  }

  const results = [];
  for (const name of names) {
    results.push({
      profile: name,
      label: info[name]?.name ?? null,
      account: info[name]?.user_name || null,
      googleCookies: await countCookies(path.join(SRC_ROOT, name, "Cookies")),
    });
  }
  return results.sort((a, b) => b.googleCookies - a.googleCookies);
}

/**
 * 普段使いプロファイルを自動化用ディレクトリへコピーする。
 * 初回と、Canva のログインが切れて普段の Chrome で入り直したときに実行する。
 */
export async function setupProfile({
  srcProfile = process.env.GEMINI_SRC_PROFILE || "Profile 1",
  dstRoot = DST_ROOT,
  log = () => {},
} = {}) {
  const src = path.join(SRC_ROOT, srcProfile);
  if (!fs.existsSync(src)) {
    throw new Error(`コピー元プロファイルがありません: ${src}`);
  }
  // コピー先を作り直すので、そこを掴んでいる Chrome は先に落とす。
  // 生きたまま消すと、以後その Chrome は壊れた状態のまま CDP に応答しなくなる。
  await killAutomationChrome(dstRoot);
  log(`コピー元: ${src}`);
  log(`コピー先: ${path.join(dstRoot, "Default")}`);

  fs.rmSync(dstRoot, { recursive: true, force: true });
  fs.mkdirSync(dstRoot, { recursive: true });
  for (const f of ["Local State", "First Run"]) {
    try {
      fs.copyFileSync(path.join(SRC_ROOT, f), path.join(dstRoot, f));
    } catch {
      // First Run は無いことがある
    }
  }

  const dst = path.join(dstRoot, "Default");
  const args = ["-a"];
  for (const e of RSYNC_EXCLUDES) args.push("--exclude", e);
  args.push(`${src}/`, `${dst}/`);
  try {
    await execFileAsync("rsync", args, { maxBuffer: 32 * 1024 * 1024 });
  } catch (e) {
    if (!RSYNC_TOLERATED_CODES.has(e.code)) throw e;
    log(`rsync が一部ファイルを取りこぼしました（コード ${e.code}）。cookie が揃っていれば問題ありません。`);
  }

  // コピーできたかどうかは転送の成否ではなく、Google の cookie が入ったかで判定する
  const cookies = await countCookies(path.join(dst, "Cookies"));
  if (cookies === 0) {
    throw new Error(
      `コピーはできましたが、${srcProfile} から Google の cookie を引き継げませんでした。` +
        "Gemini にログインしている Chrome プロファイルを src_profile に指定してください。",
    );
  }

  const { stdout } = await execFileAsync("du", ["-sh", dstRoot]);
  const size = stdout.split("\t")[0]?.trim() ?? "?";
  log(`コピー完了: ${size} / Google cookie ${cookies} 個`);
  return { srcProfile, dst, size, cookies };
}

/** 自動化用プロファイルをデバッグ起動する。既に待ち受けていれば何もしない。 */
export async function launchChrome({
  port = DEFAULT_PORT,
  dstRoot = DST_ROOT,
  timeoutMs = 16000,
  log = () => {},
} = {}) {
  const already = await isAlive(port);
  if (already) {
    log(`既にポート ${port} で待ち受け中`);
    return { started: false, port, version: already };
  }
  if (!profileExists(dstRoot)) {
    throw new Error("自動化用プロファイルがありません。先に gemini_setup_profile を実行してください。");
  }
  if (!fs.existsSync(CHROME_BIN)) {
    throw new Error(`Google Chrome が見つかりません: ${CHROME_BIN}`);
  }

  // 同じ user-data-dir を掴んだままの古いプロセスが残っているとポートを開けない
  await killAutomationChrome(dstRoot);

  log(`デバッグ起動（ポート ${port}）`);
  const child = spawn(
    CHROME_BIN,
    [
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${dstRoot}`,
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
