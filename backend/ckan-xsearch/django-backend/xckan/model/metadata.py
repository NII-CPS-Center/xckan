# coding: utf-8
from abc import ABC
import datetime
from html.parser import HTMLParser
from io import StringIO
import json
from logging import getLogger
import re
import traceback

logger = getLogger(__name__)


class MLStripper(HTMLParser):
    """
    Strip HTML Tags from string.
    ref: https://stackoverflow.com/questions/753052/
    """

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()
        self.tag_started = set()
        self.is_mltext = False

    def handle_starttag(self, tag, attrs):
        self.tag_started = self.tag_started | set(tag)

    def handle_endtag(self, tag):
        if tag in self.tag_started:
            self.is_mltext = True
            self.tag_started = self.tag_started - set(tag)

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self, mltext: str):
        self.feed(mltext)
        self.close()
        if self.is_mltext:
            stripped = self.text.getvalue()
        else:
            stripped = mltext

        return stripped


def strip_tags(html):
    s = MLStripper()
    string = s.get_data(html)
    string = re.sub(r'([ \t\u3000])+(?=.)', ' ', string)
    string = re.sub(r' *([\r\n]|\\n)+ *(?=.)', ' / ', string)
    string = re.sub(r'\n+$', '', string)
    return string


def unnest(obj, dic={}, prefix=''):
    """
    Unnest nested object.
    """
    if isinstance(obj, list):
        for x in obj:
            unnest(x, dic, prefix)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = prefix + '.' + k if len(prefix) > 0 else k
            unnest(v, dic, new_prefix)
    elif prefix not in dic:
        dic[prefix] = obj
    else:
        if not isinstance(dic[prefix], list):
            if dic[prefix] == obj:
                pass
            else:
                dic[prefix] = [dic[prefix], obj]
        elif obj not in dic[prefix]:
            dic[prefix].append(obj)

    return dic


