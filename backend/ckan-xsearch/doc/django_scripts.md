# Django スクリプト

実装済みの Django script の使い方を説明します。

Django script は Solr とサイトデータベースに直接アクセスするため、
バックエンドサーバが起動していない場合でも実行できます。

スクリプトは `django-backend/scripts/*.py` にあります。

# `check_site.py`

登録ずみ CKAN サイトが応答するかどうかチェックし、
応答する場合はサイトのシステムの情報を返します。

```
$ python django-backend/manage.py runscript check_site
DATA GO JP データカタログサイト(https://www.data.go.jp/data/dataset/): CkanMetadata
青い森オープンデータカタログ(https://opendata.pref.aomori.lg.jp/dataset/): ShirasagiMetadata
東京都オープンデータカタログサイト(https://catalog.data.metro.tokyo.lg.jp/dataset/): CkanMetadata
静岡県オープンデータ(https://opendata.pref.shizuoka.jp/dataset/): ShirasagiMetadata
鳥取県オープンデータ(https://odp-pref-tottori.tori-info.co.jp/dataset/): ShirasagiMetadata
町田市オープンデータカタログサイト(http://opendata.city.machida.tokyo.jp/dataset/): CkanMetadata
東三河オープンデータ(https://opendata-east-mikawa.jp/search/type/dataset/): MikawaMetadata
```

オプションパラメータを指定すると、指定された文字列をサイト URL に
含むサイトだけを表示します。

```
$ python django-backend/manage.py runscript check_site --script-args shizuoka.jp
静岡県オープンデータ(https://opendata.pref.shizuoka.jp/dataset/): ShirasagiMetadata
```

オプションパラメータ `show-fields` を指定すると、サンプルメタデータを
解析し、`xckan_*` フィールドを表示します。

```
$ python django-backend/manage.py runscript check_site --script-args shizuoka.jp show-fields
静岡県オープンデータ(https://opendata.pref.shizuoka.jp/dataset/): ShirasagiMetadata
  xckan_id: opendata.pref.shizuoka.jp__dataset:91331960-0597-4531-aa8b-12e5dcf8cb7b
  xckan_title: 農産物直売所
  xckan_site_name: ふじのくにオープンデータカタログ
  xckan_site_url: https://opendata.pref.shizuoka.jp/dataset/6282.html
  xckan_last_updated: 2018-05-31T00:00:00Z
  xckan_original_id: 91331960-0597-4531-aa8b-12e5dcf8cb7b
  xckan_description: 市内のファーマーズマーケット開催情報です。データ形式 lodでも公開しています。http://data.odp.jig.jp/rdf/jp/shizuoka/shimada/661.rdf【リソース】FarmersMarket.csv
```

# `sitemap.py`

Google 用の sitemap を作成します。

```
$ python django-backend/manage.py runscript sitemap
13:00:19 INFO No entry is updated.
```

作成したサイトマップファイルは `django-backend/scripts/sitemaps/`
に出力されます。

```
$ ls django-backend/scripts/sitemaps/
sitemap_catalog.data.metro.tokyo.lg.jp__dataset.xml.gz
sitemap_index.xml
sitemap_odp-pref-tottori.tori-info.co.jp__dataset.xml.gz
sitemap_opendata-east-mikawa.jp__search__type__dataset.xml.gz
sitemap_opendata.city.machida.tokyo.jp__dataset.xml.gz
sitemap_opendata.pref.aomori.lg.jp__dataset.xml.gz
sitemap_opendata.pref.shizuoka.jp__dataset.xml.gz
sitemap_www.data.go.jp__data__dataset.xml.gz
```

# `update.py`

メタデータの更新処理を行ないます。

実際に更新されるかどうかは、サイトごとに設定された
更新間隔と、前回更新日時によって決まります。

