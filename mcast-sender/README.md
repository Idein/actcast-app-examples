# UDP Multicast 送信サンプル


**※このサンプルアプリケーションはActcastOS 3 に対応しています**


## 概要

Raspberry Piで [UDP Multicast](https://ja.wikipedia.org/wiki/IP%E3%83%9E%E3%83%AB%E3%83%81%E3%82%AD%E3%83%A3%E3%82%B9%E3%83%88) を使って相互通信するデモアプリです。

送信側はこのディレクトリのアプリを、受信側は [UDP Multicast 受信サンプル](../mcast-receiver) を使ってください。

または片方を [individuwill/mcast](https://github.com/individuwill/mcast) などの送受信プログラムで代用することもできます。

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)


## Actsim での動作確認

### actdk の準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE_IP>
```

actdk run で actsim で実行します

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```


## actcastos での動作確認

### actdk upload してアプリを作り act インストールする

- `.actdk/setting.json` の `app_server_id` を ベンダコンソールのアプリケーション ID (`https://actcast.io/groups/<GROUP_ID>/dev/apps/<APP_ID>`
)に変更します
- `actdk upload` コマンドを実行します
- `https://actcast.io/groups/<GROUP_ID>/dev/apps/<APP_ID>/builds` でビルドが完了するのを待ちます
- ビルドが完了したら 「テスト」を押して act を作成し、actcastos の入ったデバイスにインストールします

## 設定項目

- `multicast_group`
  - UDP Multicast 送信先の [グループアドレス](https://ja.wikipedia.org/wiki/IP%E3%83%9E%E3%83%AB%E3%83%81%E3%82%AD%E3%83%A3%E3%82%B9%E3%83%88#IP%E3%83%9E%E3%83%AB%E3%83%81%E3%82%AD%E3%83%A3%E3%82%B9%E3%83%88%E3%82%B0%E3%83%AB%E3%83%BC%E3%83%97%E3%82%A2%E3%83%89%E3%83%AC%E3%82%B9)
- `multicast_port`
  -  UDP Multicast 送信先のポート番号
- `multicast_message`
  - 送信するメッセージ
