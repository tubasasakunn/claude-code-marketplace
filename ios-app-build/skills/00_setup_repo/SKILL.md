---
name: 00_setup_repo
description: 新規iOSアプリのリポジトリを作ります。swift-base テンプレートのコピー、appstore.config.json の記入、xcodegen プロジェクト生成、GitHub リポジトリ作成と push、production ブランチ、Actions 権限、Secrets 投入までを一気に行います。CONCEPT.md と DESIGN.md ができた直後、01_create_xcode_cicd の前に実行してください。
---

# リポジトリのセットアップ (00_setup_repo)

## このスキルの位置

```
concept-crafting → design-crafting → [00_setup_repo] → 01_create_xcode_cicd → 02_register_appstore → ...
```

`Idea/<連番>_<アプリ名>/CONCEPT.md` と `DESIGN.md` が既にあることが前提。

## リポジトリの配置

app-builder は submodule でアプリと共有物を束ねる。

```
app-builder/
  .claude/skills/     このスキル群
  Idea/00N_<名前>/    CONCEPT.md, DESIGN.md
  common/
    swift-base/       submodule: テンプレート（毎回 pull して使う）
    marketing/        submodule: ストア画像・SNS 投稿の素材とスクリプト
  apps/
    <appname>/        submodule: 各アプリ（このスキルで作る）
```

**submodule は毎回最新に追従させる。** テンプレートの修正が取りこぼされる。

```bash
cd ~/workspace_tmp/ios-app-build-workspace
git submodule update --init --remote common/swift-base common/marketing
```

## 前提の確認

```bash
gh auth status                 # GitHub CLI がログイン済みか
which xcodegen || brew install xcodegen
ls common/swift-base           # テンプレートがあるか（無ければ上の update）
```

`${CLAUDE_PLUGIN_ROOT}/scripts/README.md` を読み、`asc_api.js` の認証情報（`~/.asc-key.json` か環境変数）を用意しておく。
`HARNESS_TOKEN` はこのスキルでは使わない（`01` 以降で使う）。

Cloudflare のトークンは `~/workspace_tmp/ios-app-build-workspace/.env` にある（`CLOUDFLARE_DEPLOY_TOKEN` / `CLOUDFLARE_ACCOUNT_ID`）。

## このスキルの範囲

**やる**: リポジトリ、ビルドが通る最小のアプリ、CI の足回り、GitHub の設定。

**やらない**（後のスキルの担当）:

- P0 機能の実装（`03_implement_app`）
- `release/<version>/` の文言・スクショ（`05_release_assets`）。**この時点ではプレースホルダのままでよい**
- App Store Connect 側の登録（`01` と `02`）

`check_release_metadata.py` はプレースホルダのままでも PASS してしまう。**ここで通っても「文言が入った」ことにはならない**。

## Step 1. テンプレートをコピーする

`swift-base` は「ストア提出・ASO・CI/CD の足回り」だけを持つテンプレート。**Swift のアプリコードは入っていない**（自分で書く）。

```bash
ROOT=~/workspace_tmp/ios-app-build-workspace
APP=Bide                       # Xcode のプロジェクト名（英字、CONCEPT.md のアプリ名）
SLUG=$(echo $APP | tr '[:upper:]' '[:lower:]')
BUNDLE=com.basaapp.$SLUG

# アプリの実体は一旦ワークツリーの外に作る（submodule は空ディレクトリに add できないため）
DIR=~/workspace/$SLUG
mkdir -p "$DIR"
rsync -a --exclude .git "$ROOT/common/swift-base/" "$DIR/"
cd "$DIR"
git init -q && git branch -m main

# 仕様書を直下に置く（実装時に参照する）
cp "$ROOT"/Idea/<連番>_$APP/CONCEPT.md .
cp "$ROOT"/Idea/<連番>_$APP/DESIGN.md .    # 無ければ省略してよい
```

## Step 2. appstore.config.json を実値で埋める

