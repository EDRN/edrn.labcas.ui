# encoding: utf-8
# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

u'''EDRN LabCAS User Interface'''

from .interfaces import IBackend
from .resources import Root, Datasets, Dataset, Upload
from .vocabularies import Vocabularies
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid_ldap import groupfinder
from zope.component import provideUtility
from zope.interface import implements
import xmlrpclib, solr


PACKAGE_NAME = __name__


class _Backend(object):
    implements(IBackend)
    def __init__(self, fileMgrURL, workflowMgrURL, stagingDir, archiveDir, solrURL):
        self.fileMgr = xmlrpclib.ServerProxy(fileMgrURL)
        self.workflowMgr = xmlrpclib.ServerProxy(workflowMgrURL)
        self.stagingDir, self.archiveDir = stagingDir, archiveDir
        self.solr = solr.SolrConnection(solrURL)
    def getFileMgr(self):
        return self.fileMgr.filemgr
    def getWorkflowMgr(self):
        return self.workflowMgr.workflowmgr  # Note case
    def getStagingDirectory(self):
        return self.stagingDir
    def getArchiveDirectory(self):
        return self.archiveDir
    def getSearchEngine(self):
        return self.solr


def main(global_config, **settings):
    u'''Return a WSGI application using the Pyramid framework that implements the LabCAS user interface.'''
    config = Configurator(settings=settings, root_factory=Root)
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
        settings['authtkt.secret'], hashalg=settings['authtkt.hashalg'], callback=groupfinder
    ))
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.add_static_view('static', 'static', cache_max_age=3600)  # use ini?
    config.add_static_view('deform_static', 'deform:static')
    config.add_route('home', '/')
    config.add_route('datasets', '/datasets', factory=Datasets)
    config.add_route('dataset', '/datasets/{datasetID}', factory=Dataset)
    config.add_route('upload', '/upload', factory=Upload)
    config.add_route('metadata', '/upload/{workflowID}', factory=Upload)
    config.add_route('accept', '/upload/{workflowID}/accept', factory=Upload)
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('people', '/people')
    config.add_route('protocols', '/protocols')
    config.add_route('ldapGroups', '/ldapGroups')
    config.scan()
    provideUtility(_Backend(
        settings['labcas.filemgr'],
        settings['labcas.workflow'],
        settings['labcas.staging'],
        settings['labcas.archive'],
        settings['labcas.solr']
    ))
    provideUtility(Vocabularies(settings['labcas.vocabularies']))
    return config.make_wsgi_app()
