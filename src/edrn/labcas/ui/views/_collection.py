# encoding: utf-8

from pyramid.view import view_config, view_defaults
from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.utils import LabCASCollection
import logging

_logger = logging.getLogger(__name__)


@view_defaults(renderer=PACKAGE_NAME + ':templates/collection.pt')
class CollectionView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='collection', permission='view')
    def __call__(self):
        collectionID = self.request.matchdict['collectionID']
        _logger.info('__call__ for collection, collectionID "%s"', collectionID)
        principals = frozenset(self.request.effective_principals)
        collection = LabCASCollection.get(collectionID, principals)
        return {'collection': collection, 'pageTitle': collection.name}
