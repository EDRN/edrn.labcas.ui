# encoding: utf-8

from pyramid.view import view_config, view_defaults
from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.utils import LabCASCollection
from edrn.labcas.ui.interfaces import ILabCASSettings
from zope.component import getUtility


_suppressedCollections = (u'ECAS Product', u'LabCAS Product')


@view_defaults(renderer=PACKAGE_NAME + ':templates/collections.pt')
class CollectionsView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='collections', permission='view')
    def __call__(self):
        principals = frozenset(self.request.effective_principals)
        canUpload = any([i for i in principals if i.startswith('cn=')])
        superGroup = getUtility(ILabCASSettings).getSuperGroup()
        canManage = superGroup in principals
        allCollections = LabCASCollection.get(principals=principals)
        collections, publicCollections = [], []
        for collection in allCollections:
            if collection.name in _suppressedCollections: continue
            collections.append(collection)
            if collection.isPublic():
                publicCollections.append(collection)
        return {
            'collections': collections,
            'hasCollections': len(collections) > 0,
            'publicCollections': publicCollections,
            'hasPublicCollections': len(publicCollections) > 0,
            'canUpload': canUpload,
            'canManage': canManage
        }
