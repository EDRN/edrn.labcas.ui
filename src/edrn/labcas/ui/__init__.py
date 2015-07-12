# encoding: utf-8

u'''EDRN LabCAS — user interface.'''

from zope.i18nmessageid import MessageFactory

PACKAGE_NAME = __name__
MESSAGE_FACTORY = MessageFactory(PACKAGE_NAME)
DEFAULT_PROFILE = u'profile-' + PACKAGE_NAME + ':default'
