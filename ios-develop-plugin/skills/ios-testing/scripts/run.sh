#!/bin/bash
# Maestroフロー実行スクリプト
# 使用方法: ./run.sh flows/01_home.yaml

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 引数チェック
if [ -z "$1" ]; then
    echo "使用方法: ./run.sh <flow.yaml>"
    echo "例: ./run.sh flows/01_home.yaml"
    echo ""
    echo "利用可能なフロー:"
    ls -1 flows/*.yaml 2>/dev/null | sed 's/^/  /'
    exit 1
fi

FLOW_FILE="$1"

# ファイル存在チェック
if [ ! -f "$FLOW_FILE" ]; then
    echo "エラー: ファイルが見つかりません: $FLOW_FILE"
    exit 1
fi

# screenshotsディレクトリ作成
mkdir -p screenshots

echo "🚀 フロー実行: $FLOW_FILE"
echo "================================================"

# Maestro実行
maestro test "$FLOW_FILE"

echo "================================================"
echo "✅ 完了！"
echo "📸 スクリーンショット: screenshots/"
ls -la screenshots/*.png 2>/dev/null | tail -5
