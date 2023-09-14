# データカタログ横断検索システムデプロイ手順書

この手順書は Ubuntu18.04 以上を対象としています。

本システムは動的にタイトルやOGPを設定するために、サーバサイドレンダリング(SSR)を利用して運用を行うことを前提とします。

## Node.jsのインストール

* 最新版をインストールため、まず nodejs, npm を apt でインストールします

```
$ sudo apt install nodejs npm
```

* npmを利用してnをインストールします

```
$ sudo npm install -g n
```

* nを使って、nodejsとnpmをインストールします

```
$ sudo n stable
```

* 古いほうのnodejs, npmはアンインストールします
```
sudo apt purge nodejs npm
```

> ここで再度ログインしてください

* nodeのバージョンを確認します

```
$ node -v
```

## ソースコードのclone

* githubよりソースコードをcloneします

```
$ git clone https://github.com/thibetanus/sip2-ckan
```

* 環境依存の設定を行ないます

```
$ cd sip2-ckan/app/sip2-ckan/
$ cp dot_env.dist .env
$ vi .env
(ここで環境変数を設定します)
```

- 利用可能な環境変数（かっこ内はデフォルト値）

    - `SERVER_PORT` (3000)

        サーバが待ち受けるポート番号を指定します。

    - `SERVER_HOST` ('0.0.0.0')

        サーバが受け付けるホストを指定します。
        外部からのアクセスを許可するには '0.0.0.0' としてください。

    - `FRONTEND_WEB` ('https://search.ckan.jp/')

        サーバのトップページの URL を指定します。

    - `BACKEND_API` ('https://search.ckan.jp/backend/api')

        バックエンドの API エンドポイントを指定します。

    - `BACKEND_AUTH` (未指定)

        バックエンド API に認証が必要な場合、認証文字列を指定します。

    - `GOOGLE_GTAG` (未指定)

        Google Analystics 用の gtag をしています。

    - `API_LOG` (未指定)

        デバッグのため、バックエンド API への応答を
        ブラウザの console に表示したい場合は `1` を指定します。


* コンパイルします

設定を変更した場合も、 `npm run build` を実行する必要があります。
```
$ cd sip2-ckan/app/sip2-ckan/
$ npm install
$ npm run build
$ npm start
```

* サーバを起動します

```
$ npm start
```

## supervisorの導入

```
$ sudo apt-get install supervisor
```

* エディタを利用して以下の `/etc/supervisor/conf.d/ckan.conf` を以下の内容で作成します

```
[program:ckan]
command = npm run start
user = ubuntu
directory = {{your clone path}}/sip2-ckan/app/sip2-ckan/
autostart = true
autorestart = true
stdout_logfile = /var/supervisor/ckan.log
stderr_logfile = /var/supervisor/ckan-stderr.log
redirect_stderr = true
```

* supervisorの登録と起動を行ないます

```
$ sudo service supervisor start 
$ sudo supervisorctl restart all
```
