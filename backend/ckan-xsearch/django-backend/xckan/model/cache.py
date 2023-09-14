# coding: utf-8

import datetime
import glob
from http.client import InvalidURL
import json
from json import JSONDecodeError
from logging import getLogger
import os
import shutil
import socket
import time
import urllib.parse
import urllib.request

from xckan.siteconf import site_config
from .solr import SolrManager
from .metadata import Metadata

logger = getLogger(__name__)
ctx = site_config.get_ssl_context()


class CkanCache:

    list_expiration_days = 1
    metadata_expiration_days = 7

    def __init__(self, cache_dir=None):
        """
        Create file cache manager object.
        The file cache for metadata will be under the specified directory.

        Parameters
        ----------
        cache_dir: Pathlike, optional
            The cache-base directory.
            If not specified, the value of CACHEDIR in siteconf.py
            will be used.
        """

        # self.nmetadata = 0

        self.base = os.path.normpath(site_config.CACHEDIR)
        if self.base[-1:] != '/':
            self.base += '/'

        self.solr_manager = SolrManager()

    def compare_list(self, site, use_cache=False):
        """
        Compare stored id_list in the Solr server
        and site's latest id_list.

        Params
        ------
        site: xckan.site.Site
            The target site
        use_cache: bool, optional
            If True, use cached package_list if available. (default: False)

        Returns
        -------
        dict
            A dict object with deleted and added id lists.
            deleted : List of ids which are stored but not in the latest list
            added: List of ids which are not stored but in the latest list
        """
        package_list = self.get_package_list(site, force=(not use_cache))
        if package_list is False:
            return False

        id_list = self.get_id_list_from_solr(site)
        del_idlist = [id for id in id_list
                      if id not in package_list['result']]
        add_idlist = [id for id in package_list['result']
                      if id not in id_list]

        return {
            "id_list - package_list": del_idlist,
            "package_list - id_list": add_idlist,
        }

    def update_site(self, site, log=None):
        """
        Update package list and metadata of the site.

        To prevent multiple queries from being made to
        a single site at the same time, lock access to the site
        using a lock file.

        The actual update process is implemented by the
        `__update_site` method.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        log: File-like object (optional)
            If set, output update log to here.

        Results
        -------
        bool
            Return True if updated successfully, otherwise False.
        """
        result = False
        logger.debug("[{}] Locking for updating".format(
            site.get_site_id()))
        if self.__lock_site(site) is False:
            logger.warning("[{}] Cannot lock the site, skipped".format(
                site.get_site_id()))
        else:
            try:
                result = self.__update_site(site, log)
            finally:
                self.__unlock_site(site)
                logger.debug("[{}] Unlocked".format(site.get_site_id()))

        return result

    def __update_site(self, site, log=None):
        """
        Performing the actual update processes of the site.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        log: File-like object (optional)
            If set, output update log to here.
        """
        site_id = site.get_site_id()

        # Check last updated datetime
        last_updated = self.get_last_updated(site)
        logger.debug("[{}] Last updated = list:{}, update:{}".format(
            site_id,
            (datetime.datetime.fromtimestamp(last_updated['list']))
            .strftime('%Y-%m-%d %H:%M:%S'),
            (datetime.datetime.fromtimestamp(last_updated['update']))
            .strftime('%Y-%m-%d %H:%M:%S'),
        ))
        if log:
            print("Last updated = list:{}, update:{}".format(
                (datetime.datetime.fromtimestamp(last_updated['list']))
                .strftime('%Y-%m-%d %H:%M:%S'),
                (datetime.datetime.fromtimestamp(last_updated['update']))
                .strftime('%Y-%m-%d %H:%M:%S')),
                file=log)

        # Step 1: Differential update
        # Use fq to update metadata that has been changed
        # since the last update time.
        elapsed_seconds = time.time() - max(
            last_updated['list'], last_updated['update'])

        logger.debug(
            "[{}] Last updated {} seconds before.".format(
                site_id, elapsed_seconds))

        # Use 'package_search' API with fq to get the changed metadata
        if not site.is_fq_available or last_updated['list'] == 0:
            logger.debug("[{}] - differential update is skipped.".format(
                site_id))
            updated = False
        else:
            logger.debug("[{}] - trying get_updated_package_list".format(
                site_id))
            updated = site.get_updated_package_list(elapsed_seconds)

        if updated is not False:
            logger.debug("[{}] - get_updated_package_list succeeded."
                         .format(site_id))
            id_list = self.__update_by_updated_package_list(site, updated)
            self.solr_manager.flash_buffer()

        # Step 2: ID based syncronization
        # Get the package_list from the CKAN site,
        # compare it with the id registered in Solr, and syncronize it.
        logger.debug("[{}] - trying get_package_list".format(site_id))
        package_list = self.get_package_list(site, force=True)
        if package_list is False:
            return False

        logger.debug("[{}] - package_list has {} id.".format(
            site_id, len(package_list['result'])))

        if updated is False and last_updated['list'] == 0:
            # Perform full update on the site
            del_idlist = []
            add_idlist = [id for id in package_list['result']]
        else:
            id_list = self.get_id_list_from_solr(site)
            del_idlist = [
                id for id in id_list if id not in package_list['result']]
            add_idlist = [id for id in package_list['result']
                          if id not in id_list]

        logger.debug("[{}] added:{}".format(
            site_id,
            json.dumps(add_idlist, ensure_ascii=False)))
        logger.debug("[{}] deleted:{}".format(
            site_id,
            json.dumps(del_idlist, ensure_ascii=False)))
        if log:
            print("Added: {}".format(
                json.dumps(add_idlist, ensure_ascii=False)),
                file=log)
            print("Deleted: {}".format(
                json.dumps(del_idlist, ensure_ascii=False)),
                file=log)
            if len(add_idlist) == 0 and len(del_idlist) == 0:
                print("No packages were added or removed.",
                      file=log)

        if len(add_idlist) > 0:
            logger.debug("[{}] Adding new datasets.".format(site_id))
            self.add_new_metadata(site, add_idlist)

        if len(del_idlist) > 0:
            logger.debug("[{}] Deleting old datasets.".format(site_id))
            self.delete_obsoleted_metadata(site, del_idlist)

        self.solr_manager.flash_buffer()

        return True

    def get_last_updated(self, site):
        """
        Get the last updated timestamp of the site
        from the modified time of the cached files.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.

        Returns
        -------
        dict
            list: timestamp
                The timestamp of `package_list.json` file.
            update: timestamp
                The timestamp of `updated_package_list.json` file.
        """
        mtime_list = 0
        mtime_update = 0

        path = self.__get_package_list_path(site)
        if os.path.isfile(path):
            mtime_list = os.path.getmtime(path)

        path = self.__get_updated_package_list_path(site)
        if os.path.isfile(path):
            mtime_update = os.path.getmtime(path)

        return {
            "list": mtime_list,
            "update": mtime_update
        }

    def get_package_list(self, site, force=False, **kwargs):
        """
        Get package_list from the CKAN site.

        If the cached file is fresh enough, return the cached content.
        Otherwise, get the latest list via the site's API and update the cache.

        Parameters
        ----------
        site: xckan.site.Site
            The target CKAN site.
        force: bool, optional
            If True, ignore the cache and get the latest list from the site.

        Returns
        -------
        dict or False
            A dict object decoded from the JSON returned by the package_list API.
            If the site returns an error, False will be returned.
        """
        site_id = site.get_site_id()

        if not force:
            cached = self.__get_cached_package_list(site)

            if cached is not False:
                logger.debug("[{}] Read cached package_list.".format(
                    site_id))
                return cached

        content = site.get_package_list()
        if content is False or content['success'] is False:
            logger.error("[{}] Can't get the latest package_list.".format(
                site_id))
            return False

        time.sleep(1.0)

        self.__update_cached_package_list(site, content)
        logger.debug(
            "[{}] Update cached package_list.".format(site_id))

        return content

    def get_package_metadata(self, site, package_id, ignore_expiration=False):
        """
        Get package metadata with id = package_id from the site.
        If the cached file is fresh enough, return the cached content.
        Otherwise, get the latest metadata via the API and update the cache.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The id of the metadata.
        ignore_expiration: bool, optional
            If set to True, do not check expiration.

        Returns
        -------
        dict
            A dict object decoded from the JSON returned by
            the package_show API.
        """
        site_id = site.get_site_id()
        if ignore_expiration:
            cached = self.__get_cached_package_metadata(
                site, package_id, expire_timestamp=0)
        else:
            cached = self.__get_cached_package_metadata(site, package_id)

        if cached is not False:
            logger.debug("[{}] Read cached matadata of {}".format(
                site_id, package_id))
            return cached

        content = site.get_package_metadata(package_id)
        if content is False or content['success'] is False:
            logger.error("[{}] Can't get the latest metadata of {}".format(
                site_id, package_id))
            return False

        time.sleep(1.0)

        logger.debug("Updating metadata in 'get_package_metadata'")
        self.__update_cached_package_metadata(site, package_id, content)

        return content

    def __get_cache_base(self):
        """
        Get the cache base directory.

        Returns
        -------
        str
            The base cache directory.
        """
        return self.base

    def __get_site_cache_base(self, site):
        """
        Get the cache base directory of the site.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.

        Returns
        -------
        str
            The base cache directory of the site.
        """
        site_id = site.get_site_id()
        return os.path.join(
            self.__get_cache_base(), site_id + '/')

    def __get_jsonl_path(self, n=None):
        """
        Get the path to the JSONL file.
        """
        if n is None:
            n = self.nmetadata

        i = int(self.n / 1000)
        filename = "metadata_{:0>3}.jsonl".format(i)
        return self.__get_cache_base() + 'jsonl/' + filename

    def get_id_list_from_solr(self, site):
        """
        Get a list of metadata IDs for the specified site from
        the Solr server.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.

        Returns
        -------
        dict
            A dict object whose keys are package_id without site_id
            and whose values are xckan_id with site_id.
        """
        site_id = site.get_site_id()
        logger.info("Getting id list of {} from Solr...".format(site_id))
        stored = self.solr_manager.search(
            q="*:*", fl="id", start=0, rows=999999,
            fq="id:{}*".format(site_id.replace(':', r'\:')))

        stored_id_list = {}
        for solr_meta in stored:
            xckan_id = solr_meta['id']
            id = xckan_id[len(site_id) + 1:]
            stored_id_list[id] = xckan_id

        return stored_id_list

    def delete_site(self, site):
        """
        Remove all cached files of the site.
        It will also remove the contents of this site from Solr.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        """
        self.remove_package_list(site)
        self.remove_updated_package_list(site)

        path = self.__get_site_cache_base(site)
        logger.info("Delete directory {} if you don't need it.".format(
            path))
        # shutil.rmtree(path)

        self.solr_manager.delete_site(site)

    def __get_package_list_path(self, site):
        """
        Get full path to the package_list file of the site.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.

        Returns
        -------
        str
            The path to the `package_list.json` file.
        """
        return os.path.join(
            self.__get_site_cache_base(site), 'package_list.json')

    def remove_package_list(self, site):
        """
        Remove cached package_list file.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        """
        path = self.__get_package_list_path(site)
        if os.path.isfile(path):
            os.remove(path)

    def __get_updated_package_list_path(self, site):
        """
        Get full path to the updated_package_list file of the site.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.

        Returns
        -------
        str
            The path to the `updated_package_list.json` file.
        """
        return os.path.join(
            self.__get_site_cache_base(site),
            'updated_package_list.json')

    def remove_updated_package_list(self, site):
        """
        Remove cached updated_package_list file.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        """
        path = self.__get_updated_package_list_path(site)
        if os.path.isfile(path):
            os.remove(path)

    def __update_by_updated_package_list(self, site, updated):
        """
        Update cached data by the result of `get_updated_package_list`.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        updated: dict
            A dict object decoded from the JSON returned by
            the package_search API.

        Returns
        -------
        list
            A list of updated metadata IDs.
        """

        # Save full result to the log file as JSON
        path = self.__get_updated_package_list_path(site)

        os.makedirs(os.path.dirname(path), 0o755, True)
        with open(path, 'w', encoding='utf-8') as f:
            logger.debug("[{}] Update updated_package_list.".format(
                site.get_site_id()))
            json.dump(updated, f, indent=2, ensure_ascii=False)

        # Save each package_metadata
        updated_id_list = []
        for result in updated['result']['results']:
            metadata = {
                "help": updated['help'],
                "success": updated['success'],
                "result": result
            }
            m = Metadata.get_instance(result)
            package_id = m.get_id()
            updated_id_list.append(package_id)
            logger.debug(
                "Updating metadata in '__update_by_updated_package_list'")
            self.__update_cached_package_metadata(site, package_id, metadata)

        return updated_id_list

    def __get_cached_package_list(self, site):
        """
        Get cached package_list content.
        The expiration period of the cached file is determined by
        `list_expiration_days`.

        Parameters
        ----------
        site: xckan.site.Site
            The target CKAN site.

        Returns
        -------
        dict or False
            A dict object decoded from the JSON returned by the package_list API.
            Returns False if the cache does not exist or is too old.
        """
        expiration_seconds = self.list_expiration_days * 86400

        path = self.__get_package_list_path(site)
        if not os.path.isfile(path):
            return False   # Not in the cache

        if os.path.getmtime(path) < time.time() - expiration_seconds:
            return False   # Too old

        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)

        return content

    def __update_cached_package_list(self, site, content):
        """
        Update cached package_list with new content.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        content: dict
            A dict object decoded from the JSON returned by
            the package_show API.
        """
        path = self.__get_package_list_path(site)

        os.makedirs(os.path.dirname(path), 0o755, True)
        with open(path, 'w', encoding='utf-8') as f:
            logger.debug(
                "[{}] Update cached package list.".format(
                    site.get_site_id()))
            json.dump(content, f, indent=2, ensure_ascii=False)

        return True

    def __get_package_path(self, site, package_id):
        """
        Get full path to the package directory of the site and package_id.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The target id.

        Returns
        -------
        str
            The path to the target directory.
        """
        site_id = site.get_site_id()
        return os.path.join(
            self.__get_cache_base(), site_id, package_id + '/')

    def __get_package_metadata_path(self, site, package_id):
        """
        Get full path to the package_metadata of the site and package_id.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The target id.

        Returns
        -------
        str
            The path to the `catalog.json` file.
        """
        return os.path.join(
            self.__get_package_path(site, package_id), 'catalog.json')

    def __get_cached_package_metadata(
            self, site, package_id, expire_timestamp=None):
        """
        Get cached package_metadata content.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The id of the metadata.
        expire_timestamp: int or None
            If set, the cached file will be expired if its timestamp is
            less than this value.
            If it is not set, it will be expired if it is older than
            'metadata_expiration_days'.

        Returns
        -------
        dict
            A dict object decoded from the JSON returned by
            the package_show API.
        """
        if expire_timestamp is None:
            expire_timestamp = time.time() - \
                self.metadata_expiration_days * 86400

        path = self.__get_package_metadata_path(site, package_id)

        if not os.path.isfile(path):
            return False   # Not in the cache

        if os.path.getmtime(path) < expire_timestamp:
            return False   # Too old

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except JSONDecodeError:
            logger.debug(
                "[{}] The cached file is invalid json format. (path: {})"
                .format(site.get_site_id(), path))
            return False

        return content

    def __update_cached_package_metadata(self, site, package_id, content):
        """
        Update cached package_metadata with new content.
        This method also registers the content in Solr.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The target id.
        content: dict
            A dict object decoded from the JSON returned by
            the package_list API.

        Returns
        -------
        bool
            If the content is valid metadata, return True,
            otherwise False.
        """
        path = self.__get_package_metadata_path(site, package_id)

        os.makedirs(os.path.dirname(path), 0o755, True)
        with open(path, 'w', encoding='utf-8') as f:
            logger.debug(
                "[{}] Update cached package metadata of {}".format(
                    site.get_site_id(), package_id))
            json.dump(content, f, indent=2, ensure_ascii=False)

        if 'result' not in content:
            return False

        ckan_metadata = content['result']
        m = Metadata.get_instance(ckan_metadata)
        solr_metadata = m.get_solr_metadata(site)
        self.solr_manager.add_document(solr_metadata)

        return True

    def add_new_metadata(self, site, add_idlist):
        """
        Retrieve the newly added metadata contained in the ID list,
        and add them to the cache and Solr.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        add_idlist: list
            The list of package_ids.
        """
        for package_id in add_idlist:
            package_path = self.__get_package_metadata_path(site, package_id)
            if os.path.exists(package_path):
                # Delete metadata file not to use cache.
                os.remove(package_path)

            content = self.get_package_metadata(site, package_id)
            if not isinstance(content, dict):
                logger.error(
                    "[{}] Can't get metadata of '{}' (Skipped)".format(
                        site.get_site_id(), package_id))
                continue

            logger.debug("Updating metadata in 'add_new_metadata'")
            self.__update_cached_package_metadata(site, package_id, content)

    def delete_obsoleted_metadata(self, site, del_idlist):
        """
        Delete obsoleted metadata from both cache and Solr.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        del_idlist: list
            The list of package_ids.
        """
        id_list = self.get_id_list_from_solr(site)
        xckan_id_list = []
        for package_id in del_idlist:
            xckan_id_list.append(id_list[package_id])
            del id_list[package_id]
            path = self.__get_package_path(site, package_id)
            if os.path.isdir(path):
                shutil.rmtree(path)

        self.solr_manager.delete_document(xckan_id_list)

    def reindex_site(self, site):
        """
        Re-create Solr index from the cached data.

        To prevent the cache file from being modified
        during index rebuilding, lock access to the site
        using a lock file.

        The actual reindex process is implemented by the
        `__reindes_site` method.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.

        Returns
        -------
        dict
            A dict object whose keys are package_id without site_id
            and whose values are xckan_id with site_id.
        """
        site_id = site.get_site_id()
        try:
            logger.debug("[{}] Locking for reindexing".format(
                site_id))
            if self.__lock_site(site) is False:
                logger.warning("[{}] Cannot lock the site, skipped".format(
                    site_id))
                id_list = False
            else:
                id_list = self.__reindex_site(site)
        finally:
            self.__unlock_site(site)
            logger.debug("[{}] Unlocked".format(site_id))

        return id_list

    def __reindex_site(self, site):
        """
        Performing the actual re-index processes of the site.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        """
        self.solr_manager.delete_site(site)
        id_list = {}

        cache_iterator = self.each_metadata(site, '2000-01-01T00:00:00')
        for metadata in cache_iterator:
            m = Metadata.get_instance(metadata)
            solr_metadata = m.get_solr_metadata(site)
            self.solr_manager.add_document(solr_metadata)

            id_list[solr_metadata['xckan_original_id']] = \
                solr_metadata['id']

        self.solr_manager.flash_buffer()

        return id_list

    def get_sites(self):
        """
        Get list of stored sites.

        Returns
        -------
        list
            The list of site_ids.
        """
        sites = []
        pattern = self.__get_cache_base() + '*/id_list.json'
        for id_list in glob.glob(pattern):
            if not os.path.isfile(id_list):
                continue

            dirname = os.path.dirname(id_list)
            pos = dirname.rfind('/')
            if pos < 0:
                continue

            site_id = dirname[pos + 1:]
            sites.append(site_id)

        return sites

    def each_metadata(self, site, since=None):
        """
        Get list of id in the site which was updated
        after the datetime specified by 'since'.

        Parameters
        ----------
        since: integer or iso-format string or None
            The reference date.

            - None(default): during this `metadata_expiration_days`
            - int: in the specified seconds
            - Datetime in ISO format: after the datetime

        Returns
        -------
        dict
            The 'result' part of the dict object decoded from
            the JSON returned by the package_show API.
        """
        if since is None:
            expiration = CkanCache.metadata_expiration_days * 86400
        elif isinstance(since, int) or isinstance(since, float):
            expiration = since
        elif isinstance(since, str):
            expiration = time.time() - datetime.datetime.fromisoformat(
                since).timestamp()

        for package_id in self.get_id_list_from_solr(site):
            metadata = self.__get_cached_package_metadata(
                site, package_id, expiration)
            if metadata is False or 'result' not in metadata:
                continue

            yield metadata['result']

    def __lock_site(self, site):
        """
        Lock site by creating a lock file.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.

        Returns
        -------
        bool
            True if the lock succeeds, False if it fails.
        """
        site_id = site.get_site_id()
        lockfile = os.path.join(site_config.LOCKDIR, site_id + '.lock')
        if os.path.exists(lockfile):
            with open(lockfile, 'r') as f:
                pid = f.read()
                logger.debug("[{}] Locked by pid={}".format(site_id, pid))

            return False

        with open(lockfile, 'w') as f:
            print("{}".format(os.getpid()), file=f)

        return True

    def __unlock_site(self, site):
        """
        Unlock site by deleting the lock file.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.

        Returns
        -------
        bool
            True if the unlock succeeds, False if it fails.
        """
        site_id = site.get_site_id()
        lockfile = os.path.join(site_config.LOCKDIR, site_id + '.lock')
        if os.path.exists(lockfile):
            os.remove(lockfile)
            return True

        logger.warning("[{}] Try to unlock but not locked".format(site_id))
        return False

    def get_resources_from_site(
            self, site, formats=None, force=False):
        """
        Download resource files from the site and
        store in the cache directory.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        formats: list of str, optional
            Formats to be downloaded. If ommitted,
            use ['pdf', 'csv', 'xls', 'xlsx'] as default.
            The format name is not case sensitive.
        force: bool
            If set to True, ignore the timestamp of the
            cache file and download the resource file.

        returns
        -------
        dict
            Aggregation of resource collection results,
            including the following information;
            - success
              Number of successful downloads
            - not_target
              Number not in the target format
            - no_url
              Number of download links not included
            - invalid_datetime
              Number of incorrect date/time expressions
            - fail
              Number of failed downloads

        Note
        ----
        This method ignores the expiration of the metadata cache file.
        """
        if formats is None:
            formats = ['pdf', 'csv', 'xls', 'xlsx']
        else:
            formats = [x.lower() for x in formats]

        stats = {
            "success": 0, "not_target": 0, "no_url": 0,
            "invalid_datetime": 0, "fail": 0,
        }

        for package_id in self.get_id_list_from_solr(site):
            content = self.get_package_metadata(
                site, package_id, ignore_expiration=True)
            if content is False:
                logger.debug(
                    "The metadata of package {} is not available.".format(
                        package_id))
                continue

            m = Metadata.get_instance(content['result'])
            for resource in m.get_resources():
                if ('url' not in resource and 'download_url' not in resource) \
                        or resource['id'] is None:
                    stats['no_url'] += 1
                    continue

                resource_format = resource.get('format') or 'null'
                if resource_format.lower() not in formats:
                    msg = "Skip resource {} since its format is {}"
                    logger.debug(msg.format(resource['id'], resource_format))
                    stats['not_target'] += 1
                    continue

                resource_file_path = self.get_resource_file_path(
                    site, package_id, resource)

                if os.path.exists(resource_file_path):
                    mtime = os.path.getmtime(resource_file_path)
                    try:
                        if 'updated' in resource:
                            updated = datetime.datetime.fromisoformat(
                                resource['updated'])
                        elif 'modified' in resource:
                            updated = datetime.datetime.fromisoformat(
                                resource['modified'])
                        elif 'created' in resource:
                            updated = datetime.datetime.fromisoformat(
                                resource['created'])
                        else:
                            updated = datetime.datetime(2000, 1, 1)

                    except ValueError as e:
                        msg = 'In {}, {} ({})'
                        logger.warning(msg.format(
                            package_id, resource['id'], e))
                        stats['invalid_datetime'] += 1
                        updated = datetime.datetime(2000, 1, 1)

                    if mtime >= updated.timestamp() and force is False:
                        logger.debug("Resource {} is up to date".format(
                            resource['id']))
                        stats['success'] += 1
                        continue

                if self.save_resource(site, package_id, resource):
                    stats['success'] += 1
                    msg = "Resource {} has been downloaded to {}"
                    logger.debug(msg.format(
                        resource['id'], resource_file_path))
                else:
                    stats['fail'] += 1
                    package_path = self.__get_package_path(site, package_id)
                    msg = "Resource {} is not available. (package path: {})"
                    logger.warning(msg.format(resource['id'], package_path))

                time.sleep(1.0)

        return stats

    def get_resource_dir(self, site, package_id: str, resource: dict):
        """
        Get the path to the resource directory.
        The directory will contain 'resource_meta.json' and
        a downloaded file.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The id of the package containing the resource.
        resource: dict
            The target resource

        Returns
        -------
        os.PathLike
            The path to the directory.
        """

        # Get path to the resource directory
        package_path = self.__get_package_path(site, package_id)
        resource_dir_path = os.path.join(
            package_path, str(resource['id']))

        return resource_dir_path

    def get_resource_metadata_path(
            self, site, package_id: str, resource: dict):
        """
        Get the path to the resource metadata.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The id of the package containing the resource.
        resource: dict
            The target resource

        Returns
        -------
        os.PathLike
            The path to the resource metadata file.
        """
        resource_meta_path = os.path.join(
            self.get_resource_dir(site, package_id, resource),
            'resource_meta.json')

        return resource_meta_path

    def get_resource_file_path(
            self, site, package_id: str, resource: dict):
        """
        Get the path to the resource file.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The id of the package containing the resource.
        resource: dict
            The target resource

        Returns
        -------
        os.PathLike, or False
            The path to the resource file.
        """
        dir_path = self.get_resource_dir(site, package_id, resource)

        # Get path to the resource file
        url = resource.get('download_url',
                           resource.get('url', None))
        if url is None:
            logger.warning("URL is empty.{},{},{}".format(
                site, package_id, resource.get('id', '(no-id)')))
            return False

        filename = os.path.basename(
            urllib.parse.unquote(url))
        if 'filename' in resource and resource['filename']:
            filename = os.path.basename(resource['filename'])

        if filename == '':
            logger.warning("The file name is empty.")
            return False

        return os.path.join(dir_path, filename)

    def save_resource(
            self, site, package_id: str, resource: dict):
        """
        Download a resource data to the resource directory.

        The directory contain `resource_meta.json` which
        stores the resource metadata and the data file.
        Download the resource file.

        Parameters
        ----------
        site: xckan.site.Site
            The target site.
        package_id: str
            The id of the package containing the resource.
        resource: dict
            The target resource

        Returns
        -------
        bool
            Return True if succeed, otherwise False.
        """
        data = None
        url = resource.get('download_url',
                           resource.get('url'))
        try:
            response = urllib.request.urlopen(url, context=ctx, timeout=10)
            if response.status >= 200 and response.status < 300:
                data = response.read()

        except (urllib.error.HTTPError, urllib.error.URLError,
                socket.timeout, InvalidURL, Exception) as e:
            logger.error(
                str(e) + "(while downloading resource from '{}')".format(url))
            return False

        if data is None or len(data) == 0:
            logger.warning(
                "Empty resource content '{}'".format(url))
            return False

        file_path = self.get_resource_file_path(
            site, package_id, resource)

        if file_path is False:
            return False

        os.makedirs(self.get_resource_dir(
            site, package_id, resource), mode=0o755,
            exist_ok=True)

        meta_path = self.get_resource_metadata_path(
            site, package_id, resource)
        with open(meta_path, 'w', encoding='utf-8') as meta:
            content = json.dumps(resource, indent=2, ensure_ascii=False)
            meta.write(content)

        with open(file_path, 'wb') as fb:
            fb.write(data)

        return True
