---
name: google-analytics
description: GA4・Firebase Analytics の実データを、既存の認証と Google 公式 Analytics MCP または設定済み CLI で読み取る。アプリの利用状況・継続・課金導線の分析や、Analytics 接続の確認・復旧時に使う。
---

# Google Analytics の読み取りと接続確認

## ログインを頼む前に、既存の接続を確認する

1. 利用可能な Analytics MCP と、対象アプリの既存 CLI・接続メモを確認する。
   Codex の登録設定は `codex mcp get google-analytics --json` で確認できる。
2. 設定された認証ファイルは、存在・種類・権限だけを確認する。秘密鍵や
   refresh token を含む JSON 全体を表示しない。アプリごとの `~/.config/` にある
   閲覧用サービスアカウントも候補に含める。
3. 対象プロパティに、小さな期間・少数の指標で読み取りリクエストを実行する。
   ファイルがあることや MCP の起動成功だけでは、データ接続成功としない。
4. 既存の閲覧権限で取得できれば再利用する。認証要求や新しい鍵の作成に進まない。
   Hioto の場合は [references/hioto.md](references/hioto.md) を先に読む。

既存のグローバル gcloud ADC を、対象アプリ用の認証で上書きしない。
新たな権限付与・認証情報の作成が必要なら、今回の依頼の範囲と現在の承認規則に従う。
このスキルは追加の権限付与を承認するものではない。

## 公式 MCP を使う

- 公式実装は [googleanalytics/google-analytics-mcp](https://github.com/googleanalytics/google-analytics-mcp)、
  Python パッケージは `analytics-mcp`。一般的な同名・類似 MCP と取り違えない。
- 認証ファイルを `GOOGLE_APPLICATION_CREDENTIALS` に指定できる。
  分析では `ANALYTICS_MCP_ALLOW_WRITE=false` とし、GA4 側も Viewer など
  対象に必要な範囲の閲覧権限を使う。
- Google Cloud プロジェクトと GA4 プロパティは別の識別子。
  API が有効でも GA4 データへの閲覧権限があるとは限らない。
- `list_tools` で実際のツールと引数を確認してから `run_report` を実行する。
  1.1.0 では `property_id`、`date_ranges`、`dimensions`、`metrics` を受け取り、
  日付の辞書キーは `start_date` / `end_date`。REST の camelCase と混ぜない。
- Admin API のアカウント一覧が空でも、既知のプロパティへの Data API 読み取りを
  確認するまでは、利用不可と断定しない。

## 認証エラーを切り分ける

- `ACCESS_TOKEN_SCOPE_INSUFFICIENT`：利用中の OAuth scope を確認する。
  GA4 閲覧には `https://www.googleapis.com/auth/analytics.readonly` を使う。
- Google の「このアプリはブロックされます」：同じ標準 gcloud OAuth クライアントで
  ログインを繰り返さない。標準 ADC クライアントで Google Cloud 外の scope を求めると
  ブロックされる場合がある。既存の閲覧用サービスアカウントをまず調べ、必要なら
  公式手順の専用 OAuth クライアント等を検討する。安全設定の解除を解決策にしない。
- 権限エラー：対象プロパティ、認証主体、API の有効化、quota project を確認し、
  観測したエラーに対応する項目だけ修正する。

[公式 MCP 手順](https://developers.google.com/analytics/devguides/MCP)と
[ADC の scope・ブロックの対処](https://docs.cloud.google.com/docs/authentication/troubleshoot-adc)
を、認証方式を変更するときに確認する。

## 分析時の注意

イベント回数とユーザー数を区別する。期間中の各イベントのユーザー数を割っただけでは、
同じ人が順に進んだファネルにならない。新規獲得・継続・課金は期間とコホートを合わせる。
アプリのイベント実装、導入バージョン、カスタムディメンションの登録時期を確認し、
テスト利用・欠測・仕様変更がある場合は集計の限界を明記する。
