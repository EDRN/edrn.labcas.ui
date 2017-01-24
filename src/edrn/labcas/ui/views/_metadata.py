# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASWorkflow, re_python_rfc3986_URI_reference, LabCASCollection, createSchema
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults
from zope.component import getUtility
import re, deform, os, os.path, logging, uuid


# Logging
_logger = logging.getLogger(__name__)


# Capture the ID number in parentheses at the end of a "Name name name (ID number)" string
_idNumberHunter = re.compile(ur'\((\d+)\)$')


# Metadata fields for NIST pipelines that generate dataset IDs
_nistMetadataFields = frozenset((u'LabNumber', u'Method', u'RoundNumber'))


@view_defaults(renderer=PACKAGE_NAME + ':templates/metadata.pt')
class MetadataView(object):
    def __init__(self, request):
        self.request = request
    def _getDatasetDir(self, metadata, dir, collectionName):
        u'''Create and return the path to the dataset directory.'''
        if u'DatasetName' not in metadata:
            raise ValueError(u'DatasetName is a required metadata')
        datasetName = metadata[u'DatasetName'].replace(u' ', u'_')
        collectionName = collectionName.replace(u' ', u'_')
        datasetDir = os.path.join(dir, collectionName, datasetName)
        if not os.path.isdir(datasetDir):
            os.makedirs(datasetDir, 0775)
        return datasetDir
    @view_config(route_name='metadata', permission='upload')
    def __call__(self):
        backend = getUtility(IBackend)
        workflowID = self.request.matchdict['workflowID']
        wfInfo = backend.getWorkflowMgr().getWorkflowById(workflowID)
        workflow = LabCASWorkflow(
            wfInfo.get('id', u'unknown'),
            wfInfo.get('name', u'unknown'),
            wfInfo.get('conditions', []),
            wfInfo.get('tasks', [])
        )
        principals = frozenset(self.request.effective_principals)
        form = deform.Form(createSchema(workflow, self.request), buttons=('submit',))
        if 'submit' in self.request.params:
            try:
                metadataAppstruct = form.validate(self.request.POST.items())
                # CA-1354 ugly kludge
                protocolName = metadataAppstruct.get('ProtocolName', None)
                if protocolName:
                    match = _idNumberHunter.search(metadataAppstruct['ProtocolName'])
                    if match:
                        metadataAppstruct['ProtocolId'] = match.group(1)
                # CA-1382 ugly kludge
                if _nistMetadataFields <= frozenset(metadataAppstruct.keys()):
                    ln = metadataAppstruct[u'LabNumber']
                    nm = metadataAppstruct[u'Method']
                    rn = metadataAppstruct[u'RoundNumber']
                    metadataAppstruct[u'DatasetName'] = u'Lab{}_{}_R{}'.format(ln, nm, rn)
                else:
                    metadataAppstruct[u'DatasetId'] = unicode(uuid.uuid4())
                    if u'DatasetName' not in metadataAppstruct:
                        metadataAppstruct[u'DatasetName'] = metadataAppstruct[u'DatasetId']
                collectionName = workflow.collectionName
                if not collectionName:
                    collectionName = metadataAppstruct[u'CollectionName']
                datasetDir = self._getDatasetDir(metadataAppstruct, backend.getStagingDirectory(), collectionName)
                if not os.path.isdir(datasetDir):
                    os.makedirs(datasetDir)
                self.request.session['metadata'] = metadataAppstruct
                self.request.session['metadataForm'] = form.render(metadataAppstruct, readonly=True)
                self.request.session['datasetDir'] = datasetDir
                self.request.session['workflow'] = workflow
                return HTTPFound(self.request.url + u'/accept')
            except deform.ValidationFailure as ex:
                return {
                    u'message': u"Some required metadata don't make sense or are missing.",
                    u'form': ex.render(),
                    u'widgetResources': form.get_widget_resources()
                }
        return {u'form': form.render(), u'widgetResources': form.get_widget_resources()}
