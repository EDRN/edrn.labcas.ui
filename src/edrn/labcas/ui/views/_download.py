# encoding: utf-8

from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASCollection
from M2Crypto import EVP
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden, HTTPUnauthorized
from pyramid.security import Everyone
from pyramid.view import view_config
from pyramid_ldap import get_ldap_connector
from zope.component import getUtility
import base64, logging, urllib, binascii

_logger = logging.getLogger(__name__)

# Adapted from http://opensourceconnections.com/blog/2013/01/17/escaping-solr-query-characters-in-python/
_escapeRules = {
    u'+': ur'\+',
    u'-': ur'\-',
    u'&': ur'\&',
    u'|': ur'\|',
    u'!': ur'\!',
    u'(': ur'\(',
    u')': ur'\)',
    u'{': ur'\{',
    u'}': ur'\}',
    u'[': ur'\[',
    u']': ur'\]',
    u'^': ur'\^',
    u'~': ur'\~',
    u'*': ur'\*',
    u'?': ur'\?',
    u':': ur'\:',
    u'"': ur'\"',
    u';': ur'\;',
    u' ': ur'\ '
}


def _escapedSeq(term):
    for char in term:
        yield _escapeRules[char] if char in _escapeRules else char


def _escapeSolrArg(term):
    term = term.replace(u'\\', ur'\\')
    return u''.join([i for i in _escapedSeq(term)])


class DownloadView(object):
    u'''API to authenticate a request and if valid download a file.'''
    def __init__(self, request):
        self.request = request
    def getCredentials(self):
        # Ripped from pyramid.authentication.BasicAuthAuthenticationPolicy
        authorization = self.request.headers.get('Authorization')
        if not authorization:
            return None
        try:
            authmeth, auth = authorization.split(' ', 1)
        except ValueError:  # not enough values to unpack
            return None
        if authmeth.lower() != 'basic':
            return None
        try:
            authbytes = base64.b64decode(auth.strip())
        except (TypeError, binascii.Error):  # can't decode
            return None
        # try utf-8 first, then latin-1; see discussion in https://github.com/Pylons/pyramid/issues/898
        try:
            auth = authbytes.decode('utf-8')
        except UnicodeDecodeError:
            auth = authbytes.decode('latin-1')
        try:
            username, password = auth.split(':', 1)
        except ValueError:  # not enough values to unpack
            return None
        return username, password
    @view_config(route_name='download')
    def __call__(self):
        fileID = self.request.matchdict['fileID']
        query = u'id:{}'.format(_escapeSolrArg(fileID))
        response = getUtility(IBackend).getSearchEngine(u'files').select(
            q=query, fields=[u'CollectionId', u'FileDownloadId']
        )
        if not response.results: raise HTTPNotFound()
        collectionID, downloadID = response.results[0].get(u'CollectionId'), response.results[0].get(u'FileDownloadId')
        if not collectionID: raise HTTPNotFound()
        try:
            username, password = self.getCredentials()
            ldapConnector = get_ldap_connector(self.request)
            user = ldapConnector.authenticate(username, password)
            if user is None: raise HTTPForbidden()
            userDN = user[0]
            groups = ldapConnector.user_groups(userDN)
            principals = [i[0] for i in groups]
            principals.append(userDN)
            principals = frozenset(principals)
        except TypeError:
            principals = frozenset(self.request.effective_principals)
            if len(principals) <= 1 and Everyone in principals:
                raise HTTPForbidden()
        collection = LabCASCollection.get(collectionID, principals)
        if not collection: raise HTTPForbidden()
        response = HTTPFound(self.request.host_url + u'/fmprod/data?productID=' + downloadID)
        key = EVP.load_key(self.request.registry.settings['labcas.hostkey'])
        key.reset_context(md='sha1')
        key.sign_init()
        key.sign_update(downloadID.encode('utf-8'))
        final = urllib.quote(base64.b64encode(key.sign_final()))
        _logger.info('For downloading file %s the cookie is %s', downloadID, final)
        response.set_cookie('labcasProductIDcookie', final, 3600, secure=True, overwrite=True, path='/fmprod')
        return response
