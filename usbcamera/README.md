# Usbcamera

※このサンプルアプリケーションはActcastOS 4にのみ対応しています

## 概要

V4LCameraCaptureを使用し、ActのFPSをAct Logに出力するサンプルアプリです。

## 前提

- 対象機種:
  - Raspberry Pi 3B
  - Raspberry Pi 3B+
  - Raspberry Pi 4B
  - Compute Module 4
  - Raspberry Pi 5B
- カメラ:
  - 任意のUSBカメラ

## 設定項目

- `display`: ディスプレイに表示するかどうかを指定します。
- `device`: 開く USB カメラのデバイスファイル (例: `/dev/video2`) を指定します。空のときは USB カメラを自動で探します。CSI カメラも接続されていると `/dev/video0` が CSI カメラになることがあるため、そのときはこの設定か自動の検出を使います。
