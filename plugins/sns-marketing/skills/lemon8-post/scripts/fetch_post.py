#!/usr/bin/env python3
"""Fetch a Hioto post's images + text for a given platform.

Usage: fetch_post.py <postId> <platform> [outdir]
  postId   e.g. post3
  platform tiktok | lemon8
  outdir   default /tmp/sns_post/<postId>_<platform>

Source of truth: https://hioto.basaapp.com/post/manifest.json
Image URL pattern: https://hioto.basaapp.com/post/<postId>/<platform>/<file>

Downloads the images in manifest order (01_cover.. = carousel order) and prints
a JSON blob with: outdir, images (ordered local paths), title, body, hashtags.
"""
import json, os, sys, urllib.request

BASE = "https://hioto.basaapp.com/post"

def get(url):
    # Some hosts 403 the default urllib UA; send a browser-like one.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def main():
    if len(sys.argv) < 3:
        print("usage: fetch_post.py <postId> <platform> [outdir]", file=sys.stderr); sys.exit(2)
    post_id, platform = sys.argv[1], sys.argv[2]
    outdir = sys.argv[3] if len(sys.argv) > 3 else f"/tmp/sns_post/{post_id}_{platform}"
    os.makedirs(outdir, exist_ok=True)

    manifest = json.loads(get(f"{BASE}/manifest.json"))
    post = next((p for p in manifest["posts"] if p["id"] == post_id), None)
    if not post:
        print(f"post {post_id} not found", file=sys.stderr); sys.exit(1)
    plat = post["platforms"][platform]

    images = []
    for fn in plat["images"]:
        url = f"{BASE}/{post_id}/{platform}/{fn}"
        dest = os.path.join(outdir, fn)
        with open(dest, "wb") as f:
            f.write(get(url))
        images.append(dest)

    out = {
        "outdir": outdir,
        "images": images,            # in carousel order
        "title": plat["title"],
        "body": plat["body"],
        "hashtags": plat["hashtags"],
        "size": plat.get("size"),
    }
    # also drop title/body/hashtags as text files for easy ADBKeyboard input
    with open(os.path.join(outdir, "title.txt"), "w") as f:
        f.write(plat["title"])
    with open(os.path.join(outdir, "body.txt"), "w") as f:
        f.write(plat["body"])
    with open(os.path.join(outdir, "hashtags.txt"), "w") as f:
        f.write(" ".join(plat["hashtags"]))
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
