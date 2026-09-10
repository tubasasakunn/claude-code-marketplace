#!/usr/bin/env node
/**
 * gemini-mcp — Gemini アプリの機能を MCP ツールとして出す。
 *
 * 相手にするのは **アプリ側にしか無い機能**（Nano Banana の画像生成、Deep Research、
 * Canvas）。テキスト生成だけなら公式 API のほうが速く壊れないので、そちらを使うこと。
 *
 * 前提は 2 つ。
 *   1. Gemini にログイン済みの Chrome プロファイルの複製があること（gemini_setup_profile）
 *   2. その複製がデバッグポート付きで起動していること（gemini_launch_chrome）
 *
 * stdout は JSON-RPC のチャネルなので、進捗ログは必ず stderr に出す。
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { DEFAULT_PORT, detectProfiles, launchChrome, profileExists, setupProfile } from "./lib/chrome.mjs";
import { ask, check, deepResearch, generateImage, latestReport } from "./lib/gemini.mjs";

const log = (msg) => process.stderr.write(`[gemini-mcp] ${msg}\n`);
const text = (s) => ({ content: [{ type: "text", text: s }] });
const fail = (s) => ({ content: [{ type: "text", text: s }], isError: true });

async function guard(fn) {
  try {
    return await fn();
  } catch (e) {
    return fail(`❌ ${e.message}`);
  }
}

const portArg = z.number().int().optional().describe(`CDP ポート（既定 ${DEFAULT_PORT}）`);
const server = new McpServer({ name: "gemini-mcp", version: "1.0.0" });

server.registerTool(
  "gemini_check",
  {
    title: "Gemini 接続の状態を見る",
    description:
      "自動化用 Chrome が動いているか、Gemini にログインできているか、どのアカウント・どのモデルかを見る。" +
      "使う前にこれを通す。プロファイル未作成なら、どの Chrome プロファイルにどの Google アカウントが" +
      "入っているかの一覧を返すので、そこから複製元を選ぶ。",
    inputSchema: { port: portArg },
  },
  async ({ port = DEFAULT_PORT }) =>
    guard(async () => {
      if (!profileExists()) {
        const rows = await detectProfiles();
        const lines = ["自動化用プロファイル: なし", "", "普段使い Chrome のプロファイル:"];
        for (const r of rows) {
          lines.push(`  ${r.profile}${r.label ? `（${r.label}）` : ""} … ${r.account ?? "未ログイン"}`);
        }
        lines.push("", "→ Gemini が使えるアカウントを選び、gemini_setup_profile に src_profile で渡してください。");
        return text(lines.join("\n"));
      }
      const s = await check({ port });
      const lines = [
        `Chrome (port ${port}): ${s.chrome ? s.browser || "待ち受け中" : "起動していない"}`,
        `Gemini: ${s.ready ? "使える" : "使えない"}`,
        `アカウント: ${s.account ?? "不明"}`,
        `モデル: ${s.model ?? "不明"}${s.paid ? "（アップグレード表示なし＝有料枠）" : "（無料枠の可能性）"}`,
      ];
      if (s.models?.length) lines.push("", `選べるモデル: ${s.models.join(" / ")}`);
      lines.push("", s.message);
      if (!s.chrome) lines.push("→ gemini_launch_chrome を実行してください。");
      return text(lines.join("\n"));
    }),
);

server.registerTool(
  "gemini_setup_profile",
  {
    title: "自動化用の Chrome プロファイルを用意する",
    description:
      "Gemini にログイン済みの Chrome プロファイルを、自動化用ディレクトリへ複製する。" +
      "Chrome 136+ が既定プロファイルのデバッグ接続を塞ぐための回避策。" +
      "Google のサービスは複製先でもログインが引き継がれる。実行すると既存の複製は作り直される。",
    inputSchema: {
      src_profile: z.string().optional().describe('複製元プロファイル名（既定 "Profile 1"）。gemini_check が一覧を出す'),
    },
  },
  async ({ src_profile }) =>
    guard(async () => {
      const r = await setupProfile({ srcProfile: src_profile, log });
      return text(
        [
          `✅ 複製しました（${r.size} / Google cookie ${r.cookies} 個）`,
          `  複製元: ${r.srcProfile}`,
          `  複製先: ${r.dst}`,
          "",
          "→ 次に gemini_launch_chrome を実行してください。",
        ].join("\n"),
      );
    }),
);

server.registerTool(
  "gemini_launch_chrome",
  {
    title: "自動化用 Chrome を起動する",
    description:
      "自動化用プロファイルをデバッグポート付きで起動する。普段使いの Chrome とは別ディレクトリなので" +
      "閉じる必要はない。canva プラグインとも別ポート・別ディレクトリなので並走できる。" +
      "すでに待ち受けていれば何もしない。",
    inputSchema: { port: portArg },
  },
  async ({ port = DEFAULT_PORT }) =>
    guard(async () => {
      const r = await launchChrome({ port, log });
      return text(
        r.started
          ? `✅ 起動しました（port ${port} / ${r.version["Browser"] ?? "Chrome"}）`
          : `既に port ${port} で待ち受けています（${r.version["Browser"] ?? "Chrome"}）`,
      );
    }),
);

server.registerTool(
  "gemini_ask",
  {
    title: "Gemini に質問する",
    description:
      "Gemini アプリに 1 往復の質問を投げて、応答テキストを返す。" +
      "**テキスト生成だけが目的なら公式 API のほうが速く壊れない。** " +
      "このツールを使う理由は、アプリ側のモデル（強化版思考モードなど）やアカウントの" +
      "コンテキストを使いたいときに限る。",
    inputSchema: {
      prompt: z.string().describe("質問文"),
      model: z.string().optional().describe('モデル名の一部（例 "Pro", "Flash", "強化版思考"）。省略で現在のまま'),
      wait_sec: z.number().int().optional().describe("応答が伸びなくなるまで待つ最大秒数（既定 120）"),
      port: portArg,
    },
  },
  async ({ prompt, model, wait_sec, port = DEFAULT_PORT }) =>
    guard(async () => {
      const r = await ask({ prompt, model, waitSec: wait_sec ?? 120, port, log });
      if (!r.text) return fail(`❌ 応答を取れませんでした。スクショ: ${r.shotsDir}`);
      return text([`（モデル: ${r.model ?? "?"}）`, "", r.text].join("\n"));
    }),
);

server.registerTool(
  "gemini_generate_image",
  {
    title: "Gemini で画像を生成する（Nano Banana）",
    description:
      "Gemini の「画像を作成」で画像を生成し、保存したパスを返す。生成に 20〜60 秒かかる。" +
      "出力される画像には SynthID の透かしが入る。" +
      "返ってきたパスを Read で開いて、意図した絵になっているか必ず目視すること。",
    inputSchema: {
      prompt: z.string().describe("生成プロンプト。英語のほうが指示が通りやすい"),
      out: z.string().optional().describe("保存先ディレクトリ。~ 展開可（既定 ~/Pictures/gemini）"),
      wait_sec: z.number().int().optional().describe("画像が出るまで待つ最大秒数（既定 180）"),
      port: portArg,
    },
  },
  async ({ prompt, out, wait_sec, port = DEFAULT_PORT }) =>
    guard(async () => {
      const r = await generateImage({ prompt, out, waitSec: wait_sec ?? 180, port, log });
      const lines = [
        `✅ ${r.saved.length} 枚を保存しました`,
        `  プロンプト: ${r.prompt}`,
        "",
        ...r.saved.map((s) => `  ${s.path} (${s.size}, ${s.bytes} B)`),
      ];
      if (r.warnings.length) lines.push("", "⚠️ 警告:", ...r.warnings.map((w) => `  ${w}`));
      lines.push("", `スクショ: ${r.shotsDir}`);
      return text(lines.join("\n"));
    }),
);

server.registerTool(
  "gemini_deep_research",
  {
    title: "Deep Research を回す",
    description:
      "Gemini の Deep Research でテーマを調査し、レポート本文を返す。" +
      "**完了まで 5〜15 分かかる。** 待ち切れなかった場合も Gemini 側では走り続けるので、" +
      "しばらくしてから gemini_deep_research_result で取り出せる。" +
      "長いレポートになるので、out にパスを渡してファイルへ保存するのを勧める。",
    inputSchema: {
      prompt: z.string().describe("調査テーマ"),
      out: z.string().optional().describe("レポートの保存先ファイルパス。~ 展開可"),
      wait_sec: z.number().int().optional().describe("完了を待つ最大秒数（既定 900）"),
      port: portArg,
    },
  },
  async ({ prompt, out, wait_sec, port = DEFAULT_PORT }) =>
    guard(async () => {
      const r = await deepResearch({ prompt, out, waitSec: wait_sec ?? 900, port, log });
      if (!r.done) return text(`⏳ ${r.message}`);
      const head = [
        `✅ 完了（${r.seconds}s / ${r.report.length} 文字）`,
        r.path ? `  保存: ${r.path}` : "  ※ out を渡すとファイルに保存できます",
        "",
      ].join("\n");
      // ファイルに保存したなら本文は冒頭だけ返す（会話を埋めないため）
      return text(head + (r.path ? r.report.slice(0, 2000) + "\n\n…（全文はファイル）" : r.report));
    }),
);

server.registerTool(
  "gemini_deep_research_result",
  {
    title: "できあがった Deep Research のレポートを取り出す",
    description:
      "直近の会話を開き直して、完成しているレポート本文を取り出す。" +
      "gemini_deep_research が待ち切れずに戻ってきたときに使う。",
    inputSchema: {
      out: z.string().optional().describe("レポートの保存先ファイルパス。~ 展開可"),
      title: z.string().optional().describe("会話タイトルの一部で絞る。省略すると上から順に探す"),
      port: portArg,
    },
  },
  async ({ out, title, port = DEFAULT_PORT }) =>
    guard(async () => {
      const r = await latestReport({ out, title, port, log });
      if (!r.report) {
        return fail(
          [
            "❌ レポートを持つ会話が見つかりませんでした。まだ調査中かもしれません。",
            r.titles?.length ? `  見た会話: ${r.titles.join(" / ")}` : "",
          ].join("\n"),
        );
      }
      const head = [
        `${r.done ? "✅ 完了" : "⚠️ 完了の合図は見えませんでした"}（${r.report.length} 文字 / ${r.title ?? "?"}）`,
        r.path ? `  保存: ${r.path}` : "",
        "",
      ].join("\n");
      return text(head + (r.path ? r.report.slice(0, 2000) + "\n\n…（全文はファイル）" : r.report));
    }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
log(`起動しました（CDP port ${DEFAULT_PORT}）`);
