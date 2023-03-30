from logging import getLogger
import re

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from reversion.admin import VersionAdmin

from .models import Site
from xckan.model.cache import CkanCache

logger = getLogger(__name__)

"""
See the following url about django admin site.
https://docs.djangoproject.com/en/3.2/ref/contrib/admin/
"""


class SiteAdmin(VersionAdmin):

    list_display = [
        'title', 'dataset_url', 'enable',
        'update_interval',
        'full_update_interval',
        'result', 'executed_at',
        'full_result', 'full_executed_at'
    ]

    fields = [
        'title', 'dataset_url', 'ckanapi_url',
        'proxy_url', 'is_fq_available', 'enable',
        'update_start_datetime', 'update_interval',
        'update_time', 'executed_at', 'result',
        'full_update_start_datetime', 'full_update_interval',
        'full_update_time', 'full_executed_at', 'full_result',
        'tag_vocabulary', 'tag_default', 'publisher', 'publisher_url',
        'contact', 'contact_email', 'notify_contact_email',
    ]

    readonly_fields = [
        'is_fq_available',
        'update_time', 'executed_at', 'result',
        'full_update_time', 'full_executed_at', 'full_result',
    ]

    def save_model(self, request, obj, form, change):
        """
        When any fields are changed and saved,
        the next update time is also updated at the same time.

        When the site name is changed,
        all documents of the site in the Solr will be removed.
        """
        try:
            old_obj = self.model.objects.get(id=obj.id)
        except ObjectDoesNotExist:
            old_obj = None

        if change:
            # Reset the next update time
            obj.update_time = obj.next_update_time()
            obj.full_update_time = obj.next_fullupdate_time()

        if old_obj is not None and old_obj.title != obj.title:
            cache = CkanCache()
            cache.delete_site(obj.get_xckan_site())
            # Reset the next update times to update as soon as possible
            obj.update_time = obj.update_start_datetime
            obj.full_update_time = obj.full_update_start_datetime

        # Add '/' to the end of the URL if not already there
        if obj.dataset_url and obj.dataset_url[-1] != '/':
            obj.dataset_url += '/'

        if obj.ckanapi_url and obj.ckanapi_url[-1] != '/':
            obj.ckanapi_url += '/'

        if obj.proxy_url and obj.proxy_url[-1] != '/':
            obj.proxy_url += '/'

        # Reformat contolled vocabulary
        obj.tag_vocabulary = re.sub(r'[\s,\u3000]+', ',', obj.tag_vocabulary)

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """
        When deleting a site, delete the cache files and
        Solr index at the same time.
        """
        logger.debug("Deleting Site:{}".format(obj))
        cache = CkanCache()
        cache.delete_site(obj.get_xckan_site())
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Override "delete seelected objects" in admin list.
        """
        cache = CkanCache()
        for site in queryset:
            logger.debug("Deleting Site:{}".format(site))
            cache.delete_site(site.get_xckan_site())

        super().delete_queryset(request, queryset)

    def get_readonly_fields(self, request, obj=None):
        """
        Set 'dataset_url' field as
        - editable before save, but
        - readonly after save
        to prevent later changes.
        """
        if obj:
            return self.readonly_fields + ['dataset_url', ]

        return self.readonly_fields


admin.site.register(Site, SiteAdmin)
