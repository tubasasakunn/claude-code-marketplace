# REFERENCE — gemini-browser の仕組み・セレクタ・トラブル対応

実測で判明した事実の記録（2026-08-02 / Chrome 150 / playwright-core 1.62 / Gemini 有料枠）。
UI 変更で壊れたときは、まずここを見る。

---

## アーキテクチャ

```
Gemini にログイン済みの Chrome プロファイル（例: Profile 7）
        │  gemini_setup_profile で複製（キャッシュ除外）
        ▼
~/Library/Application Support/Google/Chrome-gemini/Default
        │  gemini_launch_chrome が --remote-debugging-port=9223 で起動
        ▼
   CDP (http://127.0.0.1:9223)
        │  mcp/lib/gemini.mjs が connectOverCDP で接続
        ▼
   https://gemini.google.com/app をブラウザ操作
```

- **Canva プラグインと並走できる。** 複製先もポートも別（Canva は `Chrome-automation` / 9222）。
- `mcp/lib/chrome.mjs` は **canva プラグインとほぼ同じ実装**。プラグインを独立して配れるように
  共有せず複製している。**Chrome まわりの事故の対処は両方に効くので、片方を直したらもう片方も見る。**

### Canva との決定的な違い

**Google 自身のサービスは、プロファイルを複製しただけでログインが引き継がれる。**
Canva では cookie の行が移っても復号できず、`canva_login` で人が入り直す必要があった。
Gemini ではそれが要らない（Profile 7 の複製で `wakaikitubasa@gmail.com` のまま使えた）。

---

## ハマりどころ詳細

### 1. 画像はダウンロードボタンから取り出せない（最重要）

生成画像の `img` は `blob:https://gemini.google.com/...` を指す。取り出そうとすると次の順に失敗する。

| 試したこと | 結果 |
|---|---|
| `getByRole("button", {name:/ダウンロード/})` をクリック | 「フルサイズでダウンロード」が出るが、これは**スナックバー通知**（`EXTENDED-SNACKBAR`）でクリック対象がない |
| そのまま `waitForEvent("download")` | タイムアウト。イベントが発火しない |
| `~/Downloads` を確認 | 落ちていない |
| ページ内で `fetch(blobUrl)` | `TypeError: Failed to fetch`（revoke 済み） |

→ **描画済みの img を canvas に写して `toDataURL` で取る。**

```js
const dataUrl = await img.evaluate((e) => {
  const c = document.createElement("canvas");
  c.width = e.naturalWidth; c.height = e.naturalHeight;
  c.getContext("2d").drawImage(e, 0, 0);
  return c.toDataURL("image/png");
});
```

blob URL は同一オリジンなので canvas が汚染されず、これが通る。取得できたのは 1024x559。

**Canva の実装は流用できない。** あちらはダウンロードボタンと `download` イベントが素直に動く。

### 2. Deep Research は 2 段構え

プロンプトを送るとまず**リサーチ計画**が出るだけで、調査は始まらない。
`リサーチを開始` ボタンを押して初めて走る。押し忘れると永久に完了しない。

完了の合図は **`I've completed your research.`**（日本語 UI でもこの英文が出る）。

### 3. Deep Research のレポートは model-response に無い

完走後も `model-response` の innerText は **127 文字程度**（完了メッセージとカードのみ）。
本文は右側の**イマーシブパネル**に出る。

```
[class*=immersive]   → 32,256 文字（レポート全文）
message-content      → 9,139 文字（部分）
model-response       → 127 文字（完了メッセージだけ）
```

`model-response` だけを監視していると「進捗ゼロ」と誤判定する。実際、完走済みのものを
15 分間空回りで監視した。

**レポートには調査過程の実況が混ざる**（「いよいよ大詰めです！」「最初の調査で多くの情報が
得られました」など）。そのまま流用しない。

### 4. モデルメニューは Angular Material ではない

`.cdk-overlay-container` にも `[role=menuitemradio]` にも入らない。実際の構造は独自要素。

```
DIV.container > DIV.popover-menu > GEM-MENU[role=menu] > GEM-MENU-ITEM[role=menuitem]
                                                       > GEM-MENU-ITEM-CONTENT > DIV.label-container > SPAN.label
```

→ `gem-menu [role="menuitem"]` で取る。各項目の innerText は「名前\n説明\nNew」なので 1 行目を使う。

**一方でツールメニュー（「+」＝アップロードとツール）は `.cdk-overlay-container` に入る。**
同じアプリ内で実装が混在しているので、片方のやり方をもう片方に当てない。

### 5. モデルボタンは aria-label で当てる

