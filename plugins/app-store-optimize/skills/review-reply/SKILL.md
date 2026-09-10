---
name: review-reply
description: リリース後のユーザレビューを読み、返信し、そこから ASO を直す。レビュー本文に出た語をキーワードに反映し、誤解が多い点は説明文で先に解く。「レビュー見て」「レビューに返信して」と言われたとき、DL が伸び悩んで原因を探すときに使う。返信は公開されて取り消せないので必ずユーザ確認を取る。
---

# レビュー返信と ASO へのフィードバック

> 審査中のステータス監視・リジェクト対応は `/ios-app-build:07_watch_review` が正本。
> ここは**公開後**のレビュー対応と、それを ASO に還す部分。

## 1. 読む

```bash
curl -s "https://harness.basaapp.com/api/appstore/reviews?appId=$APP_ID&limit=20" \
  -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for r in d['reviews']:
    print(r['createdDate'][:10], '★'*int(r['rating']), r['territory'], '| 返信済' if r['hasResponse'] else '| 未返信')
    print(' ', (r['title'] or '')[:60])
    print(' ', (r['body'] or '')[:200].replace('\n',' '))
"
```

`$HARNESS_TOKEN` は各アプリの `.claude/secrets.env` から読む。`$APP_ID` は
`appstore.config.json` か ASC で確認する。

## 2. 返信する

```bash
curl -s -X POST "https://harness.basaapp.com/api/appstore/reviews/<reviewId>/response" \
  -H "Authorization: Bearer $HARNESS_TOKEN" -H "Content-Type: application/json" \
  -d '{"body":"..."}'
```

**返信は公開される。取り消せない。送る前に必ず文面をユーザに見せて確認を取る**
（`/common:talk_to_user`）。

| ステータス | 意味 |
|---|---|
| 400 | `body` が空、または JSON が壊れている |
| 503 | `ASC_RW_*`（App Manager ロールのキー）が harness に設定されていない |
| 502 | ASC 側のエラー。レスポンスの `body` に Apple の理由が入っている |

### 書き方

- **謝罪から入らない。** 事実に答える
- 機能要望に「検討します」と言わない。**入れるか入れないかを、理由とともに言う**
- バグ報告には、再現条件を聞くか、直した版のバージョンを示す
- テンプレの繰り返しは逆効果。1件ずつ書く
- 効能を謳わない（医療・セラピー・メンタルヘルス）

## 3. ASO に還す ★ここが本題

レビューは**実際のユーザが使った言葉**のサンプルで、キーワード調査より精度が高い。

| レビューに現れたもの | どう直すか |
|---|---|
| 機能を指す語が自分の文言と違う（ユーザは「日記」、自分は「記録」） | `keywords.txt` にユーザ側の語を入れる。タイトル/サブタイトルと**重複させない** |
| 同じ誤解が複数件（「〇〇ができないと思った」） | `description.txt` の冒頭3行で先に解く。ストア画像1枚目のコピーも見直す |
| 期待と違ったという低評価 | サブタイトルが約束しすぎている。`/app-store-optimize:screenshot-crafting` で1枚目を作り直す |
| 特定機能への好評が集中 | その機能を1枚目に昇格。`promotional_text.txt`（審査なしで随時更新可）で即出す |

反映の手順:

1. `/app-store-optimize:aso` でフィールド設計を見直す（語の重複を作らない原則を守る）
2. `/swift-app:release-assets` で `release/<version>/` の .txt を書き換える
3. `python3 scripts/check_release_metadata.py <version>` を通す（`PASS` 必須）
4. main にマージ → `appstore-metadata.yml` が ASC に反映

`promotional_text.txt` だけは**審査を通さず随時更新できる**ので、レビューで見つかった誤解の
応急処置に使える。

## 完了条件

- [ ] 未返信のレビューを一覧できた
- [ ] 返信する文面をユーザに見せ、承認を得てから送った
- [ ] レビューから拾った語・誤解を ASO の変更案として書き出した（直すか直さないかを決めた）
