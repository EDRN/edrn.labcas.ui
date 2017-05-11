# encoding: utf-8

u'''EDRN LabCAS UI: completions.  Used to power auto-complete widgets by providing possible values'''

from edrn.labcas.ui.interfaces import IVocabularies
from pyramid.view import view_config
from zope.component import getUtility
from pyramid_ldap import get_ldap_connector
import re


# Capture the common name (cn) at the front of an LDAP distinguished name (dn)
_cnHunter = re.compile(ur'^cn=([^,]+),')


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


class SitesCompletionsView(_CompletionsView):
    u'''Completions for sites.'''
    @view_config(route_name='sites', renderer='json')
    def __call__(self):
        return self._getMatches(getUtility(IVocabularies).getSites().values())


class OrgansCompletionsView(_CompletionsView):
    u'''Completions for Organs.'''
    @view_config(route_name='organs', renderer='json')
    def __call__(self):
        return self._getMatches(getUtility(IVocabularies).getOrgans().values())


class DisciplinesCompletionsView(_CompletionsView):
    u'''Completions for Disciplines.'''
    @view_config(route_name='disciplines', renderer='json')
    def __call__(self):
        return self._getMatches(getUtility(IVocabularies).getDisciplines().values())


class SpeciesCompletionsView(_CompletionsView):
    u'''Completions for species.'''
    @view_config(route_name='species', renderer='json')
    def __call__(self):
        return self._getMatches(getUtility(IVocabularies).getSpecies().values())


class SpecimenTypesCompletionsView(_CompletionsView):
    u'''Completions for specimen types.'''
    @view_config(route_name='specimenTypes', renderer='json')
    def __call__(self):
        return self._getMatches(getUtility(IVocabularies).getSpecimenTypes().values())


class LDAPGroupsCompletionsView(_CompletionsView):
    u'''Completions for LDAP groups in EDRN.'''
    @view_config(route_name='ldapGroups', renderer='json')
    def __call__(self):
        c = get_ldap_connector(self.request)
        ldapGroups = [dn for dn, attrs in c.user_groups(u'uid=*') if not dn.startswith(u'system.')]
        groupNames = [_cnHunter.match(i).group(1) for i in ldapGroups if _cnHunter.match(i)]
        return self._getMatches(groupNames)
