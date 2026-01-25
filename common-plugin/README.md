# common-plugin

汎用的な開発支援プラグイン。Git操作を効率化するスキルを提供します。

## インストール

```bash
/plugin install common-plugin@tubasasakunn-marketplace
```

## スキル一覧

| スキル | 説明 | 呼び出し方 |
|--------|------|------------|
| [commit](skills/commit/) | 日本語Conventional Commitsでコミット | `/commit` |
| [push](skills/push/) | リモートに安全にpush | `/push` |

## 使用例

### コミット

```
/commit
```

変更を確認し、すべてステージングして日本語Conventional Commitsでコミットします。

### プッシュ

```
/push
```

リモートとの状態を確認してから安全にpushします。

## 機能詳細

### commit

- `git status`, `git diff`で変更を確認
- 全変更を自動ステージング
- Conventional Commits形式（日本語）でメッセージ生成
- Co-Authored-By自動付与

#### Type一覧

| Type | 用途 |
|------|------|
| feat | 新機能追加 |
| fix | バグ修正 |
| docs | ドキュメント変更 |
| style | フォーマット変更 |
| refactor | リファクタリング |
| test | テスト追加・修正 |
| chore | ビルド・ツール変更 |

### push

- リモートとの差分確認
- 競合検出と警告
- 新規ブランチ対応（`-u`フラグ自動付与）
- force push禁止

## Hooks

### Slack通知

Claude Codeの通知をSlackチャンネルに転送します。

**必要な環境変数:**

```bash
export SLACK_TOKEN='xoxb-...'
export SLACK_CHANNEL_ID='C0...'
```

通知タイミング:
- 許可リクエスト時
- 60秒以上のアイドル時
- 認証成功時
- MCPツール入力要求時

## 注意事項

両スキルとも手動呼び出し専用（`disable-model-invocation: true`）です。自動的には呼び出されず、明示的に`/commit`や`/push`を実行する必要があります。

## バージョン

- v1.1.0 - Slack通知hooks追加
- v1.0.0 - 初回リリース
