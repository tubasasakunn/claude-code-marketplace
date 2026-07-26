---
name: canva-image-gen
description: Canva の AI 画像生成（Dream Lab / 旧 Magic Media）を、ログイン済みの普段使い Chrome をブラウザ操作（CDP）して CLI から実行し、画像をダウンロードします。Canva で画像を生成したい・Canva の AI 画像を CLI/自動化したい場合に使用してください。
---

# canva-image-gen

## 概要

Canva の AI 画像生成は**公式 API では提供されていない**。そこで、ログイン済みの普段使い Chrome に
Playwright(CDP) で接続し、Dream Lab（ドリームラボ）をブラウザ操作してプロンプトから画像を生成・
ダウンロードする。比率・スタイル・保存先を CLI オプションで指定できる。

実機検証済み（macOS / Chrome 149 / Node 22）。

## 前提

- macOS、Google Chrome、Node.js 18+
- Canva に**ログイン済み**の Chrome プロファイルがあること

## セットアップ（初回のみ）

```bash
cd <このスキル>/scripts
npm install                       # playwright-core（ブラウザDL不要）
chmod +x setup_profile.sh launch_chrome.sh

# 普段使いプロファイル(既定 "Profile 1")を自動化用にコピー。
# 別プロファイルなら: SRC_PROFILE="Profile 7" ./setup_profile.sh
./setup_profile.sh
```

> **なぜコピーが要るか** → Chrome 136+ はデフォルトプロファイルへの `--remote-debugging-port` を
> 無効化する。コピーした別ディレクトリを使って回避する。詳細は [REFERENCE.md](REFERENCE.md)。

## 使い方

```bash
cd <このスキル>/scripts
./launch_chrome.sh                # 自動化用Chromeをデバッグ起動（普段のChromeは閉じなくてOK）
node canva_magic_media.js "巨大な鯨が雲海を泳ぐ, 朝焼け, 油彩風" --ratio 9:16 --out ~/Pictures/canva
```

### オプション

| オプション | 説明 | 既定 |
|---|---|---|
| `--ratio <比率>` | `16:9 / 9:16 / 1:1 / 4:3 / 3:4 / 2:1` | 変更しない |
| `--style <名前>` | スタイルパネルの日本語ラベル（例: `写真`, `アニメ`） | 変更しない |
| `--out <パス>` | 保存先ディレクトリ（`~` 展開可） | `scripts/output` |
| `--wait <秒>` | 生成完了の最大待ち秒数 | `75` |

- 1プロンプトあたり4枚生成され、保存先に `NN_<プロンプト>.jpg` で保存される。
- 各ステップのスクショは `scripts/shots/` に残る（デバッグ用）。

## 仕組み（要約）

1. `setup_profile.sh` … 普段使いプロファイルを `~/Library/Application Support/Google/Chrome-automation/Default` へコピー（キャッシュ除外）。
2. `launch_chrome.sh` … そのコピーを `--remote-debugging-port=9222` で起動。
3. `canva_magic_media.js` … CDP 接続 → Dream Lab を開く → 比率/スタイル設定 → プロンプト入力 → Enter 生成 → 「画像をダウンロード」で保存。

## ハマりどころ（必ず読む）

- **デバッグポートが開かない** → Chrome 136+ のデフォルトプロファイル保護。プロファイルをコピーして使う（本スキルは対応済み）。
- **Cookie バナーが操作を妨げる** → スクリプトが起動時に自動で閉じる。
- **比率の選択肢は `role="button"` ではなく `role="option"`** → セレクタ注意。
- **複数プロファイルがあり、どれに Canva ログインがあるか不明** → Cookies(SQLite) の `host_key LIKE '%canva.com%'` で特定。
- **Homebrew Python が壊れていて pip 不可** → Node 版を使う（本スキルは Node）。

詳細・正確なセレクタ・トラブル対応は [REFERENCE.md](REFERENCE.md) を参照。

## 終了条件

- [ ] `npm install` 済み & `setup_profile.sh` でプロファイルコピー済み
- [ ] `launch_chrome.sh` で 9222 が待ち受け
- [ ] `node canva_magic_media.js "..."` で画像が保存先に出力される
