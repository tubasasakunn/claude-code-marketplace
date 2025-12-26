#!/bin/bash
# 全フローを順番に実行するスクリプト
# 使用方法: ./run_all.sh
# 注意: 全てclearStateで毎回クリーンスタート

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 全フロー実行開始"
echo "================================================"

# screenshotsディレクトリをクリーンアップ
rm -rf screenshots/*
mkdir -p screenshots

# オンボーディングフロー
ONBOARDING_FLOWS=($(ls flows/onboarding_*.yaml 2>/dev/null | sort))

if [ ${#ONBOARDING_FLOWS[@]} -gt 0 ]; then
    echo ""
    echo "📱 オンボーディングのスクリーンショット撮影..."
    echo "------------------------------------------------"

    for flow in "${ONBOARDING_FLOWS[@]}"; do
        if [ -f "$flow" ]; then
            echo "▶️  $flow"
            maestro test "$flow" || echo "⚠️  $flow でエラーが発生しました"
        fi
    done
fi

# メイン画面のフロー（数字で始まるファイル）
MAIN_FLOWS=($(ls flows/[0-9]*.yaml 2>/dev/null | sort))

if [ ${#MAIN_FLOWS[@]} -gt 0 ]; then
    echo ""
    echo "📱 メイン画面のスクリーンショット撮影..."
    echo "------------------------------------------------"

    for flow in "${MAIN_FLOWS[@]}"; do
        if [ -f "$flow" ]; then
            echo "▶️  $flow"
            maestro test "$flow" || echo "⚠️  $flow でエラーが発生しました"
        fi
    done
fi

echo ""
echo "================================================"
echo "✅ 全フロー実行完了！"
echo ""
echo "📸 撮影したスクリーンショット:"
ls -la screenshots/*.png 2>/dev/null || echo "スクリーンショットがありません"
