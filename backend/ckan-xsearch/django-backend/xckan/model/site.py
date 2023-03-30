# coding: utf-8

import datetime
import json
from logging import getLogger
import socket
import time
import urllib.parse
import urllib.request

from xckan.siteconf import site_config
from xckan.model.metadata import Metadata

logger = getLogger(__name__)
ctx = site_config.get_ssl_context()


class Site:

    def __init__(
        self,
        name,
        url_top=None,
        url_api=None,
        proxy=None,
        is_fq_available=False,
    ):
        """
        Set URLs of the site-top and API endpoint.
        Both urls must end with '/'.
        """
        self.name = name
        self.url_top = url_top if url_top is None or url_top.endswith(
            '/') else url_top + '/'
        self.url_api = url_api if url_api is None or url_api.endswith(
            '/') else url_api + '/'
        self.proxy = proxy if proxy is None or proxy.endswith(
            '/') else proxy + '/'
        self.tag_default = None
        self.is_fq_available = is_fq_available
        self.re_vocab = None  # Compiled regexp object of controlled vocabulary

        self.sample_metadata = None

    @staticmethod
    def read_from_conf():
        """
        Read site list from conf file and return the list.
        The location of the conf file is defined in CKANLIST in siteconf.py.
        The conf file format should be:

        [ {"url":"<Site top url>", "api":"<Api endpoint>"}, ... ]
        """

        site_list = []
        conffile = site_config.CKANLIST

        with open(conffile, 'r', encoding='utf-8') as f:
            ckan_list = json.load(f)
            for site in ckan_list:
                if 'name' not in site:
                    raise RuntimeError(
                        "'name' is required but missing in {}".format(
                            json.dumps(site, ensure_ascii=False)))

                if 'url' not in site:
                    raise RuntimeError(
                        "'url' is required but missing in {}".format(
                            json.dumps(site, ensure_ascii=False)))

                if site['url'][0:1] in ('!', '#'):  # disabled
                    continue

                if 'api' not in site:
                    if site['url'][-9:] == '/dataset/':
                        site['api'] = site['url'][0:-8] + 'api/3/action/'
                    elif site['url'][-8:] == '/dataset':
                        site['api'] = site['url'][0:-7] + 'api/3/action/'
                    else:
                        raise RuntimeError(
                            "'api' is missing in {}".format(
                                json.dumps(site, ensure_ascii=False)))

                site_list.append(
                    Site(site['name'], site['url'], site['api'],
                         site.get('proxy'))
                )

        return site_list

    def get_name(self):
        return self.name

    def get_top(self):
        return self.url_top

    def get_api(self):
        return self.url_api

    def get_proxy(self):
        return self.proxy

    def get_api_base(self):
        url = self.get_api()
        pos = url.rfind('/api')
        if pos < 0:
            raise RuntimeError(f"Can't extract base-api url from '{url}'")

        baseurl = url[0:pos + 1]   # end with '/'
        return baseurl

    def get_site_id(self):
        """
        Generate identifier of the site from the url_top.
        """
        url_compose = urllib.parse.urlparse(self.url_top[0:-1])
        # logger.debug("url_compose.netloc:'{}', url_compose.path:'{}'".format(
        # url_compose.netloc, url_compose.path))
        site_id = (url_compose.netloc + url_compose.path).replace('/', '__')
        # logger.debug("url: {}, site_id: {}".format(self.url_top, site_id))

        return site_id

    def get_package_list(self):
        """
        Call 'package_list' API.
        If the response is not valid, return False.
        """
        site_id = self.get_site_id()
        from_proxy = False

        if self.proxy is not None:
            # Request to the proxy server
            url = self.proxy + 'package_list?fq={}'.format(
                urllib.parse.quote('id:' + site_id + r'\:*'))
            try:
                response = urllib.request.urlopen(url, context=ctx, timeout=10)
                from_proxy = True
            except (urllib.error.HTTPError, urllib.error.URLError,
                    socket.timeout) as e:
                logger.error(str(e) + "while accessing proxy '{}'".format(url))
                return False

        if not from_proxy:
            # Request to the original ckan server
            url = self.get_api() + 'package_list'
            try:
                response = urllib.request.urlopen(url, context=ctx, timeout=10)
                from_proxy = False
            except (urllib.error.HTTPError, urllib.error.URLError,
                    socket.timeout) as e:
                logger.error(
                    str(e) + " while accessing '{}'".format(url)
                )
                return False

        body = response.read()
        if body is None or len(body) == 0:
            logger.warning(
                "Cannot read dataset list from '{}', skipped.".format(url))
            return False

        try:
            result = json.loads(body.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            logger.warning(
                "Not JSON response from '{}', skipped.".format(url))
            return False

        if from_proxy:
            # translate xckan-id to the original-id.
            result['result'] = [
                x[len(site_id) + 1:] for x in result['result']
            ]

        # Unique id
        result['result'] = list(set(result['result']))

        return result

    def get_package_metadata(self, package_id):
        """
        Call 'package_show' API.
        If the response is not valid, return False.
        """

        site_id = self.get_site_id()
        from_proxy = False

        if self.proxy is not None:
            # Request to the proxy server
            url = self.proxy + 'package_show?id=' + urllib.parse.quote(
                site_id + ':' + package_id)
            try:
                response = urllib.request.urlopen(url, context=ctx, timeout=10)
                from_proxy = True
            except Exception as e:
                logger.error(
                    str(e) + " while accessing proxy '{}'".format(url))
                return False

        if not from_proxy:
            url = self.get_api() + 'package_show?id=' + urllib.parse.quote(
                package_id)

            try:
                response = urllib.request.urlopen(url, context=ctx, timeout=10)
                from_proxy = False
            except Exception as e:
                logger.error(
                    str(e) + " while accessing '{}'".format(url))
                return False

        body = response.read()
        if body is None or len(body) == 0:
            logger.error(
                "Cannot read metadata from '{}'".format(url))
            return False

        try:
            result = json.loads(body.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            logger.warning(
                "Not JSON response from '{}', skipped.".format(url))
            return False

        return result

    def get_updated_package_list(self, since=None):
        """
        Get updated packages modified/created after the datetime
        specified by 'since'.

        Parameters
        ----------
        since: integer or iso-format string or None
            The reference date.

            - None(default): during this 24 hours
            - int: in the specified seconds
            - Datetime in ISO format: after the datetime

        Returns
        -------
        dict
            A dict object decoded from the JSON returned by
            the package_search API.
            Returns False if the server could not be connected
            or if an error is returned.
        """
        # https://www.data.go.jp/data/api/3/action/package_search?fq=(metadata_modified:["2020-06-20T00:00:00Z" TO *] OR metadata_created:["2020-06-20T00:00:00Z" TO *])  # noqa: E501

        site_id = self.get_site_id()
        if self.proxy is None:
            from_proxy = False
        else:
            from_proxy = None

        if since is None:
            since = datetime.datetime.utcfromtimestamp(
                time.time() - 86400)
        elif isinstance(since, int) or isinstance(since, float):
            since = datetime.datetime.utcfromtimestamp(
                time.time() - since)
        elif isinstance(since, str):
            since = datetime.datetime.fromisoformat(since)

        start = 0   # default start position to be fetched
        rows = 100  # default number of rows to be fetched at once
        count = None

        from_str = since.strftime('%Y-%m-%dT%H:%M:%SZ')
        results = []

        while count is None or start < count:
            if from_proxy is None or from_proxy is True:
                query = {
                    'fq': r'id:{}\;* AND xckan_last_updated:["{}" TO *]'.format(
                        site_id, from_str),
                    'start': start,
                    'rows': rows
                }
                params = urllib.parse.urlencode(query)
                url = self.proxy + 'package_search?' + params
                logger.debug("Updating from url;'{}'".format(url))

                try:
                    response = urllib.request.urlopen(
                        url, context=ctx, timeout=10)
                    from_proxy = True
                except Exception as e:
                    logger.error(
                        str(e) + " while accessing proxy '{}'".format(url))
                    return False

            if from_proxy is None or from_proxy is False:
                query = {
                    'fq': ('(metadata_modified:["{0}" TO *] OR '
                           'metadata_created:["{0}" TO *])').format(from_str),
                    'start': start,
                    'rows': rows
                }
                # params = urllib.parse.quote(q)  # , safe='([]):*')
                params = urllib.parse.urlencode(query)
                url = self.get_api() + 'package_search?' + params

                try:
                    response = urllib.request.urlopen(
                        url, context=ctx, timeout=10)
                    from_proxy = False
                except Exception as e:
                    logger.error(
                        str(e) + " while accessing '{}'".format(url))
                    return False

            body = response.read()
            try:
                result = json.loads(body.decode('utf-8'))
            except json.decoder.JSONDecodeError:
                logger.error(
                    "Not JSON response from '{}'".format(url))
                return False

            results += result['result']['results']
            start = len(results)
            count = result['result']['count']

            # Verify that the query is executed correctly
            if len(results) > 0:
                m = Metadata.get_instance(results[0])
                if m is False:
                    raise RuntimeError(
                        "Cannot detect metadata class.\n"
                        + json.dumps(
                            results[0], indent=2, force_ascii=False))

                if from_proxy is False and not m.support_fq():
                    logger.warn(
                        "The result of 'package_search' API is not reliable.")
                    return False

            time.sleep(1)

        result['result']['results'] = results

        return result

    def test_top(self):
        """
        Ping check to the top url.
        """
        for i in range(1, 3):
            try:
                urllib.request.urlopen(self.get_top(), context=ctx, timeout=10)
                return True
            except (urllib.error.HTTPError, urllib.error.URLError,) as e:
                logger.error(str(e))
                return False
            except ConnectionResetError as e:
                logger.error(str(e))
                time.sleep(1)

        return False

    def test_list_api(self):
        """
        API check using 'package_list' and 'package_search'
        """
        metadata = self.__get_sample_metadata()

        if not metadata:
            return False

        return True

    def get_site_class(self):
        metadata = self.__get_sample_metadata()
        if metadata is False:
            logger.error("Cannot get sample metadata.")
            return False

        c = Metadata.get_class(metadata)
        if c is False:
            logger.error(
                "Cannot detect metadata class.\n"
                + json.dumps(metadata, indent=2, ensure_ascii=False))
            return False

        return c.__name__

    def get_required_fields(self, metadata=None):
        """
        Get the required fields retrieved when storing
        the metadata of this site in Solr.
        """
        if metadata is None:
            metadata = self.__get_sample_metadata()

        m = Metadata.get_instance(metadata)
        results = {}
        solr_metadata = m.get_solr_metadata(self)
        for k, v in solr_metadata.items():
            if k[0:6] == 'xckan_':
                results[k] = v

        return results

    def __get_sample_metadata(self):
        if self.sample_metadata is not None:
            return self.sample_metadata

        res = self.get_package_list()

        if not res or 'result' not in res or \
                not isinstance(res['result'], list) or \
                len(res['result']) < 1:
            return False

        package_id = res['result'][0]
        res = self.get_package_metadata(package_id)

        if not res:
            return False

        self.sample_metadata = res['result']

        return self.sample_metadata
