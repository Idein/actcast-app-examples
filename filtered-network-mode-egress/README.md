# filtered-network-mode-egress

**※このサンプルアプリケーションは ActcastOS 3, 4 に対応しています**

## 概要

`network_mode: filtered` の egress 制限を確認するサンプルです。

このアプリは SOCKS5 プロキシ 経由で外向き通信を行い、
マニフェストの `filter_rules.egress` で許可された通信のみ成功することを確認します。

- 許可される通信の例
  - `https://actcast.io:443` へのアクセス
  - `http://172.24.175.1:8000` へのアクセス
- 拒否される通信の例
  - `https://idein.jp:443` へのアクセス
  - `http://172.24.175.1:9000` へのアクセス
- プロキシを使わない通信は失敗する想定

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)

## 開発モードでの動作確認

### 準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```

### actdk run

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

ログには以下のような通知が出力されます。

```json
debug_log| req: https://actcast.io
[{"result":"https://actcast.io -> OK | 200"}]
debug_log| req: https://www.idein.jp
[{"result":"https://www.idein.jp -> Err | SOCKSHTTPSConnectionPool(host='www.idein.jp', port=443): Max retries exceeded with url: / (Caused by NewConnectionError(\"SOCKSHTTPSConnection(host='www.idein.jp', port=443): Failed to establish a new connection: 0x02: Connection not allowed by ruleset\"))"}]
debug_log| req: http://172.24.175.1:8000
[{"result":"http://172.24.175.1:8000 -> OK | 200"}]
debug_log| req: http://172.24.175.1:9000
[{"result":"http://172.24.175.1:9000 -> Err | SOCKSHTTPConnectionPool(host='172.24.175.1', port=9000): Max retries exceeded with url: / (Caused by NewConnectionError(\"SOCKSConnection(host='172.24.175.1', port=9000): Failed to establish a new connection: 0x02: Connection not allowed by ruleset\"))"}]
```

`without_proxy` のログは、プロキシ未使用通信が失敗したことを示します。

## 本番環境での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、作成したアプリケーション ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

## 設定項目

- `target_urls`: 疎通確認に使う接続先URLのリスト (例: `https://actcast.io,http://172.24.175.1:8000`)
- `check_without_proxy`: プロキシなしによる通信を試すかどうかのフラグ


## 追加のフィルタールール

[additional_filter_rules.json を配置することで](https://actcast.io/docs/ja/ApplicationDevelopment/Reference/ApplicationSchemas/#additional_filter_rules)  Act に対する追加のフィルタールールをテストできます。
