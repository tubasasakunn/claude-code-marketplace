---
name: cloud-routines
description: Claude Code の Routines（クラウド上でスケジュール/API/GitHub イベントにより自動実行されるエージェント）の作成・管理・設計を支援します。「routine を作りたい」「定期的にクラウドで自動実行したい」「/schedule で予約したい」「スケジュールエージェント / cron / GitHub トリガーで Claude を動かしたい」場合に使用してください。ローカル実行の /loop は対象外（クラウド/web 版のみ）。
---

# Cloud Routines（クラウド版スケジュールエージェント）

## 概要
Routines は「プロンプト + リポジトリ + コネクタ + トリガー」の設定を保存し、**Anthropic 管理のクラウド上で自動実行**する仕組み。ローカルマシンの起動状態に依存しない。本スキルはクラウド/web 版の Routines 専用で、ローカルの `/loop` は扱わない（違いは [REFERENCE.md](REFERENCE.md) 参照）。

- **対象プラン**: Pro / Max / Team Premium / Enterprise（Claude Code on the web 有効が前提）
- **ステータス**: リサーチプレビュー（仕様変更の可能性あり）

## いつこのスキルを使うか
- routine を新規作成 / 編集 / 一覧 / 手動実行したい
- 「クラウドで定期実行」「cron で予約」「GitHub の PR/issue に反応して自動実行」したい
- routine で何ができる／できないか、料金・制約を知りたい

## ワークフロー

routine 作成依頼を受けたら、次の順で進める：

1. **トリガー種別を確定**（3 種）
   - **スケジュール**: cron / プリセット（hourly・daily・weekdays・weekly）/ 一回限り
   - **API**: 外部システムから fire エンドポイントで起動
   - **GitHub イベント**: PR / issue 等に反応
2. **作成手段を選ぶ**
   - **スケジュール型のみ**は CLI の `/schedule` で作成可能 → スキル `schedule` に委譲してよい
   - **API / GitHub トリガー** や コネクタ・環境・権限の細かい設定は **Web UI 必須**（https://claude.ai/code/routines）
3. **必須要素を埋める**: 名前 / プロンプト / 対象リポジトリ（1個以上）/ クラウド環境 / コネクタ / 権限
4. **制約を事前確認**（下記「設計時チェック」）し、抵触するなら設計を見直す
5. **作成後の確認方法を伝える**: Web UI のラン履歴、API なら返却される session URL

### CLI（スケジュール型）クイック例
```
/schedule daily PR review at 9am
/schedule tomorrow at 9am, summarize yesterday's merged PRs
/schedule in 2 weeks, open a cleanup PR
/schedule list      # 一覧
/schedule update    # 編集（cron 式直接指定も可）
/schedule run       # 手動実行（Run now 相当）
```
> CLI で作れるのはスケジュール型のみ。API/GitHub トリガーは Web UI で作成する。

## 設計時チェック（routine 設計前に必ず確認）
- [ ] 実行間隔は **1時間以上**か（1時間未満は不可。短間隔が必要ならローカル `/loop`）
- [ ] **日次実行上限**内か（Pro=5回/日、Max≈15回/日。超過で 429）
- [ ] **ローカルファイルに依存していない**か（毎回 fresh clone。secret は環境変数で渡す）
- [ ] **人間の承認・中断が不要**か（実行中プロンプト不可、完全自動）
- [ ] push 先が **`claude/` 接頭辞ブランチ**で足りるか（既存ブランチへは別フラグ要）
- [ ] 必要な外部ドメインが **ネットワーク許可**内か（許可外は 403、環境設定で追加）
- [ ] MCP は **コネクタ or `.mcp.json`** か（ローカル `claude mcp add` のサーバーは使えない）
- [ ] GitHub 利用時、連携（PAT / Claude GitHub App）が済んでいるか

## よくある落とし穴
- **Green ステータス ≠ タスク成功**。インフラ正常を示すだけ。成否はセッション内容で確認する。
- **routine は個人アカウント紐付け**で共有不可。出力（commit/Slack 投稿等）も実行ユーザー名義。
- **一回限り実行は日次上限にカウントされない**（通常の利用量のみ消費）。
- 予定時刻を逃しても**自動リトライなし**（アイドル後に1回だけ実行）。

## 詳細ドキュメント
- [REFERENCE.md](REFERENCE.md) — 制約・料金・API・`/loop` との違い・出典の詳細

## 終了条件
- [ ] トリガー種別が確定している
- [ ] 適切な作成手段（CLI `/schedule` か Web UI）を案内した
- [ ] 設計時チェックに抵触しないことを確認した
- [ ] 作成後の結果確認方法を伝えた
