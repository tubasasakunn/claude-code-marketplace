# 根拠

主張を3段階に分けて記す。**ベンダー実測は査読も第三者検証もない自社データ**で、
「up to（最大）」は平均ではなく best case を指す。方向性の参考にはなるが、
意思決定の唯一の根拠にはしない。

---

## Apple 公式（一次情報）

### 露出についての唯一の記述

> Depending on the orientation of your screenshots, the first one to three images will appear
> in search results **when no app preview is available**, so make sure these highlight the
> essence of your app.

<https://developer.apple.com/app-store/product-page/>

読み取れるのは3点。**① 枚数は 1〜3 枚の幅がある ② 向きによって変わる
③ App プレビュー動画があるとスクショは検索結果に出ない**。
最悪ケースは1枚 → **1枚目が単独で完結する設計が唯一の安全策**。

**「縦なら3枚・横なら1枚」は Apple 公式には存在しない。**
公式5ページと WWDC / Tech Talks のトランスクリプトを走査して不在を確認済み。
出所は ASO ベンダー StoreMaven（後述）。Apple 自身は Tech Talks 110349 で
「landscape か portrait のどちらが効くかはテストせよ」と述べており、規定を置く意図がない。

### 仕様

| 項目 | 内容 |
|---|---|
| 枚数 | 1〜10 枚 |
| 6.9″ 縦 | 1260 × 2736（1290×2796 / 1320×2868 も受理される） |
| 6.9″ 横 | 2736 × 1260 |
| 形式 | .png / .jpg / .jpeg。**アルファチャンネル・透過は不可** |
| 自動縮小 | UI が全デバイスで同一なら最高解像度のみ入稿すれば小サイズへ自動スケール |
| プレビュー | 最大 3 本。**並べ替えても常にスクショより前に表示される**。無音で自動再生 |
| ダークモード | **対応アプリはダークモードのスクショを1枚以上入れることを Apple が推奨** |
| CPP | 最大 70 ページ。キーワードを割り当てると既定ページの代わりに検索結果へ出る |
| PPO | 最大 3 treatment。素材は検索結果と **Today / Games / Apps タブ**にも出る |

構図について Apple が唯一助言しているのは**ダークモードの1枚**だけ。

### 2026 の変化

WWDC26 セッション 205「Enhance your presence on the App Store」で
**Product Page Header**（スクショとは別の画像／動画をページ冒頭に置ける）と
**Asset Library**（全掲載面の素材を一元管理）が導入された。

> Instead of showing the default app screenshots, you can use an impactful image or video,
> to make your app stand out in the Search Results.

**「検索結果に出るのは最初の数枚のスクショ」という前提が崩れる。**
承認済み素材は追加審査なしで Header と検索結果に使い回せる。
<https://developer.apple.com/videos/play/wwdc2026/205/>

### 特集用アートはストア画像と設計思想が正反対

Apple が特集掲載時に要求する Promotional Artwork は
**ロゴ・UI・文字・アプリアイコン・価格・タグライン・Apple 製品や端末の描画がすべて禁止**
（「No logos, UI, or copy of any kind」）。レイヤー分割済みの `.psd`、被写体は切れずに全身、
ユニバーサルテンプレートは 5244 × 2950。Apple 側が改変・合成して各掲載面へ流用する前提。

**文字入りのストア画像は特集用アートに流用できない。** 特集を狙うなら文字なしのキーアートを別途用意する。
仕様全文（JS 不要で読める公式 URL）:
<https://help.apple.com/asc/appspromoart/en.lproj/static.html>

Featuring Nomination は App Store Connect から提出できる。推奨リードタイムは最短3週間、
広い特集狙いは3か月前。補足資料として URL を5本添付できる。

---

## ベンダー実測（StoreMaven／自社計測・第三者検証なし）

同社は「4年超のテストと 5 億超のストアセッションの分析」と自称。現在サイトは消滅しており、
以下はキャッシュから回収した原文にもとづく。

