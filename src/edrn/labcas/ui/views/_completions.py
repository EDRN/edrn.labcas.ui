# encoding: utf-8

u'''EDRN LabCAS UI: completions.  Used to power auto-complete widgets by providing possible values'''

from edrn.labcas.ui.interfaces import IVocabularies
from pyramid.view import view_config
from zope.component import getUtility
import re


class _CompletionsView(object):
    u'''Abstract completions view.  Subclass this and provide a suitable __call__ method linked
    with a named route.'''
    def __init__(self, request):
        self.request = request
    def _getMatches(self, possibleValues):
        u'''Given a list of ``possibleValues`` use what the user has typed so far (given in the request
        parameter ``term``) to generate a list of potential matches.
        '''
        term = self.request.params.get(u'term', u'')
        possibleValues.sort()
        if not term: return possibleValues
        regex = re.compile(term, re.IGNORECASE)
        matches = [i for i in possibleValues if regex.search(i)]
        return matches


class PeopleCompletionsView(_CompletionsView):
    u'''Completions for people in EDRN.'''
    @view_config(route_name='people', renderer='json')
    def __call__(self):
        return self._getMatches(getUtility(IVocabularies).getPeople().values())


class ProtocolCompletionsView(_CompletionsView):
    u'''Completions for protocols studied by EDRN.'''
    @view_config(route_name='protocols', renderer='json')
    def __call__(self):
        return self._getMatches(getUtility(IVocabularies).getProtocols().values())
