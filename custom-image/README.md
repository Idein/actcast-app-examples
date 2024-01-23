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

## ベースイメージのビルド方法

> [!NOTE] 
> ベースイメージ `ghcr.io/idein/custom-image-example` は予め公開されているため、動作確認のために改めてビルドする必要はありません。

```bash
cd custom-image
# イメージのビルド (時間がかかります)
docker buildx build --platform linux/amd64 -t ghcr.io/idein/custom-image-example --load .
```

`.actdk/dependencies.json` に `base_image` として `ghcr.io/idein/custom-image-example` が指定されており、`actdk build --release` や `actdk upload` ではここでビルドしたイメージが使われます。


## Actsim での動作確認

### 準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```

### actdk run

`actdk run` により Actsim 上でアプリケーションの動作確認をすることができます。停止させるには `Ctrl + C` を押します。
このコマンドでは、ベースイメージは[公開されているもの](https://github.com/Idein/actcast-app-examples/pkgs/container/custom-image-example)が使われます。

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

以下のようなログが出力されます。

```json
[{"python_version": "3.12.0 (main, Nov 29 2023, 03:48:30) [GCC 10.2.1 20210110]"}]
```

ベースイメージを変更・再ビルドした場合は、以下のコマンドにより動作確認が可能です。

```bash
actdk build --release
actdk deploy <IDENTIFIER_YOU_LIKE>
actdk run -a --release <IDENTIFIER_YOU_LIKE>
```

詳細は [ActDK のコマンドリファレンス](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/Reference/Actdk/)を参照してください。

## Actcast Agent での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

Act Log で以下のようなログを確認できます。

```json
[{"python_version": "3.12.0 (main, Nov 29 2023, 03:48:30) [GCC 10.2.1 20210110]"}]
```