```
$ python django-backend/manage.py runscript update
13:24:23 INFO DATA GO JP データカタログサイト: Next update at 2022-03-05T05:00:00+00:00 -> Skip
13:24:23 INFO 青い森オープンデータカタログ: Next update at 2022-03-05T05:00:00+00:00 -> Skip
13:24:23 INFO 東京都オープンデータカタログサイト: Next update at 2099-01-01T00:00:00+00:00 -> Skip
13:24:23 INFO 静岡県オープンデータ: Next update at 2022-03-05T05:00:00+00:00 -> Skip
13:24:23 INFO 鳥取県オープンデータ: Next update at 2099-01-01T00:00:00+00:00 -> Skip
13:24:23 INFO 町田市オープンデータカタログサイト: Next update at 2022-03-06T00:00:00+00:00 -> Skip
13:24:23 INFO 東三河オープンデータ: Next update at 2099-01-01T00:00:00+00:00 -> Skip
13:24:23 INFO DATA GO JP データカタログサイト: Next full update at 2022-04-01T15:00:00+00:00 -> Skip
13:24:23 INFO 青い森オープンデータカタログ: Next full update at 2022-04-01T15:00:00+00:00 -> Skip
13:24:23 INFO 静岡県オープンデータ: Next full update at 2022-03-26T15:00:00+00:00 -> Skip
13:24:23 INFO 町田市オープンデータカタログサイト: Next full update at 2022-04-02T04:00:00+00:00 -> Skip
13:24:23 INFO Update (differencial) done.
13:24:23 INFO Update (full) done.
```

オプションパラメータを指定すると、指定された文字列をサイト URL 
またはサイト名に含むサイトだけを更新します。

```
$ python django-backend/manage.py runscript update --script-args shizuoka.jp
$ python django-backend/manage.py runscript update --script-args shizuoka.jp
13:24:56 INFO 静岡県オープンデータ: Next update at 2022-03-05T05:00:00+00:00 -> Skip
13:24:56 INFO 静岡県オープンデータ: Next full update at 2022-03-26T15:00:00+00:00 -> Skip
13:24:56 INFO Update (differencial) done.
13:24:56 INFO Update (full) done.
```

オプションパラメータ `force` を指定すると、スケジュールされた
更新時刻より前であっても更新処理を実行します。

```
$ python django-backend/manage.py runscript update --script-args shizuoka.jp force
13:25:51 INFO 静岡県オープンデータ: Next full update at 2022-03-26T15:00:00+00:00 -> Skip
13:25:52 INFO [opendata.pref.shizuoka.jp__dataset] Starting update
13:25:52 DEBUG [opendata.pref.shizuoka.jp__dataset] Locking for updating
13:25:52 DEBUG [opendata.pref.shizuoka.jp__dataset] Locking for updating
13:25:52 DEBUG [opendata.pref.shizuoka.jp__dataset] Last updated = list:2022-03-05 13:02:35, update:2022-03-05 13:02:28
13:25:52 DEBUG [opendata.pref.shizuoka.jp__dataset] Last updated = list:2022-03-05 13:02:35, update:2022-03-05 13:02:28
13:25:52 DEBUG [opendata.pref.shizuoka.jp__dataset] Last updated 1397.0529131889343 seconds before.
13:25:52 DEBUG [opendata.pref.shizuoka.jp__dataset] Last updated 1397.0529131889343 seconds before.
...
13:26:01 DEBUG [opendata.pref.shizuoka.jp__dataset] Unlocked
13:26:01 DEBUG [opendata.pref.shizuoka.jp__dataset] Unlocked
13:26:01 INFO [opendata.pref.shizuoka.jp__dataset] Update done
13:26:01 INFO Update (differencial) done.
13:26:01 INFO Update (full) done.
```

オプションパラメータ `force-full` を指定すると、
Solr に登録されているメタデータを一度削除し、
CKAN サイトまたはキャッシュされているメタデータファイルから
Solr 用メタデータを作成しなおし、 Solr に登録します。

```
$ python django-backend/manage.py runscript update --script-args shizuoka.jp force-full
...
```
