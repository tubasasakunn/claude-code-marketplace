---
name: ppo-experiment
description: App Store の Product Page Optimization（PPO）でストア画像を A/B テストする。3 案を用意して既存ページと合わせ 25% ずつに割り、asc CLI で実験の作成・スクリーンショットのアップロード・審査提出・配信開始・結果の取得までを通す。ストア画像を比較したい、どの案が効くか実データで決めたい、A/B テストを回したい、PPO を作りたいときに使用してください。画像そのものを作る工程は screenshot-build が担当します。
---

# ストア画像を A/B テストする (ppo-experiment)

## これは何か

App Store Connect の **Product Page Optimization（PPO）** で、ストア画像の案を
実トラフィックで比較する。`screenshot-build` が作った案を ASC に載せ、審査に出し、
配信して、結果を取るところまで。

**treatment は最大 3 つ。** 既存ページ（コントロール）と合わせて 4 通りを比較できる。

## 前提

- **アプリが公開済み**であること（`READY_FOR_SALE` の版が要る）。審査中・未公開では作れない
- **案が 3 つ揃っている**こと。作り方は `/app-store-optimize:screenshot-build`
- `asc` CLI が認証済み（`asc auth status` で確認）

## トラフィックの割り方

`--traffic-proportion` は**実験全体に回す割合**で、treatment 間は均等に分割される。

| 指定 | 各案 | 既存ページ |
|---|---|---|
| `--traffic-proportion 75` | **25% ずつ** | 25% |
| `--traffic-proportion 45` | 15% ずつ | 55% |
| `--traffic-proportion 30` | 10% ずつ | 70% |

3 案で 25% ずつにしたいなら **75** を指定する。各案に 25 を指定するのではない。

差を早く出したいなら 75、現行の露出を守りたいなら 45。規模の小さいアプリで 30 に
すると、有意差が出るまでかなり待つことになる。

## 手順

### 1. 対象の版を選ぶ

```bash
asc versions list --app <APP_ID> | python3 -c "
import sys, json
for v in json.load(sys.stdin)['data']:
    a = v['attributes']
    print(v['id'], a['versionString'], a['appStoreState'])
"
```

`READY_FOR_SALE` の最新版の ID を使う。

### 2. 実験を作る

```bash
asc product-pages experiments create --version-id <VERSION_ID> \
  --name "Screenshots 2026-07 A/B/C" --traffic-proportion 75
```

返る `id` が実験 ID。`state: PREPARE_FOR_SUBMISSION` / `reviewRequired: true` になる。

### 3. treatment を 3 つ作る

```bash
for t in "A 手軽さ：..." "B 情緒：..." "C SNSでない：..."; do
  asc product-pages experiments treatments create --experiment-id <EXP_ID> --name "$t"
done
```

**名前は結果を読むときの唯一の手がかり**になる。「案A」ではなく、何を訴求した案かが
分かる名前を付ける。

### 4. ロケールを作る

```bash
asc product-pages experiments treatments localizations create \
  --treatment-id <TREATMENT_ID> --locale ja
```

配信しているロケールぶん作る。

### 5. スクリーンショットを入れる

```bash
asc product-pages experiments treatments localizations screenshot-sets sync \
  --localization-id <LOCALIZATION_ID> --device-type IPHONE_69 \
  --path <out ディレクトリ> --confirm
```

`sync` は既存を消してから入れ直すので、やり直しが効く（`upload` は追加）。
ディレクトリを渡すと中の PNG が名前順に並ぶ。

### 6. 審査に出す

PPO は**必ず Apple の審査を通る**。いきなり開始はできない。

```bash
# 提出を作る
SUB=$(asc review submissions-create --app <APP_ID> --platform IOS \
        | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

# 実験を項目として載せる
asc review items-add --submission "$SUB" \
  --item-type appStoreVersionExperiments --item-id <EXP_ID>

# 提出
asc review submissions-submit --id "$SUB" --confirm
```

`WAITING_FOR_REVIEW` になれば提出完了。**この時点ではまだ誰にも配信されない。**

### 7. 審査が通ったら開始する

```bash
asc product-pages experiments update --experiment-id <EXP_ID> --started true
```

ここで初めて実トラフィックが振られる。

### 8. 結果を見る

```bash
asc product-pages experiments view --experiment-id <EXP_ID>
asc product-pages experiments treatments list --experiment-id <EXP_ID>
```

表示回数とコンバージョンが treatment ごとに返る。**有意差が出るまで止めない**——
数日で判断すると曜日の偏りを拾う。

