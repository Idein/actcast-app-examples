# convert-camera-images-to-grayscale

## 概要
このアプリはデバイスのカメラで読み込んだ画像を、グレースケール画像に変換するサンプルアプリです。  
変換結果は、デバイスに接続したディスプレイや Actcast の [TakePhoto](https://actcast.io/docs/ja/ActManagement/TakePhoto/) 機能を使って確認できます。

## 前提
- 対象機種
  - [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
  - [ai cast](https://www.idein.jp/ja/news/230208-aicast-release)
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

アプリケーションの動作中に以下のコマンドを実行すると、グレースケール画像を data URL 形式で取得できます。
```bash
actdk photo
```

> 接続したディスプレイに画像を表示する場合は `act_settings.json` を以下のように変更してください。
> ```json
> {
>  "display": true
> }
> ```

## Actcast Agent での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

接続したディスプレイや Actcast の [TakePhoto](https://actcast.io/docs/ja/ActManagement/TakePhoto/) 機能を使って変換されたグレースケール画像を確認できます。

### 設定項目

- `display`: デバイスに接続したディスプレイにグレースケール画像を表示する。
