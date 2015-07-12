# encoding: utf-8

u'''EDRN LabCAS: a "LabCAS".'''

from edrn.labcas.ui import MESSAGE_FACTORY as _
from plone.supermodel import model
from zope import schema
from five import grok
from zope.lifecycleevent.interfaces import IObjectAddedEvent
import plone.api, os, os.path


class ILabCAS(model.Schema):
    u'''A "LabCAS".'''
    title = schema.TextLine(
        title=_(u'Name'),
        description=_(u'The name of this LabCAS instance.'),
        required=True,
    )
    description = schema.Text(
        title=_(u'Description'),
        description=_(u'A short summary of this LabCAS instance.'),
        required=False,
    )
    dataDeliveryURL = schema.TextLine(
        title=_(u'Data Delivery URL'),
        description=_(u"URL to the CAS Product Server's data delivery endpoint."),
        required=True,
    )
    solrURL = schema.TextLine(
        title=_(u'SOLR URL'),
        description=_(u'URL to the SOLR search endpoint.'),
        required=True,
    )
    curatorServiceURL = schema.TextLine(
        title=_(u'Curator Service URL'),
        description=_(u'URL to the curator services endpoint.'),
        required=True,
    )
    curatorServiceUsername = schema.TextLine(
        title=_(u'Curator Username'),
        description=_(u'Username to access the curator services endpoint.'),
        required=True,
    )
    curatorServicePassword = schema.TextLine(
        title=_(u'Curator Password'),
        description=_(u'Credential to authenticate the curator services username.'),
        required=True,
    )
    stagingDir = schema.TextLine(
        title=_(u'Staging Directory'),
        description=_(u'Server-side directory where uploaded data files are staged.'),
        required=True,
    )


@grok.subscribe(ILabCAS, IObjectAddedEvent)
def createStagingDir(obj, event):
    if not ILabCAS.providedBy(obj): return
    factory = plone.api.portal.get_tool('portal_factory')
    if factory.isTemporary(obj): return
    if not os.path.isdir(obj.stagingDir):
        os.makedirs(obj.stagingDir)

