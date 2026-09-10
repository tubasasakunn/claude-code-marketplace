---
name: note-setup
description: note-workspace で note.com への接続（note-mcp）を用意する。uv での導入、ブラウザログインによるセッション保存、認証の確認、壊れたときの復旧まで。「note に繋がらない」「note_login が要る」「note-mcp のツールが見えない」ときや、新しいマシンで初めて note-workspace を使うときに使う。
allowed-tools: Bash, Read, Write, Edit
---

# note.com 接続のセットアップ（note-mcp）

note.com には**公式 API がない**。ここで使う [`drillan/note-mcp`](https://github.com/drillan/note-mcp) は
note.com の**非公開エンドポイントを叩く非公式ツール**で、作者自身が DISCLAIMER で
「仕様変更で壊れうる／アカウント制限のリスクがある／無保証」と明記している。

**この前提を運用に落とすと次の 3 つになる。守る。**

1. **公開は自動でやらない。** 下書き保存までを機械、公開は人が押す（`/note:note-publish` も確認を挟む）
2. **記事の正本はローカルの Markdown。** note 側が壊れても `articles/` から作り直せる状態を保つ
3. **壊れたら直す前に「仕様が変わったのか」を疑う。** 直近で note 側の変更により取得系が壊れた事例がある

## 1. 依存を入れる

note-workspace 直下で完結させる（`pyproject.toml` に note-mcp を書いてある）。

```bash
cd ~/workspace/note-workspace
uv sync
uv run playwright install chromium
```

`uv sync` が note-mcp の解決で失敗するときは上流が動いている。`pyproject.toml` の
`note-mcp` の行を `git+https://github.com/drillan/note-mcp.git@<動くコミット>` に固定する。

## 2. MCP が見えているか確認する

`.mcp.json` は note-workspace にコミット済み。**MCP の起動は Claude Code の再起動が要る。**

```bash
claude mcp list
```

`note-mcp` が出ない場合:

- note-workspace を**プロジェクトルートにして** `claude` を起動しているか（`.mcp.json` はプロジェクトスコープ）
- 初回は `.mcp.json` の承認プロンプトが出る。承認しないとサーバは起動しない
- `uv run python -m note_mcp` を手で叩いてエラーを読む（cwd が note-workspace であること）

## 3. ログインする（初回・セッション切れ時）

```
note_check_auth    # まず現状を見る
note_login         # ブラウザが開くので手でログインする（最大300秒）
```

`note_login` は**ブラウザウィンドウを開いて人間がログインする**方式。パスワードを
スキルやリポジトリに書かない。セッションはローカルに保存される。

ログイン後にユーザー名の自動取得が失敗したら、プロフィール URL から手で入れる:

```
note_set_username(username="<https://note.com/xxx の xxx>")
```

### `note_login` がタイムアウトし続けるとき

`note_login` は Playwright の Chromium を**新規起動**して、URL が `/login` から離れるのを待つ。
この検出が効かず、5 分でも 10 分でもタイムアウトすることがある（2026-08-02 に発生）。
`/tmp/note_mcp_login.log` に `is_logged_in(https://note.com/login) = False` が並び続けるのが症状。

**新しいブラウザで入り直させるのではなく、普段使いの Chrome のセッションを移植する。**
（普段使いの Chrome は既に note にログインしている。CDP で掴もうとしても、Chrome 136+ は
デフォルトプロファイルへの `--remote-debugging-port` を無視するので、cookie を読むほうが早い）

```bash
# 1) どのプロファイルに note.com の cookie があるか数える
CD="$HOME/Library/Application Support/Google/Chrome"
for p in "$CD"/*/Cookies; do
  cp "$p" /tmp/ck.db 2>/dev/null || continue
  echo "$(basename "$(dirname "$p")"): $(sqlite3 /tmp/ck.db \
    "select count(*) from cookies where host_key like '%note.com'")"
done; rm -f /tmp/ck.db
```

```python
# 2) 復号する（Keychain の許可ダイアログが出るので人に押してもらう）
import shutil, sqlite3, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

pw = subprocess.run(["security","find-generic-password","-w","-s","Chrome Safe Storage"],
                    capture_output=True, text=True).stdout.strip().encode()
key = PBKDF2HMAC(algorithm=hashes.SHA1(), length=16, salt=b"saltysalt",
                 iterations=1003).derive(pw)

def dec(blob):
    if not blob or blob[:3] not in (b"v10", b"v11"): return None
    c = Cipher(algorithms.AES(key), modes.CBC(b" "*16)).decryptor()
    p = c.update(blob[3:]) + c.finalize()
    p = p[:-p[-1]]                       # PKCS7
    if len(p) > 32:                      # Chrome 127+ は先頭 32B がドメインハッシュ
        try: p[:32].decode("ascii")
        except UnicodeDecodeError: p = p[32:]
    return p.decode("utf-8", "replace")
```

`_note_session_v5` を取り出したら、**生きているものを選ぶ**。
同じ名前の cookie が複数プロファイルにあっても、たいてい 1 つしか通らない。

```python
import httpx
h = {"Cookie": f"_note_session_v5={v}", "Accept": "application/json"}
httpx.get("https://note.com/api/v2/current_user", headers=h).json()["data"]
# -> {"id": ..., "urlname": ..., "nickname": ...} が返れば生きている。401 なら死んでいる
```

最後に note-mcp のセッションとして保存する:

```python
import time
from note_mcp.auth.session import SessionManager
from note_mcp.models import Session
SessionManager().save(Session(cookies={"_note_session_v5": v},
                              user_id="<id>", username="<urlname>",
                              expires_at=None, created_at=int(time.time())))
```

`note_check_auth` が「認証済みです」を返せば通っている。

**この手順で扱うのは cookie の値そのもの。ログには出さないし、リポジトリにも置かない。**

## 4. 疎通を確認する

```
note_list_articles(status="all", limit=5)
```

記事一覧が返れば通っている。ここまで来たら `/note:note-post` に進む。

## 使えるツール（note-mcp）

| 用途 | ツール |
|---|---|
| 認証 | `note_login` `note_check_auth` `note_logout` `note_set_username` |
| 作成 | `note_create_from_file`（**主に使う**・Markdown ファイルから下書き）`note_create_draft` |
| 取得・更新 | `note_get_article` `note_update_article` `note_list_articles` |
| 画像 | `note_insert_body_image` `note_upload_eyecatch` `note_upload_body_image` |
| 確認 | `note_show_preview` `note_get_preview_html` |
| 公開・削除 | `note_publish_article` `note_delete_draft` `note_delete_all_drafts` |

通常はこの 17 個が見える（実測）。ブラウザでトラフィックを取って非公開 API を解析する
`investigator_*` 系は **`INVESTIGATOR_MODE=1` を付けて起動したときだけ**生える。
note 側の仕様変更で壊れたときの調査用で、執筆・投稿では使わない。

## 壊れたときの切り分け

| 症状 | 見るところ |
|---|---|
| ツールが 1 つも見えない | `.mcp.json` の承認、Claude Code の再起動、`claude mcp list` |
| 「ログインが必要です」 | `note_check_auth` → `note_login` でセッションを取り直す |
| `note_login` がタイムアウトし続ける | ブラウザ未導入なら `uv run playwright install chromium`。入っていれば上の Chrome cookie 移植へ |
| `Executable doesn't exist at .../chromium-XXXX` | `uv run playwright install chromium`（初回・Playwright 更新後） |
| 作成は通るが本文が崩れる | Markdown → note 互換 HTML の変換仕様。`note_get_preview_html` で実際の HTML を見る |
| 下書きにタグが付かない | 仕様。`draft_save` は永続化しない。公開時に `file_path` で入る（`/note:note-publish`） |
| 公開済み記事を直したのに変わらない | 仕様。`note_update_article` のあと `note_publish_article` をもう一度通す |
| 急に全部 404 / 形が変わった | note 側の仕様変更を疑う。上流の issue を見る。**直すより先に記事をローカルに退避** |

## やらないこと

- **`note_delete_all_drafts` を使わない。** 下書きの一括削除は事故しかない。消すなら
  `note_delete_draft` で 1 本ずつ、`confirm=False` の確認を挟んでから
- **認証情報をリポジトリに置かない。** セッションは note-mcp がローカルに持つ。
  `.claude/secrets.env` にも書かない（ここは public marketplace ではないが、そもそも不要）
