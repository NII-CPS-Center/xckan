インストール手順
================

CKAN横断検索システムをインストールする手順を説明します。

バックエンドサーバのインストール
--------------------------------

GitHub からソースコード一式を clone します。 ::

  $ git clone git@github.com:InfoProto/ckan-xsearch.git
  $ cd ckan-xsearch
  $ pipenv --python 3.7
  $ pipenv shell
  $ pip install --upgrade pip pipenv setuptools wheel
  $ pipenv install --dev


Solr のインストール
-------------------

Apache Solr 公式サイトから最新版をダウンロード、インストールします。
その後、 port 8983 で Solr サーバを起動し、コレクション "ckan-xsearch" を
作成します。 ::

  $ curl -SL https://ftp.jaist.ac.jp/pub/apache/lucene/solr/8.9.0/solr-8.9.0.tgz | tar xfz -
  $ ./solr-8.9.0/bin/solr start -p 8983
  $ ./solr-8.9.0/bin/solr create -c ckan-xsearch -p 8983
  $ ./solr-8.9.0/bin/solr config -c ckan-xsearch -p 8983 \
    -action set-user-property \
    -property update.autoCreateFields \
    -value false

サーバが起動したら、コレクションのスキーマを更新します。
バックエンドサーバをインストールしたディレクトリ（
``xckan-schema.json`` ファイルがあるディレクトリ）で実行してください。 ::

  $ curl -X POST -H 'Content-type:application/json' \
    --data-binary @xckan-schema.json \
    http://localhost:8983/solr/ckan-xsearch/schema

バックエンドサーバの設定
------------------------

バックエンドサーバの設定ファイルを作成します。 ::

  $ cp django-backend/xckan/siteconf.py.dist django-backend/xckan/siteconf.py

この設定ファイルを編集してバックエンドの動作を指定します。
必要最低限の設定は以下の環境変数でも可能です。

- ``XCKAN_SOLR``

  Solr サーバのエンドポイント URL を指定します。指定しない場合、
  ``http://localhost:8983/solr/ckan-xsearch/`` です。
  Solr Cloud を利用していてエンドポイントが複数存在する場合は、
  ``http://localhost:8001/solr/ckan-xsearch/,http://localhost:8002/solr/ckan-xsearch/``
  のようにカンマで区切って列挙してください。

- ``XCKAN_LOGFILE``

  ログファイルを出力するパス。指定しない場合、 ``siteconf.py`` が
  配置されているディレクトリ下の ``logs/ckan.log`` です。

- ``XCKAN_CACHEDIR``

  横断検索対象のサイトから収集したメタデータを格納するディレクトリ。
  指定しない場合、 ``$HOME/cache/`` です。

- ``XCKAN_LOCKDIR``

  横断検索対象のサイトへのクローリングプロセスが
  重複実行しないようにロックするロックファイルを作るディレクトリ。
  指定しない場合は ``/tmp/`` を利用します。

  複数のバックエンドサーバを一台のサーバ上で走らせる場合、
  このディレクトリは全て同じにしてください。そうしない場合は
  同一ホストからの DOS アタックが行なわれていると判断され、
  検索対象のサイトからアクセスをブロックされる可能性があります。

- ``XCKAN_LOGDIR``

  クエリログを保存するディレクトリ。指定しない場合、
  ``$HOME/query_log/`` を利用します。

- ``XCKAN_ALLOWED_HOSTS``

  このバックエンドサーバにアクセス可能なホストのリストを指定します。
  無指定の場合は ``.localhost`` つまり同一サーバからしかアクセスできません。
  どこからでもアクセス可能にするには ``*`` を指定します。
  それ以外のホストからアクセス可能にするには、
  FQDN をカンマで区切って列挙してください。

  例： ``.localhost,.nii.ac.jp``

- ``XCKAN_DB_ENGINE``

  横断検索対象のサイトリストなどを管理するデータベースの
  エンジンを指定します。指定しない場合、
  ``django.db.backends.sqlite3`` を利用します。

  データベースの設定については以下のページを参考にしてください。
  https://docs.djangoproject.com/en/3.2/ref/settings/#databases

- ``XCKAN_DB_NAME``

  データベースの名を指定します。指定しない場合、
  ``django-backend/xckan.sqlite3`` を利用しますが、
  絶対パスで指定することを推奨します。
  Sqlite3 以外のエンジンを指定した場合は必ず指定してください。

- ``XCKAN_DB_USER``

  データベースに接続するユーザ名を指定します。
  Sqlite3 では無効です。

- ``XCKAN_DB_PASS``

  データベースに接続するパスワードを指定します。
  Sqlite3 では無効です。

- ``XCKAN_DB_HOST``

  データベースサーバのホスト名を指定します。
  Sqlite3 では無効です。

- ``XCKAN_DB_PORT``

  データベースサーバのポート番号を指定します。
  Sqlite3 では無効です。

Tips: ``pipenv`` を利用する場合は ``.env`` に設定を書いておくと
自動的に読み込まれます。

上記の設定が完了したら、データベースを初期化します。 ::

  $ python django-backend/manage.py makemigrations
  $ python django-backend/manage.py migrate

この状態で開発用バックエンドサーバを起動して確認することができます。 ::

  $ python django-backend/manage.py runserver '0.0.0.0:8000'

http://localhost:8000/ にアクセスするとトップ画面が表示されます。
エラーが出た場合には、メッセージに従って修正してください。

**管理者エラーメール通知の設定**

管理者にエラーをメールで通知したい場合、以下の環境変数も設定してください。

- ``ADMINS``

  管理者名とメールアドレスのリストを列挙したリストを JSON 形式で指定します。

  例：

      ADMINS=[["ckan-master","master@example.com"],["ckan-staff","staff@example.com"]]

- ``SERVER_EMAIL``

  メールサーバが受け付ける発信者メールアドレスを指定します。

  例：``xckan-error@search.ckan.jp``


バックエンドサーバの起動
------------------------

開発用サーバは同時複数アクセスに対応していないので、実運用の際には
gunicorn を利用します。

まず、静的ファイルを収集します。 ::

  $ python django-backend/manage.py collectstatic

途中で既存のファイルを上書きするかを yes/no で聞かれたら yes と答えます。

次に gunicorn サーバを実行します。 ::

  $ gunicorn --chdir=django-backend --bind=0.0.0.0:8000 conf.wsgi

終了するときはプロセスを停止してください。

管理ツール
----------

バックエンド管理ツールを利用します。
まず管理者アカウントを作成します。 ::

  $ python django-backend/manage.py createsuperuser

http://localhost:8000/admin/ にアクセスすると、管理者ログイン画面が
表示されます。


メタデータ更新（クローリング）
------------------------------

クローリングは cron などで一定時間ごとに以下のコマンドを起動してください。 ::

  $ python django-backend/manage.py runscript update

前回チェックしてから、サイトの設定で指定した時間が経過していない
サイトはスキップされますので、更新間隔は10分程度に設定しても
問題ありません。
