# published-port

**※このサンプルアプリケーションは ActcastOS 3 に対応していません。こちらを参考にアプリケーションを実装する場合、[ActcastOS 3 Migration ガイド](https://actcast.io/docs/ja/ApplicationDevelopment/ForActcastOS3/) に従って Actcast OS 3 に対応させてください**

## 概要

外部からの通信を待ち受けるアプリです。
アプリのマニフェストの `published_ports` フィールドを利用することでアプリをサーバーにすることができます。

この例ではアプリ内で HTTP サーバーを起動し 8080 番ポートで待ち受けています。
デバイスに対して HTTP GET リクエストを投げると `{"message": "Hello, World!"}` という JSON を返します。

