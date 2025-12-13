# Claude Code 出力スタイル

## 概要

出力スタイルはClaude Codeのシステムプロンプトを変更し、ソフトウェアエンジニアリング以外の用途にも適応可能にします。

---

## 組み込みスタイル

| スタイル | 説明 |
|----------|------|
| `default` | 標準のソフトウェアエンジニアリング向け |
| `explanatory` | 教育的な「インサイト」を提供しながらタスク完了 |
| `learning` | 協調学習モード。`TODO(human)`マーカーを追加して自分で実装を促す |

---

## 仕組み

- デフォルト以外のスタイルはコード生成固有の指示を除外
- カスタム指示をシステムプロンプトに追加
- ローカルプロジェクトレベル（`.claude/settings.local.json`）に保存

---

## スタイルの変更

### メニューから

```
/output-style
```

### 直接指定

```
/output-style explanatory
```

### 新規作成

```
/output-style:new I want an output style that ...
```

---

## カスタムスタイルの作成

### 保存場所

| タイプ | 場所 |
|--------|------|
| ユーザー | `~/.claude/output-styles/` |
| プロジェクト | `.claude/output-styles/` |

### ファイル形式

```markdown
---
name: My Custom Style
description:
  A brief description of what this style does
---

# Custom Style Instructions

You are an interactive CLI tool that helps users with...

## Specific Behaviors

[Define how the assistant should behave...]
```

---

## 他機能との比較

### vs CLAUDE.md

| 項目 | 出力スタイル | CLAUDE.md |
|------|-------------|-----------|
| 効果 | システムプロンプト変更 | ユーザーメッセージ追加 |
| デフォルト指示 | 置換可能 | 追加のみ |

### vs --append-system-prompt

| 項目 | 出力スタイル | --append-system-prompt |
|------|-------------|------------------------|
| 効果 | システムプロンプト変更 | システムプロンプトに追加 |
| デフォルト指示 | 置換可能 | そのまま維持 |

### vs サブエージェント

| 項目 | 出力スタイル | サブエージェント |
|------|-------------|-----------------|
| 対象 | メインエージェントループ | 委譲タスク |
| 設定 | システムプロンプトのみ | モデル、ツール、コンテキスト |

### vs スラッシュコマンド

| 項目 | 出力スタイル | スラッシュコマンド |
|------|-------------|-------------------|
| 概念 | 保存されたシステムプロンプト | 保存されたプロンプト |

---

## ユースケース

### explanatory

コードベースを学習中の開発者向け:
- 実装選択の理由を説明
- パターンを解説
- ベストプラクティスを共有

### learning

コーディングスキルを向上させたい開発者向け:
- 小さなコード部分を自分で実装
- `TODO(human)`マーカーで練習箇所を示す
- ガイド付き学習体験

### カスタム

特定のワークフローやドメイン向け:
- 技術ライター向け
- データ分析向け
- 特定のフレームワーク向け

---

## 例: カスタムスタイル

### 技術ライター向け

```markdown
---
name: Technical Writer
description: Focuses on documentation and explanation
---

# Technical Writing Style

You are an AI assistant focused on technical writing.

## Behaviors

- Prioritize clarity and readability
- Use simple language
- Include examples for complex concepts
- Structure content with clear headings
- Suggest documentation improvements
```

### レビュー特化

```markdown
---
name: Code Reviewer
description: Focuses on code review and feedback
---

# Code Review Style

You are an expert code reviewer.

## Behaviors

- Focus on code quality
- Identify potential bugs
- Suggest improvements
- Point out security concerns
- Never write code directly, only review
```

---

## Tips

- ソフトウェアエンジニアリング以外の用途に活用
- 学習目的には`learning`スタイル
- チームで共有する場合はプロジェクトに保存
