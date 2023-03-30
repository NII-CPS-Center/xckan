# カタログ横断検索システム（Docker版）

2023-02-28 sagara@info-proto.com

## このパッケージについて

このパッケージは、カタログ横断検索システムのフロントエンド、
バックエンドおよび Solr を Docker 上で動作させるために必要な
ファイル一式をまとめたものです。

Docker が実行可能な環境を別途用意してください。
Windows および MacOS の Docker Desktop 4.6.1,
Ubuntu の Docker version 20.10.18 で動作確認済みです。

## 使い方

- サービス起動

    次のコマンドでサービスを起動します。バックグラウンドで動かすので
    `-d` を付けてください。

        % docker compose up -d

    Ubuntu で実行する場合、 docker の設定によっては
    root 権限が必要な場合があります。その場合は sudo 権限を持つ
    アカウントで `docker compose` の前に `sudo` を付けてください。

        % sudo docker compose up -d

    以下の説明では単に `docker compose` と表記します。

- 検索画面（フロントエンド）

    ブラウザで `http://localhost:23000/` を開いてください。
    Docker サービスを動かしているマシン以外からアクセスしたい場合は
    設定を変更する必要があります。「設定」セクションの
    「フロントエンドの初期設定」を参照してください。

    画面上部の「データセットを検索」と表示されている欄に
    キーワードを入力し、虫眼鏡のアイコンをクリックすると
    データセットを検索することができます。

    最初はメタデータが登録されていないため、
    「0件のデータが見つかりました」という表示になります。

- サイト管理画面（バックエンド）

    ブラウザで `http://localhost:25000/` を開いてください。
    Docker サービスを動かしているマシン以外からアクセスしたい場合は
    設定を変更する必要があります。「設定」セクションの
    「バックエンド環境変数」を参照してください。

    右上隅の "ログイン" リンクをクリックし、バックエンド管理者アカウントの
    ユーザ名とパスワードを入力します。デフォルト設定のままならば
    ユーザ名もパスワードも `xckan-docker` です。

    ログインできたら、トップメニューの "CKANサイト一覧" リンクを
    クリックしてください。ここに登録済みのサイト一覧が表示されます。
    最初は「(サイトが登録されていません)」と表示されるはずです。

    左上隅の "インポート" ボタンを押し、 `backend`
    ディレクトリにある `xckan_sitelist.json` ファイルを
    アップロードすると、サイトを一括登録できます。

    個別に登録したい場合は、右上の "管理サイト" リンクから
    「Django 管理サイト」に移動してください。ここでサイトや
    ユーザの登録や編集を行なうことができます。

    インポートしたサイトは念のため更新不可の状態になっています。
    一覧から任意のサイトを選択し、"検査" ボタンを押してください。
    そのサイトがアクセス可能であれば、更新可能に設定されます。
    
    更新開始日時や更新間隔を変更したい場合は "管理" ボタンから
    Django 管理サイトに移動できます。

- サイトメタデータの更新（任意の時点で）

    サイトを登録し、更新可能に設定したら、メタデータを収集して
    インデックスを更新します。以下のコマンドを実行してください。

        % docker compose exec backend python manage.py runscript update

    CKANサイトにアタックをかけられていると誤解されないように、
    メタデータの取得は1秒に1件に制限していますので、時間がかかります。
    
    定期的に更新するには、 cron などで一定時間ごとにこのコマンドを
    実行する必要があります。

- サービスの停止

    次のコマンドで、バックグラウンドで動いているサービスを停止します。

        % docker compose down

- サービスの再起動

    一度停止したサービスを再起動する場合は以下のコマンドを
    実行してください。収集したメタデータはコンテナ外のボリューム
    `backend_volume` と `solr_volume` に保存されているため、
    これらのボリュームを削除しなければサービスの停止・再起動を
    行なっても失われません。

        % docker compose up -d

- 収集したメタデータの削除

    何らかの理由で収集したメタデータを削除したい場合、
    `backend_volume` と `solr_volume` を削除してから再起動してください。

        % docker compose down -v
        % docker compose up -d