class Metadata(ABC):
    """
    The abstract class of metadata classes.
    """

    @staticmethod
    def get_class(metadata):
        """
        Get the subclass compatible with the metadata.
        """
        if not isinstance(metadata, dict) and not isinstance(metadata, list):
            return False

        for c in [
            ShirasagiMetadata,  # SHIRASAGI
            CkanMetadata,     # ckan, dkan
            MikawaMetadata,   # opendata-east-mikawa.jp
            KagawaMetadata   # opendata.pref.kagawa.lg.jp
        ]:
            if c.is_compatible(metadata):
                return c

        return False

    @staticmethod
    def get_instance(metadata):
        """
        Get the subclass object of the metadata
        """
        c = Metadata.get_class(metadata)
        if c is False:
            return False

        return c(metadata)

    def __init__(self, metadata):
        """
        Initialize by python-dict data (decoded JSON)
        """

        self.metadata = metadata

    def support_fq(self):
        return False

    def get_id(self):
        return False

    def get_title(self):
        return False

    def get_site_url(self):
        return False

    def get_max_value(self, values: list):
        candidates = []
        for value in values:
            if value is not False and value is not None:
                candidates.append(value)

        if len(candidates) == 0:
            return None

        return max(candidates)

    def get_last_updated(self):
        return self.get_max_value([
            self.reformat_date_field(self.metadata['metadata_created']),
            self.reformat_date_field(self.metadata['metadata_modified'])
        ])

    def get_resources(self):
        """
        Get list of resources.
        """
        return False

    def get_description(self):
        return False

    @staticmethod
    def reformat_date_field(dt_str):
        """
        Reformat CKAN's datatime value to Solr compatible.
        """

        if dt_str is None or dt_str == '':
            return None

        m = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', dt_str)
        if not m:
            return None

        try:
            dt = datetime.datetime.strptime(m.group(0), '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return None

        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    def get_solr_metadata(self, site, metadata=None):
        """
        Convert original metadata to Solr compatible metadata
        which will be stored.
        """
        try:
            m = self.__get_solr_metadata(site, metadata)
            return self.filter_fields(m)
        except Exception as e:
            logger.error(
                "Cannot convert metadata {}:{} to Solr, reason:{}".format(
                    site.get_site_id(), self.get_id(), e))
            logger.error(traceback.format_exc())
            exit(-1)

    def filter_fields(self, m: dict):
        """
        Leave only the metadata items to be registered and delete the rest.
        """
        filtered = {}
        for k, v in m.items():
            if k.endswith('_date'):
                v = self.reformat_date_field(str(v))

            if v is not None:
                filtered[k] = v

        return filtered

    def __get_solr_metadata(self, site, metadata):
        validated = {}
        if metadata is None:
            metadata = self.metadata.copy()

        # get site location
        site_id = site.get_site_id()

        # validated = metadata.copy()
        validated = unnest(metadata, {}, '')

        # Generate values from metadata
        if type(validated['name']) is not str:
            validated['name'] = str(validated['name'])

        validated['id'] = site_id + ':' + self.get_id()
        validated['xckan_original_id'] = validated.get(
            'xckan_original_id', self.get_id())
        validated['xckan_title'] = validated.get(
            'xckan_title', self.get_title())
        validated['xckan_site_name'] = validated.get(
            'xckan_site_name', site.get_name())
        validated['xckan_site_url'] = validated.get(
            'xckan_site_url', site.get_api_base() + self.get_site_url())
        validated['xckan_last_updated'] = validated.get(
            'xckan_last_updated', self.get_last_updated())
        validated['xckan_description'] = validated.get(
            'xckan_description', self.get_description())
        if isinstance(validated['xckan_description'], str):
            validated['xckan_description'] = \
                validated['xckan_description'][0:5000]

        if 'metadata_created' in metadata:
            validated['metadata_created'] = self.reformat_date_field(
                metadata['metadata_created'])

        if 'metadata_modified' in metadata:
            validated['metadata_modified'] = self.reformat_date_field(
                metadata['metadata_modified'])

        if 'indexed_ts' in metadata:
            validated['indexed_ts'] = self.reformat_date_field(
                metadata['indexed_ts'])

        # Unnest Nested elements
        if 'tags' in metadata:
            validated['tags'] = self.__process_tags(metadata)

        if 'groups' in metadata:
            validated['groups'] = self.__process_groups(metadata)

        if 'organization' in metadata:
            validated['organization'] = self.__process_organization(metadata)

        if 'resources' in metadata:
            res_description = list(filter(lambda x: x, map(
                lambda x: x.get('description'), metadata['resources'])))
            validated['res_description'] = res_description

            res_format = list(filter(lambda x: x, map(
                lambda x: x.get('format'), metadata['resources'])))
            validated['res_format'] = res_format

            res_type = list(filter(lambda x: x, map(
                lambda x: x.get('resource_type'), metadata['resources'])))
            validated['res_type'] = res_type

            res_url = list(filter(lambda x: x, map(
                lambda x: x.get('url'), metadata['resources'])))
            validated['res_url'] = res_url

            if 'resources.last_modified' in validated:
                orig = validated['resources.last_modified']
                if orig is not None:
                    modified = []
                    for x in orig:
                        if x is not None:
                            modified.append(self.reformat_date_field(x))

                    validated['resources.last_modified'] = modified

        if 'extras' in metadata:
            # validated['extras'] = metadata['extras']
            for extra in metadata['extras']:
                if 'value' not in extra or 'key' not in extra:
                    continue

                key = 'extras_' + extra['key'].lower()
                if key not in validated:
                    validated[key] = []

                validated[key].append(extra['value'])

        # Extract controlled tags
        validated['xckan_tags'] = self.extract_controlled_tags(
            site,
            validated['xckan_title']
            + validated['xckan_description']
            + ' '.join(validated.get('tags', []))
            + ' '.join(validated.get('groups', []))
            + validated.get('organization', '')
            + ' '.join(validated.get('res_description', []))
        )

        # Keep original data
        validated['data_dict'] = json.dumps(self.metadata, ensure_ascii=False)

        return validated

    def __process_tags(self, metadata):
        tags = metadata['tags']
        if not isinstance(tags, list):
            return []

        if len(tags) == 0:
            return []

        if isinstance(tags[0], str):
            return tags

        if isinstance(tags[0], dict) and \
           'name' in tags[0]:
            return list(filter(lambda x: x, map(
                lambda x: x.get('name'), tags)))

        raise RuntimeError("Unexpected format in 'tags'")

    def __process_groups(self, metadata):
        groups = metadata['groups']
        if not isinstance(groups, list):
            return []

        if len(groups) == 0:
            return []

        if isinstance(groups[0], str):
            return groups

        if isinstance(groups[0], dict) and \
                'name' in groups[0]:
            return list(filter(lambda x: x, map(
                lambda x: x.get('name'), groups)))

        raise RuntimeError("Unexpected format in 'groups'")

    def __process_organization(self, metadata):
        organization = metadata['organization']

        if organization is None or organization is False:
            return None

        if isinstance(organization, str):
            return organization

        if isinstance(organization, dict):
            if 'is_organization' in organization and \
                    not organization['is_organization']:
                return None

            if 'title' in organization:
                return organization['title']

            if 'name' in organization:
                return organization['name']

        raise RuntimeError("Unexpected format in 'organization'")

    def extract_controlled_tags(self, site, from_text):
        """
        Extract controlled vocabulary tags from text.

        If vocabulary was not assigned to the site, or no word in
        the assigned vocabulary are found in the text,
        return the default tag (which might be None).

        Otherwise, returns the list of all candidates found.
        """
        if site.re_vocab is None:
            if isinstance(site.tag_default, str):
                return [site.tag_default]

            return site.tag_default

        tags = site.re_vocab.findall(from_text)
        if len(tags) == 0:
            if isinstance(site.tag_default, str):
                return [site.tag_default]

            return site.tag_default

        tags = (list)(filter(None, set(tags[0])))
        return tags


class CkanMetadata(Metadata):
    """
    Original CKAN system
    """

    @staticmethod
    def is_compatible(metadata):
        if 'id' not in metadata \
                or not isinstance(metadata['id'], str) \
                or 'name' not in metadata \
                or 'title' not in metadata:
            return False

        return True

    def support_fq(self):
        return True

    def get_id(self):
        return self.metadata['name']

    def get_title(self):
        return self.metadata['title']

    def get_site_url(self):
        return 'dataset/' + self.metadata['name']

    def get_solr_metadata(self, site):
        metadata = super().get_solr_metadata(site)

        # If the metadata has 'extras_xckan_*' fields,
        # store the value in the xckan_* field.
        # For example, if 'extras_xckan_site_url' contains the
        # destination URL, store that value in 'xckan_site_url'.
        # This will make it possible to go to that URL directly
        # from the cross-search system.

        for key, value in metadata.items():
            if key.startswith('extras_xckan_'):
                new_key = key[7:]
                metadata[new_key] = value

        return metadata

    def get_resources(self):
        if 'resources' in self.metadata:
            return self.metadata['resources']

        return []

    def get_description(self):
        description = self.metadata.get('notes') or ''
        description = strip_tags(description)

        resource_names = []
        for resource in self.metadata.get('resources', []):
            v = resource.get('name')
            if v:
                v = strip_tags(v)
                if v not in resource_names:
                    resource_names.append(v)

            v = resource.get('description')
            if v:
                v = strip_tags(v)
                if v not in resource_names:
                    resource_names.append(v)

        # Resource description is stored in extras field
        # in "data.go.jp"
        for extra_kv in self.metadata.get('extras', []):
            if extra_kv.get('key') in ('description', 'resource_names'):
                v = extra_kv.get('value')
                if v:
                    v = strip_tags(v)
                    if v not in resource_names:
                        resource_names.append(v)

        if len(resource_names) > 0:
            description += '【リソース】{}'.format(
                ' / '.join(resource_names))

        tags = []
        for tag in self.metadata.get('tags', []):
            if isinstance(tag, str):
                tags.append(strip_tags(tag))
            elif isinstance(tag, dict) and 'name' in tag:
                tags.append(strip_tags(tag['name']))

        if len(tags) > 0:
            description += '【キーワード】{}'.format(
                ' / '.join(tags))

        return description


class ShirasagiMetadata(Metadata):
    """
    Shirasagi, a CKAN-like opendata system used in
      https://opendata.pref.aomori.lg.jp/dataset
    """

    @staticmethod
    def is_compatible(metadata):
        if 'uuid' not in metadata \
                or 'filename' not in metadata \
                or 'title' in metadata:
            return False

        return True

    def support_fq(self):
        return False

    def get_id(self):
        return self.metadata['uuid']

    def get_title(self):
        return self.metadata['name']

    def get_site_url(self):
        return self.metadata['filename']

    def get_last_updated(self):
        return self.get_max_value([
            super().reformat_date_field(self.metadata['created']),
            super().reformat_date_field(self.metadata['updated']),
            super().reformat_date_field(self.metadata['released'])
        ])

    def get_solr_metadata(self, site):
        return super().get_solr_metadata(site)

    def get_resources(self):
        if 'resources' in self.metadata:
            return self.metadata['resources']

        return []

    def get_description(self):
        """
        The description is contained in "text" field of the
        original metadata.

        Note
        ----
        "text" is not available in Solr because
        it is reserved for full-text indexing.
        """
        description = self.metadata.get('text') or ''
        description = strip_tags(description)

        resource_names = []
        for resource in self.metadata.get('resources', []):
            v = resource.get('name')
            if v:
                v = strip_tags(v)
                if v not in resource_names:
                    resource_names.append(v)

        if len(resource_names) > 0:
            description += '【リソース】{}'.format(
                ' / '.join(resource_names))

        tags = ' / '.join(
            [strip_tags(x) for x in self.metadata.get('tags', [])])
        if len(tags) > 0:
            description += '【キーワード】{}'.format(tags)

        return description


class MikawaMetadata(Metadata):
    """
    CKAN-like opendata system being used in
      https://opendata-east-mikawa.jp/

    `package_show` API returns an array of metadata.
    """

    @staticmethod
    def is_compatible(metadata):
        if not isinstance(metadata, list):
            return False

        if len(metadata) != 1:
            return False

        m = metadata[0]

        if 'id' not in m \
                or not isinstance(m['id'], str) \
                or 'name' not in m \
                or 'title' not in m \
                or 'filename' in m:
            return False

        return True

    def support_fq(self):
        return False

    def get_id(self):
        return self.metadata[0]['name']

    def get_title(self):
        return self.metadata[0]['title']

    def get_site_url(self):
        return 'node/' + self.metadata[0]['name']

    def __get_datetime(self, datetime_str):
        # "月, 03/27/2017 - 00:00"
        m = re.search(r'\d{2}/\d{2}/\d{4} - \d{2}:\d{2}',
                      datetime_str)
        # logger.debug("str:'{}', m:{}".format(datetime_str, m))

        if not m:
            return None

        try:
            dt = datetime.datetime.strptime(m.group(0), '%m/%d/%Y - %H:%M')
        except ValueError:
            return None

        res = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        # logger.debug("result: {}".format(res))
        return res

    def get_last_updated(self):
        return self.get_max_value([
            self.__get_datetime(self.metadata[0]['metadata_created']),
            self.__get_datetime(self.metadata[0]['metadata_modified'])
        ])

    def get_solr_metadata(self, site):
        metadata = self.metadata[0]
        return super().get_solr_metadata(site, metadata)

    def get_resources(self):
        if 'resources' in self.metadata[0]:
            return self.metadata[0]['resources']

        return []

    def get_description(self):
        metadata = self.metadata[0]
        description = metadata.get('notes') or ''
        description = strip_tags(description)

        resource_names = []
        for resource in metadata.get('resources', []):
            v = resource.get('description')
            if v:
                v = strip_tags(v)
                if v not in resource_names:
                    resource_names.append(v)

        if len(resource_names) > 0:
            description += '【リソース】{}'.format(
                ' / '.join(resource_names))

        tags = [strip_tags(tag.get('name'))
                for tag in metadata.get('tags', [])]
        if len(tags) > 0:
            description += '【キーワード】{}'.format(
                ' / '.join(tags))

        return description


class KagawaMetadata(Metadata):
    """
    CKAN-like opendata system being used in
      https://opendata.pref.kagawa.lg.jp/

    Note
    ----
    As of 2022-03-03, the metadata of the Tottori Prefecture
    Open Data Site is also determined to be ShirasagiMetadata.
    """

    @staticmethod
    def is_compatible(metadata):
        if 'uuid' in metadata \
                or 'filename' not in metadata \
                or 'title' not in metadata \
                or 'name' not in metadata:
            return False

        return True

    def support_fq(self):
        return False

    def get_id(self):
        return str(self.metadata['id'])

    def get_title(self):
        return self.metadata['title']

    def get_site_url(self):
        return self.metadata['filename']

    def get_last_updated(self):
        return self.get_max_value([
            self.metadata['metadata_created'],
            self.metadata['metadata_modified']
        ])

    def get_solr_metadata(self, site):
        return super().get_solr_metadata(site)

    def get_resources(self):
        if 'resources' in self.metadata:
            return self.metadata['resources']

        return []

    def get_description(self):
        """
        The description is contained in "text" field of the
        original metadata.

        Note
        ----
        "text" is not available in Solr because
        it is reserved for full-text indexing.
        """
        description = (self.metadata.get('text') or '') \
            + (self.metadata.get('notes') or '')
        description = strip_tags(description)

        resource_names = []
        for resource in self.metadata.get('resources', []):
            v = resource.get('name')
            if v:
                v = strip_tags(v)
                if v not in resource_names:
                    resource_names.append(v)

        if len(resource_names) > 0:
            description += '【リソース】{}'.format(
                ' / '.join(resource_names))

        tags = []
        for tag in self.metadata.get('tags', []):
            if isinstance(tag, dict):
                if 'display_name' in tag:
                    tags.append(tag['display_name'])
                elif 'name' in tag:
                    tags.append(tag['name'])
                elif 'title' in tag:
                    tags.append(tag['title'])
            elif isinstance(tag, str):
                tags.append(tag)
            else:
                msg = "Unexpected tags in {}({}) (skipped)"
                logger.warning(msg.format(
                    self.get_title(), self.get_id()))
                break

        tags = ' / '.join(tags)
        if len(tags) > 0:
            description += '【キーワード】{}'.format(tags)

        return description
