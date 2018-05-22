# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from pyramid.view import view_config, view_defaults


@view_defaults(renderer=PACKAGE_NAME + ':templates/about.pt')
class AboutView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='about')
    def __call__(self):
        return {}
