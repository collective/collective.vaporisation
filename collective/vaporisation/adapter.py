"""
Adapters for the tagcloud
"""

# -*- coding: utf-8 -*-
from random import shuffle
from zope.component import adapts, getSiteManager
from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from interfaces import ISteamer, IVaporizedCloud


class Steamer(object):

    adapts(IVaporizedCloud)
    implements(ISteamer)

    def __init__(self, context):
        self.context = context

    def getStepForTag(self, tag):
        """ Only used for display purposes """

        def calculateTagSize(step):
            return int(100 + step * 10)

        occurence = self.context.tagsTree[tag]['weight']

        if self.context.lowest == self.context.highest:
            return 100, occurence

        lowest = float(self.context.lowest)
        highest = float(self.context.highest)

        step = ((float(occurence) - lowest) /
                (highest - lowest) *
                self.context.steps)

        return calculateTagSize(step), occurence

    def getTagsFromTree(self, keywords):
        """ Returns a list of dicts with the needed infos """
        
        tags = list()
        
        for keyword in keywords:
            if keyword in self.context.tagsTree:
                size, weight = self.getStepForTag(keyword)
                index = self.context.tagsTree[keyword]['index']
                tags.append(dict(name=keyword,
                                 weight=weight,
                                 size=size,
                                 index=index))
        return tags


    def getConnectionsFor(self, keywords):
        """ Will retrieve the related keywords of the given keyword """
        
        tags = None
        for keyword in keywords:            
            if keyword in self.context.tagsTree:
                tag = self.context.tagsTree[keyword]
                if tags is None:
                    tags = set(tag['connections'])
                else:
                    tags = tags.intersection(set(tag['connections']))

        if tags is None:
            return list()

        return self.getTagsFromTree(tuple(tags))


    def getVaporizedCloudFor(self, subjects=None):
        """ Returns the available clouds and relatives """
        if not self.context.joint or not subjects:
            return self.getTagsFromTree(self.context.keywords)

        return self.getConnectionsFor(subjects)


    def updateWitnessWeights(self, value):
        """ Witnesses are just used as weight for fonts """
        
        if value > self.context.highest:
            self.context.highest = value
        if value < self.context.lowest:
            self.context.lowest = value


    def updateTree(self, index, keywords):
        """ Triggered on the update """
        
        tags = self.context.tagsTree
        for keyword in keywords:
            if keyword in self.context.tagsTree:
#                self.context.tagsTree[keyword]['weight'] += 1
                addition = [k for k in keywords
                            if k != keyword and
                            k not in self.context.tagsTree[keyword]['connections']]
                self.context.tagsTree[keyword]['connections'].extend(addition)
                if index not in self.context.tagsTree[keyword]['index']:
                    self.context.tagsTree[keyword]['index'].append(index)

            else:
                tag = dict(weight = 1,
                           connections = [k for k in keywords if k != keyword],
                           index = [index])
                self.context.tagsTree[keyword] = tag

