# Local Video Server

**このアプリケーションは ActcastOS 3、4 に対応しています。**

## 概要

カメラの映像を、デバイスと同じネットワークに接続したブラウザから確認できます。
Local Video Server（LVS）は、actfw-core 2.10.0で導入された機能です。

このアプリのAWB設定は、actfw-core 2.23.0で追加された
LibcameraCaptureのホワイトバランス指定機能を使用します。
LVSとAWB指定機能は、導入されたバージョンが異なります。
AWBの変更には、ActcastOS 4とCSIカメラが必要です。

## 設定と映像の確認

1. Actcast Web UIで対象のAct設定を開き、設定を変更して保存します。
2. アプリを再起動して設定を反映します。
3. デバイスと同じネットワークのブラウザで
   `http://<device_local_ip>:5100`を開き、映像を確認します。

`<device_local_ip>`は、デバイスのIPアドレスに置き換えてください。
[デバイスのmDNS](https://actcast.io/docs/ja/DeviceManagement/DeviceInfo/#mdns)を
有効にしていれば、`http://<hostname>.local:5100`でもアクセスできます。
このページは映像確認用です。AWBを含む設定の変更はActcast Web UIで行います。
起動後は自動調整が落ち着くまで、映像を数秒待って確認してください。

## Act設定

| 設定 | 既定値 | 内容 |
| --- | --- | --- |
| `display` | `false` | `true`にすると、HDMIディスプレイに映像とFPSを表示します |
| `use_usb_camera` | `false` | CSIカメラを使います。USBカメラを使う場合は`true`にします |
| `local_video_server` | `true` | ブラウザへの映像配信を有効にします |
| `quality` | `75` | LVSのJPEG画質。0〜100で指定し、高いほど画質とデータ量が増えます |
| `awb_mode` | `auto` | 下表からホワイトバランスの方式を選択します |
| `awb_gain_r` | `1.6` | Manualの赤の固定ゲイン、またはGreyWorldの赤の初期ゲインです |
| `awb_gain_b` | `1.6` | Manualの青の固定ゲイン、またはGreyWorldの青の初期ゲインです |
| `awb_k` | `0.45` | GreyWorldの補正の強さです。0より大きく1以下で、小さいほど緩やかに調整します |

## ホワイトバランス（AWB）

通常は既定の`auto`を使用してください。照明や撮影対象に応じて、
`awb_mode`を変更できます。

| `awb_mode` | 動作 |
| --- | --- |
| `auto` | カメラの自動AWB。設定を省略した場合もこの動作です |
| `greyworld` | 撮影画像のRGBから赤・青のゲインを継続的に調整します |
| `manual` | 自動AWBを無効にし、赤・青のゲインを固定します |
| `incandescent` | 白熱灯向けの自動AWB |
| `tungsten` | タングステン照明向けの自動AWB |
| `fluorescent` | 蛍光灯向けの自動AWB |
| `indoor` | 室内照明向けの自動AWB |
| `daylight` | 昼光向けの自動AWB |
| `cloudy` | 曇天向けの自動AWB |
| `custom` | カメラ側のカスタムAWB。対応する環境で使用してください |

### 設定例

- **GreyWorld**：`awb_mode`を`greyworld`にします。最初は赤・青の初期ゲインを
  それぞれ`1.6`、`awb_k`を`0.45`にして確認してください。
- **Manual**：`awb_mode`を`manual`にし、`awb_gain_r`と`awb_gain_b`を調整します。
  `awb_k`は使用しません。
- **照明プリセット**：例えば室内照明では`awb_mode`を`indoor`にします。
  ゲインと`awb_k`は使用しません。

### 利用時の注意

照明プリセットも自動調整です。対応するモードや調整範囲は、カメラとその設定に依存します。
Manualのゲインは正の有限値かつカメラの対応範囲内、GreyWorldの初期ゲインは
0.5〜8.0を指定してください。GreyWorldは、単色が画像の大部分を占める場合に
色かぶりが生じることがあります。

ActcastOS 3とUSBカメラでは`auto`を使用してください。
それ以外を指定すると、アプリは起動時にエラーになります。

古いactfw-coreなどでAWB指定機能に対応していない場合は、アプリのログに警告を出し、
指定したAWB設定を適用せずに従来のカメラ設定で動作します。
