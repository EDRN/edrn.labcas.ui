# encoding: utf-8

u'''Workflow Metadata'''

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASWorkflow, createSchema
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults
from zope.component import getUtility
import re, deform, logging, uuid, datetime


# Logging
_logger = logging.getLogger(__name__)


# Capture the ID number in parentheses at the end of a "Name name name (ID number)" string
_idNumberHunter = re.compile(ur'\((\d+)\)$')


# Metadata fields for NIST pipelines that generate dataset IDs
_nistMetadataFields = frozenset((u'LabNumber', u'Method', u'RoundNumber'))


@view_defaults(renderer=PACKAGE_NAME + ':templates/wfmetadata.pt')
class WFMetadataView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='wfmetadata', permission='upload')
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
                # Transform date objects into strings
                for key, value in metadataAppstruct.items():
                    if isinstance(value, datetime.date):
                        metadataAppstruct[key] = value.isoformat()
                tasks = [i['id'] for i in workflow.tasks]
                backend = getUtility(IBackend)
                backend.getWorkflowMgr().executeDynamicWorkflow(tasks, metadataAppstruct)
                self.request.session.flash(
                    u'LabCAS is now executng your workflow. It may take some time for results to appear.',
                    'info'
                )
                return HTTPFound(self.request.route_url('collections'))
            except deform.ValidationFailure as ex:
                return {
                    u'message': u"Some required metadata don't make sense or are missing.",
                    u'form': ex.render(),
                    u'widgetResources': form.get_widget_resources()
                }
        return {u'form': form.render(), u'widgetResources': form.get_widget_resources()}
