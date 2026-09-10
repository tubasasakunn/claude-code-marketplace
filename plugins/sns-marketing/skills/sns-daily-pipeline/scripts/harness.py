#!/usr/bin/env python3
"""harness API client for the SNS pipeline.

harness (https://harness.basaapp.com) lets this pipeline:
  - read REAL App Store Connect download numbers  -> sharper analysis (true KPI = installs)
  - post routine progress/completion to Slack      -> "what I did" reports (per llms.txt)
  - notify the user on LINE                        -> exception/alert reporting only
  - read the user's recent LINE messages           -> pull-style intent ("止めて"/"変えて")

POLICY (per user, aligned with llms.txt channel split):
  - SLACK = routine reports: progress / completion / "what I did this run" (NORMAL flow).
  - LINE  = EXCEPTIONS ONLY: failures (adb missing / post failed), notable anomalies
    (big DL spike or drop, a post wildly over/under-performing), or runs needing a human.
  So a normal successful run ends with ONE Slack report; failures still go to LINE.

Credentials come from env vars HARNESS_TOKEN / HARNESS_BASE, else from the sibling
file ../.harness.env (chmod 600). No third-party deps (urllib only).

CLI:
  harness.py downloads --date YYYY-MM-DD [--bundle com.x.y]
       Daily rows for a date. Apple's Sales SUMMARY mixes first-time installs,
       app UPDATES, and IAP into one report (Product Type Identifier: 1*=install,
       7*=update, else=IAP/sub). With --bundle, prints {units, updates, iap} where
       units = first-time installs only (the KPI). Without --bundle, prints
       downloadUnits/updateUnits/iapUnits plus raw totalUnits (gross) and rows.
  harness.py dl-series --bundle com.x.y [--end YYYY-MM-DD] [--days 7]
       {date: units} of FIRST-TIME INSTALLS (type 1*) over the last N days, plus an
       `updates` map; app updates (7*) & IAP are excluded from series. 404/not-ready
       days are skipped (listed in `missing`).
  harness.py slack --text "..." [--channel C0..]   # Slack post (ROUTINE progress/completion)
  harness.py push --text "..."                 # LINE push to default user (EXCEPTIONS ONLY)
  harness.py inbox [--limit 10]                # recent LINE messages (newest first), as text
  harness.py ask --title T --question Q [--options "a,b,c"]
       Create a form page + LINE-notify. Prints {id,url,miniAppUrl}. Use only when a run
       genuinely needs a human decision (not routinely).
  harness.py answers --id PAGE_ID             # latest form responses for a page
  harness.py store-get --key memo/foo.json     # read an arbitrary R2 object
  harness.py store-put --key memo/foo.json --json '{...}'   # write an R2 object
  harness.py health                            # connectivity check
"""
import argparse, json, os, sys, datetime, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))


def _creds():
    base = os.environ.get("HARNESS_BASE")
    token = os.environ.get("HARNESS_TOKEN")
    if not (base and token):
        env = os.path.join(HERE, "..", ".harness.env")
        if os.path.exists(env):
            for line in open(env, encoding="utf-8"):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k == "HARNESS_BASE" and not base:
                    base = v.strip()
                if k == "HARNESS_TOKEN" and not token:
                    token = v.strip()
    if not (base and token):
        sys.exit("harness: missing HARNESS_TOKEN/HARNESS_BASE (env or .harness.env)")
    return base.rstrip("/"), token


def _req(method, path, body=None):
    base, token = _creds()
    url = base + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("User-Agent", "curl/8.5.0")  # Cloudflare 1010-blocks default urllib UA
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read().decode()
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}
    except Exception as e:
        return 0, {"error": str(e)}
    try:
        return 200, json.loads(raw)
    except Exception:
        return 200, {"raw": raw}


def _matches(row, bundle):
    return bundle in (row.get("SKU"), row.get("Apple Identifier")) or \
        (bundle and row.get("SKU", "").lower() == bundle.lower())


