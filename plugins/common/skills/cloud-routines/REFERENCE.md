# Cloud Routines リファレンス

Claude Code の Routines（クラウド版スケジュールエージェント）の詳細。SKILL.md の補足。

## 1. 実行環境
- Anthropic 管理のクラウドインフラで実行。ローカルマシンの起動不要、ブラウザを閉じても継続。
- 結果は専用 session ID と claude.ai 上の URL で参照可能。
- 2026-04-14 にリサーチプレビューとして公開。Pro/Max/Team/Enterprise で利用可。

## 2. 作成・管理方法
### Web UI（https://claude.ai/code/routines）
- **New routine** から作成。設定項目: 名前 / プロンプト / リポジトリ（1個以上）/ クラウド環境 / トリガー / コネクタ / 権限。
- 詳細ページで編集・一時停止/再開・ラン履歴閲覧・削除が可能。
- **API / GitHub トリガーの作成は Web UI 必須。**

### CLI `/schedule`（スケジュール型のみ）
- `/schedule <自然言語>` で作成、`list` / `update` / `run`。
- `update` 時に cron 式を直接指定できる。

## 3. スケジュール指定
- **プリセット**: hourly / daily / weekdays / weekly
- **cron**: 標準5フィールド（minute hour day-of-month month day-of-week）
- **一回限り（one-off）**: 将来時刻に1回。実行後自動無効化。自然言語可。
- **最小間隔: 1時間**（未満はリジェクト）
- タイムゾーン: ローカル入力 → UTC 変換。実行は予定時刻から数分以内（同一 routine は同じオフセット）。
- 予定を逃しても自動リトライなし。

## 4. できること / できないこと
### できる
- Shell / Git コマンド、リポジトリ操作（clone / branch / push）
- リポジトリにコミット済みのカスタムスキル実行
- MCP コネクタ連携（Slack / Linear / Google Drive 等）
- 環境変数で渡したシークレット / API トークンの利用
- 含めたコネクタの読み書きツールを**承認プロンプトなしで**使用

### できない / 制約
- **ローカルファイルアクセス不可**（毎回 fresh clone）
- **実行中の人間判断・中断・再開なし**（完全自動）
- **セッション再利用なし**（GitHub トリガーは各イベントで独立セッション、状態保持不可）
- push はデフォルト **`claude/` 接頭辞ブランチのみ**（既存ブランチは `Allow unrestricted branch pushes` フラグ要）
- 5時間ローリングウィンドウ制限が適用される
- **ローカル MCP サーバー（`claude mcp add`）は使えない** → `.mcp.json` かコネクタ登録

### ネットワーク
- デフォルトは Trusted network access。パッケージレジストリ / クラウド API / コンテナレジストリ / 開発向けドメインは既定許可。
- 許可外ドメインは `403 Forbidden`（x-deny-reason: host_not_allowed）。環境設定でカスタムドメイン追加可。
- MCP コネクタは Anthropic サーバー経由のため個別ホワイトリスト不要。

## 5. 結果の受け取り
- Web UI のラン履歴から full session を閲覧。
- API トリガー時は response に session URL を返却:
  ```json
  { "type": "routine_fire",
    "claude_code_session_id": "session_...",
    "claude_code_session_url": "https://claude.ai/code/session_..." }
  ```
- 出力: PR 作成 / Slack・Linear 等コネクタ経由通知。
- **Green ステータス = インフラ正常**であり、タスク成功とは別。成否は session 内容で確認。

## 6. 料金・前提
| プラン | Routine | 日次実行上限 |
|--------|---------|------------|
| Pro | 対応 | 5 runs/day |
| Max 5x/20x | 対応 | ≈15 runs/day（推定） |
| Team Premium | 対応 | per-user cap |
| Enterprise | 対応 | カスタム |

- 実行は通常の subscription usage を消費 + 別途 daily routine run cap。
- 上限超過: Usage Credits ON の組織は metered overage 継続、OFF は reject（API は `429 rate_limit_error`）。
- **一回限り実行は日次上限にカウントされない**（通常利用量のみ）。
- 前提: Claude Code on the web 有効。リポジトリ利用に GitHub 連携（Fine-grained PAT / OAuth via Claude GitHub App）。GitHub トリガー時は Claude GitHub App インストール必須。
- 消費確認: https://claude.ai/settings/usage と https://claude.ai/code/routines。

## 7. ローカル `/loop` との違い
| 項目 | Routines（クラウド） | /loop（ローカル） |
|------|----------------------|-------------------|
| 実行環境 | Anthropic クラウド | ローカルマシン |
| マシン起動 | 不要 | 必須 |
| ローカルファイル | 不可 | 可 |
| 永続性 | 永続 | セッション内（7日で失効） |
| 最小間隔 | 1時間 | 1分 |
| トリガー | スケジュール / API / GitHub | 時間のみ |
| 権限プロンプト | なし（自動） | セッション設定を継承 |
| 停止 | 編集で pause / delete | Esc |

**使い分け**: 信頼できる無人タスク・GitHub 反応・外部トリガーは Routines。開発中のポーリング・ローカルファイル必須・1分間隔は `/loop`。

## 8. API トリガーの注意
- ヘッダ `anthropic-beta: experimental-cc-routine-2026-04-01` 必須（実験的、仕様変更予定）。
- 1 routine = 1 トークン。トークン表示は1回のみ、再生成で旧トークン失効。
- Idempotency key 非対応 → 重複リクエストは複数セッションを生成。
- per-routine / per-account の時間ごとキャップあり。超過イベントはドロップ（リトライなし）。

## 9. 組織・管理
- routine は個人アカウント紐付け、チーム共有不可。出力は実行ユーザー名義。
- Team / Enterprise 管理者は組織全体で Routines を無効化可能（サーバー側設定、ローカル上書き不可）。

## 出典
- https://code.claude.com/docs/en/routines.md
- https://code.claude.com/docs/en/scheduled-tasks.md
- https://code.claude.com/docs/en/claude-code-on-the-web.md
- https://platform.claude.com/docs/en/api/claude-code/routines-fire
- https://code.claude.com/docs/en/whats-new/2026-w16
