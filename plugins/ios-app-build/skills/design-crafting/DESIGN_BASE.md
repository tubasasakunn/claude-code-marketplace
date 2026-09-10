# DESIGN_BASE.md — デザインの基礎嗜好

新規アプリの UI を設計・実装するときの出発点。過去の自作アプリ4本
（createQuestion / hioto / tastingcoffee / mylibrary）の全 Swift ソースを実測調査し、
**アプリを問わず反復していた共通嗜好だけ**を抽出したもの。

> ⚠️ ここに書くのは「毎回無意識にそうしていた共通項」だけ。
> 特定アプリ固有の意匠（固有パレット・キャラクター・特定のテーマ群など）は
> 新アプリが引っ張られないよう意図的に書かない。新アプリ固有の世界観は
> この基礎の上に、そのアプリのコンセプトから導出すること。

---

## 0. 一行で

**静かな紙の上で、コンテンツに色を語らせる。**
クリーム色の「紙」に墨色の文字。カードはフラットか最薄の影。
ブランドの一色を固定せず、コンテンツ・文脈が色を持ち込む。

---

## 1. 色

- **純白・純黒を使わない。**
  - 背景: クリーム系オフホワイト（過去実測は `#F7F4F0` / `#F5EDE3` / `#FAF7F0` / `#FFFBEB` の帯域）。
    「画面」ではなく「紙」を作る。
  - テキスト: 暖色寄りの墨色（`#1F1B16` / `#1A1A1A` 帯域）。副次テキストは暖色グレー（`#6F6A63` 帯域）。
  - ダーク面を作る場合も無彩の黒でなく、暖色に寄せた焦茶〜墨の暗色にする。
- **単一ブランドカラーを固定しない。** アクセントはコンテンツ・文脈・ユーザー選択が決める
  （何がアクセントを決めるかは、そのアプリのコンセプトから導出する）。
  好みの色相はアース・暖色・くすみ系（ブラウン、テラコッタ、くすみティール等）。
  ビビッドな原色をブランド色として据えることはしない。
- **色付き半透明タグのパターン**: アクセント色を opacity 0.1〜0.3 で背景に敷き、
  上に不透明の同系色でテキスト・アイコンを載せる。ダークモードでは opacity を増量補正する。
- 色は必ずセマンティックトークン経由（`Tokens.Colors.textPrimary` 等）。hex のベタ書き禁止。

## 2. 形

- **角丸は 12〜16 の中庸**（カード標準）。必ず `style: .continuous`。
  小要素・チップは 8、シート等の大面は 20 前後。極端に丸くも角ばってもしない。
- **Capsule はチップ・タグ・ピルにだけ**使う。カードは RoundedRectangle。この使い分けを崩さない。
- **影はほぼゼロがベースライン。** まず完全フラットを検討し、輪郭は 1pt のヘアライン枠で取る。
  浮かせる必要があるときだけ最薄から足す（`black.opacity(0.04〜0.1), radius 4〜10, y 2〜5`）。
  強い影は最重要 CTA など 1 画面 1 箇所までの格上げ表現。
- **選択状態は「反転」**: 選択 = 墨色で塗りつぶし＋文字を紙色に反転、
  非選択 = 白地＋1pt ヘアライン。色を足さずに白黒を入れ替える。

## 3. タイポグラフィ

- 基本は**システムフォント（SF Pro）**。weight は medium / semibold / bold 寄り。
- **`.fontDesign(.rounded)` は使わない**（使うとしても局所アクセントに数箇所まで）。
  かわいさより端正さ。
- **serif は「紙的・文学的コンテンツ」にだけ**差す（引用、カード状の記録物、結論の提示など）。
  UI クロームには使わない。
- **数字は mono で大きく見せる**（日付・進捗・統計値）。データを装飾として扱う。
  巨大数字は Dynamic Type 非追従の固定サイズでよい。本文系は Dynamic Type 追従。
- カスタムフォントは飛び道具。導入するなら 2 ファミリまで（本文用＋数字/ラベル用 mono）とし、
  `Font.custom` の直書きを禁止してトークン経由にする。

## 4. 余白

基準の階段（過去2アプリでトークンが完全一致していたもの）:

```
xxs=4  xs=6  sm=8  md=12  lg=16  xl=20  xxl=24  xxxl=32
```

- **標準単位は 16**（カード内 padding・要素間隔）。
- 画面全体の大きな余白（オンボーディング等）だけ 32〜40 に跳ぶ。
- 数値の直書きをせずトークン経由。微調整は `Tokens.Spacing.sm + 2` の形で意図を残す。

## 5. 動き

- **「弾む」より「収まる」**: spring は `response 0.3〜0.5, dampingFraction 0.7〜0.85` の帯域。
  dampingFraction を 0.7 未満にしない。
- **ボタン押下**: `easeOut(duration: 0.18〜0.2)` ＋ `scaleEffect 0.92〜0.96`（＋opacity 0.92 程度）。
- 演出的な遅延アニメ（グラフ描画等）は `easeInOut(1.0〜1.5) + delay` を許容。
- **`@Environment(\.accessibilityReduceMotion)` 対応を全アニメーション箇所で徹底**
  （`reduceMotion ? nil : animation` パターン）。
