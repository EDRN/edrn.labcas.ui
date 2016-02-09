# encoding: utf-8

from pyramid.security import Allow, Authenticated


class Upload(object):
    __acl__ = [
        (Allow, Authenticated, 'upload'),
    ]
    def __init__(self, request):
        pass
