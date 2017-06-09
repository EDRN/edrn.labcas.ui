# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.utils import LabCASCollection
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults
from M2Crypto import EVP
import humanize, base64, logging, urllib

_logger = logging.getLogger(__name__)


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
            response = HTTPFound(self.request.host_url + u'/fmprod/data?productID=' + f.fileID)
            key = EVP.load_key(self.request.registry.settings['labcas.hostkey'])
            key.reset_context(md='sha1')
            key.sign_init()
            key.sign_update(f.fileID.encode('utf-8'))
            final = urllib.quote(base64.b64encode(key.sign_final()))
            _logger.info('For file %s the cookie is %s', f.fileID, final)
            response.set_cookie('labcasProductIDcookie', final, 3600, secure=True, overwrite=True, path='/fmprod')
            return response
        else:
            # View the file metadata
            return {
                'collection': collection,
                'dataset': dataset,
                'f': f
            }
