---
name: canva-image-gen
description: Canva の AI 画像生成（Dream Lab / 旧 Magic Media）を、ログイン済み Chrome をブラウザ操作（CDP）して実行し、画像をダウンロードします。MCP ツール（canva_check_chrome / canva_setup_profile / canva_launch_chrome / canva_login / canva_generate_image）として呼べます。Canva で画像を生成したい・Canva の AI 画像を自動化したい場合に使用してください。
---

# canva-image-gen

## 概要

Canva の AI 画像生成は**公式 API では提供されていない**。そこで、Canva にログイン済みの Chrome に
Playwright(CDP) で接続し、Dream Lab（ドリームラボ）をブラウザ操作してプロンプトから画像を生成・
ダウンロードする。

**通常は MCP ツールを使う。** CLI（`scripts/canva_magic_media.js`）も残してあるが、
ロジックの正本は `canva/mcp/lib/` で、CLI はそれを呼ぶ薄いラッパにすぎない。

実機検証済み（macOS / Chrome 150 / Node 22 / playwright-core 1.62）。

## 前提

- macOS、Google Chrome、Node.js 18+
- Canva のアカウント（ログイン操作を 1 回、人がやる必要がある）

## MCP ツール

| ツール | 何をするか |
|---|---|
| `canva_check_chrome` | 接続とログインの死活。未設定ならどのプロファイルに Canva の cookie があるか候補を出す |
| `canva_setup_profile` | 普段使いプロファイルを自動化用ディレクトリへ複製する |
| `canva_launch_chrome` | 自動化用プロファイルをデバッグポート付きで起動する |
| `canva_login` | 自動化用 Chrome で Dream Lab を開き、人がログインし終えるのを待つ |
| `canva_generate_image` | プロンプトから 4 枚生成し、保存したパスを返す |

### 手順

```
canva_check_chrome        # 状態を見る。ここで次にやることが分かる
  ↓ プロファイルが無ければ
canva_setup_profile       # src_profile は check が出した候補から選ぶ
  ↓
canva_launch_chrome
  ↓ ログインが通っていなければ
canva_login               # ★ ユーザーに Chrome で入ってもらう。人の操作が要る
  ↓
canva_generate_image      # prompt / ratio / style / out / wait_sec
```

**`canva_login` は人の手が要る。** 呼ぶ前にユーザーへ「Chrome が開くのでログインしてほしい」と伝える。
黙って呼ぶと、誰も操作しないまま数分待って失敗する。

### canva_generate_image の引数

| 引数 | 説明 | 既定 |
|---|---|---|
| `prompt` | 生成プロンプト（英語のほうが通りやすい） | 必須 |
| `ratio` | `16:9 / 9:16 / 1:1 / 4:3 / 3:4 / 2:1` | 変更しない |
| `style` | スタイルパネルの日本語ラベル（例 `写真`, `アニメ`） | 変更しない |
| `out` | 保存先ディレクトリ（`~` 展開可） | `~/Pictures/canva` |
| `wait_sec` | 生成完了の最大待ち秒数 | 75 |

- 1 プロンプトあたり **4 枚**生成され、`NN_<プロンプト>.jpg` で保存される。
  返ってきたパスを Read で開いて、最良の 1 枚を選ぶ。
- 各ステップのスクショは `$TMPDIR/canva-mcp-shots/` に残る（`CANVA_MCP_SHOTS_DIR` で変更可）。

## ログインの厄介さ（最重要）

**プロファイルをコピーしただけでは、ログインは引き継げないことがある。**

`canva_setup_profile` は普段使いプロファイルの cookie ごと複製する。cookie の行は確かに移るし、
`canva_check_chrome` も「ログイン OK」と言う。それでも Dream Lab を開くと
`/ja_jp/login/?redirect=/dream-lab/` に飛ばされ、「おかえりなさい！→ 続行」が出る。
この「続行」は押しても戻らない（25 秒待っても遷移しないことを確認済み）。

Chrome の cookie 暗号化が強化され、複製先のプロファイルでは復号できなくなっているため。
REFERENCE.md にあった「同一ユーザーなら別ディレクトリでも復号できる」は、Chrome 150 では成立しない。

**このときは `canva_login` で、自動化用プロファイルに人が一度入り直す。** 一度通せばログインは残る。

## CLI（フォールバック）

MCP が使えない文脈（素の shell、他リポジトリからの呼び出し）では CLI を使う。

```bash
cd <このスキル>/scripts
./launch_chrome.sh    # 自動化用 Chrome をデバッグ起動（普段の Chrome は閉じなくてよい）
node canva_magic_media.js "巨大な鯨が雲海を泳ぐ, 朝焼け, 油彩風" --ratio 9:16 --out ~/Pictures/canva
```

オプションは `--ratio` `--style` `--out` `--wait` で、MCP の引数と同じ。
依存は `canva/mcp` 側に入るので、`mcp/bin/start.sh` を一度通してから使う。

## 仕組み（要約）

```
普段使い Chrome プロファイル（Canva ログイン済み）
      │  canva_setup_profile で複製（キャッシュ除外）
      ▼
~/Library/Application Support/Google/Chrome-automation/Default
      │  canva_launch_chrome が --remote-debugging-port=9222 で起動
      │  cookie が復号できなければ canva_login で人が入り直す
      ▼
   CDP (http://127.0.0.1:9222)
      │  mcp/lib/dreamlab.mjs が connectOverCDP で接続
      ▼
   https://www.canva.com/dream-lab/ をブラウザ操作
```

## ハマりどころ（必ず読む）

- **コピーした cookie が復号できずログイン画面に飛ぶ** → `canva_login` で入り直す（上記）。
- **タブが 0 枚の Chrome には接続できない** → `Browser.setDownloadBehavior` が
  「Browser context management is not supported」で落ちる。起動しっぱなしで全タブを閉じられた
  Chrome がこれ。lib が接続前に空タブを 1 枚作って回避している。
- **デバッグポートが開かない** → Chrome 136+ のデフォルトプロファイル保護。コピーを使う（対応済み）。
- **Cookie バナー / セッション再開ダイアログが操作を妨げる** → lib が自動で閉じる。
- **比率の選択肢は `role="button"` ではなく `role="option"`** → セレクタ注意。
- **どのプロファイルに Canva ログインがあるか不明** → `canva_check_chrome` が cookie 数で候補を出す。

詳細・正確なセレクタ・トラブル対応は [REFERENCE.md](REFERENCE.md) を参照。

## 終了条件

- [ ] `canva_check_chrome` が「Chrome 待ち受け中／Canva ログイン OK」を返す
- [ ] `canva_generate_image` が画像を保存し、そのパスを返す
- [ ] 保存された画像を Read で開いて、意図した絵になっていることを目視した
