# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from pyramid.view import view_config, view_defaults


@view_defaults(renderer=PACKAGE_NAME + ':templates/home.pt')
class HomeView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='home')
    def __call__(self):
        return {}
