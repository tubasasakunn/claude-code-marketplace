---
name: 08_run_pipeline
description: アイデア一言を受け取り、コンセプト出しから App Store の審査提出までを一気に走らせる指揮役です。各工程をサブエージェントへ委譲してコンテキストを守り、判断が要る場面だけ LINE でユーザに問い、それ以外は自分で決めて進めます。「〇〇なアプリを作って」と言われたら、これを使ってください。
---

# パイプラインを通す (08_run_pipeline)

## これは指揮役である

**自分で手を動かさない。** 各工程を**サブエージェントに委譲**し、返ってきた結果を検証し、次へ渡す。
自分のコンテキストは「どこまで進んだか」と「引き継ぐ値」だけで埋める。

アプリ1本の全工程を1つのエージェントで抱えると、必ずコンテキストが尽きる（実測で尽きた）。

## 走らせる前に

`CLAUDE.md` と `PIPELINE.md` を読む。`talk_to_user` の作法に従う。

```bash
cd ~/workspace/ios-app-build-workspace
git submodule update --init --remote common/swift-base common/marketing
export LINE_ASK=${CLAUDE_PLUGIN_ROOT}/scripts/line_ask.sh
export ASC_API=${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js
export HARNESS_TOKEN=$(grep '^API_TOKEN=' ~/workspace/harness/.env | cut -d= -f2-)
```

前提が生きているか、**最初に全部見る**。途中で気づくと手戻りが大きい。

```bash
osascript -e 'tell application "System Events" to return UI elements enabled'   # アクセシビリティ
node $ASC_API GET "/v1/apps?limit=1&fields%5Bapps%5D=name" | head -1            # ASC APIキー
curl -s https://harness.basaapp.com/api/asc/session/validate -H "Authorization: Bearer $HARNESS_TOKEN"
gh auth status 2>&1 | head -2
```

`valid: false` なら、この時点で `02` のセッション再取得をユーザに依頼しておく（後で待たされない）。

## 進捗の記録

**`~/workspace/ios-app-build-workspace/.run/<slug>.md` に、節目ごとに書き足す。**
自分が落ちても、次のセッションがここから再開できる。

```markdown
# Bide
- slug: bide / bundle: com.basaapp.bide
- appId: 6789382610
- ciProductId: 6B650524-...
- ciWorkflowId: 73DF1413-...
- [x] concept  [x] design  [x] 00  [x] 01  [x] 02  [ ] 03 ...
- メモ: アプリ名 "Bide" は取られていたので "Bide：待ち方の記録" にした
```

## 工程

各工程は **1エージェント1スキル**。プロンプトには必ず入れる:

- 対象アプリの slug / bundle id / appId など**引き継ぐ値**
- 「スキル `<名前>/SKILL.md` を読み、その手順どおりに実行せよ」
- **触ってはいけないもの**（他アプリ、他リポジトリ）
- 「完了条件のチェックリストを全部満たしたか、API で裏を取って報告せよ」

### 1. コンセプト（`concept-crafting`）

ユーザのアイデア一言を渡す。成果物は `Idea/00N_<名前>/CONCEPT.md`。

**アプリ名は仮**である。Web 検索で衝突しなくても、Apple 側で取られていることがある（`01` で判明する）。

終わったら LINE で報告し、**先へ進む**。ここで承認を待たない（戻せるので）。

### 2. デザイン（`design-crafting`）

**ここは待つ。** 配色と世界観はユーザの好みで決まる。

アーティファクトで案を並べ、URL を LINE で送り、返信を待つ（`talk_to_user` の「見せて決める」）。
返信が無ければ **60分待って、第1案で進める**。その旨を LINE に書いておく。

### 3〜4. リポジトリと CI/CD（`00_setup_repo` → `01_create_xcode_cicd`）

`01` は **GUI を触る唯一の工程**。ここだけは慎重に。

