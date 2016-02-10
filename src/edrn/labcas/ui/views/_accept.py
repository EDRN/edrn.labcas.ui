# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASWorkflow
from pyramid.view import view_config, view_defaults
from zope.component import getUtility


@view_defaults(renderer=PACKAGE_NAME + ':templates/accept.pt')
class AcceptView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='accept', permission='upload')
    def __call__(self):
        return {'metadataForm': self.request.session['metadataForm']}
