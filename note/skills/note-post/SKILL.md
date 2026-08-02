---
name: note-post
description: note.com の記事を新規に1本作って下書き保存まで持っていく。ネタ出し・構成・執筆・アイキャッチ生成・ローカル Markdown 化・note への下書き作成・プレビュー確認まで。「note に書いて」「note 記事作って」「今週の開発をまとめて」と言われたときに使う。公開はしない（公開は note-publish）。
allowed-tools: Bash, Read, Write, Edit, Glob, Skill, WebSearch, WebFetch
---

# note 記事を 1 本作る（下書きまで）

**このスキルは公開しない。下書き保存までで必ず止まる。** 公開は `/note:note-publish`。

記事の**正本はローカルの Markdown**（`articles/<slug>/article.md`）。note 側は出力先にすぎない。
note が壊れてもここから作り直せる状態を保つ。

## 0. 前提を確認する

```
note_check_auth
```

通っていなければ `/note:note-setup`。ツールが 1 つも見えないときも同じ。

## 1. ネタと角度を決める

**「何を書くか」が決まっていないまま書き始めない。** 材料の取り方:

| 記事の種類 | 材料の取り方 |
|---|---|
| 開発の記録 / Build in Public | `git log --oneline --since="1 week ago"`、`git diff --stat`、ADR、リリースノート |
| アプリの宣伝 | `apps/<app>/` の `appstore.config.json`・ストア文言・実画面。ASO 資産を転用する |
| 知見・解説 | 実際に踏んだ失敗と、その解決に使った実データ。手元にログが残っているものを選ぶ |
| 反応を見て決める | `/last30days <ジャンル>` で直近 30 日の Reddit / HN / YouTube の実発言を取る |

角度が既存記事とかぶっていないか `articles/README.md` で確認する。
**同じ話でも切り口を変える**（作った話 / 売れなかった話 / 数字の話 / 技術選定の話）。

## 2. 規範を読む

**書き始める前に必ず読む。飛ばさない。**

1. `/note:note-craft` … 媒体としての note、タイトル・書き出し・構成・タグ・画像の規範
2. `note-craft/NOTES.md` … ユーザの確定した指摘（**一般原則より優先**）
3. `writing` プラグインの `japanese-tech-writing` と `cognitive-rhythm-writing`

## 3. 記事ファイルを作る

```
articles/<YYYY-MM-DD>-<slug>/
  article.md      ← 記事の正本
  images/         ← 本文画像・アイキャッチ
```

`article.md` の先頭は **YAML フロントマター**。`note_create_from_file` がここから
タイトル・タグ・アイキャッチを読む。

```markdown
---
title: 個人開発の iOS アプリを 22 本出して、伸びたのは 3 本だった
tags:
  - 個人開発
  - iOS
  - SwiftUI
eyecatch: ./images/eyecatch.png
---

本文をここから書く。H1 は使わない（タイトルが持つ）。

## 見出しは H2

本文中の画像は相対パスで参照する。アップロードは自動でされる。

![実際のダウンロード推移](./images/downloads.png)
```

- **フロントマターの `title` を必ず書く。** ないと本文の最初の H1/H2 が奪われる
- 目次が要る長さなら本文冒頭に `[TOC]` を置く（note 側で目次に変換される）
- 数式は `$${...}$$`（KaTeX 互換）

## 4. 画像を用意する

規範は `note-craft` の「図・画像」。**手順として外せないのは次の 3 つ。**

- **アイキャッチを note 用に作る。** ストア画像の切り出しで済ませない。
  作ったら **300px と 208px に縮小して Read で開く。** 主題が読めなければ作り直す

  ```bash
  python3 -c "
  from PIL import Image
  im = Image.open('articles/<slug>/images/eyecatch.png')
  for w in (300, 208):
      im.resize((w, int(im.height*w/im.width)), Image.LANCZOS).save(f'/tmp/eye_{w}.png')"
  ```

- **記事の背骨を図にする。** スクショだけで出さない。比較表・工程図・対比のどれかを 1 枚。
  ブランド色は `apps/<app>/appstore.config.json` の `brand` から取る。
  日本語フォントは Noto Sans JP（可変軸）を使う

  ```python
  ft = ImageFont.truetype("/tmp/NotoSansJP.ttf", size); ft.set_variation_by_axes([weight])
  ```

- **本文画像は証拠になるものだけ**（実画面・グラフ・Before/After・ログ）。
  生成したら **Read で開いて目視確認する。** 文字化け・見切れ・重なり・可読性を見る
- 形式は JPEG / PNG / GIF / WebP、1 枚 10MB 以内

## 5. 出す前に機械チェックを通す

**目視の前に機械で潰す。** note に上げてから気づくと、更新が 2 段（`/note:note-publish` 参照）になる。

```bash
uv run python - <<'PY'
from pathlib import Path
from note_mcp.utils.markdown_to_html import markdown_to_html
body = Path("articles/<slug>/article.md").read_text().split("---\n", 2)[2]
html = markdown_to_html(body)
print("生の ** の残り:", html.count("**"), "(0 でなければ太字が効いていない)")
print("<strong>     :", html.count("<strong>"), "(意図した数と一致するか)")
print("裸の URL     :", html.count('">http'), "(リンクになっていない URL)")
PY
```

