---
name: local-cron
description: このマシンの crontab を操作して、定期ジョブや「指定時刻に1回だけ走って自分の登録を消すワンショット」を仕込みます。「毎晩◯時に走らせたい」「今日の21時に1回だけ実行したい」「cron に登録して」「予約実行」「あとで自動で流したい」と言われたとき、また深夜バッチが同じ日の別の時刻に後続処理を仕込むような2層パイプラインを組むときに使ってください。ローカル実行が対象で、クラウド側のスケジュール実行は cloud-routines が正本です。
allowed-tools: Bash, Read, Write, Edit
---

# ローカル crontab を操作する (local-cron)

## いつ使うか

- **定期実行**: 毎晩 00:12 にバッチを回す、毎週月曜にレポートを出す
- **ワンショット予約**: 今日の 21:10 に1回だけ投稿する、15分後にリトライする
- **2層パイプライン**: 深夜のジョブが「その日の最適な時刻」を計算して後続を仕込み、
  後続は発火時に自分の登録を消す（＝ゴミが溜まらない）

クラウドで走らせたいなら [[cloud-routines]]、対話セッション中の反復なら `/loop` を使う。
**このスキルは実機操作やローカルファイルが要る＝そのマシンでしか動かない仕事**のためのもの。

## なぜ crontab を直に書かないのか

素朴に `crontab -l | ...| crontab -` を書くと、以下で確実に事故る。`cronctl.sh` はこの4つを潰してある。

| 罠 | 何が起きるか |
|---|---|
| **`%` が改行になる** | crontab のコマンド欄では、エスケープしていない `%` は改行に変換される。URL やフォーマット文字列を含むコマンドが途中で切れる |
| **クォートと引数境界の崩壊** | スペースを含む引数がバラける。入れ子のクォートは書くほど壊れる |
| **read-modify-write の競合** | `crontab -l \| ... \| crontab -` は非アトミック。ワンショットの自己削除と別プロセスの登録が重なると行が消える |
| **絶対パスの直書き** | `/home/alice/...` と書くと別サーバー・別ユーザーで動かない |

`cronctl.sh` の対策は順に、**コマンドを argv ごと base64 で埋め込む**（base64 の文字種に `%` は無く、
NUL 区切りなので引数境界も保たれる）、**flock で crontab の読み書きを直列化**、
**`$HOME` 配下のパスは `"$HOME/..."` というリテラルで書き出す**（cron はコマンド欄を `/bin/sh -c` で
実行するので、実行するマシンの `$HOME` に展開される＝**ユーザー名やホームの位置が違うサーバーでも
同じ行がそのまま通る**）。

## 使い方

`${CLAUDE_PLUGIN_ROOT}/skills/local-cron/cronctl.sh`。**コマンドは必ず `--` の後ろに置く。**

```bash
CRONCTL="${CLAUDE_PLUGIN_ROOT}/skills/local-cron/cronctl.sh"

# 1回だけ（発火時に自分の crontab 行を消す）
"$CRONCTL" once "21:10"              --tag SNS --label app=hioto --log ~/logs/sns.log -- ~/bin/post.sh hioto
"$CRONCTL" once "2026-07-29 18:30"   --tag SNS --label app=anki  -- ~/bin/post.sh anki
"$CRONCTL" once "+15m"               --tag RETRY --label build   -- ~/bin/retry.sh

# 繰り返し（5フィールドの cron 式。消えない）
"$CRONCTL" repeat "12 0 * * *" --tag SNS --label nightly --log ~/logs/sns.log -- ~/bin/analyze.sh

# 今すぐ背景で（cron を経由せずデタッチ実行）
"$CRONCTL" now --log ~/logs/sns.log -- ~/bin/analyze.sh hioto

# 確認と削除
"$CRONCTL" list --tag SNS
"$CRONCTL" cancel <id>
"$CRONCTL" clear --tag SNS --match app=hioto
```

### `<when>` に書ける形

| 書き方 | 意味 |
|---|---|
| `"HH:MM"` | 今日のその時刻。**過ぎていれば翌日** |
| `"YYYY-MM-DD HH:MM"` | その日時。**過ぎていれば約2分後に倒す**（滞留したジョブを1年待たせない） |
| `"+15m"` / `"+2h"` | 相対時刻 |

### オプション

| オプション | 用途 |
|---|---|
| `--tag TAG` | グループ名。`list` / `clear` の絞り込み単位（既定 `CRONCTL`） |
| `--label TEXT` | 人間向けの識別子。`clear --match` の対象にもなる |
| `--log FILE` | 実行の stdout/stderr を追記。**cron はデフォルトでメールに流して消えるので、実質必須** |
| `--id ID` | ID を自分で決める（既定は `<epoch ms>-<label>`） |

`clear` は `--tag` か `--match` のどちらかが必須。**引数無しで全消しはできない**（事故防止）。
なお `clear` / `cancel` が触るのは `cronctl` が書いた行だけで、**手で書いた既存の crontab 行は消さない**。

## 設計の型: 2層パイプライン

「深夜に考えて、その日のうちの最適な時刻に実行する」形。後続は**発火時にまず自分を消す**ので、
コマンドが失敗しても長時間走っても crontab にゴミが残らない。

```
[毎晩 00:12 repeat] 分析ジョブ
      └─ 結果から最適な時刻を決めて once を仕込む
            └─ [その日 21:10 once] 実行ジョブ → 発火時に自分を削除
```

再実行の冪等性は **「仕込む前に自分のタグを clear する」** で担保する（毎晩 clear→再arm）。

```bash
"$CRONCTL" clear --tag SNS --match "app=$APP"     # 前回分を消してから
"$CRONCTL" once "$DT" --tag SNS --label "app=$APP" --log "$LOG" -- "$RUN" "$APP" post
```

動く実例は [examples/two-layer-pipeline.sh](examples/two-layer-pipeline.sh)。
実運用の適用例は `sns-marketing` プラグインの `sns-daily-pipeline/run_daily.sh`。

## Claude に無人実行させる場合

cron から Claude を起動するなら `--dangerously-skip-permissions` を付ける（許可プロンプトで固まるため）。
同じジョブの多重起動は `flock` で防ぐ。

```bash
flock -n /tmp/myjob.lock claude -p "<プロンプト>" --dangerously-skip-permissions >> "$LOG" 2>&1
```

## 落とし穴

- **cron の PATH は最小限**。`~/.local/bin` は入っていない。スクリプト冒頭で `export PATH` するか絶対パスで呼ぶ
- **cron に環境変数は引き継がれない**。`$DISPLAY`、トークン類、`nvm`/`pyenv` の設定は自分で読み込む
- **`--log` を付けないと出力が消える**（ローカルメールに落ちて誰も読まない）
- 相対パスのコマンドは登録時に絶対パスへ解決される。cron の作業ディレクトリは `$HOME`
- `once` は「分・時・日・月」を固定するので**同じ日時の指定は年をまたぐと再発火し得る**が、
  発火時に自己削除するため実際には残らない
- **crontab が空のマシンでは cron デーモン自体が動いているか確認する**（`systemctl status cron`）
