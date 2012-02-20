from DateTime import DateTime

from zope.formlib import form
from zope.event import notify
from zope.interface import implements
from zope.component._api import getAdapter

from plone.memoize import ram
from plone.app.portlets.portlets import base
from plone.app.form.validators import null_validator

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from collective.vaporisation.interfaces import ISteamer, ICloudRenderer, IVaporizedCloud, ICustomizableCloud
from collective.vaporisation.events import TreeUpdateEvent
from collective.vaporisation import logger

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('collective.vaporisation')

from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget

from time import time


def _cloud_key(method, self):
    if not self.data.timeout:
        return time()
    timestamp = time() // (60 * self.data.timeout)
    user_id = self.context.portal_membership.getAuthenticatedMember().getId()
    if not user_id:
        user_id = 'anonymous' 
    params =  "%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s" % (self.data.name,
                                                self.data.steps,
                                                self.data.joint,
                                                self.data.limit,
                                                self.data.startpath,
                                                self.data.restrict,
                                                self.data.type,
                                                self.data.indexes_to_use,
                                                self.data.white_list,
                                                self.data.mode_to_use,
                                                self.request.QUERY_STRING,
                                                str(user_id),
                                                str(self.data.timeout),
                                                getToolByName(self.context, 'portal_url')())
    key = "%s:%s" % (timestamp,params)
    return str(hash(key))

class PseudoAssignment(object):
    implements(IVaporizedCloud)
pseudoassignment = PseudoAssignment()
    
class Assignment( base.Assignment ):
    """ The tagcloud itself """

    implements( IVaporizedCloud, ICustomizableCloud )

    # Tag storage
    keywords = list()
    all_keys = list()
    tagsTree = dict()

    # Weight
    highest  = 0
    lowest   = 0

    # Customization
    name     = u""
    steps    = 10
    joint    = True
    limit    = 0
    restrict = tuple()
    startpath = None
    type = tuple()
    indexes_to_use = ('Subject',)
    white_list = tuple()
    mode_to_use = ('default',)
    timeout = 100
    sort=True

    def __init__(self, name=u"", steps=10, joint=True, limit=0, restrict=(), startpath=None, type=tuple(), 
                 indexes_to_use=('Subject',),white_list=tuple(),mode_to_use=('default'),timeout=100,sort=True):
        self.name = name
        self.steps = steps
        self.joint = joint
        self.limit = limit
        self.restrict = restrict
        self.startpath = startpath
        self.type = type
        self.indexes_to_use = indexes_to_use
        self.white_list = white_list
        self.mode_to_use = mode_to_use
        self.timeout = timeout
        self.sort=True
    
    @property
    def title(self):
        """ The title property for the menus. """
        return self.name

