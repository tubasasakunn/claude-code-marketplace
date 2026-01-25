---
name: ios-design
description: iOS/SwiftUIのデザインレビューを実行します。画像（スクリーンショット）やSwiftUIコードを入力として受け取り、HIG準拠・アクセシビリティ・Liquid Glass実装を総合レビューします。UIデザインのレビュー、iOS 26 Liquid Glass、HIG準拠チェック、デザイン改善提案について質問された場合に使用してください。
argument-hint: [画像パス または ファイルパス]
context: fork
agent: general-purpose
---

# iOS Design Review

$ARGUMENTS をレビュー

## 終了条件

以下のいずれかで終了:
1. **すべて✅**: 問題なし、レビュー完了
2. **改善提案を提示**: ユーザーが内容を確認し、追加質問なし
3. **ユーザーが終了を指示**: 明示的に終了

**⚠️/❌がある場合**: 改善提案を必ず含め、ユーザーの確認を待つ

---

## クイックリファレンス

### Liquid Glass適用ルール

| 適用すべき場所 | 禁止 |
|---------------|------|
| NavigationBar, TabBar, Sidebar | リストセル・カード背景 |
| Modal, FloatingControl | カスタム背景色との併用 |

### API対応表

| 確認項目 | Good | Bad |
|---------|------|-----|
| 素材 | `.glassEffect(.regular)` | `.background(.ultraThinMaterial)` |
| グループ | `GlassEffectContainer` | `HStack`/`ZStack` |
| アニメーション | `.glassEffectID()` | `.matchedGeometryEffect()` |
| 色 | `.primary`, `.secondary` | `Color.white`, `Color.black` |

---

## ワークフロー

```
- [ ] ステップ1: 入力読み取り
- [ ] ステップ2: レビュー実行
- [ ] ステップ3: 結果出力
- [ ] ステップ4: 確認
```

### ステップ1: 入力読み取り

Readツールで入力を読み取る:
- 画像パス → 画像として読み取り
- ファイルパス → コードとして読み取り

**読み取り成功時のみ続行**

### ステップ2: レビュー実行

[CHECKLIST.md](CHECKLIST.md)に従ってチェック:
1. HIG準拠
2. アクセシビリティ
3. 実装品質

Liquid Glass詳細は[REFERENCE.md](REFERENCE.md)を参照。

### ステップ3: 結果出力

以下のフォーマットで報告:

```markdown
## iOS Design Review

### 概要
[入力の簡潔な説明]

### HIG準拠 ✅/⚠️/❌
- [チェック結果]

### アクセシビリティ ✅/⚠️/❌
- [チェック結果]

### 実装品質 ✅/⚠️/❌
- [チェック結果]

### 改善提案
1. [優先度高] ...
2. [優先度中] ...

### コード例（該当する場合）
[改善後のコード]
```

### ステップ4: 確認

ユーザーに確認:
- 追加でレビューしたい箇所があるか
- 改善提案についての質問があるか
