# encoding: utf-8

from pyramid.view import view_config, view_defaults
from edrn.labcas.ui import PACKAGE_NAME
from zope.component import getUtility
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASProduct


@view_defaults(renderer=PACKAGE_NAME + ':templates/datasets.pt')
class DatasetsView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='datasets', permission='view')
    def __call__(self):
        backend = getUtility(IBackend)
        productTypes = backend.getFileMgr().getProductTypes()
        principals = frozenset(self.request.effective_principals)
        products = []
        for product in productTypes:
            typeMetadata = product.get('typeMetadata', {})
            owners = frozenset(typeMetadata.get('OwnerGroup', []))
            if not principals.isdisjoint(owners):
                products.append(LabCASProduct(product.get('id', u'UNKNOWN'), product.get('name', u'UNKNOWN')))
        products.sort()
        return {'products': products, 'hasProducts': len(products) > 0}
