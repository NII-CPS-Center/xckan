"""
Create Google sitemap.

Usage:
python django-backend/manage.py runscript sitemap
python django-backend/manage.py runscript sitemap [--script-args [force] [ping]]

Options:
The "force" option forces a sitemap update.
The "ping" option notifies Google of sitemap updates.

Ref: https://www.sitemaps.org/protocol.html
"""
import datetime
import glob
import gzip
import logging
import os
import re
from typing import Optional, Union
import urllib.request

from sites.models import Site as AdminSite
from xckan.model.cache import CkanCache
from xckan.model.site import Site as XckanSite  # noqa: F401

logger = logging.getLogger(__name__)
cache = CkanCache()

xckan_dataset_url = os.environ.get(
    'XCKAN_DATASET_URL', 'https://search.ckan.jp/datasets/')
xckan_sitemap_url = os.environ.get(
    'XCKAN_SITEMAP_URL', 'https://harvest.ckan.jp/sitemaps/')


def get_page_url(dataset_id: str, dataset_url: Optional[str] = None):
    dataset_url = dataset_url or xckan_dataset_url
    if dataset_url[-1] != '/':
        dataset_url += '/'

    return dataset_url + dataset_id


def get_sitemap_dir() -> os.PathLike:
    """
    Get the directory path where the sitemap files are/will be placed.

    Note
    ----
    The default location is "sitemaps/" under the directory
    where this script is located.
    If you want to change it, specify it in the environment
    variable ``XCKAN_SITEMAP_DIR``
    """
    default_dir = os.path.join(
        os.path.dirname(__file__), "sitemaps")
    sitemap_dir = os.environ.get('XCKAN_SITEMAP_DIR', default_dir)
    os.makedirs(sitemap_dir, mode=0o755, exist_ok=True)
    return sitemap_dir


def get_sitemap_filename(
        site: XckanSite,
        suffix: Optional[int] = None) -> os.PathLike:
    if suffix is None:
        sitemap_basename = "sitemap_{}.xml.gz".format(site.get_site_id())
    else:
        sitemap_basename = "sitemap_{}_{}.xml.gz".format(
            site.get_site_id(), suffix)

    fullname = os.path.join(get_sitemap_dir(), sitemap_basename)
    return fullname


def get_sitemap_url_from_file(
        filename: Union[str, os.PathLike]) -> os.PathLike:
    basename = os.path.basename(filename)
    fullname = os.path.join(xckan_sitemap_url, basename)
    return fullname


def get_sitemapindex_filename() -> os.PathLike:
    fullname = os.path.join(get_sitemap_dir(), 'sitemap_index.xml')
    return fullname


def get_sitemap_files(site: XckanSite) -> list:
    sitemapfiles = glob.glob(
        get_sitemap_filename(site)[0:-7] + '_*.xml.gz')
    return sitemapfiles


def read_package_list_from_sitemap(site: XckanSite) -> dict:
    re_loc = re.compile(r'<loc>(.*)</loc>')
    re_lastmod = re.compile(r'<lastmod>(.*)</lastmod>')
    packages = {}
    for file in get_sitemap_files(site):
        buf = ""
        with gzip.open(file, mode="rt") as gzipf:
            for line in gzipf:
                buf += line
                if '</url>' in line:
                    m = re_loc.search(buf)
                    loc = os.path.basename(m.group(1))
                    m = re_lastmod.search(buf)
                    lastmod = m.group(1)
                    packages[loc] = lastmod
                    buf = ""

    return packages


