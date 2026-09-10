---
name: gemini-browser
description: Gemini アプリ限定の機能（Nano Banana の画像生成、Deep Research、モデル切替）を、ログイン済み Chrome のブラウザ操作（CDP）で回します。MCP ツール（gemini_check / gemini_setup_profile / gemini_launch_chrome / gemini_ask / gemini_generate_image / gemini_deep_research / gemini_deep_research_result）として呼べます。Gemini で画像を作りたい・Deep Research を回したい場合に使用してください。テキスト生成だけなら公式 API を使ってください。
---

# gemini-browser

## いつ使うか。いつ使わないか

**使わない場合が先。テキスト生成だけなら公式 API を使う。**
Gemini には公式 API があり、そちらのほうが速く、壊れず、規約上も素直に使える。
それでもブラウザ操作を選ぶ理由は、**アプリ側にしか無い機能**を使いたいときに限る。

| やりたいこと | 手段 |
|---|---|
| テキスト生成・要約・分類 | **公式 API**（このスキルではない） |
| Nano Banana で画像を作る | このスキル |
| Deep Research でレポートを作る | このスキル |
| 強化版思考モードなどアプリ限定のモデルを使う | このスキル |

Google は自動化に厳しい。**規約上のリスクとアカウント制限の可能性を承知のうえで、自分の
アカウントの範囲で使うこと。** 一括処理や連投はしない。

実機検証済み（macOS / Chrome 150 / Node 22 / playwright-core 1.62 / Gemini 有料枠）。

## MCP ツール

| ツール | 何をするか |
|---|---|
| `gemini_check` | 接続・ログイン・アカウント・モデルを見る。未設定なら Chrome プロファイル一覧を返す |
| `gemini_setup_profile` | Gemini にログイン済みのプロファイルを自動化用へ複製する |
| `gemini_launch_chrome` | 複製をデバッグポート付きで起動する（既定 9223） |
| `gemini_ask` | 1 往復の質問。`model` でモデルを切り替えられる |
| `gemini_generate_image` | 画像を生成して保存する（Nano Banana） |
| `gemini_deep_research` | Deep Research を回してレポートを返す（5〜15 分） |
| `gemini_deep_research_result` | できあがったレポートを後から取り出す |

### 手順

```
gemini_check              # 状態を見る。次にやることが分かる
  ↓ プロファイルが無ければ
gemini_setup_profile      # src_profile は check が出した一覧から選ぶ
  ↓
gemini_launch_chrome
  ↓
gemini_generate_image / gemini_deep_research / gemini_ask
```

**canva プラグインと並走できる。** 複製先（`Chrome-gemini`）もポート（9223）も別なので、
Canva 用の Chrome を落とさずに使える。

### モデル

`gemini_check` が実際に選べる一覧を返す。検証時点では次の 4 つ。

```
3.5 Flash-Lite / 3.6 Flash / 3.1 Pro / 強化版思考モード
```

`gemini_ask` の `model` は部分一致でよい（`"Flash"`, `"強化版思考"` など）。

## Nano Banana（画像生成）

```
gemini_generate_image(prompt="...", out="~/Pictures/gemini")
```

- 生成に 20〜60 秒。1 リクエストで 1 枚のことが多い
- 出力は概ね 1024x559。**SynthID の透かしが入る**
- **保存されたパスを Read で開いて目視すること。** 意図と違う絵が出ることはよくある

## Deep Research

```
gemini_deep_research(prompt="調べたいテーマ", out="~/research/report.md")
```

- **5〜15 分かかる。** 待ち切れずに戻ってきても Gemini 側では走り続けるので、
  しばらくしてから `gemini_deep_research_result` で取り出す
- レポートは数万字になる。`out` を渡してファイルへ落とし、会話に全文を貼らない
- **レポート本文にリサーチ過程の実況が混ざる**（「いよいよ大詰めです！」など）。
  そのまま記事や資料に流用せず、必要な部分だけ抜くこと

## ハマりどころ（必ず読む）

- **画像はダウンロードボタンから取れない。** 押しても出るのはスナックバー通知で、
  `download` イベントは発火せず、既定フォルダにも落ちない。`blob:` の fetch も失敗する。
  **描画済みの img を canvas に写して取る**のが唯一通る道（lib が対応済み）
- **Deep Research は 2 段構え。** プロンプト送信 → リサーチ計画 → **「リサーチを開始」を押す**。
  押さないと始まらない
- **レポートは `model-response` に無い。** そこは 127 文字程度で、本文はイマーシブパネルにある
- **モデルメニューは Angular Material ではない。** `gem-menu > gem-menu-item[role=menuitem]`
  という独自要素で、`.cdk-overlay-container` にも `menuitemradio` にも入らない
- **ログイン判定に cookie 数を使わない。** プロンプト欄の実在で判定する
- **タブが 0 枚の Chrome には接続できない。** lib が接続前に空タブを作って回避している

詳細は [REFERENCE.md](REFERENCE.md)。

## 終了条件

- [ ] `gemini_check` が「Gemini: 使える」とアカウント・モデルを返す
- [ ] 画像なら、保存されたパスを Read で開いて目視した
- [ ] Deep Research なら、レポートをファイルに保存し、実況部分を除いて使った
