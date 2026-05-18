# filtered-network-mode-ingress

**※このサンプルアプリケーションは ActcastOS 3, 4 に対応しています**

## 概要

`network_mode: filtered` の ingress 制限を確認するサンプルです。

このアプリはコンテナ内の TCP 8080 番ポートで HTTP サーバーを起動し、
`{"message": "Hello, World!"}` を返します。

外部公開は `published_ports` により `host_port: 3000 -> container_port: 8080` で行います。
アクセス可否は `filter_rules.ingress` の送信元 IP 制限に従います。

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

アプリ起動後、許可されているクライアント IP から以下にアクセスします。

```bash
curl http://<DEVICE_IP>:3000
```

レスポンス例:

```json
{"message": "Hello, World!"}
```

## 本番環境での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、作成したアプリケーション ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

## 設定項目

このサンプルでは `setting_schema.json` の設定項目はありません。

## 注意事項

`published_ports.container_port` と `filter_rules.ingress.container_port` の両方に一致した場合の通信できます。

## 追加のフィルタールール

[additional_filter_rules.json を配置することで](https://actcast.io/docs/ja/ApplicationDevelopment/Reference/ApplicationSchemas/#additional_filter_rules)  Act に対する追加のフィルタールールをテストできます。
