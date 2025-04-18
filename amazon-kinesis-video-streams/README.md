# Kinesis Video Stream example

**※このサンプルアプリケーションはActcastOS 3 に対応しています**

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

actsim にDockerfile を転送します
`<REMOTE>` actsim がインストールされた Raspberry Pi の IP アドレスです

ユーザ名とパスワードは [actsim のセットアップ時に決めたもの](https://actcast.io/docs/ja/ApplicationDevelopment/GettingStarted/SetupActsim/) です

```bash
rsync -e=ssh pi@<REMOTE> Dockerfile /home/pi/Dockerfile
```

ssh でログインして し docker build します

```bash
ssh pi@<REMOTE>
```

```bash
cd ~/
mkdir workspace
chmod 777 workspace
cd workspace
mv ~/Dockerfile ./
sudo docker build --output=. .
```

docker image のビルドが終わったら Dockerfile 隣に .so がコピーされていることを確認します

```console
$ ls /home/pi/workspace
drwxr-xr-x 2 pi   pi     4096 Nov 18 06:45 .
drwxr-xr-x 3 root root   4096 Jan 28  2022 ..
-rw-r--r-- 1 pi   pi     1448 Nov 18 06:45 Dockerfile
-rwxr-xr-x 1 root root 471872 Nov 15 09:29 libKinesisVideoProducer.so
-rwxr-xr-x 1 root root 601760 Nov 15 09:29 libcproducer.so
-rwxr-xr-x 1 root root 528340 Nov 15 09:30 libgstkvssink.so
```

コピーを確認したら actsim からログアウトし、
actsim にできたこの 3 つの shared object を `rsync` 等でホストマシンの `app/*` へコピーします

```bash
rsync -e=ssh pi@<REMOTE>:/home/pi/workspace/\*.so ./app/
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
4. 2, 3 で作った アクセスキーとストリーム名を入れた `act_settings.json` を作ります

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


