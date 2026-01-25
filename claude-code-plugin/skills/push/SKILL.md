---
name: push
description: 現在のブランチをリモートにpush。リモートとの状態確認後に実行。/pushで呼び出し。
disable-model-invocation: true
allowed-tools:
  - Bash(git *)
---

# Git Push スキル

現在のブランチをリモートリポジトリにpushする。

## 実行手順

### 1. 現在の状態確認

並列で以下を実行:
- `git branch --show-current` - 現在のブランチ名
- `git status` - 未コミットの変更確認
- `git fetch origin` - リモートの最新情報を取得

### 2. リモートとの差分確認

```bash
git log --oneline origin/<branch>..HEAD 2>/dev/null || echo "新規ブランチ（リモートに存在しない）"
```

pushされるコミットを表示。

### 3. 競合チェック

```bash
git log --oneline HEAD..origin/<branch> 2>/dev/null
```

リモートに新しいコミットがある場合は警告し、以下を提案:
- `git pull --rebase` でリモートの変更を取り込む
- または `git merge origin/<branch>` でマージ

### 4. Push実行

```bash
git push origin <current-branch>
```

新規ブランチの場合（upstreamが未設定）:
```bash
git push -u origin <current-branch>
```

### 5. 結果確認

```bash
git log --oneline -1
git status
```

## 注意事項

- **force push禁止**: `--force`や`-f`は使用しない
- **未コミットの変更がある場合**: 先にコミットするよう促す
- **リモートに新しいコミットがある場合**: pullを先に実行するよう提案

## エラー時の対応

### リモートに新しいコミットがある
```
error: failed to push some refs to 'origin'
```
→ `git pull --rebase origin <branch>` 後に再度push

### 認証エラー
```
fatal: Authentication failed
```
→ SSH鍵やトークンの設定を確認するよう案内
