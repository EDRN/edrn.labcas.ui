# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASProduct, computeCollaborativeGroupURL
from pyramid.view import view_config, view_defaults
from pyramid.response import FileResponse
from zope.component import getUtility
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
import humanize, zipfile, os, os.path, threading
import tempfile  # FIXME: if /tmp lacks space, we fail


_tempFileRemovalTimeout = 10.0  # seconds


@view_defaults(renderer=PACKAGE_NAME + ':templates/dataset.pt')
class DatasetView(object):
    def __init__(self, request):
        self.request = request
    def humanFriendlySize(self, size):
        return unicode(humanize.naturalsize(size)).replace(u' ', u' ')  # There's a NO-BREAK SPACE in there.
    @view_config(route_name='dataset', permission='view')
    def __call__(self):
        backend = getUtility(IBackend)
        datasetID = self.request.matchdict['datasetID']
        product = backend.getFileMgr().getProductTypeById(datasetID)
        p = LabCASProduct.new(product, frozenset(self.request.effective_principals))
        params = self.request.params
        if 'version' in params and 'name' in params and 'archiveVersion' not in params:
            # Download single file
            versionNum, name = int(params['version']), params['name']
            version = p.versions[versionNum]
            for f in version:
                if f.name == name:
                    physicalLocation, contentType = f.physicalLocation, f.contentType
                    return FileResponse(physicalLocation, self.request, content_type=contentType.encode('utf-8'))
            raise HTTPNotFound(detail='File "{}" not found in version {} of product "{}"'.format(
                name, versionNum, p.name
            ))
        elif 'archiveVersion' in params:
            # Download multiple files
            # FIXME: overly large archives cause browser to hang and we fail
            versionNum = int(params['archiveVersion'])
            version = p.versions[versionNum]
            files = [unicode(i[8:]) for i in params if i.startswith(u'include.') and params[i] == u'on']
            if len(files) == 0:
                raise HTTPFound(self.request.url, message=u'No files were selected.')
            zipFileDesc, zipFileName = tempfile.mkstemp(u'.zip', u'labcas-')
            with zipfile.ZipFile(os.fdopen(zipFileDesc, 'w'), 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
                for name in files:
                    for candidateFile in version:  # FIXME: this won't scale for huge datasets
                        if candidateFile.name == name:
                            os.chdir(os.path.dirname(candidateFile.physicalLocation))
                            z.write(name)
            remover = threading.Timer(_tempFileRemovalTimeout, os.remove, (zipFileName,))
            remover.daemon = True
            remover.start()
            return FileResponse(zipFileName, self.request, content_type='application/zip')
        else:
            # View files
            metadata = product['typeMetadata'].items()
            metadata.sort(lambda a, b: cmp(a[0], b[0]))
            cgURL = computeCollaborativeGroupURL(p)
            return {
                'datasetID': datasetID,
                'description': product.get('description'),
                'metadata': metadata,
                'product': p,
                'cgURL': cgURL
            }
