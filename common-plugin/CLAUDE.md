# common-plugin

汎用的な開発支援プラグインです。

---

## 作業ルール

### 1. ブランチ運用

**ユーザーとの会話開始時に必ず新しいブランチを作成してください。**

```bash
git checkout -b <作業内容を表すブランチ名>
```

- ブランチ名は作業内容がわかる名前にする（例: `feature/add-login`, `fix/button-style`）
- mainブランチで直接作業しない

### 2. INDEX.mdの更新

**全ての作業完了後、差分を確認しINDEX.mdを更新してください。**

1. 現在の差分を確認:
   ```bash
   git diff
   git status
   ```

2. INDEX.mdに各ファイルの内容を記載:
   ```markdown
   # INDEX

   ## ファイル一覧

   ### agents/
   - `investigator.md` - バグ調査・実装方法調査を行うサブエージェント

   ### commands/
   - `implement.md` - 機能実装を反復して完成させるコマンド
   - `ui-implement.md` - UI実装を反復して完成させるコマンド
   ```

3. 新規ファイル追加・ファイル変更があった場合は必ず反映する

### 3. コミットとBranch.md

**INDEX.md更新後、コミットしてBranch.mdを作成してください。**

1. 変更をコミット:
   ```bash
   git add .
   git commit -m "<変更内容の要約>"
   ```

2. Branch.mdにブランチの機能を記載:
   ```markdown
   # Branch: <ブランチ名>

   ## 概要
   [このブランチで実装した機能の概要]

   ## 変更内容
   - [変更1]
   - [変更2]

   ## 関連ファイル
   - [ファイルパス]: [変更内容]
   ```

3. Branch.mdもコミット:
   ```bash
   git add Branch.md
   git commit -m "Add Branch.md"
   ```

---

## 作業フロー まとめ

```
会話開始
  ↓
[1] 新しいブランチを作成
  ↓
[作業実施]
  ↓
[2] 差分確認 → INDEX.md更新
  ↓
[3] コミット → Branch.md作成 → コミット
  ↓
会話終了
```
