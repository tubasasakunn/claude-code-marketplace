# iOS Testing with Maestro - リファレンス

---

## ディレクトリ構成

```
maestro/
├── DOCUMENT.md        # 画面一覧とファイル対応表
├── flows/
│   ├── _common/       # 共通サブフロー
│   └── *.yaml         # 各画面のテストフロー
└── screenshots/       # 出力先
```

---

## DOCUMENT.mdテンプレート

```markdown
# Maestro UIテスト ドキュメント

## 画面一覧

| No | 画面名 | フローファイル | スクリーンショット |
|----|--------|---------------|-------------------|
| 01 | ホーム | flows/01_home.yaml | screenshots/01_home.png |

## 共通サブフロー

| ファイル | 説明 |
|----------|------|
| _common/setup.yaml | オンボーディング完了 |
```

---

## よく使うコマンド

### タップ

```yaml
- tapOn: "テキスト"
- tapOn:
    id: "accessibilityIdentifier"
- tapOn:
    point: "50%, 50%"
- tapOn:
    text: "スキップ"
    optional: true
```

### 待機

```yaml
- extendedWaitUntil:
    visible: "ホーム"
    timeout: 5000
```

### スワイプ

```yaml
# 右から左（次ページ）
- swipe:
    start: "80%, 50%"
    end: "20%, 50%"

# 下から上（スクロール）
- swipe:
    start: "50%, 80%"
    end: "50%, 20%"
```

### サブフロー

```yaml
- runFlow: _common/setup.yaml
```

---

## ベストプラクティス

### 1. clearStateで再現性確保

```yaml
- launchApp:
    clearState: true
```

### 2. IDを優先

テキストよりaccessibilityIdentifierが安定:

```yaml
# 推奨
- tapOn:
    id: "save_button"

# テキスト変更で壊れやすい
- tapOn: "保存する"
```

### 3. optionalを活用

表示されない可能性があるダイアログ:

```yaml
- tapOn:
    text: "許可しない"
    optional: true
```

---

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| 要素が見つからない | `inspect_view_hierarchy`でID確認、座標指定にフォールバック |
| 画面遷移が速すぎる | `extendedWaitUntil`で待機を追加 |
| オンボーディングが表示されない | `clearState: true`でアプリ状態をリセット |

---

## 参考リンク

- [Maestro公式ドキュメント](https://maestro.mobile.dev/)
- [コマンドリファレンス](https://maestro.mobile.dev/reference/commands)
