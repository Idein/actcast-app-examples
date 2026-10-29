# Custom Image Example

**※このサンプルアプリケーションはActcastOS 3 と 4 に対応しています**

## 概要

カスタムイメージ機能を使う例です。
デフォルトのベースイメージより新しいバージョンの Python をインストールしたイメージをビルドし、そのイメージを使ってアプリケーションを実行します。

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
  - ファームウェアバージョン: 3.0.0 以降
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
  - バージョン: 1.51.0 以降
- [Docker](https://www.docker.com/), [buildx extension](https://github.com/docker/buildx)

## カスタムイメージの指定方法

`.actdk/dependencies.json` に `base_image` として `ghcr.io/idein/custom-image-example-bullseye`または`ghcr.io/idein/custom-image-example-bookworm` が指定されており、`actdk build` や `actdk upload` では後述する方法でビルドしたイメージが使われます。

`custom-image-bullseye`にはPython 3.12が、`custom-image-bookworm`にはPython 3.14がインストールされています。


## ベースイメージのビルド方法

このサンプルアプリで使用しているベースイメージのビルド方法を説明します。

> [!NOTE]
> ベースイメージ `ghcr.io/idein/custom-image-example-bookworm` 及び `ghcr.io/idein/custom-image-example-bullseye` は予め公開されているため、動作確認のために改めてビルドする必要はありません。

```bash
cd custom-image
# 事前に QEMU を有効にする必要があります
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
# イメージのビルド (時間がかかります)
docker buildx build --platform linux/arm64 -t ghcr.io/idein/custom-image-example-bookworm --load .
# bullseye向けイメージのビルド
docker buildx build --platform linux/arm/v7 -t ghcr.io/idein/custom-image-example-bullseye -f Dockerfile.bullseye --load .
```

### CA 対策と公開イメージの更新 (PBI-3365)

ベースは `bookworm-10` / `bullseye-4` を使います。Python と pip は
`/etc/ssl/certs/ca-certificates.crt` を使用します。bookworm の初回 pip 更新は
`--use-deprecated=legacy-certs` と `PIP_CERT` を併用し、ensurepip 同梱の古い
certifi を信頼に追加しません。bullseye の get-pip にも `--cert` を渡します。
更新先は修正済みcertifiを同梱する pip 26.2.2 以上とします。
更新後の pip は同梱 certifi も使うため、以下で両方のストアを確認します。

ビルド後、このディレクトリで外部通信なしのチェックを実行します。

```bash
docker run --rm --network none --platform linux/arm64 \
  -v "$PWD/tests:/tests:ro" --entrypoint python3 \
  ghcr.io/idein/custom-image-example-bookworm /tests/check-ca.py
docker run --rm --network none --platform linux/arm/v7 \
  -v "$PWD/tests:/tests:ro" --entrypoint python3 \
  ghcr.io/idein/custom-image-example-bullseye /tests/check-ca.py
```

対象ルート2個の除外、Amazon Root CA 1 の維持、クロス署名中間CA6個の拒否、
pip の CA 指定を確認します。通常の Actsim 起動も確認後、レジストリへログイン済みの
環境で両イメージを公開します。

```bash
docker push ghcr.io/idein/custom-image-example-bookworm:latest
docker push ghcr.io/idein/custom-image-example-bullseye:latest
```

このサンプルは `.actdk/dependencies.json` でカスタムイメージを明示しているため、
ActDK の標準ベースイメージ更新だけでは反映されません。利用端末で新イメージを
pull してから Act を再ビルドし、公開した digest と CA チェック結果を記録してください。
PR のマージだけでは、既存の公開イメージや Act は更新されません。

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
