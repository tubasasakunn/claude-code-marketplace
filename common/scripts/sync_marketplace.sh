#!/bin/bash
# SessionStart: スキルの正本（marketplace）を最新にする。
#
# - 作業クローンを pull --rebase する（push はしない。中間状態を撒かないため）
# - プラグインのキャッシュを更新する（反映は次セッションから）
# - 未 push のコミットがあれば知らせる（push 忘れの検出）
#
# 失敗してもセッションは止めない。ネットワークが無い環境でも黙って通す。
set -u

CLONE="$HOME/workspace_tmp/claude-code-marketplace"
MARKETPLACE="tubasasakunn-marketplace"

[ -d "$CLONE/.git" ] || exit 0

if [ -n "$(git -C "$CLONE" status --porcelain 2>/dev/null)" ]; then
  echo "[marketplace] 未コミットの変更があるため pull を飛ばした: $CLONE"
else
  git -C "$CLONE" pull --rebase --quiet 2>/dev/null \
    || echo "[marketplace] pull できなかった（オフライン等）: $CLONE"
fi

ahead=$(git -C "$CLONE" rev-list --count @{u}..HEAD 2>/dev/null || echo 0)
if [ "${ahead:-0}" -gt 0 ]; then
  echo "[marketplace] 未 push のコミットが ${ahead} 件ある。スキルの変更は push しないと他リポジトリに届かない: $CLONE"
fi

command -v claude >/dev/null 2>&1 && \
  claude plugin marketplace update "$MARKETPLACE" >/dev/null 2>&1 || true

exit 0
