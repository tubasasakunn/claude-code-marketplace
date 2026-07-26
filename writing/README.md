# writing — 日本語の文章規範

| スキル | 中身 |
|---|---|
| `japanese-tech-writing` | 技術文書・書籍原稿の規範。一文一行・パラグラフライティング・論証の厳密さ・読み手の負荷・視点と語り・演出の抑制・LLM っぽい空句の禁止・冗長の排除 |
| `cognitive-rhythm-writing` | 緩急の設計。装飾ではなく認知モードの切替（観察→逡巡→断定→再観察）と未回収の緊張の管理として扱い、文の拍・段落の密度波形・駄文の判別・執筆後の点検手順を定める |

## 出所（★ここは他人の著作）

どちらも **k16shikano さんの gist からコピーしたもの**。参照ではなくコピーなので、
**更新は自動で入らない**（gist に `.claude-plugin/plugin.json` が無く、プラグインとして
参照できないため）。

| スキル | 元 gist | 取得時点 |
|---|---|---|
| `japanese-tech-writing` | https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d | 2026-07-24 の版 |
| `cognitive-rhythm-writing` | https://gist.github.com/k16shikano/eb2929f13ed19c97188393d297be8432 | 2026-07-09 の版 |

更新を取り込むときは上の gist を見て差分を当てる:

```bash
git clone https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d.git /tmp/g1
diff /tmp/g1/SKILL.md writing/skills/japanese-tech-writing/SKILL.md
```

**内容には手を入れないこと。** 自分の好みを足したいときは別スキルに分けて、こちらは
上流のコピーとして保つ（そうしないと更新の取り込みができなくなる）。