このファイルが `scripts/` と `fastlane/` の**正本**。プレースホルダのままだと後続のスクリプトが全部壊れる。

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('appstore.config.json')
c = json.loads(p.read_text())
c['app']['name'] = 'Kazoe'
c['app']['bundle_id'] = 'com.basaapp.kazoe'
c['app']['scheme'] = 'Kazoe'
c['app']['xcodeproj'] = 'Kazoe.xcodeproj'
c['app']['deployment_target'] = '17.0'
c['appstore']['contact_email'] = 'bassa.application@gmail.com'
c['appstore']['github_repo'] = 'tubasasakunn/kazoe'
c['appstore']['marketing_domain'] = 'kazoe.basaapp.com'
p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + '\n')
PY
```

`brand` の色は `DESIGN.md` のカラーパレットから写す（DESIGN.md がまだ無ければ後回しでよい）。

`marketing_domain` は **プロトコル無しのホスト名**で書く（`kazoe.basaapp.com`）。テンプレートの既定値は `https://` 付きだが、後段のスクリプトはホスト名を期待する。

**カテゴリ**は `App Store Connect` のカテゴリ定数（大文字スネークケース）。CONCEPT.md に指定が無ければ、アプリの性質から選ぶ。よく使うもの:

`PRODUCTIVITY` / `LIFESTYLE` / `UTILITIES` / `HEALTH_AND_FITNESS` / `PHOTO_AND_VIDEO` / `EDUCATION`

> 実際に ASC へ反映されるのは `release/<version>/primary_category.txt` の方で、`appstore.config.json` の `appstore.primary_category` はどのスクリプトからも読まれない。**両方に同じ値を書いておくこと**（食い違うと後で混乱する）。

```bash
echo "LIFESTYLE"    > release/1.0/primary_category.txt
echo "PRODUCTIVITY" > release/1.0/secondary_category.txt
```

## Step 3. project.yml と最小のアプリコードを置く

xcodegen 運用にする（`.xcodeproj` は git 管理しない。`project.yml` が正本）。

`deploymentTarget` は **CONCEPT.md の記載を優先する**（下の例の値は例示にすぎない）。
`DEVELOPMENT_TEAM` は **Apple Developer の Team ID**。この組織では `7NN5KD3TSU`。確認するには:

```bash
node ${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js GET "/v1/bundleIds?limit=1" | python3 -c "
import json,sys; s,b=sys.stdin.read().split('\n',1); print(json.loads(b)['data'][0]['attributes']['seedId'])
"
```

```yaml
# project.yml  （Bide の例。名前・bundle id・deploymentTarget は自分のアプリの値に置き換える）
name: Bide
options:
  bundleIdPrefix: com.basaapp
  deploymentTarget:
    iOS: "17.0"
  developmentLanguage: ja
  createIntermediateGroups: true

settings:
  base:
    MARKETING_VERSION: "1.0"
    CURRENT_PROJECT_VERSION: "1"
    SWIFT_VERSION: "5.0"
    SWIFT_APPROACHABLE_CONCURRENCY: YES
    SWIFT_DEFAULT_ACTOR_ISOLATION: MainActor

targets:
  Bide:
    type: application
    platform: iOS
    deploymentTarget: "17.0"
    sources:
      - path: Bide
    settings:
      base:
        PRODUCT_NAME: Bide
        PRODUCT_BUNDLE_IDENTIFIER: com.basaapp.bide
        INFOPLIST_FILE: Bide/Info.plist
        GENERATE_INFOPLIST_FILE: NO
        ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon
        TARGETED_DEVICE_FAMILY: "1"
        # 自動署名。アーカイブ時は CODE_SIGNING_ALLOWED=NO で回避するのでここは Automatic のままでよい。
        DEVELOPMENT_TEAM: 7NN5KD3TSU
        CODE_SIGN_STYLE: Automatic
```

### Info.plist（`GENERATE_INFOPLIST_FILE: NO` なので全部自分で書く）

3キーだけでは Xcode のバリデーションを通らない。最低限これだけ要る。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key><string>ja</string>
  <key>CFBundleExecutable</key><string>$(EXECUTABLE_NAME)</string>
  <key>CFBundleIdentifier</key><string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>CFBundleName</key><string>$(PRODUCT_NAME)</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>$(MARKETING_VERSION)</string>
  <key>CFBundleVersion</key><string>$(CURRENT_PROJECT_VERSION)</string>
  <!-- 独自暗号を使わない宣言。書いておくと審査時の輸出コンプラ質問を自動で満たせる -->
  <key>ITSAppUsesNonExemptEncryption</key><false/>
  <key>UILaunchScreen</key><dict/>
  <key>UISupportedInterfaceOrientations</key>
  <array><string>UIInterfaceOrientationPortrait</string></array>
