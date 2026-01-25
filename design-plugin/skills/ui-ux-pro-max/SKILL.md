---
name: ui-ux-pro-max
description: UI/UXデザインを100点満点で評価します。design review、UI評価、デザイン改善、ダサいUI修正について言及された場合に使用してください。
context: fork
agent: general-purpose
argument-hint: "[screenshot/code/url]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - WebFetch
  - Bash
---

# UI/UX Pro Max

$ARGUMENTS を100点満点で評価し、問題点を具体的に指摘する。

---

## ワークフロー

```
- [ ] ステップ1: 入力の取得
- [ ] ステップ2: 関連データの検索
- [ ] ステップ3: 10カテゴリ評価
- [ ] ステップ4: 問題点の分類
- [ ] ステップ5: レポート出力
```

---

## ステップ1: 入力の取得

| 入力タイプ | 対応 |
|------------|------|
| 画像パス | Readで読み込み |
| コードパス | Readで読み込み |
| URL | WebFetchで取得 |
| インライン | そのまま評価 |

入力が不明確な場合は確認を求める。

---

## ステップ2: 関連データの検索

評価対象に応じて、検索スクリプトで関連ガイドラインを取得:

```bash
# UXガイドライン検索
python design-plugin/skills/ui-ux-pro-max/scripts/search.py "contrast accessibility" --domain ux

# スタイルガイド検索
python design-plugin/skills/ui-ux-pro-max/scripts/search.py "glassmorphism" --domain style

# カラーパレット検索
python design-plugin/skills/ui-ux-pro-max/scripts/search.py "saas fintech" --domain color

# タイポグラフィ検索
python design-plugin/skills/ui-ux-pro-max/scripts/search.py "modern professional" --domain typography

# スタック別ガイドライン（React, SwiftUI等）
python design-plugin/skills/ui-ux-pro-max/scripts/search.py "button component" --stack react
```

**利用可能なドメイン**: style, color, chart, landing, product, ux, typography, prompt
**利用可能なスタック**: html-tailwind, react, nextjs, vue, svelte, swiftui, react-native, flutter

---

## ステップ3: 10カテゴリ評価

各カテゴリ10点満点で採点。

| # | カテゴリ | 主な観点 |
|---|----------|----------|
| 1 | ビジュアル階層 | 情報優先度、視線誘導、CTA |
| 2 | タイポグラフィ | フォント選択、サイズ階層、可読性 |
| 3 | カラー設計 | コントラスト比、配色調和 |
| 4 | スペーシング | 余白の一貫性、8pxグリッド |
| 5 | インタラクション | hover/focus状態、フィードバック |
| 6 | アクセシビリティ | WCAG準拠、キーボードナビ |
| 7 | レスポンシブ | モバイル対応、44pxタッチターゲット |
| 8 | パフォーマンス | アニメーション時間、重いエフェクト |
| 9 | 一貫性 | スタイル統一、パターン再利用 |
| 10 | UXベストプラクティス | ローディング、エラー表示 |

### 減点基準

詳細は [SCORING.md](SCORING.md) を参照。主な減点:

- コントラスト比4.5:1未満: -4点
- focus不可視: -3点
- モバイル未対応: -5点
- キーボード操作不可: -3点

---

## ステップ4: 問題点の分類

| 重要度 | 基準 |
|--------|------|
| **Critical** | アクセシビリティ違反、重大なUX問題 |
| **Major** | ユーザー体験を損なう問題 |
| **Minor** | 改善推奨だが機能に影響なし |

---

## ステップ5: レポート出力

```markdown
# UI/UX評価レポート

## 総合スコア: XX/100点 【ランク】

| スコア | ランク |
|--------|--------|
| 90-100 | S |
| 80-89 | A |
| 70-79 | B |
| 60-69 | C |
| 50-59 | D |
| 0-49 | F |

## カテゴリ別スコア

| カテゴリ | スコア | 判定 |
|----------|--------|------|
| ビジュアル階層 | X/10 | ◯/△/✕ |
| ... | ... | ... |

## 問題点

### Critical
1. **[問題名]** - 場所: / 問題: / 修正:

### Major
1. ...

### Minor
1. ...

## 良い点
- ...

## 改善優先順位
1. ...
```

---

## 終了条件

- [ ] 全10カテゴリのスコア算出済み
- [ ] 総合スコア算出済み
- [ ] 問題点をCritical/Major/Minorに分類済み
- [ ] 各問題に修正方法を記載済み
- [ ] 改善優先順位を提示済み

---

## 参照ドキュメント

- [SCORING.md](SCORING.md) - 詳細な減点基準
- [data/](data/) - 評価基準データ（CSV形式）
