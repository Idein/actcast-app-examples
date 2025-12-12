# Kinesis Video Stream example

**※このサンプルアプリケーションはActcastOS 4 向けです**

OS3 向けのサンプルは [こちら](https://github.com/Idein/actcast-app-examples/tree/b595cf3a830f143bd845353b9a6c6de40efdcaf0/amazon-kinesis-video-streams)

## 概要

Raspberry Piに接続されたカメラの映像をKinesis Video Streamに配信するサンプルアプリです。

## 前提

- 対象機種: [ActcastOS 4 がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- Raspberry Pi に接続可能なカメラ
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [AWS Kinesis Video Stream](https://docs.aws.amazon.com/ja_jp/kinesisvideostreams/latest/dg/producer-sdk-cpp.html)

## ビルド方法

Actcast OS4 の入った Raspberry Pi を用意します。
こちらの手順のとおりに [Dev Mode を有効化](https://actcast.io/docs/ja/ApplicationDevelopment/DevMode/) してください。

__※開発者モードを有効化してから ssh でログインできるようになるまで数分かかる場合があります。__

### kvssink のビルド

gstreamer 経由で kinesis video stream を使うためには `app/*` に以下の shared object が必要です。

- libKinesisVideoProducer.so
- libgstkvssink.so
- libcproducer.so
- libkvsCommonCurl.so

これらは [ソースコード](https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp) からビルドする必要があります。
依存ライブラリのバージョンを揃えるために ssh で開発者モードを有効にしたデバイスにログインして docker コンテナの中でビルドします。

開発者モードを有効にしたデバイスにDockerfile を転送します。

```bash
rsync -e='ssh -i /path/to/privkey' ./Dockerfile actcast@<REMOTE>:/home/actcast/Dockerfile
```

- `<REMOTE>` は開発者モードを有効にしたデバイスの IP アドレス、または mdns で`<HOSTNAME>.local` です。
- `/path/to/privkey` はデバイスの開発者モードを有効にしたときに登録した公開鍵と対になる秘密鍵へのパスです。

デバイスに ssh でログインします。

```bash
ssh actcast@<REMOTE> -i /path/to/privkey
```

ホームディレクトリに Dockerfile があることを確認します。

```console
$ pwd
/home/actcast
$ ls -la | grep Docker
-rw-r--r-- 1 actcast actcast   1059 Dec 12 13:13 Dockerfile
```

docker build します。

```bash
docker build -t kvs-libs .
```

ビルドが終わったら、コンテナから shared object をコピーします。

```bash
cid=$(docker create kvs-libs /bin/bash -lc "true")
docker cp "$cid:/opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/libKinesisVideoProducer.so" .
docker cp "$cid:/opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/libgstkvssink.so" .
docker cp "$cid:/opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/dependency/libkvscproducer/kvscproducer-src/libcproducer.so.1.6.0" .
docker cp "$cid:/opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/dependency/libkvscproducer/kvscproducer-src/libkvsCommonCurl.so.1.6.0" .
```

.so がホームディレクトリにコピーされていることを確認します。

```console
$ ls /home/actcast | grep \.so
-rwxr-xr-x 1 actcast actcast 463440 Dec 12 14:41 libcproducer.so.1.6.0
-rwxr-xr-x 1 actcast actcast 245248 Dec 12 12:58 libgstkvssink.so
-rwxr-xr-x 1 actcast actcast 249352 Dec 12 12:57 libKinesisVideoProducer.so
-rwxr-xr-x 1 actcast actcast  85224 Dec 12 14:41 libkvsCommonCurl.so.1.6.0

```

不要になったコンテナとイメージを削除します。

```bash
docker rm "$cid"
docker rmi kvs-libs
```

ssh しているデバイスからログアウトします。

```bash
exit
```

デバイスでビルドした shared object を `rsync` 等でホストマシンの `app/*` へコピーします

```bash
rsync -e='ssh -i /path/to/privkey'  \
  -av --prune-empty-dirs  --include='*/-' --include='*.so' --include='*.so.*' --exclude='*' \
  actcast@<REMOTE>:/home/actcast/ ./app/
```

symlink を作成します。

```bash
cd app
ln -s libcproducer.so.1.6.0 libcproducer.so.1
ln -s libcproducer.so.1 libcproducer.so
ln -s libkvsCommonCurl.so.1.6.0 libkvsCommonCurl.so.1
ln -s libkvsCommonCurl.so.1 libkvsCommonCurl.so
```

.so ファイルが揃っていることを確認します。

```console
$ ls -la | grep \.so
lrwxrwxrwx 1 idein developers     17 Dec 12 15:05 libcproducer.so -> libcproducer.so.1
lrwxrwxrwx 1 idein developers     21 Dec 12 15:05 libcproducer.so.1 -> libcproducer.so.1.6.0
-rwxr-xr-x 1 idein developers 463440 Dec 12 14:41 libcproducer.so.1.6.0
-rwxr-xr-x 1 idein developers 245248 Dec 12 12:58 libgstkvssink.so
-rwxr-xr-x 1 idein developers 249352 Dec 12 12:57 libKinesisVideoProducer.so
lrwxrwxrwx 1 idein developers     21 Dec 12 15:07 libkvsCommonCurl.so -> libkvsCommonCurl.so.1
lrwxrwxrwx 1 idein developers     25 Dec 12 15:07 libkvsCommonCurl.so.1 -> libkvsCommonCurl.so.1.6.0
-rwxr-xr-x 1 idein developers  85224 Dec 12 14:41 libkvsCommonCurl.so.1.6.0

```

## 開発者モードを有効にしたデバイスでの動作確認

kvs アプリを動かすためには以下のファイルが必要です。

- `app/libKinesisVideoProducer.so`
- `app/libgstkvssink.so`
- `app/libcproducer.so`
- `app/libcproducer.so.1`
- `app/libcproducer.so.1.6.0`
- `app/libkvsCommonCurl.so`
- `app/libkvsCommonCurl.so.1`
- `app/libkvsCommonCurl.so.1.6.0`
- `act_settings.json`

### actdk の準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。
デバイス名は仮に kvstest にしています。

```bash
actdk remote add kvstest@<REMOTE>
```

### Kinesis Video Stream の準備

AWS コンソールで Kinesis Video Stream を使うためには以下の準備が必要です。

1. AmazonKinesisVideoStreamsFullAccess を持つ IAM User を作ります
2. アクセスキーを生成します
3. Kinesis Video Stream を作成します
4. 2, 3 で作った アクセスキーとストリーム名を入れた `act_settings.json` を作ります

### actdk run で開発モードデバイス上での動作確認

`actdk run` によりデバイス上でアプリケーションの動作確認をすることができます。
停止させるには `Ctrl + C` を押します。

```bash
actdk run -a kvstest
```

### KinesisVideoStream への配信確認

AWS の Kinesis Video Stream のコンソールを確認してください。

![aws console demo](./demo.png?raw=true)

## Actcast Agent での動作確認

アプリを作成して Actcast Agent で動作確認を行います。

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。


