# REFERENCE — canva-image-gen の仕組み・セレクタ・トラブル対応

開発中に判明した事実とハマりどころの記録。UI 変更でスクリプトが壊れたときは、まずここを見る。

---

## アーキテクチャ

```
普段使い Chrome プロファイル(Profile 1, Canvaログイン済み)
        │  setup_profile.sh でコピー（キャッシュ除外）
        ▼
~/Library/Application Support/Google/Chrome-automation/Default
        │  launch_chrome.sh が --remote-debugging-port=9222 で起動
        ▼
   CDP (http://127.0.0.1:9222)
        │  canva_magic_media.js が connectOverCDP で接続
        ▼
   https://www.canva.com/dream-lab/  をブラウザ操作
```

- **CDP 接続方式**を使う理由 = ログイン済みの実プロファイルにそのまま乗るため。
  Playwright の `launchPersistentContext` で実プロファイルを直接開くと、Chrome の
  プロファイルロックと競合しやすい。起動済み Chrome に `connectOverCDP` で「接続」する方が安定。
- `playwright-core` を使う（`playwright` ではない）。CDP 接続のみでブラウザを自前 DL しないため。

---

## ハマりどころ詳細

### 1. Chrome 136+ がデフォルトプロファイルのデバッグを無効化（最重要）

`--remote-debugging-port` を**デフォルトの user-data-dir** と併用すると、Chrome は
セキュリティ上の理由（マルウェアによる Cookie 窃取対策）でデバッグポートを**開かない**。
プロセスにフラグは付くのに `curl http://127.0.0.1:9222/json/version` が通らない、という症状。

→ 回避策＝プロファイルを**別ディレクトリにコピー**してそれを使う（`setup_profile.sh`）。
コピー時点の Cookie/ログインはそのまま引き継がれる。macOS の Cookie 暗号鍵は Keychain にあり
同一ユーザーなら別ディレクトリでも復号できる。

### 2. プロファイルが複数あり「Default」が存在しないことがある

このユーザー環境では `Default` フォルダが無く、`Profile 1`〜`Profile 8` が存在した。
どれに Canva ログインがあるかは Cookies(SQLite) を見て判定：

```bash
SRC="$HOME/Library/Application Support/Google/Chrome"
cp "$SRC/Profile 1/Cookies" /tmp/ck.db
sqlite3 /tmp/ck.db "SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%canva.com%';"
```

プロファイルの表示名は `Local State` の `profile.info_cache.<dir>.name` で確認できる。
（このケースでは Profile 1 = "開発用" が Canva ログイン濃厚 = canva cookie 30個）

### 3. Cookie 同意バナーがクリックを妨げる

Dream Lab を開くと Cookie バナーが下部に出てボタンクリックを遮ることがある。
スクリプトは起動直後に「すべてのCookieを許可する」等を押して閉じる（`dismissCookie`）。

### 4. アスペクト比メニューの項目は role=option

- 比率トグル（現在値表示）: `<button>` でテキストが `\d+:\d+`、role は実質 combobox（aria-label「縦横比」）。
- 展開後の各比率: **`role="option"`**（button ではない）。
  → `getByRole("option", { name: "9:16", exact: true })` で選ぶ。
  最初 `getByRole("button", {name})` で書いて TimeoutでハマったのはこれがOptionだったため。

### 5. Homebrew Python 3.14 が壊れていて pip/venv 不可

`pyexpat` が libexpat と不整合で `pip` 自体が ImportError。`python3.13 -m venv` も ensurepip 失敗。
→ 健全な **Node.js** に切り替えて解決。本スキルが Node 実装なのはこの経緯による。

---

## 確定セレクタ一覧（2025 時点の Dream Lab）

| 要素 | ロケータ |
|---|---|
| プロンプト入力 | `getByPlaceholder("心に描いたイメージを教えてください")`（textarea） |
| 生成実行 | プロンプト欄で `Enter`（明示的な生成ボタンはアイコンのみ） |
| 比率トグル | `locator("button", { hasText: /^\d+\s*:\s*\d+$/ })` |
| 比率の各項目 | `getByRole("option", { name: "16:9"\|"9:16"\|"1:1"\|"4:3"\|"3:4"\|"2:1", exact: true })` |
| スタイル | `getByRole("button", { name: "スタイル" })` → パネル内ラベルを `getByText(name, {exact:true})` |
| ダウンロード | `getByRole("button", { name: "画像をダウンロード" })`（生成済み画像ごと、クリックで直DL） |

- 新規生成の検知 = 「画像をダウンロード」ボタンの**個数増加**で判定（生成前後で count を比較）。
- 最新画像はギャラリー先頭に並ぶので、新規 N 枚は `dlBtn.nth(0..N-1)`。

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| 9222 が開かない | プロセスにフラグはあるか確認 → デフォルトプロファイルを使っていないか確認 → `setup_profile.sh` のコピーを使う |
| ログインが切れている | `./setup_profile.sh` を再実行してコピーを更新（普段の Chrome で再ログイン後） |
| プロンプト欄が見つからない | UI 変更の可能性。`scripts/shots/` のスクショを見て placeholder 文言を確認し `PROMPT_PLACEHOLDER` を更新 |
| 比率/スタイルが効かない | `role` が変わった可能性。DevTools で role を確認しロケータ修正 |
| 生成が間に合わない | `--wait` を増やす（例 `--wait 120`） |
| ダウンロードが保存されない | `connectOverCDP` の download イベントを使用。保存先の書き込み権限を確認 |

---

## 注意

- 自分のアカウントで、Canva の利用規約の範囲内で使うこと。
- UI 変更でロケータが壊れる前提の作り。スクショ(`shots/`)を残しているのは復旧を速くするため。
