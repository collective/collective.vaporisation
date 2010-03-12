# -*- coding: utf-8 -*-
from DateTime import DateTime
from zope.interface import implements
from zope.lifecycleevent import ObjectModifiedEvent
from interfaces import ITreeUpdateEvent, ISteamer
from collective.vaporisation import logger
from zope.component._api import getAdapter


class TreeUpdateEvent( ObjectModifiedEvent ):
    """ We need to rebuild the tree from here
    """
    implements( ITreeUpdateEvent )


def UpdateTreeOnCloudChanges( obj, event ):
    adapter = getAdapter(obj, ISteamer,obj.mode_to_use)
    adapter.setTree()
    logger.info('Tagcloud "%s" has been updated (%s)'
                % (obj.name, DateTime()))
