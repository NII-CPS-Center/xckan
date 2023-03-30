import json
from logging import getLogger

import pysolr

from xckan.siteconf import site_config

logger = getLogger(__name__)


class Api(object):
    # see: https://lucene.apache.org/solr/guide/8_5/the-standard-query-parser.html

    def __init__(self):
        self.endpoint = site_config.SOLR_CKAN_XSEARCH
        self.solr = None

    def __solr_to_ckan(self, results):
        """
        Convert Solr search results to ckan metadata list.
        """
        datasets = []
        for x in results:
            x0 = {
                'xckan_id': x.get('id', ''),
                'xckan_title': x.get('xckan_title', ''),
                'xckan_site_name': x.get('xckan_site_name', ''),
                'xckan_site_url': x.get('xckan_site_url', ''),
                'xckan_last_updated': x.get(
                    'xckan_last_updated', '2000-01-01T00:00:00Z'),
                'xckan_description': x.get('xckan_description', ''),
            }
            if not isinstance(x['data_dict'], str):
                x['data_dict'] = x['data_dict'][0]

            x1 = json.loads(x['data_dict'])
            if isinstance(x1, list):
                if len(x1) == 1:
                    x1 = x1[0]
                else:
                    x1 = None

            if x1 is None:
                xx = x0
            else:
                xx = dict(x0, **x1)

            if 'score' in x:
                xx['score'] = x['score']

            datasets.append(xx)

        return datasets

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

    def __get_first_args(self, args: dict):
        """
        Keep only the first one of the values corresponding to
        each parameter.

        Parameters
        ----------
        args: dict
            A dictionary object whose keys are parameter names
            and whose values are a list of corresponding values.

        Return
        ------
        dict
            A dictionary object whose keys are parameter names
            and whose values are the first value of corresponding
            values.
        """
        new_args = {}
        for key, values in args.items():
            if isinstance(values, list):
                new_args[key] = values[0]
            else:
                new_args[key] = values

        return new_args

    def package_list(self, **kwargs):
        """
        Return list of all packages.
        'fq' parameter can be used to filter packages.
        """
        args = self.__get_first_args(kwargs)
        start = args.get('start', args.get('offset', 0))
        rows = args.get('rows', args.get('limit', 9999999))
        if 'fq' in args:
            fq = args.get('fq')
        else:
            fq = "*:*"

        results = self.__get_solr().search(
            q="*:*", fl="id", start=start, rows=rows, fq=fq
        )

        id_list = list(map(lambda x: x['id'], results))
        return id_list

    def package_show(self, **kwargs):
        """
        Return all information of the package specified by the 'id' param.
        """
        args = self.__get_first_args(kwargs)
        id = args.get('id', None)
        if id is None:
            raise RuntimeError("'id' is required")

        results = self.__get_solr().search(
            q=f"id:\"{id}\""
        )

        datasets = self.__solr_to_ckan(results)
        if len(datasets) > 0:
            dataset = datasets[0]
        else:
            raise RuntimeError("Not found")

        return dataset

    def package_search(self, **kwargs):
        """
        Search packages using the specified parameters.
        """
        args = self.__get_first_args(kwargs)
        results = self.__get_solr().search(
            args.get('q', '*:*'),
            **{
                "fq": args.get('fq', '*:*'),
                "fl": "* score",
                "start": args.get('start', "0"),
                "rows": args.get('rows', "10"),
                "sort": args.get('sort', "score desc"),
                "facet": "on",
                "facet.field": [
                    "xckan_site_name",
                    "organization",
                    "res_format",
                    "xckan_tags",
                    "tags",
                    "groups"
                ],
                "facet.mincount": 1
            }
        )
        logger.warning(results)
        datasets = self.__solr_to_ckan(results)

        return {
            "q": kwargs,
            "count": results.hits,
            "facets": results.facets,
            "qtime": results.qtime,
            "results": datasets
        }

    def site_statistics(self, nres=None, **kwargs):
        """
        Return site statistics.

        Parameters
        ----------
        nres: Any
            if nres is set, count resources in each sites.
        """
        results = self.__get_solr().search('*:*', **{
            "facet": "on",
            "facet.field": ["xckan_site_name"],
            "facet.mincount": 1,
            "rows": 0
        })
        resp = results.raw_response

        stats = {}

        # Get number of documents
        stats['ndocs'] = resp['response']['numFound']

        # Get sites and ndocs
        site_list = resp['facet_counts']['facet_fields']['xckan_site_name']
        sites = {}
        for i in range(0, len(site_list), 2):
            sites[site_list[i]] = {
                "ndocs": site_list[i + 1],
            }

        stats['nsites'] = len(sites)
        stats['sites'] = sites

        if nres is None:
            return stats

        # Generate resource list
        start = 0
        rows = 128
        nres = 0
        while start < stats['ndocs']:
            results = self.__get_solr().search('*:*', **{
                "fl": "xckan_site_name,resources.id",
                "start": start,
                "rows": 100
            })
            for result in results:
                if 'resources.id' not in result:
                    n = 1  # print(result, file=sys.stderr)
                else:
                    n = len(result['resources.id'])

                nres += n
                site_name = result['xckan_site_name']
                if 'nresources' not in sites[site_name]:
                    sites[site_name]['nresources'] = 0

                sites[site_name]['nresources'] += n

            start += rows

        stats['nresources'] = nres

        return stats


api = Api()

if __name__ == '__main__':
    print(api.site_statistics())
    print(api.package_search(q="消費", rows=0))
    pass