- **実行前に `${CLAUDE_PLUGIN_ROOT}/scripts/ciproduct_snapshot.sh` を取る。実行後に diff する**
- Xcode を再起動し、対象プロジェクトだけを開かせる
- `Create Workflow…` が無効なら、原因3つを潰させる。最後がセッション切れなら **LINE で再サインインを依頼して待つ**
- アプリ名が取られていたら、`CONCEPT.md` のストア表示名で再試行。それも駄目なら **LINE で名前を聞く**

終わったら **appId / ciProductId / ciWorkflowId** を `.run/<slug>.md` に書く。

### 5. ASC 登録（`02_register_appstore`）

プライバシー宣言で ASC セッションが切れていたら、リレーの URL を LINE で送って待つ。

### 6. 実装（`03_implement_app`）

**ここが一番長い。** サブエージェントに任せ、その間に `04_build_front` を別のエージェントで並行させてよい
（front はアプリコードに依存しない。URL だけ先に決まる）。

ビルドが緑になったら、**スクリーンショットを自分の目で見る**（`Read` ツール）。
DESIGN.md と食い違っていたら、直させる。

### 7〜8. サイトとストア素材（`04_build_front` → `05_release_assets`）

`05` のストア文言は **審査リスクを自分で読む**。医療・セラピー・効能の表現があれば書き直させる。
デモデータがストア画像に写る。

### 9. 審査提出（`06_submit_review`）

**提出は戻せない。** 提出前チェックを全部通してから、LINE で一言入れて出す（許可は待たなくてよい。
ここまで来たら出すのが前提だから）。

```
✅ Bide を審査に出します

ビルド VALID / プライバシー published / 価格 無料 / 配信 175地域
規約・サポート 200 / primaryLocale ja

10分待って「stop」が来なければ提出します。
```

### 10. 監視（`07_watch_review`）

審査結果は数日かかる。**セッションを跨ぐ。**
`.run/<slug>.md` に「提出済み、結果待ち」と書いて終える。

次にセッションを開いたとき `GET /api/mail/summary` を見れば、Apple のメールが拾える。

## 判断の分岐点（ここだけユーザに聞く）

| 場面 | 聞き方 |
|---|---|
| デザインの決定 | アーティファクトを見せて選ばせる。60分で第1案 |
| アプリ名が取られていた | ストア表示名で自動再試行 → それも駄目なら聞く |
| Xcode の Apple ID が切れた | 再サインインを依頼。**待つしかない** |
| ASC のログインが切れた | リレー URL を送る。**待つしかない** |
| 審査提出の直前 | 10分の猶予を告げて、来なければ出す |
| 事故が起きた | 何が壊れ、何が無事で、どうするかを報告。続行判断を聞く |

**それ以外は自分で決める。** リトライ、エラーの修正、実装の細部、次の工程。

## 失敗したとき

**工程が落ちても、パイプライン全体を止めない。**

1. ログを読み、原因を特定する。スキルの「トラブルシューティング」に載っていることが多い
2. 直して**同じ工程を再実行**する（各スキルは冪等に書いてある）
3. 2回直しても駄目なら、**LINE で報告して判断を仰ぐ**。「返信がなければこうする」を添える

**スキル文書に無い罠を踏んだら、その場でスキルに書き足す。** 次に踏まないために。
これがこのパイプラインの育て方である。

## やってはいけないこと

- **自分で実装しない。** 指揮役がコードを書き始めると、コンテキストが尽きて全体が止まる
- **工程の完了を報告だけで信じない。** サブエージェントは「できました」と言う。API で裏を取る
- **他アプリを触らせない。** サブエージェントのプロンプトに毎回「触ってはいけないもの」を書く
- **進捗を実況しない。** LINE は節目だけ

## 完了条件

- [ ] `.run/<slug>.md` に appId / ciProductId / ciWorkflowId と全工程のチェックが残っている
- [ ] `appStoreState` が `WAITING_FOR_REVIEW`
- [ ] `<slug>.basaapp.com` の4ルートが 200
- [ ] `apps/<slug>` が submodule として app-builder に繋がり、push されている
- [ ] 踏んだ罠がスキルに書き足されている
