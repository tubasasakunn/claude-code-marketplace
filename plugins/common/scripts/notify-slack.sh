#!/bin/bash

# Slack通知スクリプト
# 環境変数: SLACK_TOKEN, SLACK_CHANNEL_ID

# 起動済みセッションでも、ローテーション後の認証情報を使用する。
if [ -r "$HOME/.config/slack/credentials.env" ]; then
  source "$HOME/.config/slack/credentials.env"
fi

if [ -z "$SLACK_TOKEN" ] || [ -z "$SLACK_CHANNEL_ID" ]; then
  exit 0
fi

if [ -z "$CLAUDE_NOTIFICATION" ]; then
  exit 0
fi

# メッセージをエスケープ（JSON用）
escape_json() {
  echo -n "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

MESSAGE=$(escape_json "$CLAUDE_NOTIFICATION")

curl -s -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL_ID\",
    \"text\": $MESSAGE,
    \"username\": \"Claude Code\",
    \"icon_emoji\": \":robot_face:\"
  }" > /dev/null 2>&1

exit 0
