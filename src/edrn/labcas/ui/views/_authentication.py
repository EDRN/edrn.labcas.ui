# encoding: utf-8

from pyramid.view import view_config, forbidden_view_config
from edrn.labcas.ui import PACKAGE_NAME
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound
from pyramid_ldap import get_ldap_connector
from deform import widget
import colander, deform


class _LoginSchema(colander.MappingSchema):
    u'''Schema for a login page'''
    username = colander.SchemaNode(
        colander.String(),
        title=u'Username',
        description=u'Your account name within the consortium.',
        validator=colander.Length(min=1)
    )
    password = colander.SchemaNode(
        colander.String(),
        title=u'Password',
        description=u'The secret sequence of characters that authenticates your username.',
        validator=colander.Length(min=1),
        widget=widget.PasswordWidget()
    )


class AuthenticationView(object):
    def __init__(self, request):
        self.request = request
    @property
    def form(self):
        schema = _LoginSchema()
        return deform.Form(schema, buttons=('submit',))
    @property
    def widgetResources(self):
        return self.form.get_widget_resources()
    @view_config(route_name='login', renderer=PACKAGE_NAME + ':templates/login.pt')
    @forbidden_view_config(renderer=PACKAGE_NAME + ':templates/login.pt')
    def login(self):
        loginURL = self.request.route_url('login')
        referrer = self.request.url
        if referrer == loginURL:
            referrer = '/'
        cameFrom = self.request.params.get('cameFrom', referrer)
        message = username = password = u''
        if 'submit' in self.request.params:
            username, password = self.request.params['username'], self.request.params['password']
            connector = get_ldap_connector(self.request)
            result = connector.authenticate(username, password)
            if result is not None:
                dn = result[0]
                fullName = result[1].get(u'cn', result[1][u'uid'])
                fullName = fullName[0]
                self.request.session['fullName'] = fullName
                del self.request.session['login']
                self.request.session.flash(u'Welcome {}. You are now logged in.'.format(fullName), 'info')
                headers = remember(self.request, dn)
                return HTTPFound(location=cameFrom, headers=headers)
            else:
                message = 'Login failed'
        self.request.session['login'] = True
        return dict(
            url=self.request.application_url + '/login',
            cameFrom=cameFrom,
            username=username,
            message=message,
            form=self.form.render()
        )
    @view_config(route_name='logout')
    def logout(self):
        try: del self.request.session['fullName']
        except KeyError: pass
        self.request.session.flash(u'You are now logged out.', queue='info')
        headers = forget(self.request)
        url = self.request.route_url('collections')
        return HTTPFound(location=url, headers=headers)
