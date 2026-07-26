---
name: sns-post
description: TikTok / Lemon8 向けの「複数画像（カルーセル）投稿」を新規に1本作る。素材合成・本文・ハッシュタグ・index.json まで用意し、post/postN/ に追加して README に反映する。動画ではなく画像を複数枚並べる投稿を作るときに使う。
allowed-tools: Bash, Read, Write, Edit, Glob, WebSearch, WebFetch
---

# SNS 投稿（カルーセル画像）の作成

TikTok（1080x1920 / 9:16）と Lemon8（1080x1440 / 3:4）の**複数画像投稿**を 1 本作る。
仕組みの正本は `post/README.md`、描画エンジンは `post/_brand.py`、コンテンツ定義は
`post/build_posts.py`（画像）と `post/build_index.py`（文言）。ブランド色・ワードマークは
`appstore.config.json`。ここは「次の 1 本を足す手順」だけ。

## 0. 準備

依存は `Pillow`, `numpy`。見出しフォント（Noto Sans/Serif JP）は `build_posts.py` が
実行時に `/tmp` へ取得する（要ネットワーク）。

## 1. 投稿のコンセプトを決める

- アプリのコンセプト・判断軸に整合する切り口か確認する。
- 既存投稿と**角度を変える**（共感ノウハウ / 映え・プロダクト / プライバシー・エモ など）。
- 構成テンプレ：**表紙（フック）→ 共感/日常 → アプリ実画面（証拠）→ ノウハウ/機能 → CTA**。
- プラットフォーム仕様（サイズ・枚数・タグ数・安全域）は `post/README.md` の表が正本。
  古くなっていそうなら WebSearch で確認して README も更新する。

## 2. （任意）フッテージを用意する

表紙・共感スライドの背景は `material/footage/<name>.(jpg|png)` を `bg` で参照する。
投稿ごとに表紙の背景を変えると 1 枚目が差別化される。生成 AI で作るなら
`material/footage/PROMPTS.md` の方針（縦9:16・顔なし・暖色・文字なし）に従う。
無ければアクセント単色のプレースホルダで埋まる。

## 3. スライドを定義する（画像）

`post/build_posts.py` の `POSTS` に `"postN"` を追加する。スライド 5 種
（`cover` / `photo` / `shot` / `info` / `cta`）のフィールドは `post/README.md` の表を参照。

- `accent` は投稿単位で 1 色（`appstore.config.json` の `brand.accents` のキー）。個別上書き可。
- `shot` の緑領域はフッテージで差し替えられる（`footage` キー）。
- TikTok は**下 1/3 に文字を置かない**（renderer が安全域を吸収するが行数を増やしすぎない）。

生成して**必ず目視確認**する（Read で画像を開く）：

```bash
cd post && python3 build_posts.py
```

崩れ・はみ出し・読みにくさがあれば文言量や `accent` を調整して再生成。
代表として cover / shot / info / cta と、3:4 が最もタイトな `lemon8` を確認する。

## 4. 本文とハッシュタグを書く（文言）

`post/build_index.py` の `COPY` に `"postN"` を追加（`tiktok` と `lemon8` 両方）：

- **TikTok**：冒頭フック→本文→CTA。タグ 3〜5（関連性重視）。
- **Lemon8**：掴み / 箇条書き▶ / まとめ / CTA。タグ最大 10、大・中・小を **3:4:3** で混ぜる。
- 直リンクは貼らず「プロフィールのリンクから」へ誘導。

```bash
cd post && python3 build_index.py
```

画像リストは実ファイルから自動収集し、`manifest.json` も更新される。

## 5. 仕上げ

- `post/README.md` の「投稿一覧」に `### postN ── <切り口>` を追記する。
- `post/__pycache__` が出たら消す（`rm -rf post/__pycache__`）。
- コミットはユーザに言われたときだけ（1 投稿 = 1 コミット）。

## 完了チェック

- [ ] `post/postN/{tiktok,lemon8}/` に画像（5〜7枚）と `index.json` が揃っている
- [ ] index.json に title / body / hashtags / images（順序）が入っている
- [ ] 画像を目視確認し、安全域・可読性・ブランド（色・ワードマーク）が崩れていない
- [ ] TikTok タグ 3〜5・Lemon8 タグ 10（大中小 3:4:3）
- [ ] `post/manifest.json` に postN が入っている
- [ ] `post/README.md` の投稿一覧に postN を追記した
