# encoding: utf-8

from pyramid.security import Allow, DENY_ALL
from edrn.labcas.ui.utils import SUPER_GROUP


class Management(object):
    def __init__(self, request):
        principals = frozenset(request.effective_principals)
        if SUPER_GROUP in principals:
            self.__acl__ = [(Allow, principal, 'manage') for principal in principals]
        else:
            self.__acl__ = [DENY_ALL]