基本的な使い方は以上です。

## 設定

設定は全て `docker-compose.yml` ファイルで管理しています。

一部の項目はこのファイルを書き換えず、環境変数を設定することで
設定を変更することができます。

- Solr サービスのポート : services.solr.ports

    デバッグ等の目的で利用できるよう、 Solr コンテナのポート 8983 を
    28983 でパブリッシュしています。このポートにブラウザで外部から
    アクセスすると、 Solr 管理ツールにアクセスできます。
    Solr 管理ツールの使い方については、公式サイトの
    [Overview of the Solr Admin UI](https://solr.apache.org/guide/8_11/overview-of-the-solr-admin-ui.html) を参照してください。

    もし既にサーバ上で 28983 を利用する他のサービスが
    動いていて利用できない場合、他の空いているポートに変更してください。
    Solr には backend サービスがアクセスしますが、Docker の
    仮想ネットワークを利用するため、変更しても影響ありません。

    セキュリティ等の理由で Solr にアクセスされたくない場合は
    ports 項目をコメントアウトしても構いません。

    変更した場合、サービスを停止し、再起動してください。
    イメージを作り直す必要はありません。

        % docker compose down
        % docker compose up -d

- バックエンドサービスのポート : services.backend.ports

    バックエンドの管理用サービスと API を提供するポート 5000 を
    25000 でパブリッシュしています。このポートにブラウザで外部から
    アクセスすると、収集する CKAN サイトを登録したり変更するための
    管理画面にアクセスできます。

    また、このサービスはフロントエンドが利用する API も提供します。
    そのためこの値を変更した場合は、「フロントエンドの初期設定」の
    `BACKEND_API` も変更し、手順に従ってフロントエンドをビルド
    し直す必要があります。

- バックエンドの初期設定 : services.backend.args

    バックエンドのイメージ作成時に参照する以下の環境変数を設定します。
    
    - `DJANGO_SUPERUSER_USERNAME` : 管理者のユーザ名
    - `DJANGO_SUPERUSER_PASSWORD` : 管理者のパスワード
    - `DJANGO_SUPERUSER_EMAIL` : 管理者のメールアドレス（未使用）

    これらの値は最初にコンテナを作成するときに参照され、
    `backend_volume` 上に作成されるデータベースに保存されます。
    そのためこれらの値を変更してコンテナを再起動しても
    管理者のユーザ名やパスワードは変わりません。

    `backend_volume` を削除してからサービスを再起動すれば
    変更が反映されますが、登録したサイトリストなども失われます。

    もしパスワードを忘れた等の理由で、管理者パスワードを
    変更したいという場合は、次のコマンドを利用してください。

        % docker compose exec backend python manage.py \
        changepassword xckan-docker

- バックエンド環境変数 : services.backend.environment
    
    バックエンドの実行時に参照する以下の環境変数を設定します。
    
    - `XCKAN_ALLOWED_HOSTS` : バックエンドサーバにアクセス可能なホスト

    Docker が動いているマシン (localhost) 以外からも
    アクセス可能にしたい場合は、次の手順で値を変更してから
    サービスを再起動してください。

        % export XCKAN_ALLOWED_HOSTS=*
        % docker compose down
        % docker compose up -d

    カタログ更新時に担当者のメールアドレスに結果通知メールを
    送信したい場合には、以下の環境変数も必要です。

    - XCKAN_SYSTEM_NAME : 通知メールに記載するシステム名
    - XCKAN_SYSTEM_FROM : 通知メールの送信元メールアドレス
    - SMTP_HOST : 通知メールを送信する SMTP サーバホスト名
    - SMTP_PORT : SMPT ポート番号
    - SMTP_USER : SMTP サーバに認証が必要な場合のユーザ名
    - SMTP_PASS : SMTP サーバに認証が必要な場合のパスワード

- フロントエンドサービスのポート : services.frontend.ports

    フロントエンドの検索用画面を提供するポート 3000 を
    23000 でパブリッシュしています。このポートにブラウザで外部から
    アクセスすると、カタログ横断検索の検索画面が開きます。

    もし既に Docker サービス上で 23000 を利用する他のサービスが
    動いていて利用できない場合、他の空いているポートに変更してください。

    変更した場合、サービスを停止し、再起動してください。
    イメージを作り直す必要はありません。

- フロントエンドの初期設定 : services.frontend.build.args

    フロントエンドのイメージ作成時に参照する以下の環境変数を設定します。

    - `SERVER_HOST` : フロントエンドにアクセスできるホスト
    - `BACKEND_API` : バックエンドの API エンドポイント
    - `API_LOG` : フロントエンドのデバッグ用ログ出力スイッチ

    これらの値はイメージを作成するときに参照されます。
    そのため値を変更してから再起動してもサービスの挙動は変更できません。
    変更したい場合、環境変数を変更してからイメージを作り直してください。

    Docker サービスが動いているマシン以外からもフロントエンド経由で
    検索を行ないたい場合、バックエンドに外部からもアクセスできるよう
    設定を変更し（「バックエンド環境変数」を参照）、
    `BACKEND_API` をそのサーバの API エンドポイントに変更します。
    その後、 frontend のイメージを作り直してサービスを再起動します。

        % export XCKAN_ALLOWED_HOSTS=*
        % export BACKEND_API=http://mydocker.server.name:25000/api
        % docker compose down
        % docker compose build frontend
        % docker compose up -d

- `.env` ファイルの利用

    環境変数を毎回設定する代わりに、この README.md ファイルと同じ
    ディレクトリに `.env` ファイルを作成し、環境変数を定義しておくと
    docker compose コマンドを実行するときに自動的に読み込みます。

        (.env の例)
        # Frontend settings
        BACKEND_API=http://xckan-dev:25000/api

        # Backend settings
        XCKAN_ALLOWED_HOSTS=*
        DJANGO_SUPERUSER_USERNAME=xckan
        DJANGO_SUPERUSER_PASSWORD=xckan

        # Mail (SMTP) server settings
        XCKAN_SYSTEM_NAME=xckan docker running on xckan-dev
        XCKAN_SYSTEM_FROM=noreply@xckan.docker
        SMTP_HOST=mysmtp.example.com
        SMTP_PORT=465
        SMTP_USER=smtpuser@mysmtp.example.com
        SMTP_PASS=ThisIsMySMTPAuthPassword00


## 補足情報

- 出力ファイル

    本システム実行中に発生したエラーや、更新時のログは
    `backend_volume` の中の `xckan.log` ファイルに保存されます。
    確認したい場合は次のコマンドを実行してください。

        % docker compose exec backend tail /ext/xckan.log

    検索ログは同じボリュームの `query_log/` ディレクトリ内に生成されます。

    ログの出力レベルやフォーマットを変更したい場合は、設定ファイル
    `backend/ckan-xsearch/django-backend/xckan/logging.json` を編集して
    backend コンテナを再起動してください。

    サイトから収集したメタデータは `backend_volume` の
    `cache/` ディレクトリに保存されています。


- 横断検索システム API

    横断検索システムの API は以下の URL でアクセスできます。

    - List metadata: 登録済みメタデータの ID リストを返します

        http://&gt;server&lt;:25000/api/package_list

    - Show metadata: 指定した ID を持つメタデータの詳細を返します

        http://localhost:25000/api/package_show?id=&lt;id&gt;

    - Search metadata: 条件に合致するメタデータのリストを返します

        http://localhost:25000/api/package_search?q=%E6%96%B0%E5%9E%8B%E3%82%B3%E3%83%AD%E3%83%8A&start=0&rows=50&sort=score+desc

    Docker サービスが動いているマシン以外からAPIにアクセスしたい場合は、
    「設定」セクションの「バックエンド環境変数」を参照し、
    バックエンドに外部からアクセスできるように設定を変更してください。