def write_sitemap(site: XckanSite, force: bool = False) -> Optional[list]:
    """
    Write sitemap files.

    Parameters
    ----------
    site: xckan.model.site.Site
        The target site.
    force: bool
        If True is passed, update the sitemap forcefully.
        Also, the value of lastmod is the current datetime,
        not the datetime the metadata was updated.

    Returns
    -------
    List of str, or None
        List of sitemap filenames.
        If the sitemap is not updated, returns None/
    """
    last_packages = read_package_list_from_sitemap(site)
    recent_packages = {}
    updated = False
    now = datetime.datetime.now().isoformat(timespec='seconds') + 'Z'

    site_id = site.get_site_id()
    stored = cache.solr_manager.search(
        q="*:*", fl="id,xckan_last_updated", start=0, rows=999999,
        fq="id:{}*".format(site_id.replace(':', r'\:')))

    for solr_meta in stored:
        package_id = solr_meta['id']
        last_updated = now if force else solr_meta['xckan_last_updated']
        if package_id not in last_packages or \
                last_updated > last_packages[package_id]:
            updated = True
            # logger.debug("UP {}: {}".format(package_id, last_updated))
        else:
            pass
            # logger.debug("   {}: {}".format(package_id, last_updated))

        recent_packages[package_id] = last_updated

    if updated is False and force is False:
        return None

    # Remove old sitemap files of this site
    for file in get_sitemap_files(site):
        logger.debug("Unlink {}".format(file))
        os.unlink(file)

    sitemap_filenames = []
    n = 0
    pages = 1 + int(
        len(recent_packages) / 50000)  # Split file by 50,000 records
    package_ids = list(recent_packages.keys())
    for page in range(pages):
        sitemap_filename = get_sitemap_filename(site, suffix=page)
        sitemap_filenames.append(sitemap_filename)
        logger.debug("Writing {}".format(sitemap_filename))

        with gzip.open(sitemap_filename, 'wt') as gzipf:
            print((
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/'
                'schemas/sitemap/0.9">'),
                file=gzipf)

            for package_id in package_ids[page * 50000: page * 50000 + 50000]:
                last_updated = recent_packages[package_id]
                print(('  <url>\n    <loc>{}</loc>\n'
                       '    <lastmod>{}</lastmod>\n  </url>').format(
                    get_page_url(package_id),
                    last_updated),
                    file=gzipf)

            print('</urlset>', file=gzipf)

    return sitemap_filenames


def run(*args):
    force_update = False
    ping_request = False
    updated = False
    sitemap_files = []
    for arg in args:
        if arg == 'force':
            logger.info(
                "Forcefully update because 'force' option is specified.")
            force_update = True
        elif arg == 'ping':
            logger.info(
                "Send ping request to Google.")
            ping_request = True

    admin_sites = AdminSite.objects.filter(enable=True).all()
    for admin_site in admin_sites:
        xckan_site = admin_site.get_xckan_site()
        if force_update:
            logger.debug("Force update '{}'".format(xckan_site.get_name()))
            res = write_sitemap(xckan_site, force=True)
        else:
            logger.debug("Checking '{}'".format(xckan_site.get_name()))
            res = write_sitemap(xckan_site)

        if res is not None:
            logger.debug("'{}' is updated.".format(xckan_site.get_name()))
            updated = True
            sitemap_files += res

    if updated is False:
        logger.info("No site had been updated.")
        exit(0)

    sitemapindex_file = get_sitemapindex_filename()
    with open(sitemapindex_file, "w", encoding="utf-8") as f:
        print((
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<sitemapindex xmlns="http://www.sitemaps.org/'
            'schemas/sitemap/0.9">'),
            file=f)

        for sitemap_file in sitemap_files:
            url = get_sitemap_url_from_file(sitemap_file)
            print((
                '  <sitemap>\n    <loc>{}</loc>\n'
                '  </sitemap>').format(url),
                file=f)

        print('</sitemapindex>', file=f)

    if ping_request:
        # Send ping message to Google central
        sitemapindex_url = get_sitemap_url_from_file(
            sitemapindex_file)
        ping_url = "https://www.google.com/ping?sitemap={}".format(
            sitemapindex_url)
        req = urllib.request.Request(ping_url)
        with urllib.request.urlopen(req) as res:
            logger.debug("Google returns '{}'".format(res.read()))
