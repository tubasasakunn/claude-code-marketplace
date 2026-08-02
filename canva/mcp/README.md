# canva-mcp

Canva Dream Lab の AI 画像生成を MCP ツールとして出すサーバー。

**Canva の画像生成に公式 API は無い。** ログイン済み Chrome に CDP でつないで画面を操作している。
UI が変われば壊れる前提の作りで、その復旧を速くするために各ステップのスクショを残す。
使い方とハマりどころは [`../skills/canva-image-gen/SKILL.md`](../skills/canva-image-gen/SKILL.md)、
セレクタと事故の記録は [`REFERENCE.md`](../skills/canva-image-gen/REFERENCE.md) が正本。

## 構成

```
mcp/
  server.mjs        MCP サーバー（stdio）。ツール定義と文言だけを持つ
  lib/
    chrome.mjs      プロファイルの複製・起動・死活。CDP の前提を整える層
    dreamlab.mjs    Dream Lab のブラウザ操作。★ セレクタの正本
  bin/start.sh      依存が無ければ入れてから server.mjs を exec する
```

`../.mcp.json` がプラグインの MCP 定義で、`${CLAUDE_PLUGIN_ROOT}/mcp/bin/start.sh` を起動する。
`node_modules` は配らないので、初回起動時に `start.sh` が `npm install` する。

## ツール

| ツール | 役割 |
|---|---|
| `canva_check_chrome` | 接続とログインの死活。未設定ならプロファイル候補を出す |
| `canva_setup_profile` | 普段使いプロファイルを自動化用へ複製 |
| `canva_launch_chrome` | デバッグポート付きで起動 |
| `canva_login` | 自動化用 Chrome で人がログインするのを待つ（人の操作が要る） |
| `canva_generate_image` | プロンプトから 4 枚生成し、保存パスを返す |

## 触るときの約束

- **stdout に何も書かない。** JSON-RPC のチャネルなので、進捗は `process.stderr` へ出す。
  `console.log` を 1 行足すだけでプロトコルが壊れる。
- **セレクタは `lib/dreamlab.mjs` にだけ書く。** CLI（`skills/canva-image-gen/scripts/`）も
  この lib を呼ぶので、二重に持つと片方だけ腐る。
- **ログイン判定に cookie 数を使わない。** 複製したプロファイルでは cookie の行があっても
  復号できず未ログイン扱いになる。判定は Dream Lab のプロンプト欄の実在で行う。

## 手で叩いて確かめる

```bash
cd canva/mcp
printf '%s\n%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"p","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | ./bin/start.sh 2>/dev/null
```

ツール単体を呼ぶなら 3 行目を `tools/call` に差し替える。

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"canva_check_chrome","arguments":{}}}
```

同じ標準入力に複数の `tools/call` を並べると**並行実行される**。
順序が要るもの（起動 → 確認）は 1 回ずつ分けて投げる。
