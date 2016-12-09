# encoding: utf-8

from pyramid.security import Allow, DENY_ALL
from edrn.labcas.ui.utils import LabCASCollection


class Collection(object):
    def __init__(self, request):
        principals = frozenset(request.effective_principals)
        collectionID = request.matchdict.get('collectionID', None)
        collection = LabCASCollection.get(collectionID, principals)
        if collection:
            self.__acl__ = [(Allow, principal, 'view') for principal in principals]
        else:
            self.__acl__ = [DENY_ALL]
