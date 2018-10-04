# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import ILabCASSettings
from edrn.labcas.ui.utils import LabCASCollection, computeHumanReadableContentType, LabCASDataset
from pyramid.httpexceptions import HTTPFound
from pyramid.response import FileResponse
from pyramid.view import view_config, view_defaults
from zope.component import getUtility
import humanize, zipfile, os, os.path, threading, tempfile, logging  # FIXME: if /tmp lacks space, we fail


_tempFileRemovalTimeout = 10.0  # seconds
_logger = logging.getLogger(__name__)


@view_defaults(renderer=PACKAGE_NAME + ':templates/dataset.pt')
class DatasetView(object):
    def __init__(self, request):
        self.request = request
    def humanFriendlySize(self, size):
        return unicode(humanize.naturalsize(size)).replace(u' ', u' ')  # There's a NO-BREAK SPACE in there.
    def humanFriendlyMimeType(self, f):
        return computeHumanReadableContentType(f.name, f.contentType)
    @view_config(route_name='dataset', permission='view')
    def __call__(self):
        principals = frozenset(self.request.effective_principals)
        collectionID = self.request.matchdict['collectionID']
        collection = LabCASCollection.get(collectionID, principals)
        datasetID = self.request.matchdict['datasetID'].replace(u"%57", u"/")
        _logger.info('__call__ for dataset, collectionID "%s", datasetID "%s"', collectionID, datasetID)
        dataset = LabCASDataset.getByDatasetID(datasetID)
        totalSize = sum([i.size for i in dataset.files()])
        params = self.request.params
        if 'Download checked files' in params:
            # Download multiple files
            # FIXME: overly large archives cause browser to hang and we fail
            ids = [unicode(i[8:]) for i in params if i.startswith(u'include.') and params[i] == u'on']
            if len(ids) == 0:
                raise HTTPFound(self.request.url, message=u'No files were selected.')
            tmpDir = getUtility(ILabCASSettings).getTmpDir()
            zipFileDesc, zipFileName = tempfile.mkstemp(u'.zip', u'labcas-', tmpDir)
            with zipfile.ZipFile(os.fdopen(zipFileDesc, 'w'), 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
                for i in ids:
                    f = dataset.files(i)
                    os.chdir(f.directory)
                    z.write(f.name)
            remover = threading.Timer(_tempFileRemovalTimeout, os.remove, (zipFileName,))
            remover.daemon = True
            remover.start()
            fr = FileResponse(zipFileName, self.request, content_type='application/zip')
            fr.content_disposition = u'attachement; filename="{}.zip"'.format(datasetID)
            return fr
        else:
            _logger.info('Dataset view: collection ID %s, dataset ID %s', collection.identifier, dataset.identifier)
            return {
                'collection': collection,
                'dataset': dataset,
                'totalSize': self.humanFriendlySize(totalSize)
            }