`button[aria-label*="モード選択ツール"]`。aria-label は
`モード選択ツールを開く（現在のモデル: Pro）` の形で、**閉じ括弧が全角**。
`/現在のモデル:\s*(.+?)\s*\)?$/` のように半角 `\)` で書くと「Pro）」まで取ってしまう。
`/現在のモデル:\s*([^)）]+)/` とする。

### 6. 応答テキストには見出しが混ざる

`model-response` の innerText は `Gemini の回答\n\n本文` の形。先頭の見出しを落とす。

### 7. ログイン判定に cookie 数を使わない

cookie が何個あろうと、Gemini 側がログイン画面を出すことはある。
判定は **プロンプト欄（`rich-textarea [contenteditable="true"]`）の実在**で行う。

### 8. アカウント判定は「@ を含む aria-label」だけを見る

`[aria-label*="Google アカウント"]` で拾うと、アカウント選択画面の
**「Google アカウント ヘルプセンターを開く」** というヘルプリンクにマッチして誤検知する。
実際にこれでアカウント切り替えの完了を誤判定した。

あわせて、URL でページを判定するときは `includes("gemini.google.com")` を使わない。
アカウント選択画面の URL は `accounts.google.com/AccountChooser?continue=https%3A%2F%2Fgemini.google.com%2Fapp`
で、**continue パラメータに gemini が入る**。`new URL(url).hostname` で見る。

### 9. タブが 0 枚の Chrome には接続できない

`/json/version` は応答するのに `connectOverCDP` が
`Protocol error (Browser.setDownloadBehavior): Browser context management is not supported.` で落ちる。
接続前に `PUT /json/new?about:blank` で空タブを 1 枚作る（`lib/chrome.mjs` の `ensureTarget`）。

### 10. 会話履歴の「直近」は目当てのものとは限らない

`gemini_deep_research_result` が「直近の会話」を無条件に開くと、画像生成を挟んだ場合に
そちらを開いてしまう。**レポートを持つ会話を上から順に探す**（`title` で絞れる）。

---

## 確定セレクタ一覧（2026-08 時点）

| 要素 | ロケータ |
|---|---|
| プロンプト入力 | `rich-textarea [contenteditable="true"]` |
| 送信 | プロンプト欄で `Enter` |
| 入力（fill は効かない） | `page.keyboard.insertText(prompt)` |
| ツールメニュー | `getByRole("button", { name: "アップロードとツール" })` |
| ツールの各項目 | `getByText("画像を作成"\|"Canvas"…, { exact: true })` |
| 奥のツール | 先に `getByText("その他のツール")` → `Deep Research` 等 |
| モデルボタン | `button[aria-label*="モード選択ツール"]` |
| モデルの各項目 | `gem-menu [role="menuitem"]` |
| リサーチ開始 | `getByRole("button", { name: /リサーチを開始/ })` |
| リサーチ完了 | `getByText(/completed your research/i)` |
| レポート本文 | `[class*=immersive]` |
| 応答本文 | `model-response`（先頭の「Gemini の回答」を落とす） |
| サイドバー | `getByRole("button", { name: "サイドバーを開く" })` |
| 会話一覧 | `[data-test-id="conversation"], .conversation-title` |

### ツールの階層

```
アップロードとツール
├ ファイルをアップロード / ドライブから追加 / その他のアップロード
├ 画像を作成          ← Nano Banana
├ 動画を作成          ← Veo（未検証）
├ 音楽を作成（New）    ← 未検証
├ Canvas             ← 未検証
└ その他のツール
   ├ Deep Research
   ├ ガイド付き学習     ← 未検証
   ├ パーソナル インテリジェンス ← 未検証
   └ Labs             ← 未検証
```

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| 9223 が開かない | Chrome 136+ の既定プロファイル保護。複製を使う（対応済み） |
| 9223 は応答するが接続できない | タブが 0 枚（上の「9」）か、プロファイルを生きたまま作り直した |
| プロンプト欄が無い | ログイン画面の可能性。スクショ（`$TMPDIR/gemini-mcp-shots/`）を見る |
| 画像が取れない | ダウンロード導線を疑わず canvas 経由か確認（上の「1」） |
| Deep Research が終わらない | 「リサーチを開始」を押せているか（上の「2」）。完了済みなら `gemini_deep_research_result` |
| レポートが空 | `model-response` を見ていないか（上の「3」）。イマーシブパネルを見る |
| モデルが切り替わらない | `gem-menu [role=menuitem]` で当てているか（上の「4」） |

---

## 注意

- 自分のアカウントで、Google の利用規約の範囲内で使うこと。
- UI 変更でロケータが壊れる前提の作り。スクショ（`$TMPDIR/gemini-mcp-shots/`）を残しているのは
  復旧を速くするため。
- **セレクタの正本は `gemini/mcp/lib/gemini.mjs`。** 直すのは常にそこ。