def _kind(row):
    """Classify a Sales-SUMMARY row by Apple's Product Type Identifier.

    Apple mixes first-time installs, app UPDATES, and IAP/subscriptions into the
    same daily report. Type ids: 1* = first-time download/redownload (the real
    install KPI), 7* = app update (NOT a new install), everything else (3*, F*,
    IA*, ...) = in-app purchase / subscription. Summing all Units conflates these
    and inflates "downloads" — updates usually dominate the row set.
    """
    pt = (row.get("Product Type Identifier") or "").strip().upper()
    if pt.startswith("1"):
        return "download"
    if pt.startswith("7"):
        return "update"
    return "other"


def _breakdown(rows, bundle):
    """Sum Units per kind for rows matching bundle (or all rows if bundle is None)."""
    out = {"download": 0, "update": 0, "other": 0}
    for r in rows:
        if bundle and not _matches(r, bundle):
            continue
        out[_kind(r)] += int(r.get("Units", 0) or 0)
    return out


def downloads(date, bundle):
    code, res = _req("GET", f"/api/appstore/downloads?date={date}")
    if code != 200:
        print(json.dumps({"date": date, "error": res.get("error", res)}, ensure_ascii=False))
        return
    rows = res.get("rows", [])
    if bundle:
        b = _breakdown(rows, bundle)
        # units = first-time installs only (the KPI); updates/iap broken out for transparency.
        print(json.dumps({"date": date, "bundle": bundle, "units": b["download"],
                          "updates": b["update"], "iap": b["other"]}, ensure_ascii=False))
    else:
        b = _breakdown(rows, None)
        print(json.dumps({"date": date, "downloadUnits": b["download"],
                          "updateUnits": b["update"], "iapUnits": b["other"],
                          "totalUnits": res.get("totalUnits"),  # raw gross from Apple (DL+updates+IAP)
                          "rows": rows}, ensure_ascii=False))


def dl_series(bundle, end, days):
    end_d = datetime.date.fromisoformat(end) if end else datetime.date.today()
    series, updates, missing = {}, {}, []
    for i in range(days):
        d = (end_d - datetime.timedelta(days=i)).isoformat()
        code, res = _req("GET", f"/api/appstore/downloads?date={d}")
        if code != 200:
            missing.append(d)
            continue
        b = _breakdown(res.get("rows", []), bundle)
        series[d] = b["download"]   # new installs only — excludes app updates (type 7*) and IAP
        updates[d] = b["update"]
    out = {k: series[k] for k in sorted(series)}
    upd = {k: updates[k] for k in sorted(updates)}
    print(json.dumps({"bundle": bundle, "series": out, "updates": upd, "missing": sorted(missing),
                      "note": "series=first-time installs only (Apple Product Type 1*); "
                              "app updates (7*) and IAP/subs are excluded from series."},
                     ensure_ascii=False))


def slack(text, channel=None):
    body = {"text": text}
    if channel:
        body["channel"] = channel
    code, res = _req("POST", "/api/slack/post", body)
    print(json.dumps({"ok": code == 200, "code": code, "res": res}, ensure_ascii=False))
    sys.exit(0 if code == 200 else 1)


def push(text):
    code, res = _req("POST", "/api/line/push", {"messages": text})
    print(json.dumps({"ok": code == 200, "code": code, "res": res}, ensure_ascii=False))
    sys.exit(0 if code == 200 else 1)


def inbox(limit):
    code, res = _req("GET", "/api/line/users")
    if code != 200:
        print(json.dumps({"error": res}, ensure_ascii=False)); return
    out = []
    for uid in res.get("userIds", []):
        c2, m = _req("GET", f"/api/line/users/{uid}/messages?limit={limit}")
        if c2 != 200:
            continue
        for ev in m.get("messages", []):
            msg = ev.get("message", {})
            out.append({"userId": uid, "ts": ev.get("timestamp"),
                        "type": msg.get("type"), "text": msg.get("text")})
    out.sort(key=lambda x: x.get("ts") or 0, reverse=True)
    print(json.dumps(out[:limit], ensure_ascii=False, indent=2))


