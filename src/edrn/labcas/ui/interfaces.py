# encoding: utf-8

from zope.interface import Interface


class IBackend(Interface):
    def getFileMgr():
        u'''Retrieves the filemgr'''
