#!/usr/bin/env python3
"""marketplace 全体を走査して skill-map の一覧部分を再生成する。

手書き部分（使い分け・迷いやすいペア）は残し、マーカーで囲まれた一覧だけを差し替える。

    python3 build_skill_map.py            # 生成して書き込む
    python3 build_skill_map.py --check    # ズレていたら exit 1（CI 用）
"""
import re
import sys
from pathlib import Path

MP = Path(__file__).resolve().parents[2]          # claude-code-marketplace/
TARGET = MP / "common" / "skills" / "skill-map" / "SKILL.md"
BEGIN = "<!-- BEGIN GENERATED — python3 common/scripts/build_skill_map.py で再生成する -->"
END = "<!-- END GENERATED -->"

# 表示順（プラグインの意味的な順序。marketplace.json の順と揃える）
ORDER = ["common", "swift-app", "ios-app-build", "app-store-optimize", "sns-marketing",
         "cloudflare", "canva"]

WHERE = {
    "common": "全リポジトリ",
    "swift-app": "各アプリリポジトリ",
    "ios-app-build": "ios-app-build-workspace",
    "app-store-optimize": "app-store-optimize-workspace",
    "sns-marketing": "sns-marketing-workspace",
    "cloudflare": "全リポジトリ（user スコープ）",
    "canva": "全リポジトリ（user スコープ）",
}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[3:end]
    out: dict[str, str] = {}
    key = None
    for line in block.splitlines():
        m = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            # YAML の折り返し指示子は捨てて後続行を本文として拾う
            out[key] = "" if val in (">-", ">", "|", "|-") else val
        elif key and line.strip():
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def one_line(s: str, limit: int = 150) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    # 最初の句点までを要約として使う
    head = re.split(r"(?<=。)", s)[0] if "。" in s else s
    if len(head) > limit:
        head = head[: limit - 1] + "…"
    return head.replace("|", "\\|")


def collect() -> list[tuple[str, list[tuple[str, str]]]]:
    result = []
    plugins = [p for p in ORDER if (MP / p / "skills").is_dir()]
    plugins += [
        d.name for d in sorted(MP.iterdir())
        if d.is_dir() and (d / "skills").is_dir() and d.name not in ORDER
    ]
    for p in plugins:
        skills = []
        for sd in sorted((MP / p / "skills").iterdir()):
            f = sd / "SKILL.md"
            if not f.is_file():
                continue
            fm = frontmatter(f)
            skills.append((fm.get("name") or sd.name, one_line(fm.get("description", ""))))
        result.append((p, skills))
    return result


def render(data) -> str:
    total = sum(len(s) for _, s in data)
    lines = [BEGIN, "", f"**全 {total} スキル / {len(data)} プラグイン**", ""]
    for plugin, skills in data:
        lines.append(f"### `{plugin}`（{len(skills)}本） — {WHERE.get(plugin, '')}で有効化")
        lines.append("")
        lines.append("| スキル | 何をするか |")
        lines.append("|---|---|")
        for name, desc in skills:
            lines.append(f"| `/{plugin}:{name}` | {desc} |")
        lines.append("")
    lines.append(END)
    return "\n".join(lines)


def main() -> int:
    check = "--check" in sys.argv
    body = render(collect())
    text = TARGET.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        print(f"マーカーが無い: {TARGET}", file=sys.stderr)
        return 2
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = head + body + tail
    if new == text:
        print("skill-map は最新 ✅")
        return 0
    if check:
        print("skill-map が古い。build_skill_map.py を実行して push すること", file=sys.stderr)
        return 1
    TARGET.write_text(new, encoding="utf-8")
    print(f"skill-map を更新した: {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
