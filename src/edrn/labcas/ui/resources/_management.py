# encoding: utf-8

from pyramid.security import Allow, DENY_ALL
from zope.component import getUtility
from edrn.labcas.ui.interfaces import ILabCASSettings


class Management(object):
    def __init__(self, request):
        principals = frozenset(request.effective_principals)
        superGroup = getUtility(ILabCASSettings).getSuperGroup()
        if superGroup in principals:
            self.__acl__ = [(Allow, principal, 'manage') for principal in principals]
        else:
            self.__acl__ = [DENY_ALL]
