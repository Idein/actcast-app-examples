# Custom Image Example

## 概要

カスタムイメージ機能を使う例です。
Python 3.12 をインストールしたイメージをビルドし、そのイメージを使ってアプリケーションを実行します。

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
  - ファームウェアバージョン: 1.34.0 以降
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
  - バージョン: 1.17.0 以降
- [Docker](https://www.docker.com/), [buildx extension](https://github.com/docker/buildx)

## カスタムイメージのビルド方法

```bash
cd custom-image
# イメージのビルド (時間がかかります)
docker buildx build --platform linux/amd64 -t ghcr.io/idein/custom-image-example --load .
```

`.actdk/dependencies.json` に `base_image` として `ghcr.io/idein/custom-image-example` が指定されており、ここでビルドしたイメージが使われます。

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

- `display`: HDMI ディスプレイへ撮影画像と分類結果 top-10 の描画を行う。
- `threshold`: 確度がこの閾値を越えたら通知を行う。