### 9. 記録を残す ★飛ばさない

**残さないと、次に同じ判断を繰り返す。** 作業場の `logs/<アプリ>/<日付>/` に置く。

```
logs/hioto/2026-07-26/
  README.md              何をテストしたか、なぜそう作ったか、結果
  A-01.jpg 〜 A-04.jpg   実際に提出した画像（幅 660 の JPEG）
  B-01.jpg 〜  C-01.jpg 〜
```

```bash
D=logs/<アプリ>/$(date +%F); mkdir -p $D
for pair in "<Aのout>:A" "<Bのout>:B" "<Cのout>:C"; do
  src="${pair%%:*}"; key="${pair##*:}"
  for i in 01 02 03 04; do
    sips --resampleWidth 660 $src/$i.png --setProperty format jpeg \
      --setProperty formatOptions 72 --out $D/$key-$i.jpg >/dev/null
  done
done
```

`README.md` に書くこと:

- **識別子** — アプリ ID / 版 ID / 実験 ID / 提出 ID / 配分 / ロケール / サイズ
- **何を比べているか** — 3 案のテーマと、割り当てたキャンバス・端末の見せ方
- **各案の全枚と見出し**、そして**なぜそう作ったか**
- **結果** — 表示回数・インストール・コンバージョン・既存比（配信後に追記）
- **わかったこと** — 数字ではなく、次に活かせる仮説の形で
- **次に試すこと** — 勝った案のどこが効いたのかを切り分ける実験

判断の理由を書くのがいちばん効く。数値だけ残しても、半年後に「なぜこの配置にしたか」
が読めない。**負けた案の理由も書く**——同じ失敗を避けられる。

## 踏んだ罠

### `--started true` は審査前だと弾かれる

```
Can't start experiment, must be reviewed!
```

`reviewRequired: true` なので、手順 6 を飛ばせない。作成しただけでは配信されないので、
**中身を ASC の画面で確認してから提出する**余裕がある。

### 6.9" のリサイズは要らない

`--device-type IPHONE_69` を指定すると **`APP_IPHONE_67` として登録される**。
1320×2868 がそのまま通るので、1290×2796 へ変換する必要はない。
Apple が 6.9" を 6.7" のスロットで受け付けるため。

CLI の `asc screenshots sizes` は 2 件しか返さず `APP_IPHONE_67` が載っていないが、
これは CLI 側の情報が古いだけで、実際には使える。

### treatment には iPad のセットも自動で作られる

現行版が iPad のスクリーンショットを持っていると、treatment にも
`APP_IPAD_PRO_3GEN_129` のセットが生まれる。iPhone だけ差し替えるなら触らなくてよい。

### CLI では画像の枚数を確認できない

`screenshot-sets list` の `relationships.appScreenshots` は常に空で返る。
入ったかどうかは `sync` の戻り値（各ファイルの `state: COMPLETE`）で判断し、
**最終確認は ASC の画面で目視する**。

### フラグ名が揺れている

同じ「版の ID」でもコマンドによって `--version` と `--version-id` が違う。
`--help` で確認してから叩く。

| コマンド | フラグ |
|---|---|
| `localizations list` | `--version` |
| `product-pages experiments create` | `--version-id` |
| `experiments view` / `update` | `--experiment-id` |
| `review submissions-submit` | `--id` |

## 中止する

```bash
# 提出を取り下げる（審査前）
asc review submissions-cancel --id <SUBMISSION_ID>

# 実験を止める（配信中）
asc product-pages experiments update --experiment-id <EXP_ID> --started false

# 実験ごと消す
asc product-pages experiments delete --experiment-id <EXP_ID>
```

## 完了条件

- [ ] 対象が `READY_FOR_SALE` の版になっている
- [ ] treatment が 3 つ、それぞれ名前で何の案か分かる
- [ ] 各 treatment に配信ロケールぶんの localization がある
- [ ] スクリーンショットが全 treatment で同じ枚数入っている（`state: COMPLETE`）
- [ ] **ASC の画面で 12 枚を目視した**（提出後の差し替えは再審査になる）
- [ ] 提出が `WAITING_FOR_REVIEW`
- [ ] 審査通過後に `--started true` した
- [ ] `logs/<アプリ>/<日付>/` に画像と README を残した
- [ ] 結果が出たら README の表と「わかったこと」を埋めた

## 関連

- `/app-store-optimize:screenshot-build` — 比較する画像そのものを作る
- `/app-store-optimize:screenshot-crafting` — 何を訴求するかの設計
- `/app-store-optimize:aso` — キーワードと競合の調査
