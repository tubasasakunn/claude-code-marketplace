# ios-testing

Maestroを使用したiOSアプリのUIテスト・スクリーンショット撮影スキル。

## 概要

Maestro MCPツールを活用してiOSシミュレータ上でのUIテストを自動化します。テストフロー作成、画面撮影、UI自動化をサポートします。

## 使用方法

`/ios-testing <テスト要件>`

```
/ios-testing ログイン画面のスクリーンショットを撮影
/ios-testing 設定画面への遷移をテスト
```

## ワークフロー

1. **要件分析** - テスト対象・操作手順を特定
2. **デバイス準備** - iOSシミュレータを起動
3. **プロジェクト情報確認** - Bundle ID、既存フローを確認
4. **テストコード作成** - Maestro YAML形式でフロー作成
5. **テスト実行** - 最大5回リトライで成功するまで実行
6. **結果報告** - 成功したYAMLとスクリーンショットを報告

## 使用するMCPツール

- `mcp__plugin_ios-develop-plugin_maestro__list_devices`
- `mcp__plugin_ios-develop-plugin_maestro__start_device`
- `mcp__plugin_ios-develop-plugin_maestro__run_flow`
- `mcp__plugin_ios-develop-plugin_maestro__inspect_view_hierarchy`
- `mcp__plugin_ios-develop-plugin_maestro__take_screenshot`

## ファイル出力

```
maestro/
├── flows/
│   └── XX_画面名.yaml     # テストフロー
└── screenshots/
    └── XX_画面名.png      # スクリーンショット
```

## 関連ドキュメント

| ファイル | 内容 |
|----------|------|
| SKILL.md | スキル本体 |
| REFERENCE.md | Maestroコマンド詳細 |
