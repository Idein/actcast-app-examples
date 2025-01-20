# UDP Multicast 送信サンプル


**※このサンプルアプリケーションはActcastOS 3 に対応しています**


## 概要

Raspberry Piで UDP Multicast を使って相互通信するデモアプリです。

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)


## Actsim での動作確認

### actdk の準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```


## 設定項目

- multicast_addr
- multicast_port