#            self.updateWitnessWeights(self.context.tagsTree[keyword]['weight'])
        self.context.tagsTree = tags


    def restrictTree(self):
        """ Will return a shuffled result """

        def sort_by_weight(key1, key2):
            return cmp(self.context.tagsTree[key2]['weight'],
                       self.context.tagsTree[key1]['weight'])

        keywords = self.context.tagsTree.keys()
        keywords.sort(sort_by_weight)

        if self.context.limit:
            keywords = keywords[:self.context.limit]

        for toDelete in self.context.tagsTree.keys():
            if toDelete not in keywords:
                del self.context.tagsTree[toDelete]
        
        self.context.keywords = keywords
        shuffle(self.context.keywords)


    def setTree(self):
        """ Initialize the cloud """
        catalog = getToolByName(self.context, 'portal_catalog')
        putils = getToolByName(self.context, 'plone_utils')
        portalurl = getToolByName(self.context, 'portal_url')
        encoding = putils.getSiteEncoding()

        self.context.tagsTree = dict()
        weights = {}
        root_path= ('/').join(portalurl.getPortalObject().getPhysicalPath())
        
        if self.context.data.startpath:
            search_path= root_path+self.context.data.startpath
        else:
            search_path= root_path
        # First, we get all the keywords used in our portal
        # Then we transform the keywords into unicode objects
        # And we keep an untouched list of keywords (for the form vocabulary)
        for index in self.context.indexes_to_use:
            control_query={'path':search_path}
            if self.context.type:
                control_query['portal_type']=self.context.type
                
            subjects = [x for x 
                        in catalog.uniqueValuesFor(index) 
                        if catalog.searchResults(index=x, **control_query)]
            
            self.context.all_keys = [unicode(k, encoding) for k in subjects]
            self.context.all_keys.sort()
            self.context.keywords = [k for k in self.context.all_keys]
        
            # Now, taking care of the restricted keywords, we build
            # a restricted list and query all the objects using them,
            # via the portal catalog.
            if self.context.white_list:
                keywords = [k.encode(encoding) for k in self.context.keywords
                            if k in self.context.white_list]
            else:
                keywords = [k.encode(encoding) for k in self.context.keywords
                                if k not in self.context.restrict]
            objects  = catalog({'path':search_path, index:keywords})
            keywords = set(keywords)
            # Using the main method, we build the references between the tags.
            # We build a list of tags for each objects, verifying the restriction.
            if index in catalog._catalog.names:
                for obj in objects:
                    obj_keywords = getattr(obj, index, None)
                    if callable(obj_keywords):
                        obj_keywords=obj_keywords()
                    allowed_keywords=set(obj_keywords).intersection(keywords)
                    allowed_keywords=[unicode(k, encoding) for k in allowed_keywords]
                    obj_uid = obj.UID
                    if callable(obj_uid):
                        obj_uid = obj_uid()
                    for k in allowed_keywords:
                        if k in weights.keys():
                            if not obj_uid in weights[k]:
                                weights[k].append(obj_uid)
                        else:
                            weights[k] = [obj_uid,]
                    self.updateTree(index,allowed_keywords)
            else:
                index_sources = catalog._catalog.indexes[index].getIndexSourceNames()
                for index_source in index_sources:
                    for obj in objects:
                        obj = obj.getObject()
                        obj_keywords = getattr(obj, index_source, None)
                        if callable(obj_keywords):
                            obj_keywords=obj_keywords()
                        allowed_keywords=set(obj_keywords).intersection(keywords)
                        allowed_keywords=[unicode(k, encoding) for k in allowed_keywords]
                        obj_uid = obj.UID
                        if callable(obj_uid):
                            obj_uid = obj_uid()
                        for k in allowed_keywords:
                            if k in weights.keys():
                                if not obj_uid in weights[k]:
                                    weights[k].append(obj_uid)
                            else:
                                weights[k] = [obj_uid,]
                        self.updateTree(index,allowed_keywords)
        self.updateWeightsTree(weights)
        self.restrictTree()
        
    def updateWeightsTree(self,weights):
        """
        Update the Tagcloud Tree with the weights
        """
        for k in weights:
            self.context.tagsTree[k]['weight'] = len(weights[k])
            self.updateWitnessWeights(self.context.tagsTree[k]['weight'])
                     
            
    def _generateCloudRelationSet(self, tags):
        """Generate a set of relations for a set of tags.
        This means: all tags used in contents that behave all given tags.
        Results tags always exclude given tags
        @return: a python set of tags in relations, or an empty set
        """
        context = self.context
        catalog = getToolByName(context, 'portal_catalog')
        root_path= ('/').join(self.context.context.portal_url.getPortalObject().getPhysicalPath())
        
        if self.context.data.startpath:
            search_path= root_path+self.context.data.startpath
        else:
            search_path= root_path
            
        results = catalog(Subject={'query':[x.encode('utf8') for x in tags], 'operator':'and'},
                          path=search_path)
        resTags = []
        for x in results:
            subjects=[y.decode('utf8') for y in x.Subject]
            resTags.extend(subjects)
        return set(resTags)-set(tags)
    