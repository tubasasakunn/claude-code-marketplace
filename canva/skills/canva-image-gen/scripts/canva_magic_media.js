#!/usr/bin/env node
/**
 * Canva Dream Lab の画像生成 CLI。
 *
 * **ロジックの正本は `canva/mcp/lib/dreamlab.mjs`**（MCP ツールと共用）。
 * ここは引数を受けて呼ぶだけの薄い層で、セレクタや待ち方をここに書かない。
 * UI 変更で壊れたときに直すのは lib のほうで、そうしないと MCP 側と CLI 側で
 * セレクタが二重管理になり、片方だけ腐る。
 *
 * 前提:
 *   - 自動化用 Chrome がデバッグ起動済み & Canva ログイン済み
 *     （MCP なら canva_launch_chrome → canva_login、手動なら ./launch_chrome.sh）
 *   - canva/mcp で依存が入っていること（`../../../mcp/bin/start.sh` を一度通せば入る）
 *
 * 使い方:
 *   node canva_magic_media.js "ネオン街を歩く柴犬, 写真風"
 *   node canva_magic_media.js "..." --ratio 9:16 --style 写真 --out ~/Pictures/canva --wait 120
 *
 * オプション:
 *   --ratio  <比率>   16:9 | 9:16 | 1:1 | 4:3 | 3:4 | 2:1   (既定: 変更しない)
 *   --style  <名前>   スタイルパネルに表示される日本語ラベル（例: 写真, アニメ）
 *   --out    <パス>   保存先ディレクトリ（既定: ./output）
 *   --wait   <秒>     生成完了の最大待ち秒数（既定: 75）
 */
const path = require("path");

const LIB = path.join(__dirname, "../../../mcp/lib/dreamlab.mjs");

function parseArgs(argv) {
  const opts = { ratio: null, style: null, out: null, wait: 75 };
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
  return opts;
}

(async () => {
  const opts = parseArgs(process.argv.slice(2));
  if (!opts.prompt) {
    console.error(
      '使い方: node canva_magic_media.js "プロンプト" [--ratio 1:1] [--style 写真] [--out <dir>] [--wait 90]',
    );
    process.exit(1);
  }

  const { generate } = await import(LIB);
  const r = await generate({
    prompt: opts.prompt,
    ratio: opts.ratio,
    style: opts.style,
    out: opts.out || path.join(__dirname, "output"),
    waitSec: opts.wait,
    log: (m) => console.log(`→ ${m}`),
  });

  for (const s of r.saved) console.log(`  ✅ ${s.path} (${s.bytes} B)`);
  for (const w of r.warnings) console.log(`  ⚠️ ${w}`);
  console.log(`→ 完了: ${r.saved.length}/${r.expected} 枚を ${r.outDir} に保存`);
  console.log(`  スクショ: ${r.shotsDir}`);
})().catch((e) => {
  console.error(`✗ ${e.message}`);
  process.exit(1);
});
