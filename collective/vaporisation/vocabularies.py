# -*- coding: utf-8 -*-

try:
    from zope.app.schema.vocabulary import IVocabularyFactory
except ImportError:
    # Plone 4.1
    from zope.schema.interfaces import IVocabularyFactory

from zope.interface.declarations import directlyProvides, implements
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from Products.CMFCore.utils import getToolByName
from zope.schema.interfaces import ITokenizedTerm, ITitledTokenizedTerm
from zope.component._api import getAdapters
from interfaces import ISteamer
from collective.vaporisation.portlets import pseudoassignment


class KeywordTerm(object):
    """Simple tokenized keyword used by SimpleVocabulary."""
    
    implements(ITokenizedTerm)
    
    def __init__(self, value):
        """Create a term from the single value
        This class prevents the use of the silly bugged SimpleTerm.
        """
        self.value = value
        self.token = value            
        self.title = value
        directlyProvides(self, ITitledTokenizedTerm)


class KeywordVocabulary(object):
    """Vocabulary factory for keywords of a cloud.
    """
    implements( IVocabularyFactory )
    
    def __call__(self, context):
        catalog = getToolByName(context, 'portal_catalog')
        putils   = getToolByName(context, 'plone_utils')
        encoding = putils.getSiteEncoding()
        subjects = []
        
        if hasattr(context, 'indexes_to_use'):
            indexes_to_use = context.indexes_to_use
        else:
            indexes_to_use = ['Subject']
            
        if hasattr(context, 'startpath'):
            root_path= ('/').join(context.portal_url.getPortalObject().getPhysicalPath())
            if context.startpath:
                search_path= root_path + context.startpath
            else:
                search_path= root_path
            if hasattr(context, 'type') and context.type:
                for index in indexes_to_use:
                     subjects = subjects + [x for x
                                           in catalog.uniqueValuesFor(index) 
                                           if catalog.searchResults({'path':search_path,'portal_type':context.type,index:x})]
            else:     
                for index in indexes_to_use:
                    subjects = subjects + [x for x 
                                          in catalog.uniqueValuesFor(index) 
                                          if catalog.searchResults({'path':search_path,index:x})]
        else:
            if hasattr(context, 'type') and context.type:
                for index in indexes_to_use:
                    subjects = subjects + [x for x
                            in catalog.uniqueValuesFor(index) 
                            if catalog.searchResults({'portal_type':context.type,index:x})]
            else:
                for index in indexes_to_use:
                    subjects = subjects + [x for x in catalog.uniqueValuesFor(index)]
        
        keywords = set([unicode(k, encoding) for k in subjects])        
        terms = [KeywordTerm(k) for k in sorted(keywords)]
        return SimpleVocabulary(terms)

KeywordVocabularyFactory = KeywordVocabulary()


class TypesVocabulary(object):
    """Vocabulary factory for types of a cloud.
    """
    implements( IVocabularyFactory )

    def __call__(self, context):
        portal_types = getToolByName(context, 'portal_types')
        portal_properties = getToolByName(context, 'portal_properties')
        metaTypesNotToList = portal_properties.navtree_properties.metaTypesNotToList
        types = [ x for x
                 in portal_types.keys()
                 if x not in metaTypesNotToList]
        terms = [SimpleTerm(type,type) for type in types]
        return SimpleVocabulary(terms)

TypesVocabularyFactory = TypesVocabulary()

class IndexesVocabulary(object):
    """Vocabulary factory for indexes of a cloud.
    """
    implements( IVocabularyFactory )

    def __call__(self, context):
        pc = context.portal_catalog
        remove_indexes = ['allowedRolesAndUsers','getRawRelatedItems','object_provides']
        indexes = [x for x in pc.indexes() 
                   if pc._catalog.indexes[x].meta_type=='KeywordIndex' 
                   and not x in remove_indexes]
        terms = [SimpleTerm(index,index) for index in indexes]
        return SimpleVocabulary(terms)

IndexesVocabularyFactory = IndexesVocabulary()

class ModeVocabulary(object):
    """Vocabulary factory for mode to use of a cloud.
    """
    implements( IVocabularyFactory )

    def __call__(self, context):
        encoders = [encoder[0] 
                    for encoder 
                    in getAdapters((pseudoassignment,), ISteamer)]
        terms = [SimpleTerm(encoder,encoder) for encoder in encoders]
        return SimpleVocabulary(terms)

ModeVocabularyFactory = ModeVocabulary()

