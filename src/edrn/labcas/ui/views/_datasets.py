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
        canUpload = any([i for i in principals if i.startswith('cn=')])
        products = []
        for product in productTypes:
            p = LabCASProduct.new(product, principals)
            if p is None: continue
            products.append(p)
        products.sort()
        return {'products': products, 'hasProducts': len(products) > 0, 'canUpload': canUpload}
