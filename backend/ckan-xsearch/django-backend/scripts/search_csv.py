"""
Search dataset from CKAN sites.

Usage:

python django-backend/manage.py runscript search_csv --script-args <keyword>...

Note:

A zip file containing the CSV of the search results
and the table of contents "toc.json" will be generated
in the current directory.
"""
import json
import logging
import os
import zipfile

from django.db.models import Q

from sites.models import Site
from sites.api import api
from xckan.model.cache import CkanCache

logger = logging.getLogger(__name__)


def run(*args):
    logging.basicConfig(level=logging.DEBUG)
    cache = CkanCache()
    query = None
    resource_filter = None

    if len(args) == 0:
        print("One or more script-args are required.")
        exit(-1)

    for arg in args:
        if arg[0:2] == 'q=':
            query = arg[2:]
        elif arg[0:3] == 'rf=':
            resource_filter = arg[3:]
        else:
            raise RuntimeError(
                "Invalid parameter '{}'".format(arg))

    if query is None:
        raise RuntimeError(
            "Query parameter 'q=<query>' is required.")

    datasets = api.package_search(q=query, rows=1000)

    toc = []
    for dataset in datasets['results']:
        package_id = dataset['xckan_id']
        site_id, package_id = package_id.split(':')
        dataset_url = site_id.replace('__', '/')
        adminsite = Site.objects.get(
            Q(dataset_url__contains=dataset_url))
        xckan_site = adminsite.get_xckan_site()

        # Count csv files
        resources = []
        for resource in dataset['resources']:
            resource_format = resource.get('format', '')
            if resource_format.lower() != 'csv':
                continue

            resources.append(resource)

        for resource in resources:
            resource_format = resource.get('format', '')
            if resource_format.lower() != 'csv':
                continue

            resource_path = cache.get_resource_file_path(
                xckan_site, package_id, resource)

            if resource_path is False or \
                    not os.path.exists(resource_path):
                continue

            resource_name = resource.get('name', '(noname)')
            if len(resources) > 1 and \
                    resource_filter and \
                    resource_filter not in resource_name:
                continue

            print("{}\t{}\t{}\t{}".format(
                xckan_site.get_name(),
                dataset['xckan_title'],
                resource_name,
                resource_path))

            toc.append([
                len(toc) + 1,
                xckan_site.get_name(),
                dataset['xckan_title'],
                resource_name,
                resource_path])

    zipfname = "{}.zip".format('-'.join(args))
    with zipfile.ZipFile(zipfname, 'w') as zipf:
        zipf.writestr('toc.json',
                      json.dumps(
                          toc, indent=2, ensure_ascii=False))

        for args in toc:
            name = "res_{:03d}.csv".format(args[0])
            with open(args[4], 'rb') as fb:
                content = fb.read()

            zipf.writestr(name, content)
