#!/usr/bin/env python3
"""Data layer for the Hioto daily SNS pipeline.

Manages two JSON files under ANALYTICS_DIR (default: the repo's analytics/):
  schedule.json  -> queue of posts to publish (with date, platforms, skill, img dir)
  history.json   -> published posts + view-count time series (for analysis)

CLI:
  schedule_lib.py next-open-date [--after YYYY-MM-DD] [--gap-days 1] [--time 19:30]
  schedule_lib.py add-post --content-dir analytics/20260616 --theme "..." \
                  [--platforms tiktok,lemon8] [--date auto|YYYY-MM-DD] [--time 19:30]
  schedule_lib.py due [--date YYYY-MM-DD]          # posts queued for that date (default: today)
  schedule_lib.py mark --id ID --status posted|failed|skipped
  schedule_lib.py record-view --ref ID --platform tiktok --date YYYY-MM-DD --count N
  schedule_lib.py list                              # human summary

All dates are local (YYYY-MM-DD). The pipeline runs as a Claude session, so 'today'
must be passed in explicitly when known (the sandbox forbids Date.now in some tools);
CLI defaults to the OS date which is fine inside a normal shell.
"""
import argparse, json, os, sys, datetime
from pathlib import Path


def _repo_root():
    """リポジトリルート（target/ と CLAUDE.md を持つ階層）を __file__ から探す。絶対パス直書きをしない。"""
    for d in Path(__file__).resolve().parents:
        if (d / "target").is_dir() and (d / "CLAUDE.md").exists():
            return d
    return Path(__file__).resolve().parents[-1]


REPO = _repo_root()
ROOT = os.environ.get("ANALYTICS_DIR") or str(REPO / "analytics")
SCHED = os.path.join(ROOT, "schedule.json")
HIST  = os.path.join(ROOT, "history.json")


def _rel(p):
    """絶対パス→リポジトリルート相対（repo 外/既に相対ならそのまま）。schedule.json を可搬にする。"""
    if not p:
        return p
    pp = Path(str(p))
    if pp.is_absolute():
        try:
            return str(pp.relative_to(REPO))
        except ValueError:
            return str(p)        # repo 外（想定外）は絶対のまま
    return str(p)                # 既に相対


def _abs(p):
    """リポジトリルート相対→絶対（既に絶対ならそのまま）。実行時の消費側へは絶対で渡す。"""
    if not p:
        return p
    return str(p) if os.path.isabs(str(p)) else str(REPO / str(p))


def _resolve_entry(entry):
    """schedule エントリのパス項目(content_dir/post_md/imgs.*)を絶対へ解決したコピーを返す。"""
    e = dict(entry)
    if e.get("content_dir"):
        e["content_dir"] = _abs(e["content_dir"])
    if e.get("post_md"):
        e["post_md"] = _abs(e["post_md"])
    if isinstance(e.get("imgs"), dict):
        e["imgs"] = {k: _abs(v) for k, v in e["imgs"].items()}
    return e

# Posting-time rules (JST), from GROWTH_PLAYBOOK.md: first 1-2h drives reach, so post
# when the audience is online. Fri/Sat 17-22 is the biggest window; weekday evening ~21h;
# Monday has the lowest usage -> avoided entirely as a POST date (see next_open_date).
# weekday(): Mon=0 .. Sun=6
TIME_RULES = {0: "21:10", 1: "21:10", 2: "21:10", 3: "21:10",
              4: "18:30", 5: "18:30", 6: "20:00"}
DEFAULT_TIME = "21:10"

def time_for(date_iso):
    return TIME_RULES.get(datetime.date.fromisoformat(date_iso).weekday(), DEFAULT_TIME)

