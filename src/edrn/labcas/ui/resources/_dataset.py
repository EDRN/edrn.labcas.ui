# encoding: utf-8

from pyramid.security import Allow, DENY_ALL
from zope.component import getUtility
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import SUPER_GROUP


class Dataset(object):
    def __init__(self, request):
        principals = frozenset(request.effective_principals)
        if SUPER_GROUP in principals:
            self.__acl__ = [(Allow, SUPER_GROUP, 'view')]
        else:
            datasetID = request.matchdict.get('datasetID', None)
            backend = getUtility(IBackend)
            product = backend.getFileMgr().getProductTypeById(datasetID)
            typeMetadata = product.get('typeMetadata', {})
            owners = frozenset(typeMetadata.get('OwnerGroup', []))
            intersection = principals & owners
            if len(intersection) > 0:
                self.__acl__ = [(Allow, principal, 'view') for principal in intersection]
            else:
                self.__acl__ = [DENY_ALL]
