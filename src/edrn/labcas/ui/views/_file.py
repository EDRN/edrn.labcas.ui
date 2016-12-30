# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.utils import LabCASCollection
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults
import humanize, os, os.path


@view_defaults(renderer=PACKAGE_NAME + ':templates/file.pt')
class FileView(object):
    def __init__(self, request):
        self.request = request
    def humanFriendlySize(self, size):
        return unicode(humanize.naturalsize(size)).replace(u' ', u' ')  # There's a NO-BREAK SPACE in there.
    @view_config(route_name='file', permission='view')
    def __call__(self):
        collectionID = self.request.matchdict['collectionID']
        datasetID = self.request.matchdict['datasetID']
        fileID = self.request.matchdict['fileID']
        principals = frozenset(self.request.effective_principals)
        collection = LabCASCollection.get(collectionID, principals)
        dataset = collection.datasets(datasetID)
        f = dataset.files(fileID)
        params = self.request.params
        if 'download' in params:
            # Download the file
            return HTTPFound(self.request.host_url + u'/fmprod/data?productID=' + f.fileID)
        else:
            # View the file metadata
            return {
                'collection': collection,
                'dataset': dataset,
                'f': f
            }