def _load(p, default):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def _save(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _today():
    return datetime.date.today().isoformat()

def next_open_date(after=None, gap_days=1, time=None):
    """First posting date with no queued/posted post, starting the day after `after`
    (or today), spacing at least `gap_days` apart. Skips Mondays (lowest usage per
    GROWTH_PLAYBOOK.md)."""
    sched = _load(SCHED, {"posts": []})
    taken = {p["scheduled_date"] for p in sched["posts"]
             if p.get("status") in ("queued", "posted") and p.get("scheduled_date")}
    start = datetime.date.fromisoformat(after) if after else datetime.date.today()
    d = start + datetime.timedelta(days=gap_days)
    for _ in range(400):
        if d.weekday() != 0 and d.isoformat() not in taken:   # weekday()==0 -> Monday
            return d.isoformat()
        d += datetime.timedelta(days=1)
    raise RuntimeError("no open date found in 400 days")

def add_post(content_dir, theme, platforms, date, time):
    sched = _load(SCHED, {"posts": []})
    if date in (None, "auto"):
        date = next_open_date()
    # derive posting time from the date's weekday unless explicitly overridden
    if time in (None, "", "auto"):
        time = time_for(date)
    cdir = _rel(content_dir.rstrip("/"))     # リポジトリルート相対で保存（可搬・自己完結）
    base = os.path.basename(cdir)            # e.g. 20260616
    pid = base
    n = 1
    existing = {p["id"] for p in sched["posts"]}
    while pid in existing:
        n += 1; pid = f"{base}-{n}"
    entry = {
        "id": pid,
        "content_dir": cdir,
        "platforms": platforms,
        "skills": {"tiktok": "tiktok-post", "lemon8": "lemon8-post"},
        "imgs": {pf: f"{cdir}/imgs/{pf}" for pf in platforms},
        "post_md": f"{cdir}/POST.md",
        "scheduled_date": date,
        "scheduled_time": time,
        "status": "queued",
        "theme": theme,
        "created": _today(),
    }
    sched["posts"].append(entry)
    _save(SCHED, sched)                       # 保存は相対。出力は消費側向けに絶対へ解決。
    print(json.dumps(_resolve_entry(entry), ensure_ascii=False, indent=2))

def due(date):
    # queued posts scheduled on or BEFORE `date` (overdue-inclusive), oldest first.
    # `==` would strand posts whose reserved day the app never runs (alternating
    # rotation); `<=` lets the app's next run pick up anything overdue.
    date = date or _today()
    sched = _load(SCHED, {"posts": []})
    items = sorted([p for p in sched["posts"]
                    if p.get("status") == "queued"
                    and p.get("scheduled_date") and p["scheduled_date"] <= date],
                   key=lambda p: p["scheduled_date"])
    # 消費側(投稿フロー)へは絶対パスで渡す（保存は相対・出力で解決）。
    print(json.dumps([_resolve_entry(p) for p in items], ensure_ascii=False, indent=2))

def mark(pid, status):
    sched = _load(SCHED, {"posts": []})
    for p in sched["posts"]:
        if p["id"] == pid:
            p["status"] = status
            p["status_updated"] = _today()
            _save(SCHED, sched)
            print(f"{pid} -> {status}")
            return
    sys.exit(f"id {pid} not found")

def record_view(ref, platform, date, count):
    hist = _load(HIST, {"posts": []})
    rec = next((p for p in hist["posts"]
                if p.get("ref") == ref and p.get("platform") == platform), None)
    if rec is None:
        rec = {"ref": ref, "platform": platform, "views": []}
        hist["posts"].append(rec)
    date = date or _today()
    rec["views"] = [v for v in rec["views"] if v["date"] != date]  # dedup same day
    rec["views"].append({"date": date, "count": int(count)})
    rec["views"].sort(key=lambda v: v["date"])
    _save(HIST, hist)
    print(f"{platform}/{ref} @ {date} = {count}")

def list_all():
    sched = _load(SCHED, {"posts": []})
    hist = _load(HIST, {"posts": []})
    print(f"== schedule.json ({len(sched['posts'])} posts) ==")
    for p in sorted(sched["posts"], key=lambda x: x.get("scheduled_date", "")):
        print(f"  {p['scheduled_date']} {p.get('scheduled_time','')}  [{p['status']}]  "
              f"{p['id']}  {','.join(p['platforms'])}  {p.get('theme','')}")
    print(f"== history.json ({len(hist['posts'])} tracked) ==")
    for p in hist["posts"]:
        last = p["views"][-1] if p.get("views") else None
        print(f"  {p['platform']}/{p['ref']}  views={[v['count'] for v in p.get('views',[])]}"
              f"  latest={last}")

def main():
    global SCHED, HIST
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", help="アプリid。指定すると content_dir を appmeta で解決し schedule/history を切替（env ANALYTICS_DIR 不要・他アプリ誤操作を防ぐ）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("next-open-date"); s.add_argument("--after"); s.add_argument("--gap-days", type=int, default=1); s.add_argument("--time", default=DEFAULT_TIME)
    s = sub.add_parser("add-post")
    s.add_argument("--content-dir", required=True); s.add_argument("--theme", default="")
    s.add_argument("--platforms", default="tiktok,lemon8"); s.add_argument("--date", default="auto"); s.add_argument("--time", default="auto")
    s = sub.add_parser("due"); s.add_argument("--date")
    s = sub.add_parser("mark"); s.add_argument("--id", required=True); s.add_argument("--status", required=True)
    s = sub.add_parser("record-view"); s.add_argument("--ref", required=True); s.add_argument("--platform", required=True); s.add_argument("--date"); s.add_argument("--count", required=True)
    sub.add_parser("list")
    a = ap.parse_args()
    if getattr(a, "app", None):   # --app 指定時は content_dir を正本に切替（誤アプリ操作を防ぐ）
        import appmeta
        cd = appmeta.get(a.app).get("content_dir")
        if cd:
            SCHED = os.path.join(cd, "schedule.json")
            HIST = os.path.join(cd, "history.json")
    if a.cmd == "next-open-date": print(next_open_date(a.after, a.gap_days, a.time))
    elif a.cmd == "add-post":     add_post(a.content_dir, a.theme, a.platforms.split(","), a.date, a.time)
    elif a.cmd == "due":          due(a.date)
    elif a.cmd == "mark":         mark(a.id, a.status)
    elif a.cmd == "record-view":  record_view(a.ref, a.platform, a.date, a.count)
    elif a.cmd == "list":         list_all()

if __name__ == "__main__":
    main()
