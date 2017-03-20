# encoding: utf-8

from zope.interface import Interface


class IBackend(Interface):
    u'''What a LabCAS backend looks like.'''
    def getFileMgr():
        u'''Retrieves the file manager'''
    def getWorkflowMgr():
        u'''Retrieves the workflow manager'''
    def getStagingDirectory():
        u'''Retrieves the path to the LabCAS staging directory'''
    def getArchiveDirectory():
        u'''Retrieves the path to the LabCAS archive directory'''
    def getSearchEngine(kind):
        u'''Retrieves the SOLR search API for the given ``kind`` of data.'''


class IVocabularies(Interface):
    u'''What the vocabulary manager resembles.'''
    def getPeople():
        u'''Returns a sequence of people working on EDRN'''
    def getProtocols():
        u'''Returns a sequence of EDRN protocol names'''


class ILabCASSettings(Interface):
    u'''Various settings for LabCAS'''
    def getSiteName():
        u'''Returns a unicode name of the site'''
    def setSiteName(siteName):
        u'''Set the name of the site'''