</dict>
</plist>
```

### Assets.xcassets（AppIcon のプレースホルダ）

`ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon` を指定したので、空だとビルドが警告・審査で弾かれる。1024×1024 の PNG を1枚置く。

```bash
mkdir -p $APP/Assets.xcassets/AppIcon.appiconset
cat > $APP/Assets.xcassets/Contents.json <<'JSON'
{ "info": { "author": "xcode", "version": 1 } }
JSON
cat > $APP/Assets.xcassets/AppIcon.appiconset/Contents.json <<'JSON'
{
  "images": [{ "filename": "icon.png", "idiom": "universal", "platform": "ios", "size": "1024x1024" }],
  "info": { "author": "xcode", "version": 1 }
}
JSON
# 単色のプレースホルダを生成（本番アイコンは後のスキルで差し替える）
python3 -c "
from PIL import Image
Image.new('RGB', (1024, 1024), (200, 200, 200)).save('$APP/Assets.xcassets/AppIcon.appiconset/icon.png')
"
```

### ビルド確認

`.gitignore` に `*.xcodeproj` を足す。そのうえで生成してビルドが通ることを確認する。

```bash
xcodegen generate
xcodebuild -project $APP.xcodeproj -scheme $APP \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro Max' build 2>&1 | tail -30
```

**`** BUILD SUCCEEDED **` を確認してから次へ。** 01 のウィザードはビルドできるプロジェクトを要求する。
失敗したら `tail -30` の中の `error:` 行を読む（`tail -3` では原因が見えない）。

## Step 4. xcodegen 運用に伴う CI の2箇所を直す ★忘れやすい

`.xcodeproj` を git 管理しないので、CI が clone した直後には存在しない。**pbxproj を読む処理が2つあり、両方とも直さないと後で必ず落ちる。**

新しめの swift-base では対応済みのはず。**実際に中身を見て確認すること。**

### 4-1. `ci_scripts/ci_post_clone.sh`（Xcode Cloud が実行する）

`PBXPROJ=` の行の**直後**（pbxproj を書き換える処理の手前）に入れる。

```sh
if [ ! -d "$REPO/$XCODEPROJ" ] && [ -f "$REPO/project.yml" ]; then
    command -v xcodegen >/dev/null 2>&1 || brew install xcodegen
    (cd "$REPO" && xcodegen generate)
fi
```

### 4-2. `scripts/sync_fastlane_metadata.py`（GitHub Actions が ubuntu で実行する）

こちらは **xcodegen を入れられない**（ubuntu ランナー）ので、`project.yml` から直接読ませる。`marketing_version()` を次のように直す。

```python
def marketing_version() -> str:
    xcodeproj = get("app", "xcodeproj", default="App.xcodeproj")
    pbxproj_path = ROOT / xcodeproj / "project.pbxproj"
    if pbxproj_path.exists():
        versions = set(re.findall(r"MARKETING_VERSION = ([^;]+);", pbxproj_path.read_text()))
    else:
        versions = set(
            re.findall(r'MARKETING_VERSION:\s*"?([\d.]+)"?', (ROOT / "project.yml").read_text())
        )
    if not versions:
        sys.exit(f"{xcodeproj} / project.yml から MARKETING_VERSION が読めない")
```

**検証する。** `.xcodeproj` を一時的にリネームして、それでも動くことを確かめる。

```bash
mv $APP.xcodeproj /tmp/_x && python3 scripts/sync_fastlane_metadata.py; mv /tmp/_x $APP.xcodeproj
```

`synced release/1.0 -> fastlane/ ...` と出れば OK。`FileNotFoundError` なら直っていない。

## Step 5. GitHub リポジトリを作り、app-builder に submodule として繋ぐ

```bash
cd "$DIR"
git add -A && git commit -qm "Initial commit from swift-base"
gh repo create "$SLUG" --private --source=. --push

# 審査提出用のブランチ（appstore-release.yml が production への push で発火する）
git branch production && git push -q origin production

