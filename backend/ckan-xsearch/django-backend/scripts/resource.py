"""
Harvest resource files from CKAN sites.

Usage
python django-backend/manage.py runscript resource [--script-args <keyword>...]

If '--script-args' option is specified,
only sites that contain all the specified keywords in their URLs
will be considered for harvesting.
"""
import json
import logging

from sites.models import Site as AdminSite
from xckan.model.cache import CkanCache
from xckan.model.site import Site as XckanSite

logger = logging.getLogger(__name__)


def harvest_resource(site: XckanSite):
    formats = ['pdf', 'csv', 'xls', 'xlsx']
    cache = CkanCache()
    stats = cache.get_resources_from_site(site, formats)
    stats['site'] = site.get_name()
    print("STATS ------")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


def run(*args):
    # logging.basicConfig(level=logging.DEBUG)

    admin_sites = AdminSite.objects.filter(enable=True).all()
    for admin_site in admin_sites:
        xckan_site = admin_site.get_xckan_site()
        do_harvest = True
        for arg in args:
            if arg not in xckan_site.url_top:
                do_harvest = False
                break

        if do_harvest:
            harvest_resource(xckan_site)
        else:
            logger.debug("Skip {}({})".format(
                admin_site.title, xckan_site.url_top))