class Renderer( base.Renderer ):
    """ Renders a tag cloud """

    implements( ICloudRenderer )
    
    _template = ViewPageTemplateFile('cloud.pt')

    def __init__(self, context, request, view, manager, data):
        super(Renderer, self).__init__(context, request, view, manager, data)
        self.subjects = None
        putils = getToolByName(context, 'plone_utils')
        self.encoding = putils.getSiteEncoding()
        self.purl = getToolByName(context, 'portal_url')()

    def generatedId(self):
        """get a unique portlet id, base on the portlet context"""
        context = self.context
        putils = getToolByName(context, 'plone_utils')
        return putils.normalizeString(self.data.title)

    def Title(self):
        return self.data.name
    
    @ram.cache(_cloud_key)
    def render(self):
        adapter = getAdapter(self.data, ISteamer,self.data.mode_to_use)
        adapter.setTree()
        if self.data.timeout:
            logger.info('Tagcloud "%s" has been updated (%s)'
                        % (self.data.name, DateTime()))
        return self._template()

    def isJointNavigation(self):
        return self.data.joint


    def currentTags(self):
        self.subjects = list()
        portlet = self.request.form.get('portlet', None)
        if portlet == self.data.__name__:
            subjects = self.request.form.get('tags', None)
            if subjects:
    
                if isinstance(subjects, str):
                    subjects = (subjects,)
                
                encoding = self.encoding
                self.subjects = [unicode(k, encoding)
                                 for k in subjects]
        return self.subjects

    
    def getVaporizedCloud(self):
        subjects = (self.subjects is not None
                    and self.subjects
                    or self.currentTags())
        adapter = getAdapter(self.data, ISteamer,self.data.mode_to_use)
        tags=adapter.getVaporizedCloudFor(subjects)
        if self.data.sort:
            tags.sort(lambda x,y:cmp(x.get('name').lower(),y.get('name').lower()))
        return tags


    def removableTags(self):  
        tags = (self.subjects is not None and self.subjects
                or self.currentTags())
        
        if not tags:
            return None

        if len(tags) == 1:
            return (dict(name=tags.pop(),
                         link=self.context.absolute_url()),)
            
        search_path = self.getStartPath()
        removable = list()

        for tag in tags:
            base_url  = 'cloud_search?portlet=%s&path=%s' % (self.data.__name__,search_path)
            query     = '%s/%s' % (self.context.absolute_url(), base_url)
            tag_url   = '&tags:list=%s'
            tags_url = ''.join([tag_url % k 
                                 for k in tags 
                                 if k != tag])
            index_url = '&%s:list=%s'
            indexes_url = ''
            for t in tags:
                if t != tag:
                    k_indexes = self.data.tagsTree[t]['index']
                    indexes_url = indexes_url + ''.join([index_url % (t,k)
                                                         for k in k_indexes])
            removable.append(
                dict(name=tag,
                     link="%s%s%s" % (query, tags_url, indexes_url))
                )
        return removable
    
    def getStartPath(self):
        root_path= ('/').join(self.context.portal_url.getPortalObject().getPhysicalPath())
        if self.data.startpath:
            return root_path+self.data.startpath
        else:
            return root_path
    
    def getLinkPath(self, tag):
        search_path = self.getStartPath()
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        link = "%s/cloud_search" % portal.absolute_url()
        portlet = self.request.form.get('portlet', None)
        query = self.request['QUERY_STRING']
        if query and portlet == self.data.__name__:
            link = "%s?%s" % (link,query)
        else:
            link = "%s?portlet=%s&path=%s" % (link,self.data.__name__,search_path)
        if tag['index']:
            index_url = "&%s:list=%s"
            indexes_url = "".join([index_url % (tag['name'], index) for index in tag['index']])
            link = "%s&tags:list=%s%s" % (link, tag['name'], indexes_url)
        return link


class AddForm( base.AddForm ):
    """ This is the tagcloud add form, rendering the customizable fields """

    def create(self, data):
        cloud = Assignment(**data)
        notify(TreeUpdateEvent(cloud.__of__(self.context)))
        return cloud

    # The form fields
    form_fields = form.Fields( ICustomizableCloud )
    form_fields['startpath'].custom_widget = UberSelectionWidget
    
    
class EditForm( base.EditForm ):
    """ A not-so-basic edit form with an update action """

    def redirectFromForm( self ):
        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''

    
    @form.action(_(u"Save"), condition=form.haveInputWidgets, name=u'save')
    def handle_save_action(self, action, data):
        if form.applyChanges(self.context,
                             self.form_fields,
                             data,
                             self.adapters):
            self.status = _(u"Changes saved and tagcloud updated.")
        else:
            self.status = _(u"No changes.")
        return self.redirectFromForm()


    @form.action(_(u"Cancel"), validator=null_validator, name=u'cancel')
    def handle_cancel_action(self, action, data):
        return self.redirectFromForm()


    # The fields
    form_fields = form.Fields( ICustomizableCloud )
    form_fields['startpath'].custom_widget = UberSelectionWidget
