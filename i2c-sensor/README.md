# i2c-sensor

**※このサンプルアプリケーションは ActcastOS 3 に対応していません。こちらを参考にアプリケーションを実装する場合、[ActcastOS 3 Migration ガイド](https://actcast.io/docs/ja/ApplicationDevelopment/ForActcastOS3/) に従って Actcast OS 3 に対応させてください**

## 概要

ラズベリーパイに搭載されているI2C通信の仕組みを用いて、KSY社製のスマートリモコンHATと接続し、温湿度情報を取得するサンプルアプリです。


## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- KSY社より販売されているSmart Remote Control HAT 型番:KSPST000000002
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)

### HATセンサーの組付け
KSY Smart Remote Control HATに付属している取扱説明書に従い、Raspberry Pi本体にHATセンサーを装着してください。

## Actsim での動作確認

### 準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```

sshなどでRaspberry Piへログインを行い
```bash
$ i2cdetect -y 1
```
などのコマンドでHATが正常に装着されていることを確認してください。

### actdk run

`actdk run` により Actsim 上でアプリケーションの動作確認をすることができます。停止させるには `Ctrl + C` を押します。

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

センサー値取得に成功した場合は、以下のようなメッセージが表示されます。

```json
[{"KSY_SmartSensor": {"timestamp": 1234567890.0000000, "ambient": 7.4, "pressure": 1015.2629431569994, "temperature": 35.6, "humidity": 25.2, "invalid_sensors": []}}]
```
センサー値取得に失敗した場合は、以下のようなメッセージが表示されます。

```json
[{"invalid_sensors": "VEML7700"}]
[{"invalid_sensors": "SHT3x"}]
[{"invalid_sensors": "Omron2smpd02e"}]
[{"HAT_Error": "Errors were detected in all sensors. There might be no HAT sensor connected, or the 'Enable I2C' setting in the actcast writer's Advanced Settings might not be turned on."}]
[{"KSY_SmartSensor": {"timestamp": 1234567890.0000000, "ambient": -9999, "pressure": -9999, "temperature": -9999, "humidity": -9999, "invalid_sensors": ["VEML7700", "Omron2smpd02e", "SHT3x"]}}]
```

全てのセンサーでエラーが出ている際には、HATセンサーの接続を確認してください。

### 各項目値の説明
- invalid_sensors:値が正常に取得できない場合に該当のセンサー名を表示

- ambient:光量 センサー名:VEML7700

- humidity:湿度 センサー名:SHT3x

- temperature:気温　センサー名:SHT3x

- pressure:気圧　センサー名:Omron2smpd02e

- timestamp:UNIXタイムスタンプ JST(Tokyo)

## Actcast Agent での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

## actcast writerの設定

I2Cの機能を利用したアプリケーションactcast上で動作させる場合には、[actcastへデバイスを登録する](https://actcast.io/docs/ja/DeviceManagement/DeviceSetup/WriteImages/)際に、Advanced settingsの項目からConfigure I2Cの設定をオンにしておく必要があります。

![image_720](https://github.com/Idein/actcast-app-examples/assets/106148688/916b5acc-1c76-4839-8079-79dd6b5b9fb8)

### 設定項目

* `interval`: センサーから値を取得する間隔(秒)

### ライセンス
このソースコードは、KSYのGitHubにあるMITライセンスの下で公開されているコードをベースにセンサー値取得部分を改変・使用しています。このプロジェクトで使用されているKSY社製のスマートリモコンHATのコードは、MITライセンスに基づいて公開されており、当社はこのライセンスの条件に従ってこれを利用しています。

MITライセンスはオープンソースライセンスの一つであり、商用利用、改変、再配布が許可されていますが、ライセンス条文の全文を製品内または製品のドキュメント内に含める必要があります。このライセンスにより、私たちはKSY社のコードを改変し、またその一部を自社製品に組み込むことが可能になっています。

このアプリケーションの開発にあたり、元のコードやアイデアを提供してくれたKSY社及びコントリビューターの皆様に深く感謝申し上げます。また、このプロジェクトに関連する全てのソースコードはMITライセンスに則って使用されています。