---
name: codex-app-server-swift
description: Codex CLI の app-server（JSON-RPC 2.0 サーバー）を、ChatGPTアカウントのOAuthログイン経由でSwift(iOS/macOS)アプリから使うための知識リファレンス。iOSデバイス上ではRust製バイナリを直接実行できないため常駐ホスト+リモートクライアント構成が必須という前提、認証4モード（apikey/chatgpt/chatgptDeviceCode/chatgptAuthTokens）の一次ソース裏取り済み仕様、エンドユーザー各自のChatGPTログインをクライアントから駆動する方法、規約上の判断軸、Swift実装のレイヤー構成とコード骨格、主要JSON-RPCメソッドをまとめる。「アプリにCodex(AIエージェント)機能を組み込みたい」「ChatGPTアカウントのサブスク枠でLLM/画像生成をアプリに入れたい」と相談された場合に使用してください。
---

# Codex App Server を Swift(iOS) から使う

## 概要

Codex CLI に同梱される `codex app-server` は JSON-RPC 2.0 の双方向通信サーバー。
**ChatGPTアカウントでログイン（OAuth）すれば、そのユーザーのChatGPT Plus/Pro/Business/Enterprise
サブスク枠でLLM推論・画像生成（`gpt-image` 系、APIキー不要）が使える。** APIキー課金とは別会計。

**大前提: iOSデバイス上でapp-server自体を動かすことはできない。** Rust製バイナリでネイティブOS依存
（tokio等）があり、モバイル実行は公式非対応。iOSアプリは常に**リモートクライアント**として、
どこか別のホストで常駐する app-server に WebSocket 経由で接続する構成一択になる。

## 成立するアーキテクチャ（2パターン）

app-server本体は常にサーバー側で動く。iOSアプリが担うのは Swift 製の JSON-RPC クライアント層だけ。
違いは「誰のChatGPTアカウントで動くか」。

### パターンA: 自分専用リモコン（最小構成）

```
[常駐ホスト: Mac / VPS / Docker]              [iOSアプリ]
$ codex login   ← 自分のChatGPTアカウントでブラウザOAuth（1回だけ）
$ codex app-server --listen ws://0.0.0.0:PORT --ws-auth ...
                                       ⇄ WebSocket (JSON-RPC 2.0)
```

ホスト側で事前に `codex login` しておく。iOSクライアントは認証済みインスタンスに繋ぐだけ。

### パターンB: エンドユーザー各自が自分のChatGPTアカウントでログイン

app-serverのプロトコル自体が**クライアント主導のログイン**を正式サポートしている
（→「認証の実際」）。ベンダー側インフラでユーザーごとに隔離した app-server インスタンス
（`CODEX_HOME` をユーザー別に分離）を立て、iOSアプリから `account/login/start` を叩いて
**そのユーザー自身のChatGPTアカウント**でログインさせる。課金・利用枠はユーザー各自のプランに乗る。
VS Code拡張と同じ構図であり、「ベンダーが1アカウントを代理プールする」形態とは規約上の扱いが全く違う。

## 規約上の判断軸 ★実装前に必ず読む

- **OK（正規）**: パターンA、およびパターンBのうち「各ユーザーが自分のアカウントでログインし、
  自分のセッションとしてのみ使う」構成。プロトコルにクライアント主導ログインAPIが公式に存在する
- **NG（リスク大）**: ベンダーが少数のChatGPTアカウント/トークンをプールし、不特定多数の
  エンドユーザーの処理を代理実行するSaaS形態。ChatGPTのOAuthトークンは個人の対話的利用向け
  ライセンスであり、バックエンドサービス化・トークンプーリングは規約に反するリスクがある
  （Anthropicは2026-02に同種利用を明示禁止済み。OpenAIは現状グレーだが同じ方向に動き得る）
- **エンタープライズで本格展開するなら**: 公式ドキュメントに「新しいエンタープライズ向け統合は
  OpenAIに連絡して known clients list に登録」との記述がある（`initialize` の `clientInfo.name` が
  Compliance Logs Platform での識別に使われる）。製品化前に問い合わせるのが確実
- ユーザーにChatGPTアカウントを要求したくない場合は、ChatGPTログインではなく
  **OpenAI APIキー（Responses API等、通常の従量課金）**。その場合はapp-serverを使う必然性は薄い

## 認証の実際（一次ソース: `codex-rs/app-server-protocol/src/protocol/v2/account.rs` で裏取り済み）

`account/login/start` リクエストの `type` で4モードを選ぶ。**リモートクライアント（iOS）から
ログインフローを開始できる**のがポイント。

