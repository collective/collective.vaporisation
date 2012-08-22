# -*- coding: utf-8 -*-

from Products.CMFPlone.PloneBatch import Batch
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.search.browser import Search as SearchView


class CloudSearch(SearchView):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def cloudQueryCatalog(self, use_types_blacklist=False, use_navigation_root=False,\
                          batch=True, b_size=10, b_start=0):
        results = []

        base_query = self.request.form.copy()
        base_query['use_types_blacklist'] = use_types_blacklist
        base_query['use_navigation_root'] = use_navigation_root
        if batch:
            base_query['b_start'] = b_start = int(b_start)
            base_query['b_size'] = b_size

        tags = base_query.get('tags', None)
        if not tags:
            results = self.context.queryCatalog(base_query)
        else:
            for tag in tags:
                indexes = base_query.get(tag, [])
                result = []
                for index in indexes:
                    spec_query = base_query.copy()
                    spec_query[index] = {'query': tag,
                                         'operator': 'and'}
                    result.extend(self.context.queryCatalog(spec_query))
                if results:
                    results_uid = [brain.UID for brain in results]
                    results = [brain
                               for brain in result
                               if brain.UID in results_uid]
                else:
                    results = result
                results = self.clearResults(results)

        results.sort(key=lambda x: x.modified, reverse=True)
        results = IContentListing(results)
        if batch:
            results = Batch(results, b_size, b_start)
        return results

    def clearResults(self, results):
        uids = []
        unique_results = []
        for result in results:
            if result.UID not in uids:
                unique_results.append(result)
                uids.append(result.UID)
        return unique_results
