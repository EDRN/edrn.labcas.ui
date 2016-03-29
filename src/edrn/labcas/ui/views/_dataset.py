# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASProduct, computeCollaborativeGroupURL
from pyramid.view import view_config, view_defaults
from pyramid.response import FileResponse
from zope.component import getUtility
from pyramid.httpexceptions import HTTPNotFound


@view_defaults(renderer=PACKAGE_NAME + ':templates/dataset.pt')
class DatasetView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='dataset', permission='view')
    def __call__(self):
        backend = getUtility(IBackend)
        datasetID = self.request.matchdict['datasetID']
        product = backend.getFileMgr().getProductTypeById(datasetID)
        p = LabCASProduct.new(product, frozenset(self.request.effective_principals))
        if 'version' in self.request.params and 'name' in self.request.params:
            versionNum, name = int(self.request.params['version']), self.request.params['name']
            version = p.versions[versionNum]
            for f in version:
                if f.name == name:
                    physicalLocation, contentType = f.physicalLocation, f.contentType
                    return FileResponse(physicalLocation, self.request, content_type=contentType.encode('utf-8'))
            raise HTTPNotFound(detail='File "{}" not found in version {} of product "{}"'.format(
                name, versionNum, p.name
            ))
        else:
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