### ユーザーの行動

| 指標 | 値 |
|---|---|
| 即決層（第一印象だけで決める） | 60% |
| 探索層 | 40% |
| 第一印象より先へスクロールしない | 60% |
| 第一印象だけで決めるインストーラ | 50% |
| 第一印象の閲覧時間 | 3〜6 秒 |
| 説明文を開くより画像を見る | 10 倍 |
| 説明文を開いた人のインストール率 | 37% |
| 上位アプリの検索流入比率 | 60〜80% |

### 効果量

| 介入 | 効果 |
|---|---|
| スクショの最適化 | CVR +28% まで |
| ギャラリー全体の最適化 | CVR +40% まで |
| 第一印象の改善 | CV +35% |
| iOS と Android で同じ素材を流用 | iOS で −20〜30% |

### 縦向き vs 横向き — 単純な優劣ではない

| 観点 | 縦向き | 横向き |
|---|---|---|
| 検索結果に出る枚数 | 最初の3枚 | 1枚のみ |
| 上位アプリの採用率（ゲーム以外） | **95%** | — |
| 上位ゲームの採用率 | — | 63% |
| 探索行動 | +13%（ページスクロール +37% / ギャラリースクロール +32%） | 低い |
| 直接インストール率 | — | +11% |
| スクロールした人のインストール率 | — | +24% |
| 検索結果からの CVR（あるゲーム1本の事例） | — | +42% |
| プレビュー動画の視聴率 | — | 2 倍 |

**横向きの効果は「動画とセット」で成立している。**

> going landscape **without having a video** can damage your overall page engagement

横向きギャラリーを使う上位ゲームの 80% 超が動画を1本以上入れている。
さらに落とし穴：**縦横を混在させたうえで動画を入れないと、全スクショが縦向きに強制変換される**。
混在（Hybrid）は上位ゲームでも 5% だけ。

→ **横向きを選ぶなら動画を作る。動画を作らないなら縦向きにする。** どちらかに揃える。

---

## 採取して分かった傾向（実測17本・目視）

- **キャプション位置は17本すべて上部。** 下見出しの例は1本も無かった
- **地に実写を使っている例は1本も無かった。** 「瞑想アプリは実写」は思い込み（Calm は青→紫のグラデーション）
- **1枚目に権威（受賞・掲載・実数）を置くのが最多数派**（Day One / Calm / Headspace / Reflectly / Stoic / Strava / Upmind）
- フレームの有無はほぼ半々
- 枚数は5〜10枚に分布し、10枚が最頻値
- 日本のアプリは**蛍光マーカー・下線装飾・チェックリスト・ピクトグラム・権威三点盛り**を好む

### 採取方法の落とし穴

**iTunes Lookup API の `screenshotUrls` は古いセットを返すことがある。**
Calm では2017年当時のスクショ（ホームボタン機）が返ってきた。Balance / Finch では空配列。
現行の店頭表示を得るには App Store の Web ページに埋め込まれた JSON から取り直す必要がある。

```bash
# 実在確認とメタデータ（スクショURLは古い可能性あり）
curl -s "https://itunes.apple.com/lookup?id=<appId>&country=jp&entity=software"
# 現行のスクショは Web ページの埋め込み JSON から
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15" \
  "https://apps.apple.com/jp/app/id<appId>" | grep -o 'PurpleSource[^"]*_iphone\.png'
```

---

## 未検証

- 「中央値7秒・2.4枚・スクロール率17%」という広く引用される数値の一次出典。
  StoreMaven の 3〜6秒・約40%（=60%がスクロールしない）と食い違う
- StoreMaven 以外（SplitMetrics / AppTweak / yellowHEAD）の独立データ
- 実UIが無い枚（ブランドパネル）が実際に審査 2.3.3 で弾かれるのか。
  Headspace / Stoic / Balance は出荷できている
- 傾け・影が Marketing Guidelines 違反として実際に指摘された事例
