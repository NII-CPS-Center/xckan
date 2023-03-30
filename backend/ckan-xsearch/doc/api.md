横断検索システム API リファレンス
=================================

> 2022-02-22 <sagara@info-proto.com>

API 一覧
--------

横断検索システム API には以下の3つの機能が実装されています。

- `package_list`
        
    登録されているカタログのリスト（IDのみ）を取得します

- `package_show`

    指定したカタログのメタデータを取得します

- `package_search`

    キーワード等の条件でカタログを検索します

CKAN では初期のバージョンでの慣例に従い、データセットを `package`
と呼んでいます。横断検索システムではデータセットを
カタログと呼びますが、 API では CKAN API に合わせて `package`
という名称を利用しています。

`package_list`
--------------

登録されているカタログの一覧を取得します。

**リクエストURL**

`(endpoint)/package_list`

**リクエストパラメータ**

- rows (int, optional)

    取得する最大件数を指定します。 省略された場合は全件返します。

- start (int, optional)

    取得を開始する位置を指定します。
    省略された場合は0件目から返します。

- fq (str, optional)

    *フィルタクエリ* を指定します。 省略された場合は `*:*`
    (全てのフィールドの全ての値) を 利用します。

**レスポンス**

以下の情報を含む JSON を返します。

- help

    呼びだした URL など、リクエストに関する情報

- success

    成功した場合は `true`, 失敗した場合は `false`

- result

    *カタログID* のリスト

**例**

登録されているカタログID一覧を10件取得します。 jq
はJSONを見やすく表示するためのコマンドで必須ではありません。

```
$ curl -X GET https://search.ckan.jp/backend/api/package_list?rows=10 | jq .
{
  "help": "https://harvest.ckan.jp:8000/api/package_list?rows=10",
  "success": true,
  "result": [
    "www.pref.ehime.jp__opendata-catalog__dataset:cb9bfc49-007c-493d-b371-4983c1f1bad2",
    "www.pref.ehime.jp__opendata-catalog__dataset:6c60d302-02c5-484c-a4ec-2712c8d6e923",
    "www.pref.ehime.jp__opendata-catalog__dataset:86e929f3-73e3-487d-aa67-fcf62b195afa",
    "yamaguchi-opendata.jp__ckan__dataset:00003",
    "www.pref.ehime.jp__opendata-catalog__dataset:6652c3d7-7544-40b5-b929-a447feebec57",
    "www.pref.ehime.jp__opendata-catalog__dataset:a069f66e-0100-415a-95b5-a52a22a64d37",
    "yamaguchi-opendata.jp__ckan__dataset:352021_budget",
    "data.bodik.jp__dataset:450006_716",
    "ckan.open-governmentdata.org__dataset:401000_kennaikeizai_201503",
    "od.city.otsu.lg.jp__dataset:p_31199_31199"
  ]
}
```

サイト名が「愛媛県オープンデータ」であるサイトから取得した
カタログID一覧を取得します。

```
$ curl -X GET 'https://search.ckan.jp/b=xckan_site_name:愛媛県オープンデータ' | jq .
{
  "help": "https://harvest.ckan.jp:8000/api/package_list?fq=xckan_site_name:%C3%A6%C2%84%C2%9B%C3%A5%C2%AA%C2%9B%C3%A7%C2%9C%C2%8C%C3%A3%C2%82%C2%AA%C3%A3%C2%83%C2%BC%C3%A3%C2%83%C2%97%C3%A3%C2%83%C2%B3%C3%A3%C2%83%C2%87%C3%A3%C2%83%C2%BC%C3%A3%C2%82%C2%BF",
  "success": true,
  "result": [
    "www.pref.ehime.jp__opendata-catalog__dataset:cb9bfc49-007c-493d-b371-4983c1f1bad2",
    "www.pref.ehime.jp__opendata-catalog__dataset:6c60d302-02c5-484c-a4ec-2712c8d6e923",
    ...
    "www.pref.ehime.jp__opendata-catalog__dataset:10dd8a19-354a-4831-836f-d9a70d20c723",
    "www.pref.ehime.jp__opendata-catalog__dataset:a05107b1-ae60-4abe-bbbd-9cee16ed494d",
    "www.pref.ehime.jp__opendata-catalog__dataset:f430008d-b920-464f-bade-b846d086aefe"
  ]
}
```

サイト名に「東京都\*」（\*はワイルドカード）を含むサイトから取得した
メタデータのうち、最後に更新された日時が "2022-0101T00:00:00Z" から
"2022-02-01T00:00:00Z" の間であるカタログのID一覧を取得します。

