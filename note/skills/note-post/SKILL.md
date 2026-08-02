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

- **アイキャッチ（必須）** → `/canva:canva-image-gen` で生成するか、アプリ宣伝記事なら
  `sns-marketing` の `carousel-craft` のブランド描画で SNS と見た目を揃える
- **本文画像は証拠になるものだけ**（実画面・グラフ・Before/After・ログ）
- 生成したら **Read で開いて目視確認する。** 文字化け・見切れ・可読性を見る
- 形式は JPEG / PNG / GIF / WebP、1 枚 10MB 以内

## 5. 下書きを作る

```
note_create_from_file(file_path="articles/<slug>/article.md")
```

- ローカル画像は自動アップロードされ、本文のパスが note の URL に置換される
- アイキャッチもフロントマターから自動で設定される
- 返ってくる**記事 ID / キー（`n` で始まる）を `articles/README.md` に記録する**

すでに下書きがある記事を直すときは、上書きではなく更新する:

```
note_get_article(article_id="...")     # 先に現状を取る
note_update_article(article_id="...", title=..., body=..., tags=[...])
```

## 6. プレビューで確認する

```
note_show_preview(article_key="n...")     # ブラウザで開く
note_get_preview_html(article_key="n...") # HTML を文字列で取る（機械チェック用）
```

**必ず実物を見る。** Markdown → note の HTML 変換で崩れる箇所がある:

- 見出しの階層、リストの入れ子
- 画像が URL に置換されているか（ローカルパスが残っていたら失敗している）
- アイキャッチが設定されているか
- コードブロックの言語指定

## 7. 記録する

`articles/README.md` に 1 行足す:

```markdown
| 2026-08-02 | [22本出して伸びたのは3本](articles/2026-08-02-22-apps/) | n1234567890ab | 下書き |
```

## 完了チェック

- [ ] `articles/<slug>/article.md` があり、フロントマターに title / tags / eyecatch が揃っている
- [ ] `note-craft` の完了チェックを通した（前置きなし・転がある・タグ 3〜5）
- [ ] `writing` の 2 規範を通した（LLM っぽい空句が残っていない）
- [ ] 画像を Read で目視確認した
- [ ] note に下書きが作られ、プレビューで崩れていないことを実際に見た
- [ ] `articles/README.md` に記事 ID を記録した
- [ ] **公開していない**（公開は人が `/note:note-publish` で判断する）
