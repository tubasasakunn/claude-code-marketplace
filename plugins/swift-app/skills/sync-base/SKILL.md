---
name: sync-base
description: swift-base の雛形資産（.claude/rules・GitHub Actions・fastlane・ci_scripts・scripts・post・ResultKit）が各アプリでどれだけ古いかを表にし、逆流と配布を判断する。スキルは marketplace が正本なので同期は要らないが、これらは CI がリポジトリ内のファイルを実行するため物理コピーが必須で、放っておくと世代が分岐する。テンプレートを直した後・アプリの挙動が他と違うとき・移行の棚卸しに使う。
---

# 雛形資産の同期（sync-base）

## なぜこれが要るか

**スキルは marketplace から pull すれば常に最新になるが、コード資産はそうならない。**
GitHub Actions はアプリリポジトリ内の `.github/workflows/` しか読まないし、Xcode Cloud は
リポジトリ内の `ci_scripts/ci_post_clone.sh` を実行する。だから物理的にコピーが必要で、
**能動的に同期しないと世代が分岐する**。

実測（2026-07-26 時点、22アプリ）:

| 資産 | 同一 | 差分 | 欠落 |
|---|---|---|---|
| `ci_scripts/ci_post_clone.sh` | **2** | **17** | 3 |
| `scripts/sync_fastlane_metadata.py` | 11 | 10 | 1 |
| `.claude/rules/` の新しい5本 | 13 | 0-1 | **8-9** |
| `fastlane/Fastfile` | 16 | 5 | 1 |

`ci_post_clone.sh` は同一が2本しかない。**アプリ側の差分は「独自進化＝正しい修正」の場合が
あるので、単純上書きは事故になる。**

## 手順

### 1. 差分レポートを出す

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_report.py \
  --base ~/workspace/ios-apps/swift-base \
  --apps ~/workspace/ios-apps \
  --resultkit ~/workspace/ios-apps/ResultKit
```

資産 × アプリのマトリクス（`=` 同一 / `!=` 差分 / `-` 欠落）とサマリが出る。
1資産だけ見るなら `--only ci_post_clone`。

### 2. 差分の中身を読んで、3つに分類する

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_report.py \
  --base ... --apps ... --diff <app> ci_scripts/ci_post_clone.sh
```

| 分類 | 例 | 対応 |
|---|---|---|
| **逆流すべき（アプリ→正本）** | mamezukan の `Package.resolved` を `xcshareddata/swiftpm/` へコピーする対策（SPM 依存があると Xcode Cloud のビルド#1が必ず落ちる） | swift-base に取り込んで、全アプリへ配る |
| **アプリ固有で正しい** | そのアプリだけの追加ターゲット・独自の環境変数 | 触らない。差分として残すことを記録する |
| **単なる取りこぼし** | `.claude/rules/` の新しい5本が9アプリに無い | そのまま配る |

**分類を飛ばして配布しないこと。** 17アプリの `ci_post_clone.sh` 差分には、そのアプリで
ビルドを通すために足された修正が混ざっている可能性がある。

### 3. 配布する

```bash
# ファイル資産（分類が済んだものだけ）
rsync -av ~/workspace/ios-apps/swift-base/.claude/rules/ \
          ~/workspace/ios-apps/<slug>/.claude/rules/

# ResultKit（vendor 方式・図鑑8アプリ）
rsync -av --delete ~/workspace/ios-apps/ResultKit/ \
                   ~/workspace/ios-apps/<slug>/<AppName>/ResultKit/
```

配布後は必ず `/swift-app:verify-build` でビルドを確認する。

## ResultKit は SPM にしない（意図的）

`ResultKit` は LIFE RESULT 図鑑ファミリー8アプリの共通実装（47ファイル・6,303行）。
**フォルダコピー（vendor）方式が設計上の選択**で、SPM パッケージ化しない:

- `public` を書かなくて済む（同一モジュールに取り込むため）
- **フィールドの ResultKit バージョンは常に混在する前提**。各アプリが好きなタイミングで更新する
- 例外は共有台帳スキーマ（`SharedLedger/SharedLedgerModels.swift`）— **前方互換を厳守**する
  （追記のみ・named migration・破壊的変更は出さない）
- アプリ固有の値は `Tokens.Family` と各アプリの `Strings.swift` に置き、**ResultKit 側へ
  書き足さない**

`GRDB` は逆にリモート SPM で入れる（`ResultKit/SharedLedger` の唯一の外部依存）。
vendor コピーだけでは入らないので、各アプリの `project.yml` に手で1回足す。

## 対象資産

| 資産 | 配布先 | 備考 |
|---|---|---|
| `.claude/rules/*.md` | 全アプリ | 正本は `/swift-app:conventions`。ファイルは自動読み込みのため配る |
| `.github/workflows/*.yml` | 全アプリ | Actions はリポジトリ内しか読まない |
| `fastlane/Fastfile` | 全アプリ | メタデータ反映・審査提出 |
| `ci_scripts/ci_post_clone.sh` | 全アプリ | Xcode Cloud が実行。ビルド番号採番 |
| `scripts/*.py` `*.sh` | 全アプリ | メタデータ検証・ストア画像生成・Secrets 投入 |
| `post/` | SNS 運用するアプリ | カルーセル投稿エンジン |
| `ResultKit/` | 図鑑8アプリ | vendor コピー |

**スキルは対象外**（marketplace が正本。アプリ側に `.claude/skills/` を置かない）。