見るのは 3 つ。

- **`**` の直後が `「` だと太字にならない。**
  CommonMark の flanking 判定で、開始デリミタの直後が約物・直前が文字だと強調の開始と
  見なされない。`減ったのは**「打ち込む」だけ**だった。` は生の `**` のまま出る。
  そもそも `japanese-tech-writing` が「初出の定義は太字、以後の言及は「」」と使い分けを
  定めているので、**この形が出たら太字を外すのが正しい**（括弧を消して太字を残すのではない）。
  **断片だけ変換すると通ってしまう**（行頭では直前が空なので開始デリミタになる）。必ず本文全体で見る
- **裸の URL はリンクにならない。** note-mcp が自動で埋め込むのは YouTube / X / note /
  Gist / Zenn などだけ。App Store・自社サイトは `[表示文字](URL)` と書く
- **`<strong>` の数が意図と合っているか。** `note-craft` は一節に一、二箇所までとしている

## 6. 下書きを作る

```
note_create_from_file(file_path="articles/<slug>/article.md")
```

- ローカル画像は自動アップロードされ、本文のパスが note の URL に置換される
- アイキャッチもフロントマターから自動で設定される
- 返ってくる**記事 ID / キー（`n` で始まる）を `articles/README.md` に記録する**
- **フロントマターの tags は下書きには載らない。** これは失敗ではない（下の罠を読む）

すでに下書きがある記事を直すときは、上書きではなく更新する:

```
note_get_article(article_id="n...")    # 先に現状を取る。数字 ID は拒否される
note_update_article(article_id="...", title=..., body=..., tags=[...])
```

### 下書き更新の罠

- **下書きにタグは載らない。** `draft_save` は `hashtags` を受け取るが永続化しない。
  タグが付くのは公開時の `PUT /v1/text_notes/{id}` だけ。
  プレビューの `hashtags:[]` を見て「失敗した」と判断しない。
  公開時に `note_publish_article(..., file_path=...)` を渡せばフロントマターから反映される
- **body を含めずに `draft_save` を投げると本文が消える。** 部分更新ではない。
  タグだけ直したくても、`note_update_article` で**本文ごと**送る
- 本文中の画像は、note に上がった URL（`https://assets.st-note.com/img/...`）を
  Markdown に書けば再アップロードされない。ローカルの正本は相対パスのまま置き、
  送る直前に置換する

## 7. プレビューで確認する

```
note_show_preview(article_key="n...")     # ブラウザで開く
note_get_preview_html(article_key="n...") # HTML を文字列で取る（機械チェック用）
```

**必ず実物を見る。** Markdown → note の HTML 変換で崩れる箇所がある:

- 見出しの階層、リストの入れ子
- 画像が URL に置換されているか（ローカルパスが残っていたら失敗している）
- アイキャッチが設定されているか
- **`<strong>` の数が意図と一致しているか**（減っていたら太字が効いていない）
- コードブロックの言語指定

`note_get_preview_html` は 28 万字ほど返ってツールの上限を超える。
返ってきたファイルパスを Python で読んで構造だけ抜く:

```python
import json, re
h = json.load(open("<返ってきたパス>"))["result"]
print([re.sub(r'<[^>]+>','',t) for _, t in re.findall(r'<h([1-3])[^>]*>(.*?)</h\1>', h, re.S)])
print(len(re.findall(r'<strong>', h)), "strong")
print(h.count("./images"), "ローカルパス残存")
```

**`<ol>` を探すときは `<ol[ >]` で当てる。** note は `<ol name="..." id="...">` を出すので、
`<ol>` で grep すると 0 件に見えて誤判定する。

## 8. 記録する

`articles/README.md` に 1 行足す:

```markdown
| 2026-08-02 | [22本出して伸びたのは3本](articles/2026-08-02-22-apps/) | n1234567890ab | 下書き |
```

## 完了チェック

- [ ] `articles/<slug>/article.md` があり、フロントマターに title / tags / eyecatch が揃っている
- [ ] `note-craft` の完了チェックを通した（前置きなし・転がある・タグ 3〜5）
- [ ] `japanese-tech-writing` を通した（LLM っぽい空句が残っていない）
- [ ] **`cognitive-rhythm-writing` の執筆後の点検手順を 5 つとも当てた**
      （話題テスト・漏出テスト・緊張台帳・拍・境界。読んで書いただけで済ませない）
- [ ] **機械チェックを通した**（生の `**` が 0、`<strong>` が意図の数、裸の URL が 0）
- [ ] **記事の背骨の図がある**（スクショだけになっていない）
- [ ] **アイキャッチを 300px に縮小して目視し、主題が読めることを確かめた**
- [ ] 画像を Read で目視確認した
- [ ] note に下書きが作られ、プレビューで崩れていないことを実際に見た
- [ ] `articles/README.md` に記事 ID を記録した
- [ ] **公開していない**（公開は人が `/note:note-publish` で判断する）
