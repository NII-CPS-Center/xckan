"""
"""
from typing import Optional
import datetime
import glob
import json
import os
import random
import re
import sys

from xckan.model.metadata import Metadata
from xckan.siteconf import site_config


def get_catalog_list() -> list:
    catalog_list = os.path.join(
        os.path.dirname(__file__),
        'catalog_list.txt')

    if os.path.exists(catalog_list):
        with open(catalog_list, 'r') as f:
            files = []
            for line in f:
                line = line.rstrip()
                files.append(line)

        return files

    cmd = 'find {} -type f -name catalog.json'.format(
        site_config.CACHEDIR)
    stream = os.popen(cmd)
    files = []
    with open(catalog_list, 'w') as f:
        for line in stream:
            line = line.rstrip()
            print(line, file=f)
            files.append(line)

    return files


def random_sampling(func, n: int = 500):
    files = get_catalog_list()
    nfiles = len(files)
    for i in range(0, n):
        r = random.randint(0, nfiles - 1)
        with open(files[r], 'r') as f:
            content = json.load(f)
            func(files[i], content['result'])


def check_all(func, limit: Optional[int] = None):
    files = get_catalog_list()
    nfiles = len(files)
    if limit is None:
        limit = nfiles

    for i in range(0, limit):
        with open(files[i], 'r') as f:
            content = json.load(f)
            func(files[i], content['result'])


def check_specified(func, path):
    with open(path, 'r') as f:
        content = json.load(f)
        func(path, content['result'])


def check_metadata(path: str, json_metadata: dict):
    m = Metadata.get_instance(json_metadata)
    if isinstance(json_metadata, list):
        # MikawaMetadata
        json_metadata = json_metadata[0]
        
    original_desc = (json_metadata.get('notes') or '') \
        + (json_metadata.get('text') or '')
    # original_desc = re.sub(r'[\r\n\t \u3000]+', ' ', original_desc)
    generated_desc = m.get_description()
    if '【リソース】' in generated_desc:
        generated_desc = generated_desc[
            :generated_desc.index('【リソース】')]

    if len(generated_desc) < len(original_desc):
        print("=== {}\n{}\n---\n{}\n===\n".format(
            path, original_desc, generated_desc))


if __name__ == '__main__':
    random.seed(datetime.datetime.now().microsecond)

    if len(sys.argv) > 1:
        check_specified(check_metadata, sys.argv[1])

    else:
        # random_sampling(check_metadata, 1000)
        check_all(check_metadata)
