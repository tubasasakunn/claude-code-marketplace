#!/usr/bin/env python3
"""プラグインのキャッシュを直接編集させない PreToolUse フック。

キャッシュ（~/.claude/plugins/cache, marketplaces）を直すと次の
`claude plugin marketplace update` で消える。実際にそれで編集が迷子になった前例がある
（ios-develop-plugin の 627 行がキャッシュ内でだけ育っていた）。
スキルの正本は marketplace の作業クローンなので、そちらへ誘導する。
"""
import json
import os
import sys

BLOCKED = ("/.claude/plugins/cache/", "/.claude/plugins/marketplaces/")


def clone_path() -> str:
    """作業クローンの場所。決め打ちにすると置き場が変わったとき案内が嘘になる。"""
    home = os.path.expanduser("~")
    for c in (os.environ.get("MARKETPLACE_CLONE", ""),
              os.path.join(home, "workspace", "claude-code-marketplace"),
              os.path.join(home, "workspace_tmp", "claude-code-marketplace")):
        if c and os.path.isdir(os.path.join(c, ".git")):
            return c.replace(home, "~", 1)
    return "~/workspace/claude-code-marketplace"


CLONE = clone_path()


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # 入力が読めないときは何もしない（編集を止めない）

    ti = data.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("notebook_path") or ""
    if not raw:
        return 0

    path = os.path.realpath(os.path.expanduser(str(raw)))
    if not any(b in path + "/" for b in BLOCKED):
        return 0

    # キャッシュ内のパスから plugin/skill を推測して、正本側のパスを案内する
    hint = ""
    for marker in ("/cache/", "/marketplaces/"):
        if marker in path:
            tail = path.split(marker, 1)[1]
            parts = [p for p in tail.split("/") if p]
            # <marketplace>/<plugin>/<version>?/skills/<skill>/...
            if "skills" in parts:
                i = parts.index("skills")
                plugin = parts[1] if len(parts) > 1 else "<plugin>"
                skill = parts[i + 1] if len(parts) > i + 1 else "<skill>"
                hint = f" 正本はおそらく {CLONE}/{plugin}/skills/{skill}/ 配下。"
            break

    reason = (
        "そこはプラグインのキャッシュなので、編集しても次の "
        "`claude plugin marketplace update` で消える（過去に実際に編集が迷子になった）。"
        f" スキルを直すときは {CLONE} で編集して commit → push すること。" + hint +
        " スキルを増減したら `python3 common/scripts/build_skill_map.py` で索引も再生成する。"
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
