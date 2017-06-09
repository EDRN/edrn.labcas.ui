# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.utils import LabCASCollection
from pyramid.httpexceptions import HTTPFound
from pyramid.response import FileResponse
from pyramid.view import view_config, view_defaults
import humanize, zipfile, os, os.path, threading, tempfile  # FIXME: if /tmp lacks space, we fail


_tempFileRemovalTimeout = 10.0  # seconds


@view_defaults(renderer=PACKAGE_NAME + ':templates/dataset.pt')
class DatasetView(object):
    def __init__(self, request):
        self.request = request
    def humanFriendlySize(self, size):
        return unicode(humanize.naturalsize(size)).replace(u' ', u' ')  # There's a NO-BREAK SPACE in there.
    @view_config(route_name='dataset', permission='view')
    def __call__(self):
        collectionID, datasetID = self.request.matchdict['collectionID'], self.request.matchdict['datasetID']
        principals = frozenset(self.request.effective_principals)
        collection = LabCASCollection.get(collectionID, principals)
        dataset = collection.datasets(datasetID)
        params = self.request.params
        if 'Download checked files' in params:
            # Download multiple files
            # FIXME: overly large archives cause browser to hang and we fail
            ids = [unicode(i[8:]) for i in params if i.startswith(u'include.') and params[i] == u'on']
            if len(ids) == 0:
                raise HTTPFound(self.request.url, message=u'No files were selected.')
            zipFileDesc, zipFileName = tempfile.mkstemp(u'.zip', u'labcas-')
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
            # View files
            return {
                'collection': collection,
                'dataset': dataset
            }
