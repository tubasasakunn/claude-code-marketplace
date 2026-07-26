#!/usr/bin/env node
// App Store Connect 公式 API を叩く最小クライアント（依存ゼロ、Node 標準 crypto で ES256 JWT 生成）。
//
// 使い方:
//   node asc_api.js GET  "/v1/apps?limit=5"
//   node asc_api.js POST "/v1/bundleIds" '{"data":{...}}'
//   node asc_api.js PATCH "/v1/ciWorkflows/xxx" '{"data":{...}}'
//   node asc_api.js DELETE "/v1/appScreenshots/xxx"
//
// 認証情報は環境変数から読む。未設定なら ~/.asc-key.json を見る。
//   ASC_KEY_ID     … App Store Connect API キーの Key ID（例 UR9DDJG58P）
//   ASC_ISSUER_ID  … Issuer ID（UUID 形式）
//   ASC_P8         … .p8 ファイルのパス（既定 ~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8）
//
// キーは **App Manager ロール** で作ること。Sales/Reports ロールだと読み取り専用になり、
// bundleIds の作成や ciWorkflows の変更が 403 になる。

const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

function loadConfig() {
  let { ASC_KEY_ID: keyId, ASC_ISSUER_ID: issuer, ASC_P8: p8 } = process.env;

  if (!keyId || !issuer) {
    const fallback = path.join(os.homedir(), '.asc-key.json');
    if (fs.existsSync(fallback)) {
      const j = JSON.parse(fs.readFileSync(fallback, 'utf8'));
      keyId = keyId || j.keyId;
      issuer = issuer || j.issuerId;
      p8 = p8 || j.p8;
    }
  }
  if (!keyId || !issuer) {
    console.error('ASC_KEY_ID と ASC_ISSUER_ID が必要です（環境変数か ~/.asc-key.json）。');
    process.exit(2);
  }
  p8 = p8 || path.join(os.homedir(), '.appstoreconnect', 'private_keys', `AuthKey_${keyId}.p8`);
  if (!fs.existsSync(p8)) {
    console.error(`秘密鍵が見つかりません: ${p8}`);
    process.exit(2);
  }
  return { keyId, issuer, p8 };
}

const b64url = (buf) =>
  Buffer.from(buf).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

function makeJwt({ keyId, issuer, p8 }) {
  const now = Math.floor(Date.now() / 1000);
  const header = b64url(JSON.stringify({ alg: 'ES256', kid: keyId, typ: 'JWT' }));
  const payload = b64url(
    JSON.stringify({ iss: issuer, iat: now, exp: now + 900, aud: 'appstoreconnect-v1' }),
  );
  const key = crypto.createPrivateKey(fs.readFileSync(p8));
  const sig = crypto.sign('sha256', Buffer.from(`${header}.${payload}`), {
    key,
    dsaEncoding: 'ieee-p1363',
  });
  return `${header}.${payload}.${b64url(sig)}`;
}

(async () => {
  const [method, reqPath, body] = process.argv.slice(2);
  if (!method || !reqPath) {
    console.error('usage: node asc_api.js <METHOD> <path> [jsonBody]');
    process.exit(2);
  }
  const cfg = loadConfig();
  const res = await fetch(`https://api.appstoreconnect.apple.com${reqPath}`, {
    method: method.toUpperCase(),
    headers: {
      Authorization: `Bearer ${makeJwt(cfg)}`,
      'Content-Type': 'application/json',
    },
    body: body || undefined,
  });
  const text = await res.text();
  // 1行目にステータス、2行目以降にボディ。呼び出し側は split('\n', 1) で分けて使う。
  console.log(res.status);
  console.log(text);
  // 4xx/5xx は非ゼロ終了にして、シェルの && 連鎖で気づけるようにする。
  if (!res.ok) process.exit(1);
})();