def ask(title, question, options):
    fields = [{"name": "decision", "label": question, "type": "text", "required": True}]
    html = f"<p>{question}</p>"
    if options:
        opts = "/".join(options.split(","))
        html += f"<p>選択肢: {opts}</p>"
    fields.append({"name": "comment", "label": "コメント(任意)", "type": "textarea"})
    code, res = _req("POST", "/api/pages", {"title": title, "html": html, "fields": fields})
    if code != 200:
        print(json.dumps({"error": res}, ensure_ascii=False)); sys.exit(1)
    pid = res["id"]
    _req("POST", f"/api/pages/{pid}/notify", {"text": f"{title}: {question}"})
    print(json.dumps({"id": pid, "url": res.get("url"), "miniAppUrl": res.get("miniAppUrl")},
                     ensure_ascii=False))


def answers(pid):
    code, res = _req("GET", f"/api/pages/{pid}/responses")
    if code != 200:
        print(json.dumps({"error": res}, ensure_ascii=False)); sys.exit(1)
    rows = []
    for v in (res.get("responses") or {}).values():
        rows.append({"data": v.get("data"), "submittedAt": v.get("submittedAt")})
    rows.sort(key=lambda x: x.get("submittedAt") or "", reverse=True)
    print(json.dumps({"id": pid, "latest": rows[0] if rows else None, "all": rows},
                     ensure_ascii=False, indent=2))


def store_get(key):
    code, res = _req("GET", f"/api/object/{key}")
    print(json.dumps(res, ensure_ascii=False, indent=2)); sys.exit(0 if code == 200 else 1)


def store_put(key, payload):
    code, res = _req("PUT", f"/api/object/{key}", json.loads(payload))
    print(json.dumps({"ok": code == 200, "res": res}, ensure_ascii=False))
    sys.exit(0 if code == 200 else 1)


def health():
    code, res = _req("GET", "/api/health")
    print(json.dumps({"code": code, "res": res}, ensure_ascii=False))
    sys.exit(0 if code == 200 else 1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("downloads"); s.add_argument("--date", required=True); s.add_argument("--bundle")
    s = sub.add_parser("dl-series"); s.add_argument("--bundle", required=True); s.add_argument("--end"); s.add_argument("--days", type=int, default=7)
    s = sub.add_parser("slack"); s.add_argument("--text", required=True); s.add_argument("--channel")
    s = sub.add_parser("push"); s.add_argument("--text", required=True)
    s = sub.add_parser("inbox"); s.add_argument("--limit", type=int, default=10)
    s = sub.add_parser("ask"); s.add_argument("--title", required=True); s.add_argument("--question", required=True); s.add_argument("--options")
    s = sub.add_parser("answers"); s.add_argument("--id", required=True)
    s = sub.add_parser("store-get"); s.add_argument("--key", required=True)
    s = sub.add_parser("store-put"); s.add_argument("--key", required=True); s.add_argument("--json", required=True)
    sub.add_parser("health")
    a = ap.parse_args()
    if a.cmd == "downloads":   downloads(a.date, a.bundle)
    elif a.cmd == "dl-series": dl_series(a.bundle, a.end, a.days)
    elif a.cmd == "slack":     slack(a.text, a.channel)
    elif a.cmd == "push":      push(a.text)
    elif a.cmd == "inbox":     inbox(a.limit)
    elif a.cmd == "ask":       ask(a.title, a.question, a.options)
    elif a.cmd == "answers":   answers(a.id)
    elif a.cmd == "store-get": store_get(a.key)
    elif a.cmd == "store-put": store_put(a.key, a.json)
    elif a.cmd == "health":    health()


if __name__ == "__main__":
    main()
