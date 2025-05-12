# Libcamera

※このサンプルアプリケーションはActcastOS 4にのみ対応しています

## 概要

LibcameraCaptureを使用し、ActのFPSをAct Logに出力するサンプルアプリです。

## 前提

- 対象機種:
  - Raspberry Pi 4B
  - Compute Module 4
  - Raspberry Pi 5B
- カメラ:
  - Raspberry Piカメラモジュール

## 設定項目

- `display`: ディスプレイに表示するかどうかを指定します。
- `libcamera_log_levels`: [Environment variables &mdash; libcamera](https://www.libcamera.org/environment_variables.html#list-of-variables) の `LIBCAMERA_LOG_LEVELS` に対応した値を指定します。
- `hflip`: 水平反転を指定します。デフォルトは `false` です。
- `vflip`: 垂直反転を指定します。デフォルトは `false` です。
- `framerate`: フレームレートを指定します。デフォルトは 30 fps です。
