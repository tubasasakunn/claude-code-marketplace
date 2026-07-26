#!/usr/bin/env python3
"""アプリ設定を1つに束ねて返す（app-agnostic）。

root は target 配下の具体を知らない＝アプリの素性（name/bundleId/ascAppId/concept/
tags/brand）は各 repo の material/manifest.json を正本とし、root 側の運用配線
（content_dir/album_prefix/gh_repo）だけ apps.json に置く。本ヘルパが両者を id で
マージして返す。target/ に material/manifest.json を持つ repo を置けば自動で対象になる。

  appmeta.py list                 # 対象アプリ id 一覧（manifest を持つもの）
  appmeta.py get <id>             # マージ済み設定を JSON で
"""
import argparse, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APPS = HERE.parent / "apps.json"


def _repo_root():
    """リポジトリルート（target/ と CLAUDE.md を持つ階層）を __file__ から探す。絶対パス直書きをしない。"""
    for d in Path(__file__).resolve().parents:
        if (d / "target").is_dir() and (d / "CLAUDE.md").exists():
            return d
    return Path(__file__).resolve().parents[-1]


ROOT = _repo_root()
TARGET = ROOT / "target"


def _abs(p):
    """apps.json の相対パス（target/<app>・analytics 等）をリポジトリルート基準の絶対パスに解決。"""
    if not p:
        return p
    p = Path(p)
    return str(p if p.is_absolute() else (ROOT / p))


def _ops():
    return json.loads(APPS.read_text(encoding="utf-8")) if APPS.exists() else {}


def _material_for(app_id, ops):
    # apps.json に repo があればそこ、無ければ target/<id>（いずれも repo ルート基準で解決）
    repo = ops.get(app_id, {}).get("repo") or str(TARGET / app_id)
    return Path(_abs(repo)) / "material"


def discover():
    """target/*/material/manifest.json を走査して id 一覧を返す。"""
    ids = {}
    for mani in TARGET.glob("*/material/manifest.json"):
        try:
            d = json.loads(mani.read_text(encoding="utf-8"))
            ids[d.get("id") or mani.parent.parent.name] = mani.parent
        except Exception:
            continue
    return ids


def get(app_id):
    ops = _ops()
    mat = _material_for(app_id, ops)
    cfg = dict(ops.get(app_id, {}))
    cfg["repo"] = _abs(cfg.get("repo") or str(mat.parent))   # 相対→絶対（呼び出し側は絶対前提）
    if cfg.get("content_dir"):
        cfg["content_dir"] = _abs(cfg["content_dir"])
    cfg["material_dir"] = str(mat)
    mani = mat / "manifest.json"
    if mani.exists():
        m = json.loads(mani.read_text(encoding="utf-8"))
        # manifest を正本に: identity 系は manifest を優先
        cfg["bundleId"] = m.get("bundleId", cfg.get("bundleId"))
        cfg["asc_app_id"] = m.get("ascAppId", cfg.get("asc_app_id"))
        cfg["concept"] = m.get("concept", cfg.get("concept", ""))
        cfg["name"] = m.get("name")
        cfg["default_accent"] = m.get("default_accent")
        tags = m.get("tags", {})
        cfg["tiktok_tags_seed"] = tags.get("tiktok", cfg.get("tiktok_tags_seed", []))
        cfg["lemon8_tags_seed"] = tags.get("lemon8", cfg.get("lemon8_tags_seed", []))
        cfg["overview"] = str(mat / m.get("overview", "OVERVIEW.md"))
    return cfg


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    g = sub.add_parser("get"); g.add_argument("id")
    a = ap.parse_args()
    if a.cmd == "list":
        ops = _ops()
        ids = sorted(k for k in set(list(ops.keys()) + list(discover().keys()))
                     if not k.startswith("_"))
        print(json.dumps(ids, ensure_ascii=False))
    else:
        print(json.dumps(get(a.id), ensure_ascii=False))


if __name__ == "__main__":
    main()
