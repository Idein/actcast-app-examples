# file-upload-to-s3

## 概要

S3 にファイルをアップロードするサンプルアプリです。
ネットワークマニフェストと SOCKS5 プロキシの設定を行うことで、プロキシ経由でのアップロードを行うことができます。

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)

## アップロード先の準備

S3 にファイルをアップロードするため、事前に [S3 のバケット](https://docs.aws.amazon.com/ja_jp/AmazonS3/latest/userguide/create-bucket-overview.html)を作成しておきます。
また、アップロードに使用するユーザーの[アクセスキーとシークレットキーを作成](https://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/id_credentials_access-keys.html)します。このとき、該当 S3 バケットへの書き込み権限 (PutObject) を付与してください。

作成したバケットの名前、リージョン、アクセスキー、シークレットキーを控えておきます。

## 動作確認の準備

このアプリは ActcastOS3 (32bit bullseye) と ActcastOS4 (64bit bookworm) の両方で動作確認が可能です。

動作確認には以下のいずれかの環境を使用します。

- Actsim (ActcastOS3 32bit bullseye)
- 開発モードが有効になった ActcastOS4 (64bit bookworm)

Actsim のセットアップは [こちら](https://actcast.io/docs/ja/ApplicationDevelopment/GettingStarted/SetupActsim/) を参照してください。

Actcast OS4 での動作確認を行う場合は、こちらの手順のとおりに [Dev Mode を有効化](https://actcast.io/docs/ja/ApplicationDevelopment/DevMode/) してください。

確認用のデバイスのセットアップが完了したら、actdk に[確認用デバイスを登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```

## 確認用デバイスでの動作確認手順

`act_settings.json` を編集し、控えておいたバケットの名前、リージョン、アクセスキー、シークレットキーに変更します。

* `AWS region`: AWS S3 のバケットのあるリージョン。
* `AWS access key id`: AWS のアクセスキー。
* `AWS secret access key`: AWS のシークレットアクセスキー。
* `bucket name`: S3 バケット名。

`actdk run` により Actsim 上でアプリケーションの動作確認をすることができます。停止させるには `Ctrl + C` を押します。

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

ファイルアップロードに成功した場合は、以下のようなメッセージが表示されます。また、S3 に `<時刻>.txt` というファイルが作られます。

```json
[{"message": "S3 upload start"}]
[{"message": "S3 upload succeeded"}]
```

ファイルアップロードに失敗した場合は、以下のようなメッセージが表示されます。

```json
[{"message": "S3 upload start"}]
[{"message": "S3 upload failed: (失敗理由)"}]
```

## 本番環境での動作確認

確認用デバイスではなく ActcastOS3 や非開発者モードの ActcastOS4 上で動作確認を行う場合の手順です。

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

## 補足説明

`root.tar` には、SOCKS プロキシ対応のパッチがあてられた `botocore` が含まれています。
`root.tar` はアプリケーションのビルド時に展開され、アプリケーションのルートディレクトリに配置されます。

