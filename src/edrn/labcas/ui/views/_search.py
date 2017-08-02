# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import computeHumanReadableContentType
from pyramid.renderers import get_renderer
from pyramid.view import view_config, view_defaults
from zope.component import getUtility
import humanize


_textLimit = 200


@view_defaults(renderer=PACKAGE_NAME + ':templates/search.pt')
class SearchView(object):
    def __init__(self, request):
        self.request = request
    def truncate(self, s):
        if s:
            if len(s) > _textLimit:
                s = s[:_textLimit]
                l = s.rfind(u' ')
                if l > _textLimit / 2:
                    s = s[:l + 1]
                s += u'…'
        return s
    def percent(self, number):
        return u'{}%'.format(int(round(number * 100, 0)))
    def humanFriendlySize(self, size):
        return unicode(humanize.naturalsize(size)).replace(u' ', u' ')  # There's a NO-BREAK SPACE in there.
    def humanReadableContentType(self, contentType):
        return computeHumanReadableContentType(u'dummy.bin', contentType)
    @view_config(route_name='search', permission='view')
    def __call__(self):
        searchMacros = get_renderer(PACKAGE_NAME + ':templates/searchmacros.pt').implementation()
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
        facetCode = [u'$(document).ready(function() {']
        discs = set()
        for i in collections.results:
            disc = i.get(u'Discipline', [None])[0]
            if disc:
                discs.add(disc)
        discs = list(discs)
        discs.sort()
        discToIDs, idsToDiscs, counter = {}, {}, 0
        for disc in discs:
            discToIDs[disc] = counter
            idsToDiscs[counter] = disc
            facetCode.append(u'''$("#disc-{}").click(function() {{
                if ($(this).prop("checked"))
                    $(".disc-{}").slideDown();
                else
                    $(".disc-{}").slideUp();
            }}); '''.format(counter, counter, counter))
            counter += 1
        cbs = set()
        for i in collections.results:
            cb = i.get(u'CollaborativeGroup', [None])[0]
            if cb:
                cbs.add(cb)
        cbs = list(cbs)
        cbs.sort()
        cbToIDs, idsToCBs, counter = {}, {}, 0
        for cb in cbs:
            cbToIDs[cb] = counter
            idsToCBs[counter] = cb
            facetCode.append(u'''$("#cb-{}").click(function() {{
                if ($(this).prop("checked"))
                    $(".cb-{}").slideDown();
                else
                    $(".cb-{}").slideUp();
            }}); '''.format(counter, counter, counter))
            counter += 1
        pis = set()
        for i in collections.results:
            pi = i.get(u'LeadPI', [None])[0]
            if pi:
                pis.add(pi)
        pis = list(pis)
        pis.sort()
        pisToIDs, idsToPIs, counter = {}, {}, 0
        for pi in pis:
            pisToIDs[pi] = counter
            idsToPIs[counter] = pi
            facetCode.append(u'''$("#p-{}").click(function() {{
                if ($(this).prop("checked"))
                    $(".p-{}").slideDown();
                else
                    $(".p-{}").slideUp();
            }}); '''.format(counter, counter, counter))
            counter += 1
        organs = set()
        for i in collections.results:
            organ = i.get(u'Organ', [None])[0]
            if organ:
                organs.add(organ)
        organs = list(organs)
        organs.sort()
        organsToIDs, idsToOrgans, counter = {}, {}, 0
        for organ in organs:
            organsToIDs[organ] = counter
            idsToOrgans[counter] = organ
            facetCode.append(u'''$("#o-{}").click(function() {{
                if ($(this).prop("checked"))
                    $(".o-{}").slideDown();
                else
                    $(".o-{}").slideUp();
            }}); '''.format(counter, counter, counter))
            counter += 1
        collections = [{
            u'name': i[u'CollectionName'],
            u'url':  self.request.route_url('collection', collectionID=i[u'id']),
            u'pi': i.get(u'LeadPI', [None])[0],
            u'organ': i.get(u'Organ', [None])[0],
            u'desc': self.truncate(i.get(u'CollectionDescription')),
            u'score': self.percent(i[u'score']),
            u'collabGroup': i.get(u'CollaborativeGroup', [None])[0],
            u'disc': i.get(u'Discipline', [None])[0]
            # Other potential metadata to include here:
            # Discipline, Organ, InstitutionId, ProtocolId, CollaborativeGroup, LeadPI, Consortium, QAState,
            # Institution, OrganId, LeadPIId, DataCustodian, CollectionDescription, ProtocolName', OwnerPrincipal
        } for i in collections.results]
        numCollections, top10Collections, collections = len(collections), collections[:10], collections[10:]
        datasets = backend.getSearchEngine(u'datasets').select(
            q=keywords,
            fields=None,
            highlight=None,
            score=True,
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        specs = set()
        for i in datasets.results:
            spec = i.get(u'Species', [None])[0]
            if spec:
                specs.add(spec)
        specs = list(specs)
        specs.sort()
        specsToIDs, idsToSpecs, counter = {}, {}, 0
        for spec in specs:
            specsToIDs[spec] = counter
            idsToSpecs[counter] = spec
            facetCode.append(u'''$("#s-{}").click(function() {{
                if ($(this).prop("checked"))
                    $(".s-{}").slideDown();
                else
                    $(".s-{}").slideUp();
            }}); '''.format(counter, counter, counter))
            counter += 1
        datasets = [{
            u'name': i[u'DatasetName'],
            u'url': self.request.route_url('dataset', collectionID=i[u'CollectionId'], datasetID=i[u'id']),
            u'cohort': i.get(u'Cohort'),
            u'version': i.get(u'DatasetVersion'),
            u'desc': self.truncate(i.get(u'DatasetDescription')),
            u'score': self.percent(i[u'score']),
            u'collection': i.get(u'CollectionName'),
            u'species': i.get(u'Species', [None])[0],
            # Other potential metadata to include here:
            # Cohort, CollectionName, CollectionId, Species, DatasetVersion, DatasetDescription, Sub-Cohort
        } for i in datasets.results]
        numDatasets, top10Datasets, datasets = len(datasets), datasets[:10], datasets[10:]
        files = backend.getSearchEngine(u'files').select(
            q=keywords,
            fields=None,
            highlight=None,
            score=True,
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        contentTypes = set()
        for i in files.results:
            contentTypes.add(i.get(u'FileType', [u'application/octet-stream'])[0])
        contentTypes = list(contentTypes)
        contentTypes.sort()
        typesToIDs, idsToTypes, counter = {}, {}, 0
        for contentType in contentTypes:
            typesToIDs[contentType] = counter
            idsToTypes[counter] = contentType
            facetCode.append(u'''$("#c-{}").click(function() {{
                if ($(this).prop("checked"))
                    $(".c-{}").slideDown();
                else
                    $(".c-{}").slideUp();
            }}); '''.format(counter, counter, counter))
            counter += 1
        facetCode.append(u'});')
        facetCode = u'\n'.join(facetCode)
        files = [{
            u'name': i[u'FileName'],
            u'url': self.request.route_url(
                'file', collectionID=i[u'CollectionId'], datasetID=i[u'DatasetId'], fileID=i[u'id']
            ),
            u'cohort': i.get(u'Cohort'),
            u'size': self.humanFriendlySize(i[u'FileSize']) if i.get(u'FileSize') else None,
            u'desc': self.truncate(i.get(u'GrossDescription', [None])[0]),
            u'score': self.percent(i[u'score']),
            u'contentType': i.get(u'FileType', [u'application/octet-stream'])[0],
            u'collection': i.get(u'CollectionName'),
            u'dataset': i.get(u'DatasetName'),
            u'shortDesc': i.get(u'Description', [None])[0]
        } for i in files.results]
        numFiles, top10Files, files = len(files), files[:10], files[10:]
        return {
            u'searchMacros': searchMacros,
            u'numCollections': numCollections,
            u'top10Collections': top10Collections,
            u'collections': collections,
            u'numRemainingCollections': len(collections),
            u'numDatasets': numDatasets,
            u'top10Datasets': top10Datasets,
            u'datasets': datasets,
            u'numRemainingDatasets': len(datasets),
            u'numFiles': numFiles,
            u'top10Files': top10Files,
            u'files': files,
            u'numRemainingFiles': len(files),
            u'contentTypes': contentTypes,
            u'facetCode': facetCode,
            u'typesToIDs': typesToIDs,
            u'idsToTypes': idsToTypes,
            u'idsToPIs': idsToPIs,
            u'pisToIDs': pisToIDs,
            u'pis': pis,
            u'idsToOrgans': idsToOrgans,
            u'organsToIDs': organsToIDs,
            u'organs': organs,
            u'idsToSpecs': idsToSpecs,
            u'specsToIDs': specsToIDs,
            u'specs': specs,
            u'idsToCBs': idsToCBs,
            u'cbToIDs': cbToIDs,
            u'cbs': cbs,
            u'idsToDiscs': idsToDiscs,
            u'discToIDs': discToIDs,
            u'discs': discs,
            u'pageTitle': u'LabCAS Search'
        }
