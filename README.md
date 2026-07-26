# claude-code-marketplace

iOS アプリ量産パイプラインの Claude Code スキル群。**全スキルの正本はこのリポジトリ**で、
各リポジトリ（アプリ・workspace）はセッション開始時に pull して取り込む。

## プラグイン

| プラグイン | 本数 | 有効にする場所 | 中身 |
|---|---|---|---|
| `common` | 8 | 全リポジトリ | LINE連絡・多モデル敵対的レビュー・git操作・cloud routine・スキル索引 |
| `swift-app` | 14 | 各アプリリポジトリ | 構成の正本・Swift規約・ビルド検証・バグ精査・ADR・全画面スクショ・AppIcon・iOS能力カタログ・リリースと審査提出・雛形同期 |
| `ios-app-build` | 11 | ios-app-build-workspace | アイデア→審査提出のパイプライン（00〜08）・コンセプト出し・デザイン仕様 |
| `app-store-optimize` | 4 | app-store-optimize-workspace | ASO調査・ストア文言・ストア画像の設計・レビュー返信 |
| `sns-marketing` | 8 | sns-marketing-workspace | TikTok / Lemon8 のカルーセル・宣伝動画・日次運用 |

スキルの一覧と使い分けは `/common:skill-map`。

## 使う側の設定

各リポジトリの `.claude/settings.json` に書く（信頼済みプロジェクトを開くと自動インストールされる）。

```json
{
  "extraKnownMarketplaces": {
    "tubasasakunn-marketplace": {
      "source": { "source": "github", "repo": "tubasasakunn/claude-code-marketplace" }
    }
  },
  "enabledPlugins": {
    "common@tubasasakunn-marketplace": true,
    "swift-app@tubasasakunn-marketplace": true
  }
}
```

## 直す側の手順

```bash
git clone git@github.com:tubasasakunn/claude-code-marketplace.git ~/workspace_tmp/claude-code-marketplace
cd ~/workspace_tmp/claude-code-marketplace
# <plugin>/skills/<name>/SKILL.md を編集
python3 common/scripts/build_skill_map.py    # スキルを増減したら索引を再生成
git commit && git push
claude plugin marketplace update tubasasakunn-marketplace
```

詳細は [CLAUDE.md](CLAUDE.md)。**`~/.claude/plugins/cache/` を直接編集しないこと**
（次の update で消える。PreToolUse フックで塞いである）。

## public なので秘密を書かない

トークン類は各アプリの `.claude/secrets.env`（private リポジトリ内）に置き、
スキルは「そこから読む」手順だけを書く。
