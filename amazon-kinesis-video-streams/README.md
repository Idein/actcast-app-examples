# Kinesis Video Stream example
## 概要
Raspberry Piに接続されたカメラの映像をKinesis Video Streamに配信するサンプルアプリです。

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- Raspberry Piに接続可能なカメラ
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)
- [AWS Kinesis Video Stream](https://docs.aws.amazon.com/ja_jp/kinesisvideostreams/latest/dg/producer-sdk-cpp.html)

## ビルド方法

### kvssink のビルド

gstreamer 経由で kinesis video stream を使うためには `app/*` に以下の shared object が必要です

- libKinesisVideoProducer.so
- libgstkvssink.so
- libcproducer.so

クロスコンパイルをしない場合 ssh で actsim にログインしてビルドします

依存をインストールします

```
sudo apt update
sudo apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-bad gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools
sudo apt install -y cmake libunwind-dev gcc g++ binutils libssl-dev git libcurl4-openssl-dev liblog4cplus-dev
```

[libgstkvssink.so](https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp) をソースコードからビルドします

```
git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git
cd amazon-kinesis-video-streams-producer-sdk-cpp
git checkout v3.4.1
mkdir build && cd build
cmake .. -DBUILD_TEST=TRUE -DBUILD_GSTREAMER_PLUGIN=TRUE -DCMAKE_INSTALL_PREFIX=.
make
```

actsim 上にできた以下の shared object をホストマシンの `app/*` へコピーします

```
libKinesisVideoProducer.so
libgstkvssink.so
dependency/libkvscproducer/kvscproducer-src/libcproducer.so
```

## Actsim での動作確認

以下のファイルが必要です

- `.actdk/setting.json`
- `app/libKinesisVideoProducer.so`
- `app/libgstkvssink.so`
- `app/libcproducer.so`
- `act_settings.json`

### actdk の準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```

### Kinesis Video Stream の準備

1. AmazonKinesisVideoStreamsFullAccess を持つ IAM User を作ります
2. アクセスキーを生成します
3. Kinesis Video Stream を作成します
4. 2, 3 で作った アクセスキーとストリーム名を入れた act_settings.json を作ります

### act_settings.json を生成

[.actdk/long_descriptions/ja](.actdk/long_descriptions/ja) を確認してください

### actdk run

`actdk run` により Actsim 上でアプリケーションの動作確認をすることができます。停止させるには `Ctrl + C` を押します。

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

## Actcast Agent での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

