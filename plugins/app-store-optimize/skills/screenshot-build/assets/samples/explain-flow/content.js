/**
 * explain-flow — 横向き（2868×1320）。左に端末、右に言葉。
 *
 * `mocks` に複数台を並べ、`arrows` でつなぐ。`checklist` は ☑ の箇条書き、
 * 見出しの `<mark>` は蛍光ペンになる。
 *
 * ★ 横向きは App Store の検索結果に 1 枚しか出ない（縦なら 3 枚）。
 *   縦横の混在もできないので、採用すると全枚が横向きになる。
 */
window.CONTENT = {
  meta: {
    app: 'Hioto',
    // iPhone 6.9" の横向き。縦の 1320×2868 を入れ替えたもの。
    size: { w: 2868, h: 1320 },
  },

  theme: {
    paper: '#F4F2EE',
    ink: '#221E1A',
    sub: '#6F655C',
    marker: '#A8C5A0',
    accent: '#C25A33',
    badgeBg: '#221E1A',
    badgeInk: '#F4F2EE',
  },

  shots: [
    {
      variant: 'flow',
      headline: ['<mark>長押しするだけ</mark>で', '1日がのこる'],
      checklist: ['編集はいらない！', '1日ぶんが 3 秒！', 'ぜんぶ端末の中！'],
      // 左（小）が Before、右（大）が After。後に書いた方が手前に来る。
      // 手前（Before）は小さく、矢印の先（After）は大きく。視線が左から右へ流れる。
      // 回転させると見かけの幅が広がるぶん 2 台が近づくので、隙間は多めに取る。
      mocks: [
        {
          name: 'iphone-flat',
          shot: '../../apps/hioto/material/note/01_camera.png',
          w: 900, x: 90, y: 380, rotate: -8,
        },
        {
          name: 'iphone-flat',
          shot: '../../apps/hioto/material/note/03_shorts.png',
          w: 1500, x: 800, y: 150, rotate: 3,
        },
      ],
      arrows: [{ from: [790, 640], to: [1210, 470], bend: 0.4, width: 16, head: 52 }],
    },

    {
      variant: 'flow',
      headline: ['撮った日が', '<mark>カレンダー</mark>に積もる'],
      checklist: ['日ごとに 1 本！', '月のふり返りつき！', '見たい日にすぐ飛べる！'],
      mocks: [
        {
          name: 'iphone-flat',
          shot: '../../apps/hioto/material/note/03_shorts.png',
          w: 900, x: 90, y: 380, rotate: -8,
        },
        {
          name: 'iphone-flat',
          shot: '../../apps/hioto/material/note/04_calendar.png',
          w: 1500, x: 800, y: 150, rotate: 3,
        },
      ],
      arrows: [{ from: [790, 640], to: [1210, 470], bend: 0.4, width: 16, head: 52 }],
    },

    // 3・4 枚目は 1 台だけ。説明を続けると単調になるので、画面そのものを見せる。
    {
      variant: 'flat',
      headline: ['その日が、勝手に', '1本の動画になる'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/05_insights.png',
        w: 1700, x: 400, y: 90,
      },
    },

    {
      variant: 'flat',
      headline: ['ぜんぶ、', 'この端末の中だけ'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/02_clip-review.png',
        w: 1700, x: 400, y: 90,
      },
      badge: { lines: ['送信', 'しません'], x: '57%', y: '24%', rotate: 7 },
    },
  ],
};
