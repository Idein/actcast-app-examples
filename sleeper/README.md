# sleeper

## 概要

`sleeper` は、Actcast アプリケーションの最小構成を示すサンプルアプリです。

このアプリは起動すると Act エラーログに `Sleeping indefinitely.` を出力し、その後は何も処理せず待機し続けます。
カメラ、推論モデル、外部サービス、ユーザー設定には依存しないため、Actcast 上でのアプリケーション作成、アップロード、Act作成、実機へのインストール、起動確認といった基本的な流れを確認する用途に使えます。

このアプリは実用的な処理を行うためのものではなく、Actcast アプリの基本的な実行経路を確認するための最小サンプルです。

## 開発モードでの動作確認手順

1. actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)する
2. `actdk run -a <IDENTIFIER_YOU_LIKE>` を実行する

## 本番環境での動作確認手順

1. [Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)する
1. `.actdk/setting.json` の `app_server_id` を作成したアプリケーション ID に変更する
1. [アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)する
