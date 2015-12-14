# encoding: utf-8

from pyramid.security import Allow, Authenticated


class Datasets(object):
    __acl__ = [
        (Allow, Authenticated, 'view'),
    ]
    def __init__(self, request):
        pass
