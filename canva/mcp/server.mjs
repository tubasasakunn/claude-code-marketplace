#!/usr/bin/env node
/**
 * canva-mcp — Canva Dream Lab の AI 画像生成を MCP ツールとして出す。
 *
 * Canva の画像生成に公式 API は無いので、ログイン済み Chrome に CDP でつないで
 * 画面を操作する。したがって次の 3 つが前提になる。
 *   1. 普段使いの Chrome プロファイルが Canva にログイン済みであること
 *   2. そのコピーが自動化用ディレクトリにあること（canva_setup_profile）
 *   3. コピーがデバッグポート付きで起動していること（canva_launch_chrome）
 *
 * stdout は JSON-RPC のチャネルなので、進捗ログは必ず stderr に出す。
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import {
  DEFAULT_PORT,
  detectCanvaProfile,
  isAlive,
  launchChrome,
  profileExists,
  setupProfile,
} from "./lib/chrome.mjs";
import { VALID_RATIOS, checkLogin, generate, waitForLogin } from "./lib/dreamlab.mjs";

const log = (msg) => process.stderr.write(`[canva-mcp] ${msg}\n`);

const text = (s) => ({ content: [{ type: "text", text: s }] });
const fail = (s) => ({ content: [{ type: "text", text: s }], isError: true });

async function guard(fn) {
  try {
    return await fn();
  } catch (e) {
    return fail(`❌ ${e.message}`);
  }
}

const server = new McpServer({ name: "canva-mcp", version: "1.0.0" });

server.registerTool(
  "canva_check_chrome",
  {
    title: "Canva 接続の状態を見る",
    description:
      "自動化用 Chrome がデバッグポートで待ち受けているか、Canva のログインが生きているかを確認する。" +
      "画像を生成する前にこれを通す。プロファイル未作成なら、どの Chrome プロファイルに Canva の" +
      "ログインがあるかの候補も返す。",
    inputSchema: {
      port: z.number().int().optional().describe(`CDP ポート（既定 ${DEFAULT_PORT}）`),
    },
  },
  async ({ port = DEFAULT_PORT }) =>
    guard(async () => {
      const lines = [];
      const hasProfile = profileExists();
      lines.push(`自動化用プロファイル: ${hasProfile ? "あり" : "なし"}`);

      if (!hasProfile) {
        const candidates = await detectCanvaProfile();
        if (candidates.length) {
          lines.push("", "Canva の cookie を持つプロファイル（多い順）:");
          for (const c of candidates.slice(0, 5)) {
            lines.push(`  ${c.profile}${c.label ? `（${c.label}）` : ""} … cookie ${c.canvaCookies} 個`);
          }
          lines.push("", `→ canva_setup_profile を src_profile="${candidates[0].profile}" で実行してください。`);
        } else {
          lines.push("→ Chrome のプロファイルから Canva の cookie を見つけられませんでした。");
        }
        return text(lines.join("\n"));
      }

      const state = await checkLogin({ port });
      lines.push(`Chrome (port ${port}): ${state.chrome ? state.browser || "待ち受け中" : "起動していない"}`);
      lines.push(`Canva ログイン: ${state.loggedIn ? `OK（cookie ${state.cookies} 個）` : "なし"}`);
      lines.push("", state.message);
      if (!state.chrome) lines.push("→ canva_launch_chrome を実行してください。");
      return text(lines.join("\n"));
    }),
);

server.registerTool(
  "canva_setup_profile",
  {
    title: "自動化用の Chrome プロファイルを用意する",
    description:
      "普段使いの Chrome プロファイルを自動化用ディレクトリへコピーする。初回と、Canva の" +
      "ログインが切れて普段の Chrome で入り直したあとに実行する。" +
      "Chrome 136+ が既定プロファイルのデバッグ接続を塞ぐための回避策で、コピー時点の" +
      "ログイン状態がそのまま引き継がれる。実行すると既存のコピーは作り直される。",
    inputSchema: {
      src_profile: z
        .string()
        .optional()
        .describe('コピー元プロファイル名（既定 "Profile 1"）。canva_check_chrome が候補を出す'),
    },
  },
  async ({ src_profile }) =>
    guard(async () => {
      const r = await setupProfile({ srcProfile: src_profile, log });
      return text(
        [
          `✅ プロファイルをコピーしました（${r.size} / Canva cookie ${r.cookies} 個）`,
          `  コピー元: ${r.srcProfile}`,
          `  コピー先: ${r.dst}`,
          "",
          "→ 次に canva_launch_chrome を実行してください。",
        ].join("\n"),
      );
    }),
);

server.registerTool(
  "canva_launch_chrome",
  {
    title: "自動化用 Chrome を起動する",
    description:
      "自動化用プロファイルをデバッグポート付きで起動する。普段使いの Chrome とは別ディレクトリなので、" +
      "普段の Chrome を閉じる必要はない。すでに待ち受けていれば何もしない。",
    inputSchema: {
      port: z.number().int().optional().describe(`CDP ポート（既定 ${DEFAULT_PORT}）`),
    },
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
  "canva_login",
  {
    title: "自動化用 Chrome で Canva にログインする",
    description:
      "自動化用 Chrome で Dream Lab を開き、人がログインし終えるのを待つ。" +
      "canva_setup_profile でプロファイルをコピーしてもログイン画面に飛ばされるとき" +
      "（Chrome の cookie 暗号化により、複製したプロファイルでは cookie を復号できないことがある）に使う。" +
      "呼ぶと Chrome の画面が前面に出るので、ユーザーに手で入ってもらう必要がある。" +
      "一度通せば、そのプロファイルにログインが残る。",
    inputSchema: {
      timeout_sec: z.number().int().optional().describe("ログイン完了を待つ最大秒数（既定 300）"),
      port: z.number().int().optional().describe(`CDP ポート（既定 ${DEFAULT_PORT}）`),
    },
  },
  async ({ timeout_sec, port = DEFAULT_PORT }) =>
    guard(async () => {
      const r = await waitForLogin({ port, timeoutSec: timeout_sec ?? 300, log });
      if (!r.loggedIn) {
        return fail(
          [
            `❌ ${r.seconds} 秒待ちましたがログインを確認できませんでした。`,
            `  現在の URL: ${r.url}`,
            "  開いている Chrome で Canva にログインしてから、もう一度実行してください。",
          ].join("\n"),
        );
      }
      return text(`✅ ログインを確認しました（${r.seconds}s）。canva_generate_image を実行できます。`);
    }),
);

server.registerTool(
  "canva_generate_image",
  {
    title: "Canva で画像を生成する",
    description:
      "Dream Lab にプロンプトを投げて画像を生成し、保存先へダウンロードする。" +
      "1 プロンプトにつき 4 枚生成されるので、返ってきたパスを読んで最良の 1 枚を選ぶ。" +
      "生成には数十秒かかる。事前に canva_check_chrome で接続を確かめておくこと。",
    inputSchema: {
      prompt: z.string().describe("生成プロンプト。英語のほうが指示が通りやすい"),
      ratio: z.enum(VALID_RATIOS).optional().describe("アスペクト比。省略すると Canva 側の現在値のまま"),
      style: z.string().optional().describe('スタイルパネルの日本語ラベル（例 "写真", "アニメ"）'),
      out: z.string().optional().describe("保存先ディレクトリ。~ 展開可（既定 ~/Pictures/canva）"),
      wait_sec: z.number().int().optional().describe("生成完了を待つ最大秒数（既定 75）"),
      port: z.number().int().optional().describe(`CDP ポート（既定 ${DEFAULT_PORT}）`),
    },
  },
  async ({ prompt, ratio, style, out, wait_sec, port = DEFAULT_PORT }) =>
    guard(async () => {
      const r = await generate({ prompt, ratio, style, out, waitSec: wait_sec ?? 75, port, log });
      const lines = [
        `✅ ${r.saved.length}/${r.expected} 枚を保存しました`,
        `  プロンプト: ${r.prompt}`,
        `  比率: ${r.ratio ?? "指定なし"} / スタイル: ${r.style ?? "指定なし"}`,
        "",
        ...r.saved.map((s) => `  ${s.path} (${s.bytes} B)`),
      ];
      if (r.warnings.length) {
        lines.push("", "⚠️ 警告:", ...r.warnings.map((w) => `  ${w}`));
      }
      lines.push("", `スクショ: ${r.shotsDir}`);
      return text(lines.join("\n"));
    }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
log(`起動しました（CDP port ${DEFAULT_PORT}）`);
