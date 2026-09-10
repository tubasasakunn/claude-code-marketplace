/**
 * deep-tilt — 寝かせた端末（iphone-lay）を目一杯使う型。
 *
 * lay は端末が横倒しなので、画面の中身も一緒に寝る。UI の細部は読めなくなるが、
 * 写真・映像そのものを大きく見せられる。Hioto のように「画面に映るもの」が
 * 主役のアプリ向け。読ませたい枚は 3・4 枚目で tilt / flat に切り替えている。
 */
window.CONTENT = {
  meta: {
    app: 'Hioto',
    size: { w: 1320, h: 2868 },
  },

  theme: {
    bg: '#17161C',
    bgLift: '#2A2733',
    ink: '#FFFFFF',
    sub: 'rgba(255, 255, 255, .68)',
    accent: '#E07B54',
    badgeBg: '#E07B54',
    badgeInk: '#17161C',
  },

  wordmark: {
    icon: '../../apps/hioto/material/app_icon_1024.png',
    text: 'Hioto',
  },

  /**
   * 1・2 枚目にまたがる寝かせた 1 台。座標は 2640×2868 のまたぎキャンバス。
   *
   * iphone-lay は画像 1024 の中で画面が x=3〜1010（中心 506.5）に入る。
   * 表示幅 3000（= 2.930 倍）なら画面は x+9〜x+2959、中心は x+1484。
   * x=-164 とすると画面が -155〜2795 に来て、切れ目（1320）の両側に均等に入る。
   *
   * 横倒しなので画面は横長に伸びる。またぎとの相性がよく、2 枚を貫く 1 本の帯になる。
   */
  spreads: [
    {
      pages: [0, 1],
      mock: {
        name: 'iphone-lay',
        shot: '../../apps/hioto/material/note/03_shorts.png',
        w: 3000, x: -164, y: 165,
      },
    },
  ],

  shots: [
    {
      variant: 'hero',
      headline: ['撮るだけで、', '<em>1日</em>がのこる。'],
      wordmark: true,
    },

    // 2 枚目。またいできた端末が主役。
    {
      variant: 'spread',
      badge: { lines: ['1日', '3秒で'], x: '74%', y: '80%', rotate: -8 },
    },

    // ここから読ませる枚。傾きを浅くして UI を追えるようにする。
    {
      variant: 'tilt',
      headline: ['その日が、勝手に', '1本の動画になる'],
      mock: {
        name: 'iphone-tilt',
        shot: '../../apps/hioto/material/note/05_insights.png',
        w: 2100, x: -378, y: 600,
      },
    },

    {
      variant: 'flat',
      headline: ['カレンダーに、', '日々が積もる'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/04_calendar.png',
        w: 2600, x: -651, y: 572,
      },
      badge: { lines: ['ぜんぶ', '端末の中'], x: '86%', y: '27%', rotate: 7 },
    },
  ],
};
