#!python3

# see: https://lucene.apache.org/solr/guide/8_5/the-standard-query-parser.html

import pysolr

solr = pysolr.Solr(
    'http://localhost:8001/solr/ckan-xsearch/', always_commit=True)
solr.ping()

# results = solr.search('banana')
results = solr.search(
    "消費",
    **{"rows": 0, "debug": "true", "facet": "on", "facet.field": "xckan_ckan_url"}
)

print(results.facets)
