# Hioto の既存 Analytics 接続

2026-11-22 に実データの読み取りまで確認したローカル設定。
認証ファイルや権限は変わり得るので、毎回小さなリクエストで確認する。

| 項目 | 値 |
|---|---|
| Google Cloud プロジェクト | `hioto-basaapp` |
| GA4 プロパティ | `559067499` |
| 設定ディレクトリ | `~/.config/hioto-analytics/`（0700） |
| 既存の認証ファイル | `~/.config/hioto-analytics/service-account.json`（0600） |
| 認証の範囲 | Hioto プロパティの Viewer、`analytics.readonly` |
| 既存 CLI | `~/.local/bin/hioto-analytics` |
| ローカル接続メモ | `~/.config/hioto-analytics/README.txt` |
| Codex MCP 登録名 | `google-analytics` |

秘密鍵の内容をこのスキルやリポジトリにコピーしない。

## まず試す

```bash
"$HOME/.local/bin/hioto-analytics" status
codex mcp get google-analytics --json
```

CLI の `status` は Data API の読み取り成功時に `authenticated: true` を返す。
MCP が未接続でも、CLI が動くなら分析を進められる。

```bash
"$HOME/.local/bin/hioto-analytics" events --start 7daysAgo --end yesterday
"$HOME/.local/bin/hioto-analytics" metadata
```

## MCP 設定を復旧する場合

次は既存の登録を置き換えるコマンド。現在の登録を確認し、修正が必要な場合だけ実行する。
既存サービスアカウントを再利用するため、ブラウザでの再ログインは不要。

```bash
codex mcp add google-analytics \
  --env GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/hioto-analytics/service-account.json" \
  --env GOOGLE_CLOUD_PROJECT=hioto-basaapp \
  --env GOOGLE_CLOUD_QUOTA_PROJECT=hioto-basaapp \
  --env ANALYTICS_MCP_ALLOW_WRITE=false \
  -- "$HOME/.local/bin/uvx" --python 3.12 --from analytics-mcp==1.1.0 analytics-mcp
```

1.1.0 はこの日に検証したバージョンであり、最新版を意味しない。
`analyticsadmin.googleapis.com` と `analyticsdata.googleapis.com` は同日に有効と確認済み。

接続検証では、MCP クライアントから `initialize` → `list_tools` → `run_report` を実行する。
書き込みツールが公開されていないことと、次のような読み取りの成功を確認する。

```json
{
  "property_id": "559067499",
  "date_ranges": [{"start_date": "7daysAgo", "end_date": "yesterday"}],
  "dimensions": ["eventName"],
  "metrics": ["eventCount", "totalUsers"],
  "limit": 20
}
```

新しい登録が現在のチャットでツールとして見えない場合も、設定の有無と
MCP プロセスを直接検証した結果を区別して報告する。

## イベントの意味はアプリ側を確認する

アプリは `~/workspace/ios-apps/hioto`。`docs/firebase-telemetry.md`、
`hioto/Services/TraceLogger.swift`、`BehaviorAnalytics.swift`、
`hioto/Paywall/PlusPaywallView.swift` が確認先。
`clip_saved` や `diary_playback` などは途中のバージョンから追加されているため、
過去の `ClipRecorded` 等と同じ観測期間だとみなさない。
`diary_playback` は再生開始の計測で、最後まで見たことを示さない。
