---
name: purchase-health
description: 課金が止まった・購入ボタンを押しても何も起きない・売上が急落した、を診断するランブック。RevenueCat SDK を更新するときのペイウォール設定チェックにも使う。コードを読んでも原因が出てこない類の課金バグ（ダッシュボード設定と SDK バージョンの相互作用）を扱う。
allowed-tools: Read, Grep, Glob, Bash
---

# 課金の健全性チェック（RevenueCat）

**課金は、コードが無罪でも壊れる。** ペイウォールの実体はダッシュボードにあり、
SDK 更新をきっかけに「今まで無視されていた設定」が突然有効になって牙をむく。
git diff をいくら追っても原因は出てこない。だからこのスキルは**サーバー側から**調べる。

`/swift-app:bug-check` は diff に現れるバグを見る。ここで扱うのは diff に現れないバグ。

---

## 1. まず「いつ・どのペイウォールで止まったか」を出す

推測から入らない。売上データが日付とペイウォールを名指ししてくれる。

```
get-chart-data chart_name=actives_new resolution=2 segment=offering_identifier
                start_date=<1年前> currency=JPY
```

`resolution=2` は月次。offering ごとの新規有料サブスク数が並ぶので、
**ゼロに落ちた月**と、**その時どの offering が配信されていたか**が同時に分かる。

落ちた月が分かったら、その前後に何をしたか git log で照合する。

```bash
git log --date=short --pretty='%h %ad %s' --since=<落ちた月の2か月前>
```

見るべきは機能追加ではなく **依存の更新**と**リリース**。SDK のバージョンを上げた
コミットが 1〜2 か月前にあれば、それが本命。

---

## 2. 実際に配信されているペイウォールを特定する

**コードを読んでも、表示されているペイウォールには辿り着けない。**
`PaywallView()` は offering を指定していないことが多く、実際の配信は実験が決める。

```
list-experiments project_id=<proj>
```

`status: running` の実験があれば、`offering_a` / `offering_b` のペイウォールが
新規ユーザーに配信されている。current offering のペイウォールを見ているのは既存ユーザーだけ。

`enrollment_mode: only_new` に注意。**既存アカウントで動作確認しても意味がない。**
正常なペイウォールが出るので、新規ユーザーだけが踏むバグを再現できない。

実験が無ければ `list-offerings` の `is_current: true` の offering がそれ。

---

## 3. 購入ボタンの checkout method を見る

ここが今回の本丸。

```
get-paywall project_id=<proj> paywall_id=<id> expand=["components"]
```

出力は巨大なのでファイルに落ちる。grep で判定する。

```bash
grep -o "web_checkout\|in_app_checkout\|purchase_button" <保存されたファイル> | sort | uniq -c
```

| 結果 | 意味 |
| --- | --- |
| `web_checkout` が出る | **赤信号。** 下の判定へ |
| `in_app_checkout` のみ | 正常（アプリ内購入） |
| `purchase_button` のみで method 無し | 正常（SDK が安全側に倒してアプリ内購入する） |

### 赤信号の判定

**`web_checkout` × Web Billing 未設定 × SDK 5.24.0 以降 = 購入ボタンが死ぬ。**

```
list-apps project_id=<proj>     # type: rc_billing が無ければ Web Billing 未設定
```

```bash
python3 -c "
import json; d=json.load(open('<path>/Package.resolved'))
print([p['state']['version'] for p in d['pins'] if 'purchases' in p['identity']])
"
```

なぜ壊れるか。RevenueCatUI の `PurchaseButtonComponentView` は **SDK 5.24.0**
（コミット `223816fe4` "Allow custom url on purchase button" #5092）で挙動が変わった。

- **5.23 以前** … `method` を一切見ず、常にアプリ内購入を実行していた
- **5.24 以降** … `method` を尊重する。`web_checkout` なら `purchaseInWeb()` に分岐し、
  `webCheckoutUrl` が nil だと `Logger.error` を吐いて **silent return**

Web Billing が無ければ URL は常に nil。つまり**ボタンを押しても何も起きず、
UI にエラーも出ない**。ユーザーからは「進まない」としか報告されない。

SDK のソースは DerivedData に落ちているので、疑わしければ直接読める。

```bash
find ~/Library/Developer/Xcode/DerivedData -maxdepth 4 -name "purchases-ios-spm"
```

---

## 4. 直す

ペイウォールの購入ボタンを `web_checkout` → `in_app_checkout` に変える。
**サーバー配信なのでアプリのリリースは不要。**

```
edit-paywall-ai project_id=<proj> paywall_id=<id>
  prompt="Change ONLY the purchase button's checkout method from web_checkout to
          in-app (store) checkout. Do NOT change any text, color, image, or layout."
get-paywall-ai-task task_id=<返ってきた id>    # succeeded まで 15 秒おきにポーリング
```

**publish する前に diff で検証する。** AI 編集がデザインを崩していないか、
機械的に確かめてからでないと publish しない。

```bash
# 修正前後の components から null 行を落として比較する
diff <(grep -v ": null$" 修正前 | sed 's/^ *//') \
     <(grep -v ": null$" 修正後 | sed 's/^ *//')
```

checkout method と revision 以外に差分が出たら publish せず、ダッシュボードで手作業に切り替える。
`render-paywall-screenshot` で before/after を目視比較するのも併用する。

問題なければ publish して、published 版に `web_checkout` が残っていないことを再確認する。

```
publish-paywall project_id=<proj> paywall_id=<id>
```

既存ユーザーには offerings キャッシュの更新（アプリ再起動〜最大 24h）で行き渡る。

---

## 5. SDK を更新するときの事前チェック

**RevenueCat SDK のバージョンを上げるリリースでは、上げる前にこれを通す。**
壊れてから気づくと、今回のように 3 か月分の売上を失う。

1. `list-experiments` で配信中のペイウォールを把握する
2. 各ペイウォールを `get-paywall expand:["components"]` して `web_checkout` を grep
3. 出たら、SDK を上げる前にペイウォール側を `in_app_checkout` に直す
4. リリース後、**新規インストール**で購入シートが出るところまで確認する

複数アプリを持っているなら、SDK を上げる前に全プロジェクトを一度に見ておく。

```
list-projects                          # 全プロジェクトの id を取る
list-offerings project_id=<各proj>     # paywall_id を取る
get-paywall ... → grep web_checkout
```

---

## 実例

2026-06 から 3 か月間、新規課金がゼロになった実際の事故がある。
時系列・原因・修正・検出の全記録は
`ios-apps/createQuestionApple/Document/2026-08-23-purchase-button-incident.md`。

要点だけ:

- 2025-09 に A/B テストを始めたとき、両バリアントの購入ボタンが `web_checkout` になっていた
- 当時の SDK 5.22.0 はこれを無視していたので、正常に売れ続けた（**設定ミスが表面化しなかった**）
- 2026-05-24 に SDK を 5.74.0 へ更新 → 翌月から購入不能
- アプリのコードは 1 行も変わっていない