- アニメーション定義も `Tokens.Motion` に集約する。

## 6. モチーフ・構成の癖

- **アナログ物のメタファー**を好む: 紙・カード・スタンプ・本などの物理的質感を
  デジタルに持ち込む方向で意匠を考える。
- **1点だけの遊び**: 全体は静かに保ち、装飾的な要素（イラスト・大きな記号・フレーム等）は
  1 画面 1 箇所だけに置く。散らさない。
- **テーマ切替（ユーザーが世界観を選べること）**への志向が強い。作る場合はテーマを
  「ライト/ダーク」でなく世界観単位で設計し、詩的な名前を付ける。
  ただし具体のテーマ群は新アプリのコンセプトから起こすこと（過去アプリから流用しない）。
- **実装規律がデザインを担保する**: 数値・色・フォント・モーションは必ず集約レイヤ
  （`Tokens` / `private enum Layout`）経由。直書きゼロを目指す。

---

## 7. 初期トークン（そのまま置いて始めてよい）

背景・墨・階段・モーションは共通嗜好そのもの。アクセントは決め打ちせず、
アプリのコンセプトが決まってから注入する。

```swift
import SwiftUI

enum Tokens {
    enum Colors {
        // 紙と墨。純白・純黒は使わない
        static let background    = Color(hex: "F7F4F0")
        static let card          = Color.white
        static let textPrimary   = Color(hex: "1F1B16")
        static let textSecondary = Color(hex: "6F6A63")
        static let hairline      = Color(hex: "1F1B16").opacity(0.12)
        // アクセントは固定しない。コンテンツ（文脈・テーマ・タグ）から注入する
    }
    enum Radius {
        static let chip: CGFloat = 8
        static let card: CGFloat = 14   // 12〜16 の帯域。必ず style: .continuous
        static let sheet: CGFloat = 20
    }
    enum Spacing {
        static let xxs: CGFloat = 4;  static let xs: CGFloat = 6
        static let sm: CGFloat = 8;   static let md: CGFloat = 12
        static let lg: CGFloat = 16;  static let xl: CGFloat = 20
        static let xxl: CGFloat = 24; static let xxxl: CGFloat = 32
    }
    enum Stroke { static let hairline: CGFloat = 1 }
    enum Motion {
        static let press = Animation.easeOut(duration: 0.18)
        static let standard = Animation.spring(response: 0.4, dampingFraction: 0.8)
    }
}
```

### 署名的コンポーネント①: 反転チップ（選択表現の共通パターン）

```swift
struct SignatureChip: View {
    let label: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.subheadline.weight(isSelected ? .semibold : .regular))
                .foregroundStyle(isSelected ? Tokens.Colors.background
                                            : Tokens.Colors.textPrimary)
                .padding(.horizontal, Tokens.Spacing.lg)
                .padding(.vertical, Tokens.Spacing.sm + 2)
                .background(Capsule(style: .continuous)
                    .fill(isSelected ? Tokens.Colors.textPrimary : Tokens.Colors.card))
                .overlay(Capsule(style: .continuous)
                    .strokeBorder(isSelected ? .clear : Tokens.Colors.hairline,
                                  lineWidth: Tokens.Stroke.hairline))
        }
        .buttonStyle(PressScaleStyle())
    }
}

struct PressScaleStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .opacity(configuration.isPressed ? 0.92 : 1.0)
            .animation(Tokens.Motion.press, value: configuration.isPressed)
    }
}
```

### 署名的コンポーネント②: 紙の上のフラットカード（影なし・ヘアライン輪郭）

```swift
struct PaperCard<Content: View>: View {
    var accent: Color? = nil   // 色はコンテンツから注入。無ければ無彩
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(Tokens.Spacing.lg)
            .background(RoundedRectangle(cornerRadius: Tokens.Radius.card,
                                         style: .continuous)
                .fill(Tokens.Colors.card))
            .overlay(RoundedRectangle(cornerRadius: Tokens.Radius.card,
                                      style: .continuous)
                .strokeBorder((accent ?? Tokens.Colors.textPrimary).opacity(0.1),
                              lineWidth: Tokens.Stroke.hairline))
            // 影を足すなら最薄から: .shadow(color: .black.opacity(0.06), radius: 8, y: 2)
    }
}
```

> `Color(hex:)` イニシャライザは各アプリで用意している拡張を使う（無ければ最初に作る）。

---

## 8. 新アプリ着手時の使い方

1. まずセクション 7 のトークンをそのまま置く（背景・墨・階段・モーションは共通嗜好）。
2. アプリのコンセプトから「何がアクセント色を決めるか」を決める（固定の一色にしない）。
3. serif / mono / 装飾の「1点の遊び」を、そのアプリの世界観から導出する。
4. 迷ったらこのファイルの原則（紙と墨・フラット＋ヘアライン・反転選択・収まる動き）に戻る。