# app-builder の apps/ 配下に繋ぐ
cd "$ROOT"
git submodule add -q "git@github.com:tubasasakunn/$SLUG.git" "apps/$SLUG"
git add .gitmodules "apps/$SLUG"
git commit -qm "apps/$SLUG を submodule として追加"
git push -q origin main
```

以降 `apps/$SLUG` が作業ディレクトリになる（`~/workspace/$SLUG` と同じリポジトリの別チェックアウトにはしない。
**混乱するので、実体は `apps/$SLUG` に一本化し、`~/workspace/$SLUG` は消してよい**）。

## Step 6. Actions の権限と Secrets ★全部コマンドでできる

SETUP.md には「手作業」と書いてあるが、**すべて自動化できる**。

```bash
# Actions が PR を作れるようにする（release-pr.yml が必要とする）
gh api -X PUT repos/tubasasakunn/$(basename $DIR)/actions/permissions/workflow \
  -f default_workflow_permissions=write -F can_approve_pull_request_reviews=true

# App Store Connect API キー（App Manager ロール）
gh secret set ASC_KEY_ID      --body "$ASC_KEY_ID"
gh secret set ASC_ISSUER_ID   --body "$ASC_ISSUER_ID"
gh secret set ASC_KEY_CONTENT --body "$(base64 -i "$ASC_P8" | tr -d '\n')"

# 審査連絡先（fastlane deliver が必須要求する。空文字だと落ちる）
gh secret set ASC_CONTACT_FIRST_NAME --body "TSUBASA"
gh secret set ASC_CONTACT_LAST_NAME  --body "WAKAIKI"
gh secret set ASC_CONTACT_PHONE      --body "+81..."       # E.164 形式
gh secret set ASC_CONTACT_EMAIL      --body "bassa.application@gmail.com"

# front/ の自動デプロイ用（04_build_front で使う）
gh secret set CLOUDFLARE_API_TOKEN  --body "$CLOUDFLARE_DEPLOY_TOKEN"
gh secret set CLOUDFLARE_ACCOUNT_ID --body "$CLOUDFLARE_ACCOUNT_ID"

gh secret list
```

審査連絡先の実値は、既にリリース済みの別アプリから API で写せる（新規に考える必要はない）。
2段階で取る: アプリ → その版 → 審査連絡先。

```bash
export ASC_API=${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js
REF_APP=6789139306   # 既存アプリ（Nagasu）の appId

# 1) 版の id を得る
VID=$(node $ASC_API GET "/v1/apps/$REF_APP/appStoreVersions?limit=1" | python3 -c "
import json,sys; s,b=sys.stdin.read().split('\n',1); print(json.loads(b)['data'][0]['id'])
")

# 2) 連絡先を読む
node $ASC_API GET "/v1/appStoreVersions/$VID/appStoreReviewDetail" | python3 -c "
import json,sys; s,b=sys.stdin.read().split('\n',1); a=json.loads(b)['data']['attributes']
print(a['contactFirstName'], a['contactLastName'], a['contactPhone'], a['contactEmail'])
"
```

> swift-base には `scripts/set_asc_secrets.sh`（`.env` を埋めて一括投入するスクリプト）も入っている。
> 好きな方を使ってよいが、**`gh secret set` を直接叩く方が、何が入るか明示的で確認しやすい**。

## Step 7. 確認

```bash
gh repo view --json name,visibility,defaultBranchRef
git branch -a
gh secret list
ls .github/workflows/     # appstore-metadata.yml / appstore-release.yml / release-pr.yml
```

## 完了条件

- [ ] `xcodebuild ... build` が `BUILD SUCCEEDED`
- [ ] GitHub に main と production の両ブランチが push されている
- [ ] `gh secret list` に ASC_* / ASC_CONTACT_* / CLOUDFLARE_* が並ぶ
- [ ] Actions の workflow permissions が `write` / PR作成可
- [ ] `ci_scripts/ci_post_clone.sh` に xcodegen 生成が入っている
- [ ] `appstore.config.json` にプレースホルダ（`<...>` や `MyApp`）が残っていない

## 次のスキル

`01_create_xcode_cicd` — Xcode の GUI を自動操作して、アプリレコードと Xcode Cloud の product を作る。
