# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.utils import LabCASCollection
from pyramid.view import view_config, view_defaults


@view_defaults(renderer=PACKAGE_NAME + ':templates/target.pt')
class TargetView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='target', permission='upload')
    def __call__(self):
        principals = frozenset(self.request.effective_principals)
        collections = LabCASCollection.get(principals=principals)
        return {
            'collections': collections,
            'hasCollections': len(collections) > 0,
        }
