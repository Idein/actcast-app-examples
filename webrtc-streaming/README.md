# WebRTC Streaming

**※このサンプルアプリケーションは ActcastOS 4 にのみ対応しています**

## 概要

カメラの映像（任意でマイクの音声も）を WebRTC でブラウザへ配信するサンプルアプリです。シグナリングには Actcast の Custom Command を使うため、専用のシグナリングサーバーは要りません。TURN は使わず、Google の STUN サーバーのみで P2P 接続します。

映像は、アプリが取得したフレームを GStreamer の `appsrc` へ渡して配信する構成です。フレームはエンコード前に Python の処理（`app/publisher.py` の `process_frame`）を通るため、Hailo の推論結果を重ねるといった前段処理を差し込めます。このサンプルでは、取得側の簡易なパイプラインからフレームを `appsink` で受け取ります。エンコードは VideoCore のハードウェアエンコーダ（`v4l2h264enc`）で行います。

## 前提

- 対象機種:
  - Raspberry Pi 4B
  - Compute Module 4
- カメラ:
  - Raspberry Pi カメラモジュール（CSI 接続）
- 音声を配信する場合は、ALSA で認識されるマイク（USB マイクなど）。マイクがない機体では、`media_type` が `both` でも映像のみで配信します
- Custom Command に対応した ActcastOS / エージェント（ActcastOS 4.32.0 以降）
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)

## Actsim での動作確認

### 準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```

### actdk run

`actdk run` により Actsim 上でアプリケーションの動作確認をすることができます。停止させるには `Ctrl + C` を押します。

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

起動したら、後述のシグナリングの流れに沿って Custom Command を発行し、映像が届くことを確認します。

## Actcast Agent での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

## シグナリングの流れ

Custom Command の payload と応答は JSON です。ICE 候補を SDP に埋め込む非トリクル方式で、2往復で接続します。

1. 視聴側が `{"op": "offer"}` を送ると、アプリはセッションを開始し、ICE 候補の収集が終わるまで待って、候補入りの SDP を `{"sdp": "..."}` の形で返します
2. 視聴側は受け取った SDP から answer を作り、`{"op": "answer", "sdp": "..."}` を送ります。これで接続が確立します

このほか、`{"op": "status"}`（セッションと ICE の状態を返す）と `{"op": "reset"}`（セッションを破棄する）に対応しています。`offer` に `"restart": true` を付けると、既存のセッションを破棄して新しいセッションを始めます。セッションは最初の `offer` で始まるため、アプリの起動直後はカメラを掴みません。

Custom Command の発行には、Actcast API の Custom Command 実行（`POST /v0/groups/<group_id>/devices/<device_id>/jobs/custom_command`、結果は `GET /v0/groups/<group_id>/devices/<device_id>/custom_command/<job_id>` で取得）などを使います。API への POST の本文に書いた JSON が、そのままアプリへの payload として渡ります。ブラウザの JavaScript から Actcast API を直接呼ぶことは CORS の制約でできないため、接続は後述のサーバ側サンプルを介して行います。

### サーバ側サンプル（Python）で試す

`server/` に、ブラウザと Actcast API の間に入るサーバのサンプル実装があります（Python の標準ライブラリのみで動作します）。サーバが Custom Command の発行と結果の取得を行い、ページの「接続」ボタン1つで offer の取得から answer の送信まで自動で進みます。API トークンはサーバ側にだけ置かれ、ブラウザには渡りません。

```bash
ACTCAST_API_TOKEN=<グループ API トークン> \
ACTCAST_GROUP_ID=<グループ ID> \
ACTCAST_DEVICE_ID=<デバイス ID> \
python3 server/server.py
```

起動したら `http://127.0.0.1:8080/` をブラウザで開きます。開発環境のデバイスでは `ACTCAST_API_BASE=https://api.dev.actcast.io` を指定します。待ち受けは既定で 127.0.0.1 です。他の端末から開きたい場合は `HOST=0.0.0.0` を指定できますが、その場合はサーバへ届く人なら誰でもデバイスへコマンドを送れる点に注意してください。

## 設定項目

- `media_type`: 配信するメディアを指定します。`video`（映像のみ）、`audio`（音声のみ）、`both`（両方。既定）

## 実装について

- Custom Command のエージェントとアプリの間のプロトコルは、`app/command_bridge.py` で直接実装しています。ハンドラは同じリクエストで複数回呼ばれることがあるため、応答はリクエストの UUID でキャッシュして冪等にしています
- offer の SDP はアプリログにも出力します（`===OFFER_BEGIN===` から `===OFFER_END===`）。actdk のログ読みで SDP を取りたい場合の保険です
- 映像のフレームは、取得用のパイプライン（`appsink` 終端）から Python を経由して、配信用パイプラインの `appsrc` へ渡ります。前段処理の差し込み口は `app/publisher.py` の `process_frame` です。実際のアプリでは、取得と推論のループが生成したフレームをここへ供給する形になります
- 開発時の動作確認用に、環境変数 `VIDEO_SRC=test` で映像・音声をテストソース（videotestsrc / audiotestsrc）に切り替えられます。この場合の映像のエンコードには `x264enc` を使います（デバイスでの通常動作ではハードウェアエンコードを使います）

## 注意事項

- ネットワークは host モードです（`network_mode: "host"`）。WebRTC の host 候補がデバイス自身の LAN アドレスになるため、同一 LAN の視聴者とも直接つながります
- host モードではアプリがホストのネットワークを直接使うため、ホスト側のサービスと待ち受けポートが衝突しないよう注意してください。このサンプルは待ち受けポートを持ちません
- ハードウェアエンコード（`v4l2h264enc`）は、エレメント単体では配信を開始できません（`VIDIOC_STREAMON` が ESRCH で失敗します。実機で確認）。`amazon-kinesis-video-streams` サンプルと同じく、前段に `v4l2convert`、後段に `video/x-h264,level=(string)4` の caps を入れた構成で使う必要があります。また、manifesto には `camera` に加えて `videocore` デバイスの宣言が必要です
- 音声デバイスの宣言は、パス明示の形にしています。素の `{"type": "sound"}` はエージェントが対応しておらず起動時に拒否され、`required: false` を付けた素の形では起動するものの `/dev/snd` のノードが渡らないためマイクが使えません。デバイスパス中のカード番号（このサンプルでは `C2`）は機体ごとに違うので、対象機で `arecord -l` を確認して合わせてください
- 音声の実マイクでの配信は、マイク付きの実機で確認済みです（このサンプルと同じデバイス宣言と配信構成で、offer への m=audio の追加から視聴側での再生まで）。マイクがない機体で映像のみにフォールバックすること（`media_type` が `both` の場合）も確認しています
