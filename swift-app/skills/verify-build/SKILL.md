---
name: verify-build
description: xcodebuild でビルド検証し、.swift 由来の warning / error をベースライン（0 / 0）と比較する。コード変更後・コミット前に必ず使う。macOS 以外の環境では静的レビューの代替手順に切り替える。
allowed-tools: Bash, Read, Grep
---

# ビルド検証

ビルドが通り、`.swift` 由来の warning / error が **0 / 0** のベースラインを
維持していることを確認する。

## 手順

1. まず `uname` で実行環境を確認する。
2. `appstore.config.json` を Read し、`app.scheme` と `app.xcodeproj` を取得する。

3. **macOS（xcodebuild が使える場合）**：取得した値で以下を実行する
   （`<scheme>` / `<xcodeproj>` を置き換える）。

   ```bash
   xcodebuild -project <xcodeproj> -scheme <scheme> \
     -destination 'generic/platform=iOS Simulator' -configuration Debug build \
     2>&1 > /tmp/log
   echo "WARNINGS=$(grep -cE '\.swift:.*warning:' /tmp/log)"
   echo "ERRORS=$(grep -cE '\.swift:.*error:' /tmp/log)"
   echo "RESULT=$(grep -E 'BUILD (SUCCEEDED|FAILED)' /tmp/log | tail -3)"
   ```

   - 警告の grep は **必ず** `\.swift:.*warning:` で絞る。素の `warning:` だと
     AppIntents 等の無関係なノイズを拾い、ベースラインと比較できない。
   - `WARNINGS=0` / `ERRORS=0` / `BUILD SUCCEEDED` 以外なら、原因の `.swift:` 行を
     `/tmp/log` から抜き出して修正し、再実行する。**0 に戻るまでコミットしない。**

4. **Linux 等（xcodebuild が無い場合）**：ビルドできないことを明言した上で、代替として
   - 変更 diff（`git diff`）の全ファイルを読み、未定義シンボル・引数ラベル不一致・
     import 漏れ・actor 隔離違反（`@MainActor` API を nonisolated から呼んでいないか）を精査する。
   - `/swift-app:audit-conventions` を実行して規約違反が増えていないか確認する。
   - 結果報告に「ビルド未検証（Linux 環境）。マージ前に macOS で /swift-app:verify-build を要実行」と必ず書く。

## 補足

- 実機でしか正しく検証できない挙動（カメラ・録画・生成・再生など）は、Simulator 用の
  Debug シードやディープリンク的な環境変数フックを用意しておくと CLI から確認しやすい。
