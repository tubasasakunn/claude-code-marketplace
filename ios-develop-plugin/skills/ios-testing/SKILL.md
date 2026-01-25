---
name: ios-testing
description: Maestroを使用してiOSアプリのUIテストを作成・実行し、成功するまで繰り返します。テスト要件を受け取り、YAMLフロー作成、テスト実行、スクリーンショット撮影を自動化します。UIテスト、スクリーンショット撮影、画面自動化について言及された場合に使用してください。
context: fork
agent: general-purpose
argument-hint: <テスト要件>
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - mcp__plugin_ios-develop-plugin_maestro__*
---

# iOS UIテスト実行エージェント

$ARGUMENTS を実行するサブエージェントです。

## 進捗チェックリスト

```
- [ ] 1. 要件分析
- [ ] 2. デバイス準備
- [ ] 3. プロジェクト情報確認
- [ ] 4. テストコード作成
- [ ] 5. テスト実行
- [ ] 6. 結果報告
```

---

## 1. 要件分析

$ARGUMENTSから以下を特定:
- テスト対象の画面・機能
- 必要な操作手順
- 撮影するスクリーンショット
- 期待する結果

---

## 2. デバイス準備

```
mcp__plugin_ios-develop-plugin_maestro__list_devices
```

デバイスが起動していない場合:
```
mcp__plugin_ios-develop-plugin_maestro__start_device (platform: ios)
```

---

## 3. プロジェクト情報確認

- `maestro/DOCUMENT.md`があれば読み込み、画面構成を把握
- 既存のフローがあれば参考にする
- アプリのBundle IDを確認

```bash
mkdir -p maestro/flows maestro/screenshots
```

---

## 4. テストコード作成

**基本構造:**
```yaml
# [画面名]のテスト
# 要件: [ユーザー要件の要約]
appId: [Bundle ID]
name: "[テスト名]"
---
- launchApp:
    clearState: true

# 画面への遷移
- [操作コマンド]

# 待機
- extendedWaitUntil:
    visible: "[対象要素]"
    timeout: 5000

# スクリーンショット
- takeScreenshot: screenshots/[ファイル名]
```

---

## 5. テスト実行（反復ループ）

**最大試行回数: 5回**

```
試行 = 1
while 試行 <= 5:
    テスト実行
    if 成功:
        → 6. 結果報告（成功）へ
    else:
        問題分析 → 修正 → 試行++

if 試行 > 5:
    → 6. 結果報告（失敗）へ
```

### 各試行のフロー

**Step A: テスト実行**
```
mcp__plugin_ios-develop-plugin_maestro__run_flow
  device_id: [device_id]
  flow_yaml: [YAMLコンテンツ]
```

**Step B: 結果判定**
- 成功 → ループ終了、結果報告へ
- 失敗 → Step Cへ

**Step C: 問題分析**
```
mcp__plugin_ios-develop-plugin_maestro__inspect_view_hierarchy
mcp__plugin_ios-develop-plugin_maestro__take_screenshot
```

**Step D: 修正適用**

| エラー種別 | 修正アクション |
|-----------|---------------|
| 要素が見つからない | ID/テキストを修正、または座標指定 |
| タイムアウト | `extendedWaitUntil`のtimeoutを増加 |
| 遷移失敗 | 操作手順を見直し、待機を追加 |
| アプリクラッシュ | `clearState: true`で再起動 |

**Step E: 次の試行へ**

---

## 6. 結果報告

### 終了条件

| 条件 | ステータス | 次のアクション |
|------|-----------|---------------|
| テスト成功 | 成功 | YAMLをファイル保存、パスを報告 |
| 5回試行後も失敗 | 失敗 | 最後のエラーと試行履歴を報告 |

### 成功時の報告

成功したYAMLをファイルに保存し、以下の形式で報告:

```
## 実行結果

### ステータス
成功

### テストコード
- パス: `maestro/flows/[ファイル名].yaml`

### スクリーンショット
- パス: `maestro/screenshots/[ファイル名].png`

### 試行回数
[N]/5回
```

### 失敗時の報告

```
## 実行結果

### ステータス
失敗（5回試行後）

### 最後のエラー
[エラーメッセージ]

### 試行履歴
1. [エラー内容] → [修正内容]
2. [エラー内容] → [修正内容]
...

### 最終テストコード
- パス: `maestro/flows/[ファイル名].yaml`

### 推奨アクション
[手動確認が必要な項目]
```

---

## コマンドリファレンス

| コマンド | 説明 | 例 |
|----------|------|-----|
| `launchApp` | アプリ起動 | `- launchApp` |
| `launchApp: clearState: true` | 状態クリアして起動 | |
| `tapOn: "テキスト"` | テキストでタップ | `- tapOn: "検索"` |
| `tapOn: id: "id"` | IDでタップ | |
| `tapOn: point: "x,y"` | 座標でタップ | `- tapOn: point: "100,200"` |
| `inputText` | テキスト入力 | `- inputText: "文字列"` |
| `swipe` | スワイプ | `start: "80%, 50%"` `end: "20%, 50%"` |
| `scroll` | スクロール | `- scroll` |
| `extendedWaitUntil: visible` | 要素待機 | `timeout: 5000` |
| `takeScreenshot` | スクショ撮影 | `- takeScreenshot: screenshots/name` |
| `runFlow` | サブフロー実行 | `- runFlow: _common/setup.yaml` |

---

## ルール

### 必須
- テストが成功するまで修正・再実行を繰り返す
- 成功したテストコードをファイルに保存
- パスを正確に報告

### ファイル命名
- フロー: `maestro/flows/[XX]_[画面名].yaml`
- スクショ: `maestro/screenshots/[XX]_[画面名].png`

### トラブルシューティング優先順位
1. `inspect_view_hierarchy`で要素確認
2. `take_screenshot`で画面確認
3. 待機時間を調整
4. 座標指定にフォールバック
