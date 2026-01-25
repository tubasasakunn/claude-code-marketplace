# design-plugin

デザインレビュー・UI/UX評価プラグイン。

## インストール

```bash
/plugin install design-plugin@claude-code-marketplace
```

## スキル一覧

| スキル | 説明 | 呼び出し方 |
|--------|------|------------|
| [mobile-ui-design](skills/mobile-ui-design/) | モバイルUI 6カテゴリ評価 | `/mobile-ui-design <画像>` |
| [ui-critique](skills/ui-critique/) | UI批評 7項目100点評価 | `/ui-critique <画像/コード>` |
| [ui-ux-pro-max](skills/ui-ux-pro-max/) | UI/UX 10カテゴリ包括評価 | `/ui-ux-pro-max <画像/コード/URL>` |
| [ux-psychology](skills/ux-psychology/) | 心理学的UX 8カテゴリ評価 | `/ux-psychology <画像>` |

## 使用例

### モバイルUIデザイン評価

```
/mobile-ui-design screenshots/home.png
```

### UI批評

```
/ui-critique screenshots/profile.png
/ui-critique src/components/Card.tsx
```

### UI/UX総合評価

```
/ui-ux-pro-max screenshots/dashboard.png
/ui-ux-pro-max https://example.com
```

### 心理学的UX評価

```
/ux-psychology screenshots/checkout.png
```

## スキル比較

| スキル | カテゴリ数 | 特徴 |
|--------|-----------|------|
| mobile-ui-design | 6 | モバイル特化、プラットフォーム準拠チェック |
| ui-critique | 7 | 批評用語で問題を言語化 |
| ui-ux-pro-max | 10 | 8スタック対応、ガイドライン検索機能 |
| ux-psychology | 8 | 心理学効果に基づく評価 |

## 機能詳細

### mobile-ui-design

- 6カテゴリ評価（タイポ、レイアウト、色彩等）
- PASS/CONDITIONAL/NEEDS_WORK/FAIL判定
- iOS HIG / Material Design準拠チェック

### ui-critique

- 7項目加重評価（視覚的階層、一貫性等）
- 批評用語（目が滑る、垢抜けない等）で問題を表現
- 残酷なまでに正直なフィードバック

### ui-ux-pro-max

- 10カテゴリ各10点満点
- S/A/B/C/D/Fランク判定
- 50スタイル、21パレット、50フォントペアリング対応

### ux-psychology

- 8心理学カテゴリ（認知、バイアス、行動誘導等）
- 心理効果名を明記した根拠ある評価
- 改善提案に心理学的裏付け

## バージョン

- v1.4.0
