# coding: utf-8

"""
Update ckan sites.

Usage
python django-backend/manage.py runscript update [--script-args [force-full | force] <keyword>...]

If '--script-args' option is specified,
only sites that contain all the specified keywords in their URLs
will be considered for updating.

If 'force-full' is specified, the sites will be forced to perform
a full update even if it is not yet the scheduled time.

If 'force' is specified, the sites will be forced to perform
a update even if it is not yet the scheduled time.

Example:

- Full update sites contains "aomori" it it is before the scheduled time.
    python django-backend/manage.py runscript update \
      --script-args force-full aomori
"""

import concurrent.futures
import datetime
import io
import logging
from pytz import timezone
from smtplib import SMTPAuthenticationError

from sites.mail import Mail
from sites.models import Site as SiteSetting
from xckan.model.cache import CkanCache

logger = logging.getLogger(__name__)


class SiteUpdater:

    def __init__(self, cache, settings, do_full_update, do_force_full_update):
        self.cache = cache
        self.threads = {}
        self.settings = settings
        if do_full_update:
            self.update_site_settings = self.settings
        else:
            self.update_site_settings = self.__get_update_site_settings()

        if do_force_full_update:
            self.full_update_site_settings = self.settings
        else:
            self.full_update_site_settings = \
                self.__get_full_update_site_settings()

    def __get_update_site_settings(self):
        update_site_settings = []
        now = datetime.datetime.now(timezone('UTC'))
        for site_setting in self.settings:
            if not site_setting.update_interval or \
               not site_setting.update_start_datetime:
                continue

            next_update_time = site_setting.update_time or \
                site_setting.update_start_datetime
            message = "{}: Next update at {}".format(
                site_setting, next_update_time.isoformat())
            if now >= next_update_time:
                update_site_settings.append(site_setting)
                logger.info("{} -> Update".format(message))
            else:
                logger.info("{} -> Skip".format(message))

        return update_site_settings

    def __get_full_update_site_settings(self):
        update_site_settings = []
        now = datetime.datetime.now(timezone('UTC'))

        for site_setting in self.settings:
            if not site_setting.full_update_interval or \
               not site_setting.full_update_start_datetime:
                continue

            next_update_time = site_setting.full_update_time or \
                site_setting.full_update_start_datetime
            message = "{}: Next full update at {}".format(
                site_setting, next_update_time.isoformat())
            if now >= next_update_time:
                update_site_settings.append(site_setting)
                logger.info("{} -> Update".format(message))
            else:
                logger.info("{} -> Skip".format(message))

        return update_site_settings

    def update_sites(self, force=False):
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=4) as executor:
            for setting in self.update_site_settings:
                if setting in self.full_update_site_settings:
                    logger.info(
                        "Skip updating {}, wating full-update".format(
                            setting))
                    continue

                xckan_site = setting.get_xckan_site()
                # site_id = xckan_site.get_site_id()
                executor.submit(self.__update_site, xckan_site, setting)

        logger.info("Update (differencial) done.")

    def __update_site(self, xckan_site, setting):
        site_id = xckan_site.get_site_id()
        logger.info("[{}] Starting update".format(site_id))

        setting.executed_at = datetime.datetime.now(timezone('UTC'))
        setting.update_time = setting.next_update_time()
        setting.result = 'Processing'
        setting.save()

        buffer = io.StringIO()

        try:
            result = self.cache.update_site(xckan_site, log=buffer)
            if result:
                setting.result = 'OK:{}'.format(
                    datetime.datetime.now().isoformat(timespec='seconds'))
            else:
                setting.result = 'NG:{}'.format(
                    datetime.datetime.now().isoformat(timespec='seconds'))
        except RuntimeError as e:
            logger.error(e)
            setting.result = 'ERR:{}({})'.format(
                datetime.datetime.now().isoformat(timespec='seconds'),
                str(e))

        setting.save()
        logger.info("[{}] Update done".format(site_id))

        # Send notification email to the contact person.
        if setting.notify_contact_email is True and \
                setting.contact_email is not None:
            try:
                Mail.send(
                    message=setting.result + "\n\n" + buffer.getvalue(),
                    subject="[XCKAN] Update result",
                    to_addresses=[setting.contact_email])
            except SMTPAuthenticationError as e:
                logger.error((
                    "Cannot connect to the SMTP server."
                    "Please check the environmental variables.") + e)
            except RuntimeError as e:
                logger.error((
                    "SMTP Host is not set."
                    "Please set 'SMTP_HOST' environmental variable ."))

        return True

    def full_update_sites(self, force=False):
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=4) as executor:
            for setting in self.full_update_site_settings:
                xckan_site = setting.get_xckan_site()
                executor.submit(self.__full_update_site, xckan_site, setting)

        logger.info("Update (full) done.")

    def __full_update_site(self, xckan_site, setting):
        site_id = xckan_site.get_site_id()
        logger.info("[{}] Starting full update".format(site_id))

        setting.full_executed_at = datetime.datetime.now(timezone('UTC'))
        setting.full_update_time = setting.next_fullupdate_time()
        setting.full_result = 'Processing'
        setting.save()

        # full update
        self.cache.solr_manager.delete_site(xckan_site)

        buffer = io.StringIO()
        try:
            result = self.cache.update_site(xckan_site, log=buffer)
            if result:
                setting.full_result = 'OK:{}'.format(
                    datetime.datetime.now().isoformat(timespec='seconds'))
            else:
                setting.full_result = 'NG:{}'.format(
                    datetime.datetime.now().isoformat(timespec='seconds'))
        except RuntimeError as e:
            logger.error(e)
            setting.full_result = 'ERR:{}({})'.format(
                datetime.datetime.now().isoformat(timespec='seconds'),
                str(e))

        setting.save()
        logger.info("[{}] Full update done".format(site_id))

        # Send notification email to the contact person.
        if setting.notify_contact_email is True and \
                setting.contact_email is not None:
            try:
                Mail.send(
                    message=setting.result + "\n\n" + buffer.getvalue(),
                    subject="[XCKAN] Full update result",
                    to_addresses=[setting.contact_email])
            except SMTPAuthenticationError as e:
                logger.error((
                    "Cannot connect to the SMTP server."
                    "Please check the environmental variables.") + e)
            except RuntimeError as e:
                logger.error((
                    "SMTP Host is not set."
                    "Please set 'SMTP_HOST' environmental variable ."))

        return True


def run(*args):
    cache = CkanCache()
    site_settings = SiteSetting.objects.filter(enable=True).all()

    do_force_full_update = False
    do_force_update = False
    sitenames = []
    for arg in args:
        if arg == 'force-full':
            do_force_full_update = True
        elif arg == 'force':
            do_force_update = True
        else:
            sitenames.append(arg)

    if len(sitenames) > 0:
        filtered_settings = []
        for site_setting in site_settings:
            do_check = True
            for sitename in sitenames:
                if sitename not in site_setting.title and \
                        sitename not in site_setting.dataset_url:
                    do_check = False
                    continue

            if do_check:
                filtered_settings.append(site_setting)

        site_settings = filtered_settings

    updater = SiteUpdater(cache, site_settings,
                          do_force_update, do_force_full_update)
    updater.update_sites()
    updater.full_update_sites()