| type | 動き | iOSからの使い勝手 |
|---|---|---|
| `apiKey` | `apiKey` を直接渡す | 可（Platform API課金になる） |
| `chatgpt` | レスポンスで `{loginId, authUrl}` が返る。クライアントがブラウザで `authUrl` を開かせる | OAuthコールバックが**app-serverホスト側のループバック**に着地するため、リモート構成では不向き |
| `chatgptDeviceCode` | レスポンスで `{loginId, verificationUrl, userCode}` が返る。ユーザーがどの端末のブラウザでもURLを開いてコード入力すれば完了 | **★iOSからはこれが本命**。コールバック不要。完了は `account/login/completed` 通知で受ける |
| `chatgptAuthTokens` | ホストアプリが access_token(JWT)・chatgptAccountId・planType を直接供給。失効時はサーバー→クライアントの `account/chatgptAuthTokens/refresh` リクエストに応答して返す | ソースコード上 **「[UNSTABLE] FOR OPENAI INTERNAL USE ONLY - DO NOT USE」** と明記。experimental gate 付き。**これに依存した設計をしない** |

- 中断は `account/login/cancel`、ログアウトは `account/logout`、現在の状態は `account/read`
- トークンは app-server が `CODEX_HOME/auth.json` に保存し、リフレッシュも自動管理する
  （`chatgptAuthTokens` モードだけはホストアプリの責務）
- 残枠・使用量は `account/rateLimits/read` / `account/usage/read` で取れる
  （`account/rateLimits/updated` 通知もある）。**ユーザーのプラン残量をUIに出せる**
- WebSocket自体の認証は別レイヤー（`--ws-auth capability-token --ws-token-file ...` /
  `--ws-auth signed-bearer-token --ws-shared-secret-file ...`）。これは「ホストへの不正接続を防ぐ鍵」
  であって、ChatGPTアカウント認証そのものではない。本番運用ではTLS必須

## 起動（常駐ホスト側）

```bash
codex login   # 初回のみ。ChatGPTアカウントでブラウザ認証
codex app-server --listen ws://0.0.0.0:4500 \
  --ws-auth capability-token --ws-token-file /path/to/token
```

stdio（デフォルト）は同一マシン上のプロセス間通信専用。iOSからのリモート接続には使えないので
必ず `--listen ws://...` を指定する。

パターンB（マルチユーザー）では、ユーザーごとに `CODEX_HOME` を分けたインスタンスを起動して
設定・認証状態・履歴を完全分離する:

```bash
CODEX_HOME=/srv/codex-homes/<userId> codex app-server --listen ws://127.0.0.1:<port> ...
```

## Swift実装

### パッケージ構成

依存ゼロの SwiftPM ライブラリとして作る（`URLSessionWebSocketTask` だけで通信できる）。

```swift
// Package.swift
.library(name: "AppServerClient", targets: ["AppServerClient"])
platforms: [.iOS(.v17), .macOS(.v10_15)]
dependencies: []
```

### レイヤー分割

| ファイル | 役割 |
|---|---|
| `WebSocket.swift` | `URLSessionWebSocketTask` で `ws(s)://` に接続 |
| `JSONRPC.swift` | リクエストID採番、method/paramsエンコード、応答/通知/サーバー起点リクエストの振り分け |
| `AppServerMethods.swift` | メソッド名の文字列定数（`thread/start` 等） |
| `AppServerPayloads.swift` / `AppServerResponseParsing.swift` | `Codable` での型付け。生JSONを上位に漏らさない |
| `AppServerEventParser.swift` | 非同期通知・サーバー起点リクエスト（承認要求等）→アプリ向け安定イベント型へのマッピング |
| `AppServerService.swift` | `startThread()` / `sendTurn()` のような高レベルAPIとして公開 |

### JSON-RPCクライアントの骨格

