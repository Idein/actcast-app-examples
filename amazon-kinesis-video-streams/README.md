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

これらは [ソースコード](https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp) からビルドする必要があります
依存ライブラリのバージョンを揃えるために ssh で actsim にログインして docker コンテナの中でビルドします

次の Dockerfile を使って docker イメージを作成します

```
FROM idein/actcast-rpi-app-base:buster-1
ENV DEBIAN_FRONTEND "noninteractive"
ENV DEBCONF_NOWARNINGS "yes"
RUN apt-get update -y
RUN apt-get \
    -o Dpkg::Options::="--force-confdef" \
    -o Dpkg::Options::="--force-confold" \
    upgrade -y
RUN apt-get install -y --no-install-recommends \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-bad gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools
RUN apt-get install -y --no-install-recommends \
    git cmake gcc g++ binutils libunwind-dev libssl-dev libcurl4-openssl-dev liblog4cplus-dev make autoconf build-essential
WORKDIR /opt
RUN git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git
WORKDIR /opt/amazon-kinesis-video-streams-producer-sdk-cpp
RUN git checkout v3.4.1
RUN mkdir build
WORKDIR /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build
RUN cmake .. -DBUILD_TEST=OFF -DBUILD_GSTREAMER_PLUGIN=TRUE -DBUILD_DEPENDENCIES=OFF -DCMAKE_INSTALL_PREFIX=.
RUN make
WORKDIR /opt
RUN cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/libKinesisVideoProducer.so /opt \
    && cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/libgstkvssink.so /opt \
    && cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/dependency/libkvscproducer/kvscproducer-src/libcproducer.so /opt
```

actsim に ssh でログインして docker image を作成します
password は raspberry です

```
ssh pi@<REMOTE>
```

```
cd ~/
mkdir workspace
chmod 777 workspace
cd workspace
vim Dockerfile
sudo docker build --tag kvssink:buster-1 .
```

docker image のビルドが終わったらコンテナを起動して shared object をコピーします

```
sudo docker run -ti -u 0:0 -v /home/pi/workspace:/workspace kvssink:buster-1 /bin/bash
```

コピーしたらコンテナを終了します

```
cp /opt/libKinesisVideoProducer.so /workspace
cp /opt/libgstkvssink.so /workspace
cp /opt/libcproducer.so /workspace
exit
```

コンテナの外に .so がコピーされていることを確認します

```
ls /home/pi/workspace
```

actsim にできたこの 3 つの shared object を `rsync` 等でホストマシンの `app/*` へコピーします

```
rsync -e ssh pi@<REMOTE>:/home/pi/workspace/libKinesisVideoProducer.so ./app
rsync -e ssh pi@<REMOTE>:/home/pi/workspace/libgstkvssink.so ./app
rsync -e ssh pi@<REMOTE>:/home/pi/workspace/libcproducer.so ./app
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

### actdk run で actsin 上での動作確認

`actdk run` により Actsim 上でアプリケーションの動作確認をすることができます。停止させるには `Ctrl + C` を押します。

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

### KinesisVideoStream への配信確認

AWS の Kinesis Video Stream のコンソールを確認してください

## Actcast Agent での動作確認

アプリを作成して Actcast Agent で動作確認を行います。

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。


