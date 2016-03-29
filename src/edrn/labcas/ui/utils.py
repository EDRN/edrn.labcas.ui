# encoding: utf-8
# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from zope.component import getUtility
from edrn.labcas.ui.interfaces import IBackend
from urlparse import urlparse
import urllib


SUPER_GROUP = u'cn=Super User,dc=edrn,dc=jpl,dc=nasa,dc=gov'
CG_BASE_URL = u'https://edrn.nci.nih.gov/collaborative-groups/'
COLLABORATIVE_GROUPS = {
    u'Lung and Upper Aerodigestive': CG_BASE_URL + u'lung-and-upper-aerodigestive-cancers-research',
    u'Prostate and Urologic': CG_BASE_URL + u'prostate-and-urologic-cancers-research-group'
}

_metadataToIgnore = frozenset((
    u'_version_',
    u'DatasetId',
    u'id',
    u'ParentDatasetId',
    u'score',
    u'Version',
    u'LeadPI'
))


class LabCASFile(object):
    u'''A file stored in a LabCASProduct'''
    def __init__(self, name, physicalLocation, size, contentType, metadata):
        self.name, self.physicalLocation, self.size, self.contentType = name, physicalLocation, size, contentType
        self.metadata = {}
        for key, value in metadata.items():
            if key.startswith(u'CAS.') or key in _metadataToIgnore: continue
            self.metadata[key] = value
    def getMetadata(self):
        metadata = self.metadata.items()
        metadata.sort(lambda a, b: cmp(a[0], b[0]))
        return metadata
    def __cmp__(self, other):
        return cmp(self.name, other.name)


class LabCASProduct(object):
    u'''A product stored within LabCAS.'''
    def __init__(self, identifier, name, versions, pi, organSite, cg):
        self.identifier, self.name, self.versions, self.pi, self.organSite = identifier, name, versions, pi, organSite
        self.cg = cg
    def __cmp__(self, other):
        return cmp(self.name, other.name)
    def getVersions(self):
        versions = self.versions.items()
        versions.sort(lambda a, b: cmp(a[0], b[0]))
        return versions
    @staticmethod
    def new(product, principals):
        typeMetadata = product.get('typeMetadata', {})
        owners = frozenset(typeMetadata.get('OwnerGroup', []))
        if SUPER_GROUP in principals or not principals.isdisjoint(owners):
            name, productID = product.get('name'), product.get('id')
            if not productID: return None
            pi = typeMetadata.get(u'LeadPI', [u'Unknown'])
            pi = pi[0]
            organ = typeMetadata.get(u'OrganSite', [u'Unknown'])
            organ = organ[0]
            cg = typeMetadata.get(u'CollaborativeGroup', [u'Unknown'])
            cg = cg[0]
            datasetName = typeMetadata.get(u'DatasetName', [name if name else productID])
            datasetName = datasetName[0]
            backend = getUtility(IBackend)
            response = backend.getSearchEngine().query('*:*', fq=['DatasetId:{}'.format(name)], start=0)
            versions = {}  # version → [files]
            for item in response.results:
                version = item.get(u'Version', u'0')
                files = versions.get(version, [])
                fileName = item.get(u'CAS.ProductName')
                if not fileName: continue
                physicalLocation = item.get(u'CAS.ReferenceDatastore')
                if not physicalLocation: continue
                physicalLocation = urlparse(urllib.unquote(physicalLocation[0])).path  # FIXME assumes file: URLs always
                mimeType = item.get(u'CAS.ReferenceMimeType')
                if not mimeType: continue
                mimeType = mimeType[0]
                size = item.get(u'CAS.ReferenceFileSize')
                if not size: continue
                size = size[0]
                files.append(LabCASFile(fileName, physicalLocation, size, mimeType, item))
                versions[version] = files
            if not versions: return None
            return LabCASProduct(productID, datasetName, versions, pi, organ, cg)
        else:
            return None


class LabCASWorkflow(object):
    u'''A workflow we can execute within LabCAS.'''
    def __init__(self, identifier, name, conditions, tasks):
        self.identifier, self.name, self.conditions, self.tasks = identifier, name, conditions, tasks
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
    def __hash__(self):
        return hash(self.identifier)


def computeCollaborativeGroupURL(product):
    return COLLABORATIVE_GROUPS.get(product.cg)
