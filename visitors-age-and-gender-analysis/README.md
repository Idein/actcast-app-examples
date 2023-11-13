# Visitors' Age and Gender Analysis

## 概要

検出ラインを跨いだ人の年齢や性別を判定するサンプルアプリです。

![Screen Capture Image](https://actcast-app-readme-static.s3-ap-northeast-1.amazonaws.com/visitors-attrs/screen_capture.png?versionId=SD2nSikJo8AHcPlrCWT779HSI7bWuLFZ "Screen Capture")

## 前提

- 対象機種: [Actcast がサポートする Raspberry Pi](https://actcast.io/docs/ja/SupportedDevices/RaspberryPi/)
- [actdk](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/ActDK/)
- [Docker](https://www.docker.com/)

## ビルド方法

```bash
make 
```

make により、以下のファイルが生成されます。

- `include/model.h`
- `app/libmodel.so` 
- `app/model.py`
- `app/libbilinear.so`

## Actsim での動作確認

### 準備

actdk に[確認用 Raspberry Pi を登録](https://actcast.io/docs/ja/ForVendor/ApplicationDevelopment/GettingStarted/TestInLocalDevice/#%e7%a2%ba%e8%aa%8d%e7%94%a8-raspberry-pi-%e3%81%ae%e7%99%bb%e9%8c%b2)します。

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

このアプリケーションには多くの設定項目がありますが、初回使用時には変更する必要はありません。

* `[Capture]` カテゴリ  
    * `capture scale`: キャプチャ画像のサイズ。キャプチャサイズを決定する次の式で使用される (320 \* `capture scale`) x (240 \* `capture scale`)  
    例) `capture scale`が4の場合、1280x960@10fps以上で画像をキャプチャしようとします。接続されたカメラに十分な能力がない場合、エラーで終了します。エラー発生時はデバイスログにActSettingsErrorとして記録されます。
    * `exposure time`: カメラの露出時間。（0で自動設定）カメラが対応していない場合この設定項目は無視されます。
    * `horizontal flip camera`: カメラが対応している場合は画像を反転して撮影します。 対応していない場合この設定項目は無視されます。
    * `camera rotation`: カメラが対応している場合はカメラを回転させて撮影します。 (0, 180 のどれか) 対応していない場合この設定項目は無視されます。
    * `capture framerate`: カメラのフレームレートを設定します。接続されたカメラに十分な能力がない場合、エラーで終了します。エラー発生時はデバイスログにActSettingsErrorとして記録されます。
* `[Crop]`カテゴリ  
このカテゴリ以下の設定は高度なオプションです。
通常の使用では、デフォルト値を変更する必要はありません。
   * `detection area ratio`: キャプチャ画像に対する検知領域vの割合（0.0 ~ 1.0の間、0.1は10%を意味します)。  
      顔検知を行う前に、キャプチャ画像から `detection area ratio` で設定された割合で画像を切り出し、「Detection Area(検知領域)」を作成します。  
      詳しくは下の画像を参照してください。  
      注意：`detection area ratio` と `detection area offset ratio` の組み合わせによっては「Detection Area」が320x240よりも小さくなり、検出精度が悪くなることがあります。
   * `detection area offset ratio`: 「Detection Area」のオフセット（0.0 ~ 1.0の間）。  
      詳しくは下の画像を参照してください。  
    
   ![](https://actcast-app-readme-static.s3-ap-northeast-1.amazonaws.com/visitors-attrs/detection_area_ratio.svg?versionId=MttstheydDlL6enkPEmnMVB2DiJQuc9w)

* `resizing method`: キャプチャ画像を必要なサイズへリサイズする際の方法。
    Note：以下のリサイズを通さない生のキャプチャ画像に対して「Detection Area」を指定することができます。(`detection_area_margin` を参照)
    * `crop` モードでは、撮影画像中心から必要なサイズ分を切り抜きます。
      ![cropモード画像](https://actcast-app-readme-static.s3-ap-northeast-1.amazonaws.com/common/resizing_method/resizing_method-crop.svg?versionId=11frKZkF.1KGGzYBJWhg4TdqeUTEIw0i "cropモード")
    * `resize` モードでは、撮影画像中心から必要なサイズと同一アスペクトの最大サイズを切り抜いた後に必要なサイズへ縮小を行います。
      ![resizeモード画像](https://actcast-app-readme-static.s3-ap-northeast-1.amazonaws.com/common/resizing_method/resizing_method-resize.svg?versionId=YxE5ZC5YHJOeEY2D8l2ospJhDArrKo2y "resizeモード")
    * `padding` モードでは、撮影画像を必要なサイズと同一アスペクトになるようにパディングした後に必要なサイズへ縮小を行います。
      ![paddingモード画像](https://actcast-app-readme-static.s3-ap-northeast-1.amazonaws.com/common/resizing_method/resizing_method-padding.svg?versionId=g4pIvKs9QAiz7p2W_AE.k8T1qK6.wb0T "paddingモード")
    * `resize(maximum)`
      1. カメラで使用可能な最大解像度を選択し、選択した解像度に適切なフレームレート（>=15fpsの制限は無視）で撮影します。
      2. 撮影した画像のサイズを `resize` と同じように変更します。
    * `padding(maximum)`
      1. カメラで使用可能な最大解像度を選択し、選択した解像度に適切なフレームレート（>=15fpsの制限は無視）で撮影します。
      2. 撮影した画像のサイズを `padding` と同じように変更します。

* `[Area]` カテゴリ
    * `notification direction` : この設定項目は `entrance line` の向きと、どのような場合に Act Log を送信するかを設定します。
       * `top_to_bottom`: `entrance line` は水平方向に描画され、`face line` が `entrance line` を上から下に通過した場合に Act Log を送信します。（推奨設定）
       * `left_to_right`: `entrance line` は垂直方向に描画され、`face line` が `entrance line` を左から右に通過した場合に Act Log を送信します。
       * `right_to_left`: `entrance line` は垂直方向に描画され、`face line` が `entrance line` を右から左に通過した場合に Act Log を送信します。
    * `entrance line`: 検出ラインの位置 (0.0 ~ 2.0で表される比率)。   
      本アプリは`entrance line`を通過した`face line`をAct Log 送信対象としています。以下の図も併せてご確認ください。
    * `limit ratio of Detection Area`: 指定された範囲内の顔を検出対象としません。領域は比率で指定します。
       * `notification direction` が `top_to_bottom` の場合、顔検出範囲を `xmin,xmax` の形式で指定することができます。
       * `notification direction` が `left_to_right` もしくは `right_to_left` の場合、顔検出範囲を `ymin,ymax`の形式で指定することができます。
      各値は 0.0 から 1.0 までの数値でなければなりません。以下の図も併せてご確認ください。

      ![area items horizontal](https://actcast.io/usercontent/a48abe91-2f07-4cd9-8418-03069ffc2da4.svg)
      
      ![area items vertical](https://actcast.io/usercontent/b1de5048-2cc1-4bfc-865a-f78886d620be.svg)

* `[Face]` カテゴリ
    * `detection area margin`: 顔検出領域のマージン。  
      「Detection Area」の端で見切れた顔画像が検出されるのを防ぐためのパラメータです。  
      このパラメータは「Detection Area」の端からの距離を「Detection Area」に対する比率で表し、指定された範囲にある顔は検出対象としません。

    * `face line`: 訪問者を検出するための「face line(顔検出基準線)」の位置(0.0 ~ 2.0で表される)。  
      この値が1.0の場合、バウンディングボックスの中央を`face line`と見なします。  
      本アプリは `face line` が  `entrance line` を通過した場合に Act Log を送信します。
      本アプリが `face line` を描画する向きは、`notification direction` によって変わります。以下の説明も併せてご確認ください。
      
      ![Faceline horizontal](https://actcast.io/usercontent/bb9d8ab1-e393-4910-82e3-6c43c2a28d9d.svg)
      `notification direction` が `top_to_bottom` の場合、`face line` は水平方向に描画されます。
      `face line` の値が0.0の場合、バウンディングボックスの上辺に`face line`が描画されます。`face line` の値が2.0の場合、バウンディングボックスの下辺に`face line`が描画されます。

      ![Faceline vertical](https://actcast.io/usercontent/0e111222-6ba3-4f5a-8c0d-323c569262cc.svg)
      `notification direction` が `left_to_right` もしくは `right_to_left` の場合、`face line` は垂直方向に描画されます。
      `face line` の値が0.0の場合、バウンディングボックスの左辺に`face line`が描画されます。`face line` の値が2.0の場合、バウンディングボックスの右辺に`face line`が描画されます。
      
    * `probability threshold`: 確度の閾値 (0.0 ~ 1.0の間)。 検出された顔の確度がこの閾値を越えた場合にデータがActcastに送信される。
    * `gender classification threshold`: 男性/女性の2値分類の閾値(-1.0 ~ 1.0の間)。`gender_score` が閾値を超えている場合、その顔は女性として分類されます。
    * `Image Brightness Correction`: 撮影した画像を明るくする処理を加えるかどうか。
    * `exclude age`: 設定された年齢以下の結果を除外する。
* `[Display]` カテゴリ
    * `display`: アプリケーションの動作を確認するために HDMIディスプレイへ表示させるかどうか。
