# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASWorkflow
from lxml import etree
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults
from zope.component import getUtility
import colander, re, deform, os, os.path


# Nifty XML constants
_namespaceURL = u'http://oodt.jpl.nasa.gov/1.0/cas'
_namespacePrefix = u'{' + _namespaceURL + u'}'
_namespaceMap = {None: _namespaceURL}


@view_defaults(renderer=PACKAGE_NAME + ':templates/metadata.pt')
class MetadataView(object):
    def __init__(self, request):
        self.request = request
    def _generateMetadata(self, metadata):
        root = etree.Element(_namespacePrefix + u'metadata', nsmap=_namespaceMap)
        for key, value in metadata.iteritems():
            keyvalNode = etree.SubElement(root, _namespacePrefix + u'keyval')
            keyNode = etree.SubElement(keyvalNode, _namespacePrefix + u'key')
            keyNode.text = unicode(key)
            valNode = etree.SubElement(keyvalNode, _namespacePrefix + u'val')
            valNode.text = unicode(value)
        return root
    def _writeMetadata(self, metadata, dir):
        u'''Write the metadata to the staging directory and return the generated directory path.'''
        if u'DatasetId' not in metadata:
            raise ValueError(u'DatasetId is a required metadata')
        datasetID = metadata[u'DatasetId']
        datasetDir = os.path.join(dir, datasetID)
        if not os.path.isdir(datasetDir):
            os.makedirs(datasetDir, 0775)
        root = self._generateMetadata(metadata)
        metadataFile = os.path.join(datasetDir, u'DatasetMetadata.xmlmet')
        doc = etree.ElementTree(root)
        doc.write(metadataFile, encoding='utf-8', pretty_print=True, xml_declaration=True)
        os.chmod(metadataFile, 0664)
        return datasetDir
    def _createSchema(self, workflow):
        # Find the task with order 1:
        schema = colander.SchemaNode(colander.Mapping())
        for task in workflow.tasks:
            if task.get('order', '-1') == '1':
                # build the form
                conf = task.get('configuration', {})
                for fieldName in task.get('requiredMetFields', []):
                    title = conf.get(u'input.{}.title'.format(fieldName), u'Unknown Field')
                    description = conf.get(u'input.{}.description'.format(fieldName), u'Not sure what to put here.')
                    dataType = conf.get(u'input.{}.type'.format(fieldName), u'http://www.w3.org/2001/XMLSchema/string')
                    if dataType == u'http://www.w3.org/2001/XMLSchema/string':
                        # Check for enumerated values
                        if u'input.{}.value.1'.format(fieldName) in conf:
                            # Collect the values
                            exp = re.compile(u'input.{}.value.[0-9]'.format(fieldName))
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
                                missing=colander.required
                            ))
                        else:
                            schema.add(colander.SchemaNode(
                                colander.String(),
                                name=fieldName,
                                title=title,
                                description=description,
                                missing=colander.required
                            ))
                    elif dataType == u'http://www.w3.org/2001/XMLSchema/integer':
                        minimum = int(conf.get(u'input.{}.min'.format(fieldName), "0"))
                        maximum = int(conf.get(u'input.{}.max'.format(fieldName), "1"))
                        schema.add(colander.SchemaNode(
                            colander.Int(),
                            name=fieldName,
                            title=title,
                            description=description,
                            validator=colander.Range(minimum, maximum),
                            missing=colander.required
                        ))
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
                datasetDir = self._writeMetadata(metadataAppstruct, backend.getStagingDirectory())
                self.request.session['metadata'] = metadataAppstruct
                self.request.session['metadataForm'] = form.render(metadataAppstruct, readonly=True)
                self.request.session['datasetDir'] = datasetDir
                return HTTPFound(self.request.url + u'/accept')
            except deform.ValidationFailure as ex:
                return {
                    u'message': u"Some required metadata don't make sense or are missing.",
                    u'form': ex.render(),
                    u'widgetResources': form.get_widget_resources()
                }
        return {u'form': form.render(), u'widgetResources': form.get_widget_resources()}
