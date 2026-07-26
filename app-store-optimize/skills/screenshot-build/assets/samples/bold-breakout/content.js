/**
 * ★ このファイルだけ書き換えれば別アプリのストア画像になる。
 *
 * 位置はすべて px。1 枚は 1320×2868。
 * `spreads` だけは「またぎキャンバス」（1320 × またぐ枚数）の座標で書く。
 *
 * mock … 端末モックアップ。name は mockup/ にあるもの（prep_mockup.py で増やせる）。
 *        w はモック画像そのものの表示幅で、画面はその中の一部。rotate で傾けられる。
 * breakouts … スクリーンショットの一部を切り出して端末の外へ飛ばす。
 *        rect は元画像のピクセル座標 [x, y, w, h]。tools/measure_cards.py で測れる。
 */
window.CONTENT = {
  meta: {
    app: 'Hioto',
    size: { w: 1320, h: 2868 },
  },

  theme: {
    bgFrom: '#E4794A',
    bgVia: '#C8542C',
    bgTo: '#8E3418',
    ink: '#FFFFFF',
    sub: 'rgba(255, 255, 255, .82)',
    // 背景の暖色に対して沈まない寒色を 1 色だけ差す。Otter が青地に緑を置くのと同じ役割。
    badgeBg: '#2F6B5C',
    badgeInk: '#FFFFFF',
  },

  wordmark: {
    icon: '../../apps/hioto/material/app_icon_1024.png',
    text: 'Hioto',
  },

  /**
   * 1 枚目と 2 枚目にまたがる 1 台。座標は 2640×2868 のまたぎキャンバス。
   *
   * 数値は tools/edit.mjs で画面を見ながら決めたもの。目安として、
   * iphone-tilt は画像 1024 の中で画面が x=99.7〜913 / y=5.3〜995 に入っているので、
   * 表示幅 3520（= 3.4375 倍）のいま、画面は x=-189〜2606 / y=20〜3422 を占める。
   *
   * つまり左右も下も大きくキャンバスの外へ抜けていて、端末は「全体を見せる」のを
   * やめて画面の中身だけを大きく見せる置き方になっている。切れ目（x=1320）は
   * 画面のやや右寄りを通る。
   */
  spreads: [
    {
      pages: [0, 1],
      mock: {
        name: 'iphone-tilt',
        shot: '../../apps/hioto/material/note/03_shorts.png',
        w: 3520, x: -532, y: 2,
      },
      breakouts: [
        {
          // rect はカードの外周。白判定だけで測ると下の細字が切れるので、
          // 実際のカードの下端（y=1030）まで含める。
          src: '../../apps/hioto/material/note/04_calendar.png',
          rect: [20, 830, 580, 200],
          w: 800, x: 89, y: 1265, rotate: -5,
        },
        {
          src: '../../apps/hioto/material/note/05_insights.png',
          rect: [28, 230, 562, 162],
          w: 760, x: 1581, y: 1720, rotate: -3,
        },
      ],
    },
  ],

  shots: [
    // 1 枚目。文字とワードマーク。端末は spreads が置く。
    {
      variant: 'hero',
      headline: ['撮るだけで、', '1日が', 'のこる。'],
      wordmark: true,
    },

    // 2 枚目。1 枚目から続く端末が主役なので、見出しは置かずバッジだけ。
    {
      variant: 'tilt',
      badge: { lines: ['1日', '3秒で'], x: '68%', y: '77.29%', rotate: -8 },
    },

    {
      variant: 'flat',
      headline: ['その日が、勝手に', '1本の動画になる'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/03_shorts.png',
        w: 2550, x: -625, y: 650,
      },
    },

    {
      variant: 'flat',
      headline: ['カレンダーに、', '日々が積もる'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/04_calendar.png',
        w: 2550, x: -625, y: 650,
      },
      badge: { lines: ['ぜんぶ', '端末の中'], x: '88%', y: '30%', rotate: 7 },
    },
  ],
};
