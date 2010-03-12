
from Products.Five import BrowserView

from Products.CMFCore.utils import getToolByName

class CloudSearch(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def cloudQueryCatalog(self,use_types_blacklist,use_navigation_root):
        base_query = {}
        results = []
        path = self.request.get('path')
        if path:
            base_query['path'] = path
        tags = self.request.get('tags', None)
        if not tags:
            self.request.set('sort_on','modified')
            self.request.set('sort_order','reverse')
            return self.context.queryCatalog(self.request,use_types_blacklist=use_types_blacklist, use_navigation_root=use_navigation_root)
        for tag in tags:
            indexes = self.request.get(tag,[])
            result = []
            for index in indexes:
                spec_query = base_query.copy()
                spec_query[index] = {'query':tag,
                                     'operator':'and'}
                result.extend(self.context.queryCatalog(spec_query,use_types_blacklist=use_types_blacklist, use_navigation_root=use_navigation_root))
            if results:
                results_uid = [brain.UID for brain in results]
                results = [brain 
                           for brain in result 
                           if brain.UID in results_uid]
            else:
                results = result
        uids = []
        unique_results = []
        for result in results:
            if result.UID not in uids:
                unique_results.append(result)
                uids.append(result.UID)
        unique_results.sort(key=lambda x: x.modified, reverse=True)
        return unique_results
  