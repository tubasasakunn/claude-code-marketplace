# REFERENCE — canva-image-gen の仕組み・セレクタ・トラブル対応

開発中に判明した事実とハマりどころの記録。UI 変更でスクリプトが壊れたときは、まずここを見る。

---

## アーキテクチャ

```
普段使い Chrome プロファイル(Profile 1, Canvaログイン済み)
        │  canva_setup_profile でコピー（キャッシュ除外）
        ▼
~/Library/Application Support/Google/Chrome-automation/Default
        │  canva_launch_chrome が --remote-debugging-port=9222 で起動
        │  Cookie が復号できなければ canva_login で人が入り直す（下の「6」）
        ▼
   CDP (http://127.0.0.1:9222)
        │  mcp/lib/dreamlab.mjs が connectOverCDP で接続（CLI もこの層を通す）
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

→ 回避策＝プロファイルを**別ディレクトリにコピー**してそれを使う（`canva_setup_profile`）。

**ただしコピーで Cookie が引き継げるとは限らない。** かつては「macOS の Cookie 暗号鍵は Keychain に
あり同一ユーザーなら別ディレクトリでも復号できる」で通っていたが、**Chrome 150 では成立しなくなった**
（2026-08-02 実測）。詳細は下の「6」。

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

### 6. コピーした Cookie が復号できず、ログイン画面に飛ばされる（Chrome 150 / 2026-08-02）

`Profile 1`（canva cookie 33 個）を丸ごとコピーし直しても、Dream Lab を開くと
`https://www.canva.com/ja_jp/login/?redirect=%2Fdream-lab%2F` にリダイレクトされる。
アカウント名入りの「おかえりなさい！→ 続行」が出るので一見ログイン済みに見えるが、
**「続行」を押しても 25 秒待っても遷移しない**（実測）。ページには reCAPTCHA enterprise の
iframe も同居している。

Cookie の**行**はコピーされるので、`host_key LIKE '%canva.com%'` の件数や
`context.cookies()` の数だけ見ていると「ログインしている」と誤判定する。
Chrome の Cookie 暗号化が強化され、複製先プロファイルでは復号できていない。

→ **`canva_login` で自動化用プロファイルに人が一度入り直す。** 一度通せばそのプロファイルに残る。
ログイン判定は cookie 数ではなく、**Dream Lab のプロンプト欄が実在するか**で行うこと。

### 7. タブが 0 枚の Chrome には connectOverCDP できない

起動しっぱなしの Chrome から全タブを閉じると、`/json/version` は応答するのに
`connectOverCDP` が次で落ちる。

```
Protocol error (Browser.setDownloadBehavior): Browser context management is not supported.
```

`/json/list` が 0 件ならこの状態。Playwright が接続時に browser context を初期化できないため。

→ 接続前に `PUT /json/new?about:blank` で空タブを 1 枚作る（`lib/chrome.mjs` の `ensureTarget`）。
`/json/new` は Chrome 111+ で **PUT でないと 405** になる。

### 8. プロファイルを作り直す前に、それを掴んでいる Chrome を落とす

`Chrome-automation` を `rm -rf` してから rsync し直すとき、そのディレクトリで動いている Chrome を
生かしたままにすると、以後その Chrome は CDP に応答しなくなる（`connectOverCDP` が 30s タイムアウト）。
プロセスは生きていて `/json/version` も返すので、原因が分かりにくい。

→ `canva_setup_profile` は先に `pkill -f "user-data-dir=<DST>"` してからコピーする。

### 9. rsync が普段使い Chrome の生きたキャッシュで落ちる

普段の Chrome が動いていると、転送中にキャッシュファイルが消えて rsync が落ちる。

```
error: mkstempat: 'WebStorage/453/CacheStorage/.../.index.XXXX': No such file or directory
error: unexpected end of file
```

→ `WebStorage` `blob_storage` `Crashpad` などキャッシュ系を除外し、**rsync の終了コード 24
（vanished source files）は許容**する。そのうえで成否は転送結果ではなく
**コピー先の Cookies に canva の行が入ったか**で判定する。

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
| 9222 が開かない | プロセスにフラグはあるか確認 → デフォルトプロファイルを使っていないか確認 → コピーを使う |
| 9222 は応答するが接続できない | タブが 0 枚（下の「7」）か、プロファイルを生きたまま作り直した（「8」） |
| ログイン画面に飛ばされる | まず `canva_setup_profile` でコピーを更新。それでも戻らないなら `canva_login`（下の「6」。Chrome 150 ではこちらが必要） |
| プロンプト欄が見つからない | まずログイン画面でないかスクショを見る（`$TMPDIR/canva-mcp-shots/`）。ログイン済みなら UI 変更なので `lib/dreamlab.mjs` の `PROMPT_PLACEHOLDER` を更新 |
| 比率/スタイルが効かない | `role` が変わった可能性。DevTools で role を確認しロケータ修正 |
| 生成が間に合わない | `wait_sec` / `--wait` を増やす（例 120） |
| ダウンロードが保存されない | `connectOverCDP` の download イベントを使用。保存先の書き込み権限を確認 |

---

## 注意

- 自分のアカウントで、Canva の利用規約の範囲内で使うこと。
- UI 変更でロケータが壊れる前提の作り。スクショ（`$TMPDIR/canva-mcp-shots/`）を残しているのは復旧を速くするため。
- **セレクタの正本は `canva/mcp/lib/dreamlab.mjs`。** CLI は同じ lib を呼ぶだけなので、直すのは常に lib 側。
