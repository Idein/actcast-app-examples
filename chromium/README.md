# chromium + 日本語入力サンプル

## 概要
ActcastOS4上で動作する chromium と日本語入力のサンプルアプリです。

## 前提
このアプリは ActcastOS 4.20.0 & actdk 1.60.0 以上でないと動作しません。

## 実行

```
actdk run -a <your_device>
```

## 設定項目

- `keylayout`: `jp` か `us` が指定できます。使用するキーボードの配列にあったものを指定してください。
- `default_url`: chromium が起動したときに表示するWebページのURLを指定してください。
- `kiosk_mode`: chromium を kiosk mode で起動したい場合 true を指定してください。
