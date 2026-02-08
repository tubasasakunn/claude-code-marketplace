# テスト・自動化 (Maestro)

## スクリーンショット撮影の流れ

```bash
# 1. ビルド
xcodebuild -scheme ProjectName -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build

# 2. SwiftData 初期化（アンインストール → 再インストール）
xcrun simctl uninstall $DEVICE $BUNDLE_ID
xcrun simctl install $DEVICE $APP_PATH

# 3. オンボーディングスキップ
xcrun simctl spawn $DEVICE defaults write $BUNDLE_ID hasCompletedOnboarding -bool true

# 4. Maestro で画面遷移
maestro --device $DEVICE test scripts/flows/nav_add.yaml

# 5. スクリーンショット撮影
xcrun simctl io $DEVICE screenshot output.png

# 6. リサイズ
sips -Z 1311 output.png
```

## Maestro フローの書き方

```yaml
appId: com.example.app
---
- tapOn:
    id: "searchField"
- inputText: "検索テキスト"
- waitForAnimationToEnd
```

## Maestro の注意事項

| 問題 | 対処法 |
|------|--------|
| プロセス置換が動かない | ファイルパスを使う |
| NavigationStack の `back` が不安定 | Detail → Edit を最後に撮影 |
| 要素が見つからない | `accessibilityIdentifier` を事前設定 |
| アプリ状態のリセット | アンインストール → 再インストール |
| AppStorage の事前設定 | `simctl spawn defaults write` |

## Accessibility Identifier の付け方

```swift
Button { } label: { Image(systemName: "gearshape") }
    .accessibilityIdentifier("settingsButton")

// Maestro から参照
// - tapOn:
//     id: "settingsButton"
```
