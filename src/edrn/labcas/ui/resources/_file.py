# encoding: utf-8

from pyramid.security import Allow, DENY_ALL
from edrn.labcas.ui.utils import LabCASCollection


class File(object):
    def __init__(self, request):
        principals = frozenset(request.effective_principals)
        collectionID = request.matchdict.get('collectionID', request.params.get('collectionID'))
        collection = LabCASCollection.get(collectionID, principals)
        if collection:
            self.__acl__ = [(Allow, principal, 'view') for principal in principals]
        else:
            self.__acl__ = [DENY_ALL]
