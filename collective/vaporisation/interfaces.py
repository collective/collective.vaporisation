# -*- coding: utf-8 -*-

from zope.schema import Int, List, Dict, Choice, Bool, Tuple, TextLine
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.interface import Interface
from zope.i18nmessageid import MessageFactory
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from plone.portlets.interfaces import IPortletDataProvider


_ = MessageFactory('collective.vaporisation')


class ITreeUpdateEvent( IObjectModifiedEvent ):
    """
    This triggers the rebuilding of the whole tree
    """

class ICustomizableCloud( IPortletDataProvider ):
    """
    Customizable parts of the cloud
    """
    # Customization
    name = TextLine(
        title=_(u"Name to display"),
        description=_(u"The name of the tagcloud. For display purposes."),
        required=True,
        default=u"Tagcloud"
        )
    
    steps = Int(
        title=_(u"Number of different sizes"),
        description=_(u"This number will also determine the biggest size."),
        required=True,
        default=10
        )

    limit = Int(
        title=_(u"Number of keywords to display"),
        description=_(u"Zero displays it all."),
        required=False,
        default=0
        )
    
    timeout = Int(title=_(u'Cloud reload timeout'),
        description=_(u'Time in minutes after which the cloud should be reloaded.'),
        required=True,
        default=100)
    
    startpath = Choice(title=_(u"Start path"),
                       description=_(u"Only the objects under this directory will be counted. If empty, the portlet will search in all the site."),
                       required=False,
                       source=SearchableTextSourceBinder({}, default_query='path:'))
    
    indexes_to_use = Tuple(
         title=_(u"Indexes to use"),
         description=_(u"Select from the list the indexes to use for the cloud"),
         default=('Subject',),
         value_type=Choice(vocabulary='collective.vaporisation.indexes'),
         required=True)
    
    type = Tuple(
        title=_(u"Type of contents"),
        description=_(u"Only the objects of this type will be counted."),
        value_type=Choice(vocabulary='collective.vaporisation.types'),
        required=False,
        )
    
    joint = Bool(
        default=False,
        required=True,
        title=_(u"Activate joint navigation"),
        description=_(u"Joint navigation puts keywords together"
                      u" for associative searches.")
        )
    
    white_list = Tuple(
        required=False,
        title=_(u"Use only the keywords of this list"),
        description=_(u"List of keywords to use in the cloud"),
        value_type=Choice(vocabulary='collective.vaporisation.keywords'),
        )

    restrict = Tuple(
        required=False,
        title=_(u"Remove from keywords list"),
        description=_(u"Restrict the cloud keywords by removing these keywords."
                      u"If there is something selected in the list over,"
                      u" the values of that list will be ignored."),
        value_type=Choice(vocabulary='collective.vaporisation.keywords'),
        )
    
    mode_to_use = Choice(
        title=_(u"Mode to use"),
        description=_(u'Select one of the possible mode to use the cloud'),
        vocabulary= 'collective.vaporisation.use_mode',
        required=True,
        default=('default',),
        )
    
    sort = Bool(
        default=True,
        required=False,
        title=_(u"Sort keywords"),
        description=_(u"If selected, the keywords will be sorted alphabetically.")
        )
    
class IVaporizedCloud(ICustomizableCloud):
    """
    A cloudy bunch of keywords
    """
    
    # storing the tags
    keywords = List(title=u"The list of keywords", default=[])
    all_keys = List(title=u"The list of all the keywords", default=[])
    tagsTree = Dict(title=u"The full tree of tags", default={})

    #informations about weights
    lowest  = Int(title=u"lowest weight", default=10)
    highest = Int(title=u"heighest weight", default=20)

    
class ISteamer(Interface):
    """
    The steamer releases the pression by letting the steam out.
    Here, the vaporisation is done !
    """

    def getStepForTag(self, tag):
        """
        This method will return a tuple that contains :
        - size of the tag to display, in %, for the template
        - The number of occurence of that tag
        The size of the tag is calculated into the inner function
        calculateTagSize, so it's easy to modify.
        If the occurence of the tags is even, they will all be displayed
        at 100%
        """
    
    def getTagsFromTree(self, keywords):
        """
        This method returns a list of dict.
        Each entry consits in a tag, with the keys :
        - name : the name of the keyword, the label
        - weight: the number of occurence of that keyword
        - size : the size in % of the tag to be displayed
        """

    def getConnectionsFor(self, keywords):
        """
        This is heart of the joint navigation.
        It returns a list of keywords.
        This list is computed from the connection keywords have
        between themselves.
        The joint navigation being cumulative, it sorts an eliminates
        keywords via an intersection.
        """

    def getVaporizedCloudFor(self, subjects=None):
        """
        This returns the keywords to display in the cloud.
        It takes in consideration the given list of keywords.
        """

    def updateWitnessWeights(self, value):
        """
        In order to calculate the sizes of the tags to be
        displayed, we have to keep track of the fatest and
        skinniest keywords.
        """

    def updateTree(self, keywords, index):
        """
        This is the main method to build the tags Tree.
        Although it is heavy duty done here, we do it only
        time to time. So, it's merciless.
        """

    def restrictTree(self):
        """
        This methods takes cares of removing the tags
        beyond the limit fixed by the user.
        To do so, it will build a complementary list
        that is the keywords, sorted by 'weight', the number
        of occurences. In order to sort the keywords, we need
        the already filled tree. It's not very optimal, but
        it is done only once.
        """
        
    def setTree(self):
        """
        Using the catalog, this method creates a blank tree.
        Taking care of keyword restrictions, it builds a full
        structure containing either the keywords and their
        properties, such as number of occurences.
        Keywords are stored as unicodes.
        """
 

class ICloudRenderer( Interface ):
    """
    The cloud renderer provides the methods to display the cloud.
    It will adapt the cloud with a steamer to gets the things out.
    """
    
    def Title(self):
        """
        Returns the name of a tagcloud
        """
    
    def update_tags_tree(self):
        """
        This is the restricted access for a manager to handle his cloud.
        It will simply trigger the private method of the vaporized cloud.
        Once refreshed, it will display a message, acknowledging the change.
        """

    def render(self):
        """
        default render method
        """
        
    def getVaporizedCloud(self):
        """
        This method return as list of dictionnaries.
        A dict contains :
        - name : the name of the tag. (unicode)
        - weight : the weight of the tag. (int)
        - size : the size of the font, for the HTML rendering. (int)
        """

    def isJointNavigation(self):
        """
        This method is a simple public accessor for the attribute 'joint' that
        defines a cloud with the joint navigation activated. It returns a bool.
        """

    def currentSubjects(self):
        """
        This method return the list of keywords actually selected.
        The result is an iterable sequence of unicodes.
        """

    def removableTags(self):        
        """
        This method return the list of keywords actually selected.
        The result is an iterable sequence of dictionaries :
        - name : the name of the tag. (unicode)
        - link : an http link that will be used in the template, for the tag.
        """

    def getStartPath(self):
        """
        This method return the complete start path
        """
    
    def getLinkPath(self):
        """
        This method calculates the link that will be used in the cloud HTML
        generation. It takes in consideration the currently selected keywords.
        This is an internal method. Never to be used outside the view itself.
        """
