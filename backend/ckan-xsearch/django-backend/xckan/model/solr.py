import datetime
from logging import getLogger

import simplejson as json
import pysolr

from xckan.siteconf import site_config
from .site import Site

logger = getLogger(__name__)


class SolrManager(object):

    def __init__(self, endpoint=None):
        # Number of documents to be kept before indexed in Solr
        self.buffer_size = 128
        self.docs = None
        self.clear_buffer()
        self.solr = None

    def __get_solr(self):
        """
        Get running-solr endpoint from the nodes.
        """
        if self.solr and self.solr.ping():
            return self.solr

        endpoints = site_config.SOLR_CKAN_XSEARCH.split(',')
        if len(endpoints) == 1:
            # Stand-alone, always use this node
            self.solr = pysolr.Solr(endpoints[0], always_commit=True)
            return self.solr
        else:
            # SolrCloud
            for endpoint in endpoints:
                solr = pysolr.Solr(endpoint, always_commit=True)
                try:
                    solr.ping()
                    self.solr = solr
                    return self.solr
                except pysolr.SolrError:
                    pass

            raise pysolr.SolrError("No endpoint responded.")

    def __del__(self):
        # Flash buffer before destroy the object.
        self.flash_buffer()

    def search(self, **kwargs):
        """
        Search by kwargs.
        """
        try:
            result = self.__get_solr().search(**kwargs)
            return result
        except pysolr.SolrError as e:
            logger.error(str(e))
            return False

    def clear_buffer(self):
        """
        Clear document buffer.
        """
        self.docs = {}

    def add_document(self, doc):
        """
        Add formatted document to the buffer.
        """
        if 'id' not in doc:
            raise RuntimeError("'id' is required.")

        if 'xckan_last_updated' not in doc or \
           doc['xckan_last_updated'] is None:
            logger.warning((
                "Missing required parameter 'xckan_last_updated' "
                "in {}, set to current time.".format(doc['id'])))
            doc['xckan_last_updated'] = datetime.datetime.now().strftime(
                '%Y-%m-%dT%H:%M:%SZ')

        self.docs[doc['id']] = doc

        # Flash buffer when the documents overflowed
        if len(self.docs) >= self.buffer_size:
            self.flash_buffer()

    def delete_document(self, doc_id):
        """
        Delete document from the index
        'doc_id' is specified by the solr indexed id (not package_id)
        If the doc_id is a list, delete documents in the list.
        """
        if doc_id is None:
            return

        if isinstance(doc_id, str):
            doc_id = [doc_id]

        if isinstance(doc_id, list) and len(doc_id) == 0:
            return

        escaped_doc_id = [i.replace(':', r'\:') for i in doc_id]

        for i in range(0, len(escaped_doc_id), 16):
            qstr = 'id:(' + ' OR '.join(escaped_doc_id[i:i + 16]) + ')'
            self.__get_solr().delete(q=qstr, commit=True)

    def flash_buffer(self):
        length = len(self.docs)

        if length == 0:
            return False

        logger.debug("buffer length = {}".format(length))

        # Prepare id list of obsoleted documents
        logger.debug("Updating documents id={}".format(
            json.dumps(list(self.docs.keys()))))

        try:
            # self.delete_document(obs_doc_id_list)
            self.__get_solr().add(list(self.docs.values()), commit=True)
        except pysolr.SolrError as e:
            # logger.error(json.dumps(
            #     self.docs, indent=2, ensure_ascii=False))
            logger.error(e)

        self.clear_buffer()

    def get_document(self, doc_id):
        results = self.__get_solr().search(q=f"id:\"{doc_id}\"")
        for result in results:
            return result

        return False

    def delete_site(self, site: Site):
        self.__get_solr().delete(
            q='id:' + site.get_site_id().replace(':', r'\:') + '*',
            commit=True
        )

    def delete_all(self):
        self.__get_solr().delete(q=r'id:*\:*', commit=True)
