# encoding: utf-8

from pyramid.view import view_config, forbidden_view_config
from edrn.labcas.ui import PACKAGE_NAME
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound
from pyramid_ldap import get_ldap_connector


class AuthenticationView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='login', renderer=PACKAGE_NAME + ':templates/login.pt')
    @forbidden_view_config(renderer=PACKAGE_NAME + ':templates/login.pt')
    def login(self):
        loginURL = self.request.route_url('login')
        referrer = self.request.url
        if referrer == loginURL:
            referrer = '/'
        cameFrom = self.request.params.get('cameFrom', referrer)
        message = username = password = u''
        if 'form.submitted' in self.request.params:
            username, password = self.request.params['username'], self.request.params['password']
            connector = get_ldap_connector(self.request)
            result = connector.authenticate(username, password)
            if result is not None:
                dn = result[0]
                headers = remember(self.request, dn)
                return HTTPFound(location=cameFrom, headers=headers)
            else:
                message = 'Login failed'
        return dict(
            url=self.request.application_url + '/login',
            cameFrom=cameFrom,
            username=username,
            message=message
        )
    @view_config(route_name='logout')
    def logout(self):
        headers = forget(self.request)
        url = self.request.route_url('home')
        return HTTPFound(location=url, headers=headers)
