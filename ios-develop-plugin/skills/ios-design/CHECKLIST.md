# iOS Design Review チェックリスト

## 1. HIG準拠

### Liquid Glass適用ルール（iOS 26）

**適用すべき場所**:
- NavigationBar
- TabBar
- Sidebar
- Modal
- FloatingControl

**禁止**:
- リストセル・カード背景（Blur Pile問題）
- カスタム背景色との併用

### タイポグラフィ

- [ ] セマンティックカラー（`.primary`, `.secondary`）を使用
- [ ] 固定色（`Color.white`, `Color.black`）を避ける
- [ ] フォントウェイトはMedium以上

### 同心円性

- [ ] UI要素の角丸がデバイスと調和
- [ ] `GlassEffectContainer`で関連要素をグループ化

---

## 2. アクセシビリティ

### システム設定対応

| 設定 | 確認項目 |
|------|---------|
| 透明度を下げる | `.identity`フォールバック |
| 視差効果を減らす | モーフィング停止時の動作 |
| コントラストを上げる | ボーダー追加時のレイアウト |

### 必須

- [ ] WCAGコントラスト比 4.5:1以上
- [ ] VoiceOver対応（accessibilityLabel等）

---

## 3. 実装品質

### API使用

| 確認 | Good | Bad |
|------|------|-----|
| 素材 | `.glassEffect(.regular)` | `.background(.ultraThinMaterial)` |
| グループ | `GlassEffectContainer` | `HStack`/`ZStack` |
| アニメーション | `.glassEffectID()` | `.matchedGeometryEffect()` |

### コードパターン

- [ ] `.interactive()`でタッチフィードバック
- [ ] `.tint()`でブランドカラー適用
- [ ] カスタム背景色を削除
