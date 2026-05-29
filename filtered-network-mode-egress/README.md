# filtered-network-mode-egress

**※このサンプルアプリケーションは ActcastOS 3, 4 に対応しています**

## 概要

`network_mode: filtered` の egress 制限を確認するサンプルです。

このアプリは SOCKS5 プロキシ 経由で外向き通信を行い、
マニフェストの `filter_rules.egress` で許可された通信のみ成功することを確認します。

- 許可される通信の例
  - `https://actcast.io:443` へのアクセス
  - `http://<target_ip>:<target_port>` へのアクセス
- 拒否される通信の例
  - `https://idein.jp:443` へのアクセス
  - `http://<target_ip>:<target_port + 1>` へのアクセス
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
debug_log| req_by_allowed_domain: https://actcast.io
[{"kind":"allowed","result":"expected","url":"https://actcast.io"}]
debug_log| req_by_denied_domain: https://idein.jp
[{"kind":"denied","result":"expected","url":"https://idein.jp"}]
debug_log| req_by_allowed_ip: http://172.17.0.1:8000
[{"kind":"allowed","result":"expected","url":"http://172.17.0.1:8000"}]
debug_log| req_by_denied_ip: http://172.17.0.1:8001
[{"kind":"denied","result":"expected","url":"http://172.17.0.1:8001"}]
debug_log| req_without_proxy: https://actcast.io
[{"kind":"without_proxy","result":"expected HTTPSConnectionPool(host='actcast.io', port=443): Max retries exceeded with url: / (Caused by NewConnectionError(\"HTTPSConnection(host='actcast.io', port=443): Failed to establish a new connection: [Errno 101] Network is unreachable\"))","url":"https://actcast.io"}]
debug_log| req_without_proxy: https://idein.jp
[{"kind":"without_proxy","result":"expected HTTPSConnectionPool(host='idein.jp', port=443): Max retries exceeded with url: / (Caused by ConnectTimeoutError(<HTTPSConnection(host='idein.jp', port=443) at 0x7fb825a3d0>, 'Connection to idein.jp timed out. (connect timeout=5)'))","url":"https://idein.jp"}]
debug_log| req_without_proxy: https://172.17.0.1:8000
[{"kind":"without_proxy","result":"expected HTTPSConnectionPool(host='172.17.0.1', port=8000): Max retries exceeded with url: / (Caused by SSLError(SSLError(1, '[SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:992)')))","url":"https://172.17.0.1:8000"}]
debug_log| req_without_proxy: https://172.17.0.1:8001
[{"kind":"without_proxy","result":"expected HTTPSConnectionPool(host='172.17.0.1', port=8001): Max retries exceeded with url: / (Caused by NewConnectionError(\"HTTPSConnection(host='172.17.0.1', port=8001): Failed to establish a new connection: [Errno 111] Connection refused\"))","url":"https://172.17.0.1:8001"}]
```

`without_proxy` のログは、プロキシ未使用通信が失敗したことを示します。

## 本番環境での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、作成したアプリケーション ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

## 設定項目

- `target_ip`: 疎通確認に使う接続先ホスト IP。


## 追加のフィルタールール

[additional_filter_rules.json を配置することで](https://actcast.io/docs/ja/ApplicationDevelopment/Reference/ApplicationSchemas/#additional_filter_rules)  Act に対する追加のフィルタールールをテストできます。
