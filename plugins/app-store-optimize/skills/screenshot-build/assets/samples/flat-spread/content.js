/**
 * flat-spread — 正面フレームを斜めに傾けて 2 枚にまたがらせる。
 *
 * 端末は iphone-flat（正面）に `rotate` を掛けているだけで、パースは付けていない。
 * だから画面の中身が歪まず、傾けたまま UI を読ませられる。
 */
window.CONTENT = {
  meta: {
    app: 'Hioto',
    size: { w: 1320, h: 2868 },
  },

  theme: {
    bg: '#6E62C6',
    bgDeep: '#4B3F9E',
    ink: '#FFFFFF',
    sub: 'rgba(255, 255, 255, .8)',
    badgeBg: '#FFFFFF',
    badgeInk: '#4B3F9E',
  },

  wordmark: {
    icon: '../../apps/hioto/material/app_icon_1024.png',
    text: 'Hioto',
  },

  /**
   * 1・2 枚目にまたがる 1 台。座標は 2640×2868 のまたぎキャンバス。
   *
   * iphone-flat は画像 1024 のほぼ中央に画面があるので（中心 516.5, 511.5 ≒ 512,512）、
   * **回転させても画面の中心はモック要素の中心とほぼ一致する**。だから
   * `x + w/2` `y + w/2` がそのまま画面の中心になり、置き場所を決めやすい。
   *
   * ここでは中心を (1490, 1560) に置いた。切れ目（x=1320）より右へ寄せてあるので、
   * 1 枚目には端末の左端だけが入り、2 枚目が主役になる。Reflectly と同じ配分。
   * 見出しは 3 行に割って右端を 770 あたりで止め、端末とぶつからないようにしている。
   * 傾きは右回り（正）。左回りにすると左上の角が張り出して見出しに近づくが、
   * 右回りでは左下の角が張り出すので、1 枚目に入る量が減る。そのぶん x を左へ寄せてある。
   * 3・4 枚目は傾けない。読ませる枚なので、正面のまま素直に見せる。
   */
  spreads: [
    {
      pages: [0, 1],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/03_shorts.png',
        w: 2600, x: 190, y: 260, rotate: 20,
      },
    },
  ],

  shots: [
    // 1 枚目。文字が主役。端末は左端だけ覗く。
    {
      variant: 'hero',
      headline: ['撮るだけで、', '1日が', 'のこる。'],
      wordmark: true,
    },

    // 2 枚目。またいできた端末が主役。
    {
      variant: 'spread',
      badge: { lines: ['長押し', 'するだけ'], x: '22%', y: '80%', rotate: -7 },
    },

    {
      variant: 'flat',
      headline: ['その日が、勝手に', '1本の動画になる'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/05_insights.png',
        w: 2400, x: -550, y: 700,
      },
    },

    {
      variant: 'flat',
      headline: ['カレンダーに、', '日々が積もる'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/04_calendar.png',
        w: 2400, x: -550, y: 700,
      },
      badge: { lines: ['ぜんぶ', '端末の中'], x: '84%', y: '26%', rotate: 8 },
    },
  ],
};
