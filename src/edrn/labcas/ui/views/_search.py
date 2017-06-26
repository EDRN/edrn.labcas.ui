# encoding: utf-8

from pyramid.view import view_config, view_defaults
from edrn.labcas.ui import PACKAGE_NAME


@view_defaults(renderer=PACKAGE_NAME + ':templates/search.pt')
class SearchView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='search', permission='view')
    def __call__(self):
        return {}
