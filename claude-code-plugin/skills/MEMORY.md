# Claude Code メモリ管理

## メモリの階層構造

Claude Codeは複数のメモリ階層を持ち、優先度順にロードされます。

### 1. エンタープライズポリシー（最高優先度）

組織全体の指示。IT/DevOpsが管理。

| OS | 場所 |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

### 2. プロジェクトメモリ

チームで共有するプロジェクト指示。

**場所**: `./CLAUDE.md` または `./.claude/CLAUDE.md`

**用途**:
- プロジェクトアーキテクチャ
- コーディング規約
- 共通ワークフロー

### 3. プロジェクトルール

モジュール式のトピック別指示。

**場所**: `./.claude/rules/*.md`

**構造**:
```
.claude/rules/
├── code-style.md
├── testing.md
└── security.md
```

**パス条件付きルール**:
```markdown
---
paths: src/api/**/*.ts
---

# API開発ルール
- 入力バリデーション必須
- 標準エラー形式を使用
```

**globパターン**:
| パターン | マッチ |
|----------|--------|
| `**/*.ts` | 全ディレクトリのTSファイル |
| `src/**/*` | src配下の全ファイル |
| `*.md` | ルートのMarkdown |

### 4. ユーザーメモリ

全プロジェクトで使用する個人設定。

**場所**: `~/.claude/CLAUDE.md`

**用途**:
- 個人のコードスタイル
- ツールのショートカット

### 5. ローカルメモリ（最低優先度）

現プロジェクトの個人設定。gitignoreに自動追加。

**場所**: `./CLAUDE.local.md`

**用途**:
- サンドボックスURL
- テストデータ

---

## メモリのインポート

`@path/to/file` 構文で他ファイルを参照可能。

```markdown
@README を参照
@docs/git-instructions.md

# 個人設定
@~/.claude/my-project-instructions.md
```

**制限**:
- 最大5階層まで
- コードブロック内では無効
- 相対・絶対パス両方可

---

## ユーザーレベルルール

個人ルールを全プロジェクトで適用。

**場所**: `~/.claude/rules/`

```
~/.claude/rules/
├── preferences.md
└── workflows.md
```

---

## 初期化

```bash
/init
```

プロジェクト用CLAUDE.mdを自動生成。

---

## メモリの編集

```
/memory
```

システムエディタで編集。

---

## ベストプラクティス

1. **具体的に**: 「コードを適切にフォーマット」→「2スペースインデント使用」
2. **構造化**: 箇条書きとMarkdown見出しで整理
3. **定期レビュー**: プロジェクト変更に合わせて更新
4. **焦点を絞る**: 1ファイル1トピック（rulesの場合）
5. **条件付き控えめに**: `paths`は本当に必要な場合のみ

---

## ロード確認

```
/memory
```

ロードされているメモリファイルを確認。

---

## シンボリックリンク

`.claude/rules/`ではシンボリックリンクをサポート。

```bash
# 共有ルールをリンク
ln -s ~/shared-claude-rules .claude/rules/shared

# 個別ファイルをリンク
ln -s ~/company-standards/security.md .claude/rules/security.md
```
