# Local Video Server

**※このサンプルアプリケーションは ActcastOS 3 にのみ対応しています**

## 概要

actfw-core 2.10.0 で導入された `LocalVideoServer` のデモです。

アプリ起動後、デバイスと同じネットワークに接続したマシンから `http://<device_local_ip>:5100` にアクセスすることで、カメラの映像を確認できます。
[デバイスの mDNS](https://actcast.io/docs/ja/DeviceManagement/DeviceInfo/#mdns) を有効にしていれば `http://<hostname>.local:5100` でもアクセスできます。

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
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

## Actcast Agent での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

### 設定項目

- `display`: HDMI ディスプレイへ撮影画像と FPS の描画を行う。
- `use_usb_camera`: Raspberry Pi Camera の代わりに USB カメラを使用する場合は `true` にする。
- `local_video_server`: Local Video Server を有効にし、5100 ポートで動画の配信を行う。`http://<device_local_ip>:5100` でアクセスできる。
- `quality`: Local Video Server の画質の設定。0 (最低画質) から 95 (最高画質) までの値を指定する。100 にすると無圧縮となる。
