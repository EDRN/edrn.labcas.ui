# encoding: utf-8
# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

u'''EDRN LabCAS User Interface'''

from .interfaces import IBackend, ILabCASSettings
from .resources import Root, Dataset, Upload, Collections, Collection, File, Management
from .vocabularies import Vocabularies
from .settings import Settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid_ldap import groupfinder
from zope.component import provideUtility, getGlobalSiteManager, getUtility
from zope.interface import implements
import xmlrpclib, solr, cPickle, logging


PACKAGE_NAME = __name__
_logger = logging.getLogger(PACKAGE_NAME)


class _Backend(object):
    implements(IBackend)
    def __init__(self, fileMgrURL, workflowMgrURL, stagingDir, archiveDir):
        _logger.warn(
            '=== Creating _Backend with fileMgrURL=%s, workflowMgrURL=%s, stagingDir=%s, archiveDir=%s',
            fileMgrURL, workflowMgrURL, stagingDir, archiveDir
        )
        self.fileMgr = xmlrpclib.ServerProxy(fileMgrURL)
        self.workflowMgr = xmlrpclib.ServerProxy(workflowMgrURL)
        self.stagingDir, self.archiveDir = stagingDir, archiveDir
    def getFileMgr(self):
        return self.fileMgr.filemgr
    def getWorkflowMgr(self):
        return self.workflowMgr.workflowmgr  # Note case
    def getStagingDirectory(self):
        return self.stagingDir
    def getArchiveDirectory(self):
        return self.archiveDir
    def getSearchEngine(self, kind):
        return solr.Solr(getUtility(ILabCASSettings).getSolrURL() + u'/' + kind)


def main(global_config, **settings):
    u'''Return a WSGI application using the Pyramid framework that implements the LabCAS user interface.'''
    _logger.warn(u'INITIALIZING %s', PACKAGE_NAME)
    globalReg = getGlobalSiteManager()
    config = Configurator(registry=globalReg, root_factory=Root)
    config.setup_registry(settings=settings)
    config.include('pyramid_chameleon')
    config.include('pyramid_beaker')
    config.include('pyramid_ldap')
    config.ldap_setup(
        settings['ldap.url'], settings['ldap.manager'], settings['ldap.password'], timeout=int(settings['ldap.timeout'])
    )
    config.ldap_set_login_query(
        base_dn=settings['ldap.user.base'],
        filter_tmpl=settings['ldap.user.filter'].decode('utf-8').replace(u'\uff05', u'%'),
        scope=int(settings['ldap.user.scope'])
    )
    config.ldap_set_groups_query(
        base_dn=settings['ldap.group.base'],
        filter_tmpl=settings['ldap.group.filter'].decode('utf-8').replace(u'\uff05', u'%'),
        scope=int(settings['ldap.group.scope']),
        cache_period=int(settings['ldap.group.cache'])
    )
    config.set_authentication_policy(AuthTktAuthenticationPolicy(
        settings['authtkt.secret'], hashalg=settings['authtkt.hashalg'], callback=groupfinder,
        secure=settings['session.secure'] == 'true', timeout=settings['session.timeout'],
        max_age=settings['session.timeout'], wild_domain=False
    ))
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.add_static_view('static', 'static', cache_max_age=3600)  # use ini?
    config.add_static_view('deform_static', 'deform:static')
    config.add_route('favicon', '/favicon.ico')
    config.add_view('edrn.labcas.ui.views.favicon_view', route_name='favicon')
    config.add_route('home', '/')
    config.add_route('search', '/search', factory=Collections)
    config.add_route('collections', '/c', factory=Collections)
    config.add_route('collection', '/c/{collectionID}', factory=Collection)
    config.add_route('file', '/c/file/{fileID}', factory=File)
    config.add_route('dataset', '/c/{collectionID}/{datasetID}', factory=Dataset)
    config.add_route('download', '/download/{fileID}')
    config.add_route('upload', '/upload', factory=Upload)
    config.add_route('start', '/start', factory=Upload)
    config.add_route('wfmetadata', '/start/{workflowID}', factory=Upload)
    config.add_route('metadata', '/upload/{workflowID}', factory=Upload)
    config.add_route('accept', '/upload/{workflowID}/accept', factory=Upload)
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('people', '/people')
    config.add_route('protocols', '/protocols')
    config.add_route('sites', '/sites')
    config.add_route('organs', '/organs')
    config.add_route('disciplines', '/disciplines')
    config.add_route('species', '/species')
    config.add_route('specimenTypes', '/specimenTypes')
    config.add_route('ldapGroups', '/ldapGroups')
    config.add_route('manage', '/manage', factory=Management)
    config.add_route('help', '/help')
    config.add_route('about', '/about')
    config.scan()
    try:
        _logger.warn(u'Attempting to initialize settings from %s', settings['labcas.settings'])
        with open(settings['labcas.settings'], 'rb') as f:
            labCASSettings = cPickle.load(f)
            _logger.warn(u'Successfully restored settings!')
    except:
        _logger.warn(u'Failed to restore settings from %s; using defaults', settings['labcas.settings'])
        labCASSettings = Settings(settings['labcas.settings'])
        labCASSettings.update()
    provideUtility(labCASSettings)
    provideUtility(_Backend(
        settings['labcas.filemgr'],
        settings['labcas.workflow'],
        settings['labcas.staging'],
        settings['labcas.archive'],
    ))
    provideUtility(Vocabularies(settings['labcas.vocabularies']))
    _logger.info(u'LabCAS UI Ready')
    return config.make_wsgi_app()
