# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from pyramid.view import view_config, view_defaults
from zope.component import getUtility
import humanize


@view_defaults(renderer=PACKAGE_NAME + ':templates/search.pt')
class SearchView(object):
    def __init__(self, request):
        self.request = request
    def percent(self, number):
        return u'{}%'.format(int(round(number * 100, 0)))
    def humanFriendlySize(self, size):
        return unicode(humanize.naturalsize(size)).replace(u' ', u' ')  # There's a NO-BREAK SPACE in there.
    @view_config(route_name='search', permission='view')
    def __call__(self):
        keywords = self.request.params.get('search')
        backend = getUtility(IBackend)
        collections = backend.getSearchEngine(u'collections').select(
            q=keywords,
            fields=None,
            highlight=None,
            score=True,
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        collections = [{
            u'name': i[u'CollectionName'],
            u'url':  self.request.route_url('collection', collectionID=i[u'id']),
            u'pi':   i[u'LeadPI'] if i.get(u'LeadPI') else None,
            u'desc': i[u'CollectionDescription'] if i.get(u'CollectionDescription') else None,
            u'score': self.percent(i[u'score'])
            # Other potential metadata to include here:
            # Discipline, Organ, InstitutionId, ProtocolId, CollaborativeGroup, LeadPI, Consortium, QAState,
            # Institution, OrganId, LeadPIId, DataCustodian, CollectionDescription, ProtocolName', OwnerPrincipal
        } for i in collections.results]
        datasets = backend.getSearchEngine(u'datasets').select(
            q=keywords,
            fields=None,
            highlight=None,
            score=True,
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        datasets = [{
            u'name': i[u'DatasetName'],
            u'url': self.request.route_url('dataset', collectionID=i[u'CollectionId'], datasetID=i[u'id']),
            u'cohort': i[u'Cohort'] if i.get(u'Cohort') else None,
            u'version': i[u'DatasetVersion'] if i.get(u'DatasetVersion') else None,
            u'desc': i[u'DatasetDescription'] if i.get(u'DatasetDescription') else None,
            u'score': self.percent(i[u'score'])
            # Other potential metadata to include here:
            # Cohort, CollectionName, CollectionId, Species, DatasetVersion, DatasetDescription, Sub-Cohort
        } for i in datasets.results]
        files = backend.getSearchEngine(u'files').select(
            q=keywords,
            fields=None,
            highlight=None,
            score=True,
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        files = [{
            u'name': i[u'FileName'],
            u'url': self.request.route_url(
                'file', collectionID=i[u'CollectionId'], datasetID=i[u'DatasetId'], fileID=i[u'id']
            ),
            u'cohort': i[u'Cohort'] if i.get(u'Cohort') else None,
            u'size': self.humanFriendlySize(i[u'FileSize']) if i.get(u'FileSize') else None,
            u'desc': i[u'GrossDescription'] if i.get(u'GrossDescription') else None,
            u'score': self.percent(i[u'score'])
        } for i in files.results]
        return {
            u'collections': collections,
            u'datasets': datasets,
            u'files': files
        }
