# encoding: utf-8

u'''EDRN LabCAS: a dataset.'''

from Acquisition import aq_inner
from edrn.labcas.ui import MESSAGE_FACTORY as _
from five import grok
from lxml import etree
from plone.memoize.instance import memoize
from plone.supermodel import model
from zope import schema
from zope.lifecycleevent.interfaces import IObjectAddedEvent
import os, os.path, plone.api, urlparse

_namespaceURL = u'http://oodt.jpl.nasa.gov/1.0/cas'
_namespacePrefix = u'{' + _namespaceURL + u'}'
_namespaceMap = {None: _namespaceURL}


class IDataset(model.Schema):
    u'''A dataset.'''
    title = schema.TextLine(
        title=_(u'Dataset Name'),
        description=_(u'Specify a name for this dataset.'),
        required=True,
    )
    description = schema.Text(
        title=_(u'Abstract'),
        description=_(u'A short summary of this dataset.'),
        required=False,
    )
    datasetDate = schema.Date(
        title=_(u'Dataset Date'),
        description=_(u'The date this dataset was generated.'),
        required=True,
    )
    leadPI = schema.TextLine(
        title=_(u'Lead PI'),
        description=_(u'Name of the principal investigator overseeing this experiment.'),
        required=True,
    )
    specimenType = schema.TextLine(
        title=_(u'Specimen Type'),
        description=_(u'Enter the type of specimen.'),
        required=True,
    )
    accessControl = schema.TextLine(
        title=_(u'Access Control'),
        description=_(u'Enter the group that is allowed to interact with this data.'),
        required=True,
    )


class View(grok.View):
    u'''View for a dataset'''
    grok.context(IDataset)
    grok.require('zope2.View')
    def uploadURL(self):
        context = aq_inner(self.context)
        url = context.absolute_url()
        path = urlparse.urlparse(url).path + u'/@@upload'
        return u'var edrnUploadURL = "{}";'.format(path)
    def numFiles(self):
        return len(self.currentFiles())
    @memoize
    def currentFiles(self):
        context = aq_inner(self.context)
        baseURL = context.absolute_url() + u'/@@retrieve?name='
        # d = context.filesystemPath + u'/' + unicode(context.id)
        # if not os.path.exists(d):
        #     os.makedirs(d)
        # entries = os.listdir(d)
        # entries.sort()
        files = []
        # for entry in entries:
        #     path = os.path.join(d, entry)
        #     if os.path.isfile(path):
        #         mtime = datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        #         url = baseURL + urllib.quote(entry)
        #         files.append(dict(name=entry, size=os.path.getsize(path), mtime=mtime, url=url))
        return files


def _addKeyValNode(element, key, value):
    keyvalNode = etree.SubElement(element, _namespacePrefix + u'keyval')
    keyNode = etree.SubElement(keyvalNode, _namespacePrefix + u'key')
    keyNode.text = key
    valNode = etree.SubElement(keyvalNode, _namespacePrefix + u'val')
    valNode.text = value



@grok.subscribe(IDataset, IObjectAddedEvent)
def generateMetadata(obj, event):
    if not IDataset.providedBy(obj): return
    factory = plone.api.portal.get_tool('portal_factory')
    if factory.isTemporary(obj): return
    root = etree.Element(_namespacePrefix + u'metadata', nsmap=_namespaceMap)
    leadPI = obj.leadPI.lower().replace(u' ', u'_')
    datasetID = obj.title.lower().replace(u' ', u'_')
    _addKeyValNode(root, u'DatasetId', leadPI + u'|' + datasetID)
    for attribute, key in (
        ('title', 'DatasetName'),
        ('datasetDate', 'DatasetDate'),
        ('leadPI', 'LeadPI'),
        ('specimenType', 'SpecimenType'),
    ):
        value = getattr(obj, attribute, u'')
        if not isinstance(value, basestring):
            value = unicode(value)
        _addKeyValNode(root, key, value)
    _addKeyValNode(root, u'UploadedBy', plone.api.user.get_current().getMemberId())
    path = os.path.join(obj.stagingDir, obj.id)
    os.makedirs(path, 0775)
    metadata = os.path.join(path, obj.id + u'.xml')
    doc = etree.ElementTree(root)
    doc.write(metadata, encoding='utf-8', pretty_print=True, xml_declaration=True)
    os.chmod(metadata, 0775)


class DataAcceptor(grok.View):
    u'''Accepts data uploaded to a dataset'''
    grok.context(IDataset)
    grok.require('cmf.ModifyPortalContent')
    grok.name('upload')
    def render(self):
        self.request.response.setHeader('Content-type', 'application/json; charset=utf-8')
        context = aq_inner(self.context)
        # d = context.filesystemPath + u'/' + unicode(context.id)
        # if not os.path.exists(d):
        #     os.makedirs(d)
        form = self.request.form
        if 'name' not in form or 'file' not in form:
            return anyjson.serialize({u'OK': 0, u'info': u'Missing "name" and/or "file" form elements'})
        name, infile = form['name'], form['file']
        target = os.path.join(d, name)
        with open(target, 'wb') as outfile:
            while True:
                buf = infile.read(512)
                if len(buf) == 0: break
                outfile.write(buf)
        return anyjson.serialize({u'OK': 1})


class DataRetriever(grok.View):
    u'''Retrieves a file from a dataset'''
    grok.context(IDataset)
    grok.require('zope2.View')
    grok.name('retrieve')
    def render(self):
        context = aq_inner(self.context)
        d = context.filesystemPath + u'/' + unicode(context.id)
        if not os.path.exists(d):
            os.makedirs(d)
        if 'name' not in self.request.form:
            raise ValueError(u'Required parameter "name" missing')
        name = self.request.form['name']