```swift
actor JSONRPCClient {
    private let task: URLSessionWebSocketTask
    private var nextID = 0
    private var pending: [Int: CheckedContinuation<[String: Any], Error>] = [:]
    var onNotification: ((String, [String: Any]?) -> Void)?

    init(url: URL, session: URLSession = .shared) {
        task = session.webSocketTask(with: url)
        task.resume()
        Task { await receiveLoop() }
    }

    // id付き → レスポンス待ち
    func call(_ method: String, params: [String: Any] = [:]) async throws -> [String: Any] {
        nextID += 1
        let id = nextID
        try await send(["method": method, "id": id, "params": params])
        return try await withCheckedThrowingContinuation { pending[id] = $0 }
    }

    // idなし → fire-and-forget（例: initialized 通知）
    func notify(_ method: String, params: [String: Any] = [:]) async throws {
        try await send(["method": method, "params": params])
    }

    private func send(_ obj: [String: Any]) async throws {
        let data = try JSONSerialization.data(withJSONObject: obj)
        try await task.send(.data(data))
    }

    private func receiveLoop() async {
        while let message = try? await task.receive() {
            guard case .data(let data) = message,
                  let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { continue }
            if let id = obj["id"] as? Int, let cont = pending.removeValue(forKey: id) {
                cont.resume(returning: (obj["result"] as? [String: Any]) ?? [:])
            } else if let method = obj["method"] as? String {
                onNotification?(method, obj["params"] as? [String: Any])
            }
        }
    }
}
```

実運用ではエラーレスポンス（`error.code`/`message`）のハンドリング、`Codable` への差し替え、
再接続ロジックを足す。ワイヤ上は `"jsonrpc":"2.0"` ヘッダを省略できる。

**注意: 上の骨格は「サーバー起点リクエスト」を扱えていない。** app-server は承認要求などで
「`id` と `method` の両方を持つメッセージ」をクライアントに送ってくる（通知ではなくリクエスト）。
受信ループで「`id` + `method` あり → クライアントが応答を返す義務があるリクエスト」として
3分岐にし、応答を書き戻す経路を必ず実装する。これを落とすとエージェントが承認待ちで永久に止まる。

### 接続シーケンス（厳守）

```
connect
  → initialize リクエスト送信（clientInfo, capabilities を含む）
  → initialized 通知を送信
  → （未ログインなら）account/login/start → ログインフロー → account/login/completed 通知
  → thread/start（新規）または thread/resume（再開）
  → turn/start（ユーザー入力）
  → item/agentMessage/delta 等の通知を購読して逐次描画
  → item/commandExecution/requestApproval 等のサーバー起点リクエストに応答
  → turn/completed
```

`clientInfo.name` はOpenAI側のクライアント識別に使われる。エンタープライズ利用では事前登録が要る場合がある。

### iOSからの device code ログイン実装例（パターンB）

```
1. account/login/start {"type": "chatgptDeviceCode"} を送る
2. レスポンス {loginId, verificationUrl, userCode} を受ける
3. userCode を画面に大きく表示し、SFSafariViewController で verificationUrl を開く
4. ユーザーが自分のChatGPTアカウントでサインインしてコード入力
5. account/login/completed 通知を受けたらログイン済みUIへ遷移
   （やめるときは account/login/cancel {loginId}）
```

## 主要JSON-RPCメソッド早見表

| カテゴリ | メソッド |
|---|---|
| ハンドシェイク | `initialize`, `initialized` |
| アカウント | `account/login/start`, `account/login/cancel`, `account/logout`, `account/read`, `account/rateLimits/read`, `account/usage/read` |
| スレッド | `thread/start`, `thread/resume`, `thread/fork`, `thread/list`, `thread/read`, `thread/archive` |
| ターン | `turn/start`, `turn/steer`, `turn/interrupt` |
| ファイル | `fs/readFile`, `fs/writeFile`, `fs/readDirectory`, `fs/watch` |
| モデル/設定 | `model/list`, `config/read`, `config/value/write` |
| スキル/プラグイン | `skills/list`, `plugin/list`, `plugin/install` |
| 単発コマンド | `command/exec`（+ `/write`, `/terminate`, `/resize`。PTY対応） |
| 音声（experimental） | `thread/realtime/start`, `appendSpeech`(TTS), `appendAudio`(STT), `appendText`, `listVoices`, `stop` → 詳細は「リアルタイム音声」節 |
| 通知（サーバー→クライアント） | `account/login/completed`, `account/updated`, `account/rateLimits/updated`, `thread/started`, `turn/started`/`turn/completed`, `item/agentMessage/delta` |
| **サーバー起点リクエスト（応答必須）** | `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, `item/tool/requestUserInput`, `item/tool/call`（クライアント側ツール実行）, `account/chatgptAuthTokens/refresh` |

## リアルタイム音声 — TTS / STT（experimental）

一次ソース: `codex-rs/app-server-protocol/src/protocol/v2/realtime.rs`（2026-07-18確認）。
全メソッドが `#[experimental]` ゲート付きなので、`initialize` の capabilities で
`experimentalApi: true` を宣言する必要があり、仕様変更リスクも織り込むこと。

