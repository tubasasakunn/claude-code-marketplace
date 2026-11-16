# 比較実験の回答

JSONのみ。各入力IDを一度ずつ出す。確率の順番は0–999、1,000–9,999、10,000–99,999、100,000–999,999、1,000,000以上。

```json
{"items":[{"id":"opaque-id","estimate":10000,"lower":100,"upper":1000000,"probabilities":[0.2,0.2,0.2,0.2,0.2],"generic":"high|mixed|low|uncertain","evidence":"短い逐語引用","reason":"中心値と二軸の理由","recognition_risk":false,"limit":"未校正、本文から観測できない要因"}]}
```

数値は0以上、lower <= estimate <= upper、probabilitiesは非負で合計1。genericは選択肢のいずれか。中心値は桁単位の予測を基本とし、12345人のような細かい精度を装わない。例の数値は既定値や正解ではない。実際に本文から推定する。
