# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from pyramid.view import view_config, view_defaults
from zope.component import getUtility


@view_defaults(renderer=PACKAGE_NAME + ':templates/search.pt')
class SearchView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='search', permission='view')
    def __call__(self):
        keywords = self.request.params.get('search')
        backend = getUtility(IBackend)
        collections = backend.getSearchEngine(u'collections').select(
            q=keywords,
            fields=None,
            highlight=None,
            score=True,
            sort=['CollectionName'],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        collections = [{
            u'name': i[u'CollectionName'],
            u'url': self.request.route_url('collection', collectionID=i[u'id'])
            # Other potential metadata to include here:
            # Discipline, Organ, InstitutionId, ProtocolId, CollaborativeGroup, LeadPI, Consortium, QAState,
            # Institution, OrganId, LeadPIId, DataCustodian, CollectionDescription, ProtocolName', OwnerPrincipal
        } for i in collections.results]
        datasets = backend.getSearchEngine(u'datasets').select(
            q=keywords,
            fields=None,
            highlight=None,
            score=True,
            sort=['DatasetName'],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        datasets = [{
            u'name': i[u'DatasetName'],
            u'url': self.request.route_url('dataset', collectionID=i[u'CollectionId'], datasetID=i[u'id'])
            # Other potential metadata to include here:
            # Cohort, CollectionName, CollectionId, Species, DatasetVersion, DatasetDescription, Sub-Cohort
        } for i in datasets.results]
        files = backend.getSearchEngine(u'files').select(
            q=keywords,
            fields=None,
            highlight=None,
            score=True,
            sort=['FileName'],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        files = [{
            u'name': i[u'FileName'],
            u'url': self.request.route_url(
                'file', collectionID=i[u'CollectionId'], datasetID=i[u'DatasetId'], fileID=i[u'id']
            )
            # Other potential metadata to include here: FileSize
        } for i in files.results]
        everything = []
        for i in collections:
            everything.append((u'collection', i))
        for i in datasets:
            everything.append((u'dataset', i))
        for i in files:
            everything.append((u'file', i))
        everything.sort(lambda a, b: cmp(a[1][u'name'], b[1][u'name']))
        return {
            u'collections': collections,
            u'datasets': datasets,
            u'files': files,
            u'everything': everything
        }
