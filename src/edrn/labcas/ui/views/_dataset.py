# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from pyramid.view import view_config, view_defaults
from zope.component import getUtility


@view_defaults(renderer=PACKAGE_NAME + ':templates/dataset.pt')
class DatasetView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='dataset', permission='view')
    def __call__(self):
        backend = getUtility(IBackend)
        datasetID = self.request.matchdict['datasetID']
        product = backend.getFileMgr().getProductTypeById(datasetID)
        metadata = product['typeMetadata'].items()
        metadata.sort(lambda a, b: cmp(a[0], b[0]))
        return {
            'datasetID': datasetID,
            'description': product.get('description'),
            'metadata': metadata
        }
