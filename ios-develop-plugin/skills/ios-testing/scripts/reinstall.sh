#!/bin/bash
# アプリを再インストールしてオンボーディングを初期化するスクリプト
# 使用方法: ./reinstall.sh
#
# 注意: APP_ID を環境変数またはスクリプト内で設定してください

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# アプリのBundle ID（プロジェクトに合わせて変更）
APP_ID="${APP_ID:-com.example.myapp}"

echo "🔄 アプリ再インストール: $APP_ID"
echo "================================================"

# 起動中のシミュレータを取得
BOOTED_DEVICE=$(xcrun simctl list devices | grep "Booted" | head -1 | sed 's/.*(\([A-F0-9-]*\)).*/\1/')

if [ -z "$BOOTED_DEVICE" ]; then
    echo "❌ エラー: 起動中のシミュレータがありません"
    echo "以下のコマンドでシミュレータを起動してください:"
    echo "  xcrun simctl boot \"iPhone 16 Pro\""
    echo "  open -a Simulator"
    exit 1
fi

echo "📱 シミュレータ: $BOOTED_DEVICE"

# アプリをアンインストール
echo "🗑️  アプリをアンインストール中..."
xcrun simctl uninstall "$BOOTED_DEVICE" "$APP_ID" 2>/dev/null || echo "（既にアンインストール済み）"

# Xcodeでビルド・インストール（プロジェクトがある場合）
if [ -f "../*.xcodeproj" ] || [ -f "../*.xcworkspace" ]; then
    echo "🔨 アプリをビルド・インストール中..."

    # xcworkspaceがあればそちらを使用
    if ls ../*.xcworkspace 1> /dev/null 2>&1; then
        WORKSPACE=$(ls ../*.xcworkspace | head -1)
        xcodebuild -workspace "$WORKSPACE" \
            -scheme "$(basename "$WORKSPACE" .xcworkspace)" \
            -destination "id=$BOOTED_DEVICE" \
            -configuration Debug \
            build install \
            2>/dev/null || echo "⚠️ ビルドに失敗しました。Xcodeでビルドしてください。"
    else
        PROJECT=$(ls ../*.xcodeproj | head -1)
        xcodebuild -project "$PROJECT" \
            -scheme "$(basename "$PROJECT" .xcodeproj)" \
            -destination "id=$BOOTED_DEVICE" \
            -configuration Debug \
            build install \
            2>/dev/null || echo "⚠️ ビルドに失敗しました。Xcodeでビルドしてください。"
    fi
else
    echo "📝 Xcodeでアプリをビルド・インストールしてください"
fi

echo ""
echo "================================================"
echo "✅ 完了！"
echo ""
echo "次のステップ:"
echo "  1. Xcodeでアプリをビルド・実行（必要な場合）"
echo "  2. ./run.sh flows/onboarding_01.yaml でオンボーディングを撮影"
