# rpi-lgpio

**このサンプルアプリケーションは ActcastOS 4 に対応しています。**

## 概要

[`rpi-lgpio`](https://rpi-lgpio.readthedocs.io/) を使い、Raspberry Pi の GPIO に接続した LED を点滅させるサンプルアプリです。

`rpi-lgpio` は Linux の GPIO character device を利用し、`RPi.GPIO` と互換性のある API を提供します。このサンプルでも `from RPi import GPIO` として読み込みます。

## 前提

- [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- ActcastOS 4
- [actdk](https://actcast.io/docs/ja/ApplicationDevelopment/GettingStarted/)
- LED 1 個
- 330 Ω 程度の電流制限抵抗 1 個
- ブレッドボードとジャンパーワイヤー

## 配線

Raspberry Pi の電源を切ってから、次のように配線してください。LED を GPIO に直接接続せず、必ず電流制限抵抗を直列に入れてください。

| Raspberry Pi | 接続先 |
| --- | --- |
| GPIO17（物理ピン 11） | 抵抗を介して LED のアノード（長い端子） |
| GND（物理ピン 6） | LED のカソード（短い端子） |

GPIO ピンを設定で変更する場合、ピン番号には物理ピン番号ではなく BCM GPIO 番号を指定します。

## Actsim での動作確認

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ApplicationDevelopment/GettingStarted/TestInLocalDevice/)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```

このディレクトリで次のコマンドを実行します。

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

LED が設定した間隔で点滅し、GPIO の出力レベルが Act Log に出力されます。

```json
[{"gpio_pin": 17, "level": true}]
[{"gpio_pin": 17, "level": false}]
```

停止するには `Ctrl+C` を押します。停止時には GPIO17 を LOW に戻し、GPIO リソースを解放します。

## 設定項目

- `gpio_pin`: LED を接続する BCM GPIO 番号（デフォルト: `17`）
- `blink_interval`: GPIO の出力レベルを切り替える間隔（秒、デフォルト: `1.0`）

ローカルで試す場合は `act_settings.json` を編集します。Actcast にアップロードしたアプリでは Act の設定から変更できます。

## Actcast Agent での動作確認

1. [Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ApplicationDevelopment/GettingStarted/CreateProject/)します。
2. `.actdk/setting.json` の `app_server_id` を、作成したアプリケーションの ID に変更します。
3. [アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

## 注意事項

- `rpi-lgpio` と `RPi.GPIO`（パッケージ名 `rpi-gpio`）は、同じ `RPi.GPIO` モジュールを提供するため同一環境に共存できません。このサンプルでは `python3-rpi-lgpio` のみをインストールします。
- `rpi-lgpio` は GPIO ピンをプロセス単位で排他的に確保します。同じ GPIO ピンを使用する別のプロセスと同時には実行できません。
- Raspberry Pi 5 では GPIO ヘッダーが `/dev/gpiochip4`、それ以外の対応ボードでは `/dev/gpiochip0` として公開されるため、ボード別の manifesto を用意しています。