- **セッション開始**: `thread/realtime/start` — `outputModality: "audio" | "text"`、`voice`
  （一覧は `thread/realtime/listVoices`）、`model` 上書き、`prompt` 等を指定
- **TTS**: `thread/realtime/appendSpeech {threadId, text}` — 任意のテキストをセッションに
  読み上げさせる。音声は `thread/realtime/outputAudio/delta` 通知で
  `{data(base64 PCM), sampleRate, numChannels, samplesPerChannel, itemId}` として届き、
  iOSでは `AVAudioEngine` でそのまま再生できる
- **STT**: `thread/realtime/appendAudio` でマイク入力（同じAudioChunk形式）を送り、
  `thread/realtime/transcript/delta` / `transcript/done` で文字起こしを受ける。
  TTSと合わせて双方向の音声会話（Codex Voice相当）が組める
- **トランスポート**: `Websocket`（JSON-RPC接続にインバンド。実装が楽）または
  `Webrtc`（クライアントがSDP offerを渡し、応答SDPは `thread/realtime/sdp` 通知。低遅延）
- **終了/異常系**: `thread/realtime/stop`、`thread/realtime/error`、`thread/realtime/closed`
- プロトコル版は `version` で指定（v1: legacy Bidi / v2: Realtime Voice API / v3: Codex Voice互換）
- 位置づけ: Codexエージェントとの音声対話用の設計。ただし `appendSpeech` は任意テキストを
  読ませられるため、実用上はTTSとしても使える。汎用TTS APIの正式な代替ではない点は認識しておく

## 画像生成を使う場合

- `image_generation` ツール（`gpt-image` 系、APIキー不要）はChatGPTログイン経由でも使える
- **既知バグ**（[openai/codex#21952](https://github.com/openai/codex/issues/21952)）: app-server は
  `[features].image_generation = false` や `--disable image_generation` を無視し、`tools[]` に
  `image_generation` を出し続ける（`codex exec` は正しく無効化される）。無効化に依存した設計をしない

## 罠

- エラー `-32001`（サーバー過負荷）は**指数バックオフで再試行**する前提でクライアントを書く
- 権限指定は新方式 `"permissions": ":workspace"` を使い、旧方式 `"sandbox": "workspaceWrite"` と
  **同時指定しない**
- 再接続時は `thread/resume` を無条件に投げず、`thread/loaded/list` → 読み込み済みなら
  `addConversationListener` + `thread/read(includeTurns: true)` を優先し、`resume` はフォールバックに留める
  （無条件resumeは二重ロード・履歴重複の原因になる）
- 型定義は `codex app-server generate-ts --out ./schemas` / `generate-json-schema --out ./schemas` で
  バージョンに対応したものを都度生成し、Swift側の型とドリフトしていないか確認する

## 参考実装・出典

- [Codex App Server（公式ドキュメント）](https://developers.openai.com/codex/app-server)
- [codex/codex-rs/app-server/README.md（プロトコル仕様）](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [codex-rs/app-server-protocol/src/protocol/v2/account.rs（認証4モードの一次定義。`chatgptAuthTokens` の "INTERNAL USE ONLY" 注記もここ）](https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/src/protocol/v2/account.rs)
- [codex-rs/app-server-protocol/src/protocol/common.rs（全メソッド名⇔型のレジストリ。メソッド名の正はここで確認）](https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/src/protocol/common.rs)
- [Codex Authentication（公式）](https://developers.openai.com/codex/auth)
- [Codex Enterprise Access Tokens（公式。Business/Enterprise向けワークスペース資格情報）](https://developers.openai.com/codex/enterprise/access-tokens)
- [Agmente — iOS client for coding agents via ACP or Codex app-server](https://github.com/rebornix/Agmente)（`AppServerClient/` 配下が本スキルのレイヤー分割の元ネタ。フルの参考実装として読む価値がある）
- [codex_sdk (Elixir) OAuth and Login](https://codex-sdk.hexdocs.pm/09-oauth-and-login.html)（非公式SDKだが `account/login/start` の各パラメータとリフレッシュ応答の実装例として有用）
- [Build for iOS（公式ユースケース）](https://developers.openai.com/codex/use-cases/native-ios-apps)
- [Using Codex CLI OAuth tokens as a backend — how it works + why it is risky](https://gist.github.com/ravidsrk/4e72b774c044917cd260560ec5831e1d)（トークンプーリング型の規約リスクの根拠）

調査日: 2026-07-18。プロトコルは活発に変わっているので、実装前に `codex app-server generate-json-schema`
で使用バージョンのスキーマを再生成して突き合わせること。
