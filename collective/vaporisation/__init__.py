"""Main product initializer
"""

from zope.i18nmessageid import MessageFactory
from collective.vaporisation import config

from Products.Archetypes import atapi
from Products.CMFCore import utils
from Products.CMFCore.permissions import setDefaultRoles

import logging

# Define a message factory for when this product is internationalised.
# This will be imported with the special name "_" in most modules. Strings
# like _(u"message") will then be extracted by i18n tools for translation.
logger = logging.getLogger('collective.vaporisation')
vaporisationMessageFactory = MessageFactory('collective.vaporisation')

