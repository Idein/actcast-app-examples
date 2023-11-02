# ImageNet Classification for ai cast

## 概要

ai cast 上で動く ImageNet Classification のサンプルアプリです。
このアプリは通常の Raspberry Pi 用アプリと違い、[Hailo-8](https://hailo.ai/products/ai-accelerators/hailo-8-m2-ai-acceleration-module/) を用いて AI 処理を行います。

## 前提

- 対象機種: [ai cast](https://www.idein.jp/ja/news/230208-aicast-release)
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)

## ビルド方法

```bash
make
```

これにより `src/resnet_v1_18.c` が ai cast 用にクロスコンパイルされて `app/libresnet_v1_18.so` が生成されます。
`src/resnet_v1_18.c` は HEF ファイルを扱うための C のプログラムで、コンパイルされた `app/libresnet_v1_18.so` は Python プログラム(`app/model.py`)から利用されます。

## Actsim での動作確認

### 準備

actdk に[確認用 ai cast を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

```bash
actdk remote add <IDENTIFIER_YOU_LIKE>@<REMOTE>
```

### actdk run

`actdk run` により Actsim 上でアプリケーションの動作確認をすることができます。停止させるには `Ctrl + C` を押します。

```bash
actdk run -a <IDENTIFIER_YOU_LIKE>
```

## Actcast Agent での動作確認

まず[Actcast に新規アプリケーションを作成](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/CreateProject/)します。

`.actdk/setting.json` の `app_server_id` を、先程作成したアプリケーションの ID に変更します。

[アプリケーションをアップロードし、実機にインストール](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestViaActcast/)します。

### 設定項目

* `display`: HDMIディスプレイへ撮影画像と分類結果top-10の描画を行う。
* `camera rotation`: 撮影画像を回転する (0 or 90 or -90 or 180)。ただし、カメラが回転に対応している必要がある。もし対応していなければ。本設定は無視される。
* `horizontal flip camera`: 撮影画像を左右反転する。ただし、カメラが回転に対応している必要がある。もし対応していなければ。本設定は無視される。
* `target class IDs`: `1,30,2,52,999`のようなカンマ区切りの対象クラスID(空は全クラス指定を意味する)。この一覧に含まれているクラスのみがActcastへの通知対象となる。
    * 例: `954,673` は "banana" と "mouse" を通知対象とする設定
* `probability threshold`: 確度がこの閾値を越えたら通知を行う。
* `crop or resize`: 撮影画像を必要なサイズへリサイズする際の方法
    * `crop` モードでは、撮影画像中心から必要なサイズ分を切り抜く
      ![cropモード画像](https://actcast-app-readme-static.s3-ap-northeast-1.amazonaws.com/common/resizing_method/resizing_method-crop.svg?versionId=11frKZkF.1KGGzYBJWhg4TdqeUTEIw0i "cropモード")
    * `resize` モードでは、撮影画像中心から必要なサイズと同一アスペクトの最大サイズを切り抜いた後に必要なサイズへ縮小を行う。
      ![resizeモード画像](https://actcast-app-readme-static.s3-ap-northeast-1.amazonaws.com/common/resizing_method/resizing_method-resize.svg?versionId=YxE5ZC5YHJOeEY2D8l2ospJhDArrKo2y "resizeモード")


## 補足説明

`root.tar` は Hailo-8 を扱うのに必要なツールチェインが同梱されています。
