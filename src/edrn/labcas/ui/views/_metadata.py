# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASWorkflow, re_python_rfc3986_URI_reference
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults
from pyramid_ldap import get_ldap_connector
from zope.component import getUtility
import colander, re, deform, os, os.path, logging


# Logging
_logger = logging.getLogger(__name__)


# Capture the ID number in parentheses at the end of a "Name name name (ID number)" string
_idNumberHunter = re.compile(ur'\((\d+)\)$')


# Capture the common name (cn) at the front of an LDAP distinguished name (dn)
_cnHunter = re.compile(ur'^cn=([^,]+),')


# Current collaborative groups
_collaborativeGroups = [
    u'N/A',
    u'Breast and Gynecologic Cancers Research Group',
    u'G.I. and Other Associated Cancers Research Group',
    u'Lung and Upper Aerodigestive Cancers Research Group',
    u'Prostate and Urologic Cancers Research Group'
]


@view_defaults(renderer=PACKAGE_NAME + ':templates/metadata.pt')
class MetadataView(object):
    def __init__(self, request):
        self.request = request
    def _getDatasetDir(self, metadata, dir):
        u'''Create and return the path to the dataset directory.'''
        if u'DatasetId' not in metadata:
            raise ValueError(u'DatasetId is a required metadata')
        datasetID = metadata[u'DatasetId']
        datasetDir = os.path.join(dir, datasetID)
        if not os.path.isdir(datasetDir):
            os.makedirs(datasetDir, 0775)
        return datasetDir
    def _createSchema(self, workflow):
        # Find the task with order 1:
        schema = colander.SchemaNode(colander.Mapping())
        for task in workflow.tasks:
            if task.get('order', '-1') == '1':
                # build the form
                conf = task.get('configuration', {})
                for fieldName in task.get('requiredMetFields', []):
                    title = conf.get(u'input.dataset.{}.title'.format(fieldName), u'Unknown Field')
                    description = conf.get(u'input.dataset.{}.description'.format(fieldName), u'Not sure what to put here.')
                    dataType = conf.get(u'input.dataset.{}.type'.format(fieldName), u'http://www.w3.org/2001/XMLSchema/string')
                    missing = colander.required if conf.get(u'input.dataset.{}.required'.format(fieldName)) == u'true' else None
                    # FIXME:
                    if dataType in (
                        u'http://www.w3.org/2001/XMLSchema/string',
                        u'http://edrn.nci.nih.gov/xml/schema/types.xml#discipline',
                        u'http://edrn.nci.nih.gov/xml/schema/types.xml#organSite',
                    ):
                        # Check for enumerated values
                        if u'input.dataset.{}.value.1'.format(fieldName) in conf:
                            # Collect the values
                            exp = re.compile(u'input.dataset.{}.value.[0-9]+'.format(fieldName))
                            values = []
                            for key, val in conf.items():
                                if exp.match(key) is not None:
                                    values.append((val, val))
                            values.sort()
                            schema.add(colander.SchemaNode(
                                colander.String(),
                                name=fieldName,
                                title=title,
                                description=description,
                                validator=colander.OneOf([i[0] for i in values]),
                                widget=deform.widget.RadioChoiceWidget(values=values),
                                missing=missing
                            ))
                        else:
                            schema.add(colander.SchemaNode(
                                colander.String(),
                                name=fieldName,
                                title=title,
                                description=description,
                                missing=missing
                            ))
                    elif dataType == u'http://edrn.nci.nih.gov/xml/schema/types.xml#collaborativeGroup':
                        # CA-1356 ugly fix but I'm in a hurry and these groups haven't changed in 10 years.
                        # FIXME: correct solution: use IVocabularies
                        schema.add(colander.SchemaNode(
                            colander.String(),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing,
                            validator=colander.OneOf(_collaborativeGroups),
                            widget=deform.widget.RadioChoiceWidget(values=[(i, i) for i in _collaborativeGroups])
                        ))
                    elif dataType == u'urn:ldap:attributes:dn':
                        principals = [
                            _cnHunter.match(i).group(1).strip() for i in self.request.effective_principals
                            if i.startswith(u'cn=')
                        ]
                        principals.sort()
                        c = get_ldap_connector(self.request)
                        ldapGroups = [
                            _cnHunter.match(i).group(1).strip() for i, attrs in c.user_groups(u'uid=*')
                            if i.startswith(u'cn=')
                        ]
                        group = colander.SchemaNode(
                            colander.String(),
                            widget=deform.widget.AutocompleteInputWidget(values=self.request.route_url('ldapGroups')),
                            name='group',
                            title=u'Group',
                            description=u'Name of an EDRN group that should be able to access this data'
                        )
                        groups = colander.SchemaNode(
                            colander.Sequence(),
                            group,
                            validator=colander.ContainsOnly(ldapGroups),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing,
                            default=principals
                        )
                        schema.add(groups)
                    elif dataType == u'http://edrn.nci.nih.gov/xml/schema/types.xml#principalInvestigator':
                        schema.add(colander.SchemaNode(
                            colander.String(),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing,
                            widget=deform.widget.AutocompleteInputWidget(values=self.request.route_url('people'))
                        ))
                    elif dataType == u'http://edrn.nci.nih.gov/xml/schema/types.xml#protocolName':
                        schema.add(colander.SchemaNode(
                            colander.String(),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing,
                            widget=deform.widget.AutocompleteInputWidget(values=self.request.route_url('protocols'))
                        ))
                    elif dataType == u'http://www.w3.org/2001/XMLSchema/integer':
                        schema.add(colander.SchemaNode(
                            colander.Int(),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing
                        ))
                    elif dataType == u'http://www.w3.org/2001/XMLSchema/boolean':
                        schema.add(colander.SchemaNode(
                            colander.Boolean(),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing
                        ))
                    elif dataType == u'http://www.w3.org/2001/XMLSchema/anyURI':
                        schema.add(colander.SchemaNode(
                            colander.String(),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing,
                            validator=colander.Regex(re_python_rfc3986_URI_reference)
                        ))
                    elif dataType == u'http://www.w3.org/2001/XMLSchema/date':
                        schema.add(colander.SchemaNode(
                            colander.Date(),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing
                        ))
                    else:
                        _logger.warn(u'Unknown data type "%s" for field "%s"', dataType, fieldName)
                break
        return schema
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
        form = deform.Form(self._createSchema(workflow), buttons=('submit',))
        if 'submit' in self.request.params:
            try:
                metadataAppstruct = form.validate(self.request.POST.items())
                # CA-1354 ugly kludge
                protocolName = metadataAppstruct.get('ProtocolName', None)
                if protocolName:
                    match = _idNumberHunter.search(metadataAppstruct['ProtocolName'])
                    if match:
                        metadataAppstruct['ProtocolId'] = match.group(1)
                datasetDir = self._getDatasetDir(metadataAppstruct, backend.getStagingDirectory())
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
