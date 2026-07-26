# CLAUDE.md — claude-code-marketplace

**iOS アプリ量産パイプラインの全スキルの正本。** スキルを追加・修正するときは必ずここを直す。

## 構成

```
.claude-plugin/marketplace.json   5プラグインの登録
common/                 全リポジトリで有効。連絡・レビュー・git・routine・スキル索引
  hooks/hooks.json        Slack通知 / SessionStart で pull / キャッシュ編集の禁止
  scripts/                notify-slack.sh, sync_marketplace.sh, guard_cache_edit.py, build_skill_map.py
swift-app/              各アプリリポジトリで有効。構成・規約・検証・リリース・審査提出
  scripts/sync_report.py  雛形資産の差分レポート
ios-app-build/          ios-app-build-workspace で有効。00〜08 のパイプライン
  scripts/                asc_api.js, ciproduct_snapshot.sh, line_ask.sh（旧 _shared）
app-store-optimize/     app-store-optimize-workspace で有効。ASO
sns-marketing/          sns-marketing-workspace で有効。SNS 投稿・宣伝動画
```

全体の索引と使い分けは **`/common:skill-map`**（一覧部分は自動生成）。

## スキルを追加・修正する手順

```bash
cd ~/workspace_tmp/claude-code-marketplace
# 1. <plugin>/skills/<name>/SKILL.md を作る or 直す
# 2. スキルを増減したら索引を再生成
python3 common/scripts/build_skill_map.py
# 3. commit → push（push しないと他リポジトリに届かない）
# 4. 反映を確認
claude plugin marketplace update tubasasakunn-marketplace
```

- **`~/.claude/plugins/cache/` を直接編集しない。** 次の update で消える。
  PreToolUse フックで deny してあるが、Bash 経由なら通ってしまうので気をつける
- **アプリや workspace の `.claude/skills/` にスキルを置かない。** そこは空のまま維持する
- SKILL.md の `description` は「何をするか」＋「いつ使うか」を書く。Claude がこれを見て選ぶ
- プラグイン内の自リソース参照は `${CLAUDE_PLUGIN_ROOT}/...` を使う（絶対パスを書かない）

## セッションの作法

- **最初に pull する**（`common` の SessionStart フックが自動でやる）
- **push は節目とセッション終了時。** セッション最初に push すると前セッションの中間状態を撒く
- 未 push があるときは SessionStart フックが警告する

## marketplace では配れないもの

CI がリポジトリ内のファイルを実行するため、以下は**物理コピーが必須**でここには置けない。

| 資産 | 正本 | 配布 |
|---|---|---|
| `.github/workflows/` `fastlane/` `ci_scripts/` `scripts/` | swift-base | `/swift-app:sync-base` |
| `.claude/rules/`（Swift を触ると自動読み込み） | swift-base（内容は `/swift-app:conventions`） | 同上 |
| `ResultKit/`（図鑑8アプリの vendor コピー） | ResultKit リポジトリ | 同上 |

**スキルは pull で自動的に最新になるが、これらは能動的に同期しないと世代が分岐する。**
実測で `ci_post_clone.sh` は22アプリ中20が正本と違っていた。

## トークン

**public リポジトリなので、ここに秘密を書かない。** harness token などは各アプリの
`.claude/secrets.env`（private リポジトリ内・Claude Code のオンライン版でも clone される）に置き、
スキル側は「`.claude/secrets.env` から読む」と手順だけ書く。