```
$ curl 'https://search.ckan.jp/backend/api/package_list?fq=xckan_last_updated:[2022-01-01T00:00:00Z%20TO%202022-02-01T00:00:00Z]%20AND%20xckan_site_name:東京都*' --globoff | jq .
{
  "help": "https://harvest.ckan.jp:8000/api/package_list?fq=xckan_last_updated:[2022-01-01T00:00:00Z%20TO%202022-02-01T00:00:00Z]%20AND%20xckan_site_name:%C3%A6%C2%9D%C2%B1%C3%A4%C2%BA%C2%AC%C3%A9%C2%83%C2%BD*",
  "success": true,
  "result": [
    "catalog.data.metro.tokyo.lg.jp__dataset:t000019d1800000024",
    "catalog.data.metro.tokyo.lg.jp__dataset:t000019d1800000023",
    "catalog.data.metro.tokyo.lg.jp__dataset:t000019d1800000022",
    "catalog.data.metro.tokyo.lg.jp__dataset:t000019d1800000021",
    "catalog.data.metro.tokyo.lg.jp__dataset:t000019d1800000020",
    ...
    "catalog.data.metro.tokyo.lg.jp__dataset:t132098d0000000061",
    "catalog.data.metro.tokyo.lg.jp__dataset:t000019d1700000024",
    "catalog.data.metro.tokyo.lg.jp__dataset:t132292d0000000006"
  ]
}
```

**注意事項**

カタログIDの順序は登録順であり、並べ替えはできません。

`package_show`
--------------

カタログIDで指定したメタデータを取得します。

**リクエストURL**

`(endpoint)/package_show`

**リクエストパラメータ**

- id (str): カタログID 必須です。

**レスポンス**

以下の情報を含む JSON を返します。

- help

    呼びだした URL など、リクエストに関する情報

- success

    成功した場合は `true`, 失敗した場合は `false`

- result

    指定したカタログのメタデータ

    元のサイトが提供するメタデータ（JSON）のフォーマットのままですが、
    横断検索システムが利用する `xckan_*`
    フィールドが追加されています。

    追加されたフィールドの詳細は用語の *フィールドクエリ* を
    参照してください。

**例**

ID が `catalog.data.metro.tokyo.lg.jp__dataset:t132292d0000000006`
であるカタログのメタデータを取得します。

```
$ curl 'https://search.ckan.jp/backend/api/package_show?id=catalog.data.metro.tokyo.lg.jp__dataset:t132292d0000000006' | jq .
{
  "help": "https://harvest.ckan.jp:8000/api/package_show?id=catalog.data.metro.tokyo.lg.jp__dataset:t132292d0000000006",
  "success": true,
  "result": {
    "xckan_id": "catalog.data.metro.tokyo.lg.jp__dataset:t132292d0000000006",
    "xckan_title": "年齢別人口",
    "xckan_site_name": "東京都オープンデータカタログサイト",
    "xckan_site_url": "https://catalog.data.metro.tokyo.lg.jp/dataset/t132292d0000000006",
    "xckan_last_updated": "2022-01-20T00:17:01Z",
    "license_title": "クリエイティブ・コモンズ 表示（CC BY）",
    "maintainer": "西東京市企画部情報推進課",
    "relationships_as_object": [],
    "private": false,
    "maintainer_email": null,
    ...
    "license_url": "https://creativecommons.org/licenses/by/4.0/deed.ja",
    "title": "年齢別人口",
    "revision_id": "7688adfe-2636-40f6-8e1e-d409ae5a6db5"
  }
}
```

**注意事項**

カタログIDは完全一致のみです。 `package_show`
では一度に複数のメタデータを取得することはできません。

`package_search`
----------------

条件を指定してカタログを検索し、メタデータのリストを取得します。

**リクエストURL**

`(endpoint)/package_search`

**リクエストパラメータ**

- q (str)

    *検索クエリ* を指定します。この項目は必須です。

    指定した文字列を単語分割し、より多くの単語をメタデータに含む
    カタログを検索します。

    検索対象となるフィールドは、`author`, `groups`, `license`,
    `maintainer`, `name`, `notes`, `organization`,
    `res_description`, `res_name`, `tags`, `text`, `title`,
    `extras_*`, `res_extras_*`, `vocab_*` ですが、横断検索側の
    チューニングによって変更される可能性があります。

    単語を分割されたくない場合は `q="男女別人口"` のように
    ダブルクォートで指定してください。

- rows (int, optional)

    取得する最大件数を指定します。 省略された場合は10件返します。

- start (int, optional)

    取得を開始する位置を指定します。
    省略された場合は0件目から返します。

- sort (str, optional)

    結果のソート順を指定します。 省略された場合は `score desc`
    (スコア降順) になります。

- fq (str, optional)

    *フィルタクエリ* を指定します。 省略された場合は \"*:*\"
    (全てのフィールドの全ての値) を 利用します。

**レスポンス**

以下の情報を含む JSON を返します。

- help

    呼びだした URL など、リクエストに関する情報

- success

    成功した場合は `true`, 失敗した場合は `false`

