#!/usr/bin/env bash
#
# 普段使いの Chrome プロファイルを「自動化用ディレクトリ」へコピーする（初回 & ログイン更新時に実行）。
#
# なぜコピーが要るか:
#   Chrome 136+ は、デフォルトのプロファイルに対して --remote-debugging-port を
#   使うとデバッグポートを無効化する（Cookie 窃取対策）。
#   そのため別ディレクトリにコピーし、それをデバッグ起動する。
#   コピー時点のログイン状態（Cookie 等）はそのまま引き継がれる。
#
set -euo pipefail

# コピー元プロファイル（Local State の info_cache で名前を確認できる）
SRC_PROFILE="${SRC_PROFILE:-Profile 1}"
SRC="${HOME}/Library/Application Support/Google/Chrome"
DST="${HOME}/Library/Application Support/Google/Chrome-automation"

echo "コピー元: ${SRC}/${SRC_PROFILE}"
echo "コピー先: ${DST}/Default"

rm -rf "${DST}"; mkdir -p "${DST}"
cp "${SRC}/Local State" "${DST}/Local State" 2>/dev/null || true
cp "${SRC}/First Run" "${DST}/First Run" 2>/dev/null || true

rsync -a \
  --exclude 'Cache' --exclude 'Code Cache' --exclude 'GPUCache' \
  --exclude 'Service Worker/CacheStorage' --exclude 'Service Worker/ScriptCache' \
  --exclude 'DawnGraphiteCache' --exclude 'DawnWebGPUCache' \
  --exclude 'GraphiteDawnCache' --exclude 'Application Cache' \
  "${SRC}/${SRC_PROFILE}/" "${DST}/Default/"

echo "✅ コピー完了: $(du -sh "${DST}" | cut -f1)"
