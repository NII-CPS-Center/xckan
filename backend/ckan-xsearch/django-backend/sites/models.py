from datetime import timedelta
import re

import aniso8601
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db import models

from xckan.model.site import Site as XckanSite


def validate_interval(value):
    try:
        aniso8601.parse_duration(value)
    except ValueError:
        raise ValidationError(
            "ISO 8601 duration format (PnYnMnDTnHnMnS) で指定してください。")


class Site(models.Model):
    title = models.CharField(
        max_length=255, db_index=True, verbose_name="サイト名")
    dataset_url = models.URLField(verbose_name="データセットURL",
                                  unique=True)
    ckanapi_url = models.URLField(verbose_name="API URL")
    proxy_url = models.URLField(null=True, blank=True,
                                verbose_name="Proxy URL")
    is_fq_available = models.BooleanField(
        default=True, null=False, verbose_name="差分更新可")
    update_start_datetime = models.DateTimeField(
        null=True, blank=True, verbose_name="更新開始日時")
    update_interval = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="更新間隔",
        validators=[validate_interval])
    result = models.CharField(
        max_length=255, default='', verbose_name="前回更新結果")
    update_time = models.DateTimeField(
        null=True, blank=True, verbose_name="更新実行予定日時")
    executed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="前回更新実行日時")

    full_update_start_datetime = models.DateTimeField(
        null=True, blank=True, verbose_name="完全更新開始日時")
    full_update_interval = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="完全更新間隔",
        validators=[validate_interval])
    full_result = models.CharField(
        max_length=255, default='', verbose_name="前回完全更新結果")
    full_update_time = models.DateTimeField(
        null=True, blank=True, verbose_name="完全更新実行予定日時")
    full_executed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="前回完全更新実行日時")

    contact = models.CharField(max_length=255, null=True, blank=True,
                               verbose_name="連絡先")
    contact_email = models.EmailField(
        null=True, blank=True, verbose_name="連絡先メール")
    notify_contact_email = models.BooleanField(
        default=True, null=False, verbose_name="連絡先へのメール通知")
    publisher = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="発行者")
    publisher_url = models.URLField(
        null=True, blank=True, verbose_name="発行者URL")
    enable = models.BooleanField(
        default=True, null=False, verbose_name="更新実行可")
    memo = models.TextField(blank=True, verbose_name="メモ")

    tag_vocabulary = models.TextField(
        null=True, blank=True, verbose_name="タグ用統制語彙")
    tag_default = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="デフォルトタグ")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """
        Required method to use `django UpdateView`
        """
        return reverse('site-detail', kwargs={'pk': self.pk})

    def next_update_time(self):
        """
        Re-calculate the next update time from the last executed time
        and the interval.

        Return
        ------
        Datetime, None
        """
        if self.update_start_datetime is None or \
                self.update_interval is None:
            return None

        if self.executed_at is None:
            return self.update_start_datetime

        last_executed_at = self.executed_at

        interval = aniso8601.parse_duration(self.update_interval)
        if interval <= timedelta(seconds=0) or \
                last_executed_at < self.update_start_datetime:
            next_update_time = self.update_start_datetime
        else:
            count = int((last_executed_at - self.update_start_datetime)
                        / interval)
            next_update_time = self.update_start_datetime\
                + interval * (count + 1)

        return next_update_time

    def next_fullupdate_time(self):
        """
        Re-calculate the next full-update time from the last executed
        time and the interval.

        Return
        ------
        Datetime, None
        """
        if self.full_update_start_datetime is None or \
                self.full_update_interval is None:
            return None

        if self.full_executed_at is None:
            return self.full_update_start_datetime

        last_executed_at = self.full_executed_at

        interval = aniso8601.parse_duration(self.full_update_interval)

        count = int(
            (last_executed_at - self.full_update_start_datetime)
            / interval)

        next_update_time = self.full_update_start_datetime \
            + interval * (count + 1)

        return next_update_time

    def get_xckan_site(self):
        """
        Return the xckan.site.Site object corresponding to this model.

        Returns
        -------
        xckan.site.Site
            The site object to handle cache files and Solr index.
        """
        xckan_site = XckanSite(
            self.title, self.dataset_url,
            self.ckanapi_url, self.proxy_url)

        # Set tag vocabulary
        xckan_site.tag_default = self.tag_default
        if self.tag_vocabulary not in (None, ''):
            vocabs = self.tag_vocabulary.split(',')
            xckan_site.re_vocab = re.compile(
                '|'.join([f'({v})' for v in vocabs]))
        else:
            xckan_site.re_vocab = None

        return xckan_site

    def get_ckan_type(self):
        """
        Return CKAN type detected by the metadata.

        Returns
        -------
        str
            The ckan site type string.
        """
        self.get_xckan_site().get_site_class()

    class Meta:
        db_table = "sites_site"
        verbose_name_plural = "CKANサイト"