- result

    以下の情報を含む検索結果（JSON）

    - q

        解析したクエリ情報

    - count

        ヒットした総件数

    - facets

        件数内訳をサイトごと（`xckan_site_name`）、
        組織ごと（`organization`）、
        リソースフォーマットごと（`res_format`）、
        キーワードごと（`tags`）、グループごと（`groups`）に
        集計した件数

        Solr の書式に従い、値と件数が交互に並ぶリスト形式です。

    - qtime

        検索に要した時間（ms）

    - results

        カタログのメタデータのリスト。

        個々の内容は `package_show` が返す結果と同じです。

**例**

サイト名に「愛媛県\*」（\*はワイルドカード）を含むサイトから、
「男女別人口」に関連するカタログを検索します。
クエリは単語集合「男女」「別」「人口」に分解され、
より多く含むものから優先で、1つでも含むものを返します
（この例では284件）。

```
$ curl 'https://search.ckan.jp/backend/api/package_search?q=男女 別人口&fq=xckan_site_name:愛媛県*' | jq .
{
  "help": "https://harvest.ckan.jp:8000/api/package_search?q=%C3%A7%C2%94%C2%B7%C3%A5%C2%A5%C2%B3%C3%A5%C2%88%C2%A5%C3%A4%C2%BA%C2%BA%C3%A5%C2%8F%C2%A3&fq=xckan_site_name:%C3%A6%C2%84%C2%9B%C3%A5%C2%AA%C2%9B%C3%A7%C2%9C%C2%8C*",
  "success": true,
  "result": {
    "q": {
      "q": [
        "男女別人口"
      ],
      "fq": [
        "xckan_site_name:愛媛県*"
      ]
    },
    "count": 284,
    "facets": {
      "facet_queries": {},
      "facet_fields": {
        "xckan_site_name": [
          "愛媛県オープンデータ",
          284,
          "BODIK ODCS",
          0,
...
```

サイト名に「愛媛県\*」（\*はワイルドカード）を含むサイトから、
「男女別人口」を含むカタログを検索します。
ダブルクォートで囲むことによりクエリは単語に分割されないため、
厳密に一致するカタログだけがヒットします（この例では11件）。 :

```
$ curl 'https://search.ckan.jp/backend/api/package_search?q="男女 別人口"&fq=xckan_site_name:愛媛県*' | jq .
{
  "help": "https://harvest.ckan.jp:8000/api/package_search?q=%22%C3%A7%C2%94%C2%B7%C3%A5%C2%A5%C2%B3%C3%A5%C2%88%C2%A5%C3%A4%C2%BA%C2%BA%C3%A5%C2%8F%C2%A3%22&fq=xckan_site_name:%C3%A6%C2%84%C2%9B%C3%A5%C2%AA%C2%9B%C3%A7%C2%9C%C2%8C*",
  "success": true,
  "result": {
    "q": {
      "q": [
        "\"男女別人口\""
      ],
      "fq": [
        "xckan_site_name:愛媛県*"
      ]
    },
    "count": 11,
    "facets": {
      "facet_queries": {},
      "facet_fields": {
        "xckan_site_name": [
          "愛媛県オープンデータ",
          11,
          "BODIK ODCS",
          0,
...
```

用語
----

**カタログID**

横断検索システムに登録されているCKANサイトから収集した
データセットを、グローバルに識別するために付与したID。
CKANサイトのデータセット一覧を表示するURLと、そのサイト内の
データセットIDを組み合わせて作成しています。

**検索クエリ**

メタデータをテキストインデックスにより検索します。
横断検索システムでは検索クエリを Solr にそのまま渡しているため、
詳細な文法については、Solr のリファレンスを参照してください。

<https://solr.apache.org/guide/8_11/the-standard-query-parser.html#standard-query-parser-response>

ただし `q.op`, `df`, `sow` には対応していません。 Standard Query Parser
以外のクエリパーザは選択できません。

**フィルタクエリ**

メタデータを検索する条件を指定し、その条件に一致する
カタログを高速に絞り込みます。横断検索システムでは フィルタクエリを Solr
にそのまま渡しているため、 詳細は Solr
のリファレンスを参照してください。

<https://solr.apache.org/guide/8_11/common-query-parameters.html#fq-filter-query-parameter>

横断検索システムでは CKAN 以外のシステムからもメタデータを
収集しているため、フィールド名はサイトによって異なる場合が
あります。横断検索システムが保証するフィールドは以下の5つです。

-   `xckan_original_id` : 元のサイトでのデータセットID
-   `xckan_title` : データセットのタイトル
-   `xckan_site_name` : サイト名（横断検索システムで定義しています）
-   `xckan_site_url` : このメタデータの情報を表示するウェブサイトのURL
-   `xckan_last_updated` : このメタデータの最終更新日時

fqで日時を指定する場合、Solrの制約により末尾は 'Z' 以外は
受け付けません（"+09" などもエラーになります）。

複数の条件を指定する場合、Solr では `fq=...&fq=...` のように
書けますが、横断検索では fq パラメータは一つしか受け付けないため
上の例のように `AND` で接続して一つのクエリにしてください。

更新履歴
--------

2022-02-22: 初版作成
