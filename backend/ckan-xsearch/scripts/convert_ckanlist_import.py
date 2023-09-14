import json
import re
import sys


def update_record(old_format):
    """
    旧 ckanlist.json フォーマットのレコードを
    新インポート機能用のフォーマットのレコードに変換する。

    example
    -------
    old_format = '''{
    "url": "https://www.data.go.jp/data/dataset/",
    "name": "DATA GO JP データカタログサイト",
    "proxy": "http://search.ckan.jp/backend/api/"
    }'''
    >>> print(json.dumps(
    ...   update_record(old_format),
    ...   indent=4, ensure_ascii=False))
    {
        "title": "DATA GO JP データカタログサイト",
        "dataset_url": "https://www.data.go.jp/data/dataset/",
        "ckanapi_url": "https://www.data.go.jp/data/api/3/action/",
        "proxy_url": "http://search.ckan.jp/backend/api/",
        "is_fq_available": false,
        "update_start_datetime": "2020-01-01T00:00:00Z",
        "update_interval": "P1D",
        "result": false,
        "update_time": null,
        "executed_at": null,
        "full_update_start_datetime": null,
        "full_update_interval": null,
        "full_result": false,
        "full_update_time": null,
        "full_executed_at": null,
        "contact": null,
        "publisher": null,
        "publisher_url": null,
        "enable": true,
        "memo": ""
    }
    """

    # Import data fields
    title = old_format.get('name', '<no name>')
    dataset_url = old_format.get('url')
    ckanapi_url = old_format.get('api')
    proxy_url = old_format.get('proxy_url')

    # Validate and auto completion
    site_enable = True
    assert(dataset_url is not None)
    if dataset_url[-1] != '/':
        dataset_url += '/'

    if dataset_url[0] == '!':
        dataset_url = dataset_url[1:].lstrip()
        site_enable = False

    if ckanapi_url and ckanapi_url[-1] != '/':
        ckanapi_url += '/'

    if ckanapi_url is None:
        ckanapi_url = re.sub(
            r'/dataset/',
            '/api/3/action/',
            dataset_url)

    if ckanapi_url[0] == '!':
        ckanapi_url = ckanapi_url[1:].lstrip()
        site_enable = False

    new_format = {
        "title": title,
        "dataset_url": dataset_url,
        "ckanapi_url": ckanapi_url,
        "proxy_url": proxy_url,
        "is_fq_available": False,
        "update_start_datetime": "2099-01-01T00:00:00Z",
        "update_interval": "P1D",
        "result": False,
        "update_time": None,
        "executed_at": None,
        "full_update_start_datetime": None,
        "full_update_interval": None,
        "full_result": False,
        "full_update_time": None,
        "full_executed_at": None,
        "contact": None,
        "publisher": None,
        "publisher_url": None,
        "enable": site_enable,
        "memo": ""
    }

    return new_format


if __name__ == '__main__':
    argv = sys.argv

    if len(argv) < 2:
        print("Usage: {} <ckanlist.json path>".format(
            argv[0]))
        exit(-1)

    with open(argv[1], 'r', encoding='utf-8') as f:
        ckanlist = json.load(f)

    results = []
    for record in ckanlist:
        results.append(update_record(record))

    print(json.dumps(
        results, indent=4, ensure_ascii=False))
