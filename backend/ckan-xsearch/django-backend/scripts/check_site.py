"""
Check CKAN type of sites.

Usage
python django-backend/manage.py runscript check_site [--script-args <keyword>...]

If '--script-args' option is specified,
only sites that contain all the specified keywords in their URLs
will be considered for harvesting.
"""
import logging

from sites.models import Site as AdminSite
from xckan.model.site import Site as XckanSite  # noqa: F401

logger = logging.getLogger(__name__)


def run(*args):
    # logging.basicConfig(level=logging.DEBUG)

    admin_sites = AdminSite.objects.filter(enable=True).all()
    for admin_site in admin_sites:
        xckan_site = admin_site.get_xckan_site()
        show_xckan_fields = False
        do_check = True
        for arg in args:
            if arg == 'show-fields':
                show_xckan_fields = True
            elif arg not in xckan_site.url_top:
                do_check = False
                break

        if not do_check:
            continue

        print("{}({}): {}".format(
            admin_site.title, admin_site.dataset_url,
            xckan_site.get_site_class()))

        if show_xckan_fields:
            for k, v in xckan_site.get_required_fields().items():
                print("  {}: {}".format(k, v))
