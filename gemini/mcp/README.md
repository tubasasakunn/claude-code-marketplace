# gemini-mcp

Gemini アプリの機能を MCP ツールとして出すサーバー。

**相手にするのはアプリ側にしか無い機能**（Nano Banana の画像生成、Deep Research、Canvas）。
テキスト生成だけなら公式 API のほうが速く壊れないので、そちらを使う。
使い方は [`../skills/gemini-browser/SKILL.md`](../skills/gemini-browser/SKILL.md)、
セレクタと事故の記録は [`REFERENCE.md`](../skills/gemini-browser/REFERENCE.md) が正本。

## 構成

```
mcp/
  server.mjs        MCP サーバー（stdio）。ツール定義と文言だけを持つ
  lib/
    chrome.mjs      プロファイルの複製・起動・死活。canva プラグインとほぼ同じ実装
    gemini.mjs      Gemini のブラウザ操作。★ セレクタの正本
  bin/start.sh      依存が無ければ入れてから server.mjs を exec する
```

`../.mcp.json` がプラグインの MCP 定義。`node_modules` は配らないので、初回起動時に
`start.sh` が `npm install` する。

## ツール

| ツール | 役割 |
|---|---|
| `gemini_check` | 接続・ログイン・アカウント・モデル。未設定ならプロファイル一覧 |
| `gemini_setup_profile` | ログイン済みプロファイルを自動化用へ複製 |
| `gemini_launch_chrome` | デバッグポート付きで起動（既定 9223） |
| `gemini_ask` | 1 往復の質問。モデル切替つき |
| `gemini_generate_image` | 画像生成（Nano Banana） |
| `gemini_deep_research` | Deep Research を回す（5〜15 分） |
| `gemini_deep_research_result` | できあがったレポートを後から取り出す |

## 触るときの約束

- **stdout に何も書かない。** JSON-RPC のチャネルなので、進捗は `process.stderr` へ。
- **セレクタは `lib/gemini.mjs` にだけ書く。**
- **画像はダウンロードボタンから取らない。** canvas 経由が唯一通る（REFERENCE の「1」）。
- **Deep Research の完了を日本語で判定しない。** 開始直後に「リサーチが完了したらお知らせします」が
  出るので誤爆する。英語の `completed your research` ＋ 進行表示なし ＋ レポート長で判定する。
- **`lib/chrome.mjs` は canva プラグインと双子。** どちらかを直したらもう片方も見る。

## 手で叩いて確かめる

```bash
cd gemini/mcp
printf '%s\n%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"p","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | ./bin/start.sh 2>/dev/null
```

同じ標準入力に複数の `tools/call` を並べると**並行実行される**。順序が要るものは分けて投げる。
