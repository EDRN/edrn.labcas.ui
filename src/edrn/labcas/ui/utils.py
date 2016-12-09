# encoding: utf-8
# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from zope.component import getUtility
from edrn.labcas.ui.interfaces import IBackend
from urlparse import urlparse
import urllib, re, datetime, logging

# Logging
_logger = logging.getLogger(__name__)

# Handy constants
SUPER_GROUP = u'cn=Super User,dc=edrn,dc=jpl,dc=nasa,dc=gov'
CG_BASE_URL = u'https://edrn.nci.nih.gov/collaborative-groups/'

# Mapping from the various random formats of EDRN collaborative groups
# to their URL paths in the EDRN Portal
COLLABORATIVE_GROUPS = {
    u'Breast and Gynecologic Cancers Research Group': CG_BASE_URL + u'breast-and-gynecologic-cancers-research-group',
    u'Breast and Gynecologic': CG_BASE_URL + u'breast-and-gynecologic-cancers-research-group',
    u'Breast': CG_BASE_URL + u'breast-and-gynecologic-cancers-research-group',
    u'G.I. and Other Associated Cancers Research Group': CG_BASE_URL + u'g-i-and-other-associated-cancers-research-group',
    u'G.I. and Other Associated': CG_BASE_URL + u'g-i-and-other-associated-cancers-research-group',
    u'Lung and Upper Aerodigestive Cancers Research Group': CG_BASE_URL + u'lung-and-upper-aerodigestive-cancers-research',
    u'Lung and Upper Aerodigestive': CG_BASE_URL + u'lung-and-upper-aerodigestive-cancers-research',
    u'Prostate and Urologic Cancers Research Group': CG_BASE_URL + u'prostate-and-urologic-cancers-research-group',
    u'Prostate and Urologic': CG_BASE_URL + u'prostate-and-urologic-cancers-research-group',
}

# Metadata we ignore in LabCAS files in addition to anything starting
# with "CAS."
_metadataToIgnore = frozenset((
    u'_version_',
    u'CollectionName',
    u'DatasetId',
    u'DatasetVersion',
    u'FileLocation',
    u'FileName',
    u'FileSize',
    u'id',
    u'LeadPI',
    u'OwnerPrincipal',
    u'ParentDatasetId',
    u'score',
    u'Version',
))


def _getSingleValue(key, mapping, default=None):
    u'''Get a single value with the matching ``key`` that maps to an array
    of values in ``mapping``; but we want just one-and-only value.  Return
    the ``default`` if there is no matching ``key``.
    '''
    values = mapping.get(key)
    if values and len(values) > 0:
        return values[0]
    return default


def _getMultipleValues(key, mapping, default=None):
    u'''Get all the values in the ``mapping`` for the given ``key``.  If
    the ``key`` isn't there, return the ``default``.
    '''
    values = mapping.get(key)
    if values is not None:
        values.sort()
        return values
    return default


class _UTC(datetime.tzinfo):
    u'''Time zone for Coordinated Universal Time (UTC); for more information, please see
    https://docs.python.org/2.7/library/datetime.html#tzinfo-objects
    '''
    zero = datetime.timedelta(0)
    def utcoffset(self, dt):
        return self.zero
    def tzname(self, dt):
        return 'UTC'
    def dst(self, dt):
        return self.zero
UTC = _UTC()


class LabCASCollection(object):
    u'''A collection of datasets stored in LabCAS'''
    def __init__(
        self, identifier, qaState, owners, name, title, description, leadPI, collaborativeGroup, organSites,
        protocolID, protocolName, dataCustodianName, dataCustodianEmail, discipline, referenceID, referenceURL
    ):
        self.identifier = identifier
        self.qaState = qaState
        self.owners = owners
        self.name = name
        self.title = title
        self.description = description
        self.leadPI = leadPI
        self.collaborativeGroup = collaborativeGroup
        self.organSites = organSites
        self.protocolID = protocolID
        self.protocolName = protocolName
        self.dataCustodianName = dataCustodianName
        self.dataCustodianEmail = dataCustodianEmail
        self.discipline = discipline
        self.referenceID = referenceID
        self.referenceURL = referenceURL
        self.datasetMapping = None
    def isPublic(self):
        return self.qaState == u'Public'
    def datasets(self, datasetID=None):
        if self.datasetMapping is None:
            self.datasetMapping = {}
            datasets = LabCASDataset.get(self.name)
            for dataset in datasets:
                self.datasetMapping[dataset.identifier] = dataset
        if datasetID is None:
            datasets = self.datasetMapping.values()
            datasets.sort()
            return datasets
        return self.datasetMapping[datasetID]
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
    @staticmethod
    def _construct(mapping, principals):
        u'''Attempt to create a LabCASCollection from the information in the
        given ``mapping`` for the user identified with the given
        ``principals``.  If the ``principals`` indicate that the collection
        cannot be created do to lack of permissions, then return None.  We
        also return None if the mapping is missing the mandatory "id" key.
        '''
        qaState = _getSingleValue(u'QAState', mapping, None)
        public = qaState == u'Public'
        owners = frozenset(_getMultipleValues(u'OwnerPrincipal', mapping, []))
        if SUPER_GROUP in principals or not principals.isdisjoint(owners) or public:
            # The logged in user is allowed access to this collection
            identifier = mapping[u'id']
            name = mapping.get(u'CollectionName', u'UNKNOWN')
            title = _getSingleValue(u'Title', mapping, u'UNKNOWN')
            description = mapping.get(u'CollectionDescription', u'UNKNOWN')
            leadPI = _getSingleValue(u'LeadPI', mapping, u'UNKNOWN')
            collaborativeGroup = _getSingleValue(u'CollaborativeGroup', mapping, u'UNKNOWN')
            organSites = _getMultipleValues(u'OrganSite', mapping, [u'UNKNOWN'])
            protocolID = _getSingleValue(u'ProtocolId', mapping, u'UNKNOWN')
            protocolName = _getSingleValue(u'ProtocolName', mapping, u'UNKNOWN')
            dataCustodianName = _getSingleValue(u'DataCustodian', mapping, u'UNKNOWN')
            dataCustodianEmail = _getSingleValue(u'DataCustodianEmail', mapping, u'UNKNOWN')
            discipline = _getSingleValue(u'Discpline', mapping, u'UNKNOWN')
            referenceID = _getSingleValue(u'ReferenceId', mapping, u'UNKNOWN')
            referenceURL = _getSingleValue(u'ReferenceUrl', mapping, u'UNKNOWN')
            return LabCASCollection(
                identifier, qaState, owners, name, title, description, leadPI, collaborativeGroup, organSites,
                protocolID, protocolName, dataCustodianName, dataCustodianEmail, discipline, referenceID, referenceURL
            )
        else:
            # Sorry pal, try when you get better permissions
            return None
    @staticmethod
    def get(identifier=None, principals=frozenset()):
        u'''Get the LabCASCollection with the given ``identifier``.  If none
        match, return None.  If ``identifier`` is None, return a sequence of
        all LabCASCollections.  Use the given ``principals`` to figure out
        which we have access to.
        '''
        backend = getUtility(IBackend)
        if identifier is None:
            collections = []
            response = backend.getSearchEngine(u'collections').select(
                q='*:*',
                fields=None,
                highlight=None,
                score=True,
                sort=['CollectionName'],
                fq=[u'*:*'],
                start=0,
                rows=99999  # FIXME: we should support pagination
            )
            for item in response.results:
                collection = LabCASCollection._construct(item, principals)
                if collection: collections.append(collection)
            return collections
        else:
            response = backend.getSearchEngine(u'collections').select(
                q='*:*',
                fields=None,
                highlight=None,
                score=True,
                sort=None,
                fq=[u'id:{}'.format(identifier.replace(u':', u'\\:'))],
                start=0,
                rows=99999  # FIXME: we should support pagination
            )
            if response.results:
                return LabCASCollection._construct(response.results[0], principals)
            else:
                return None


class LabCASDataset(object):
    u'''A dataset stored in a LabCASCollection'''
    def __init__(self, identifier, name, metadata):
        self.identifier, self.name, self.metadata = identifier, name, metadata
        self.fileMapping = None
    def getMetadata(self):
        metadata = self.metadata.items()
        metadata.sort(lambda a, b: cmp(a[0], b[0]))
        return metadata
    def files(self, fileID=None):
        if self.fileMapping is None:
            self.fileMapping = {}
            files = LabCASFile.get(self.identifier)
            for f in files:
                self.fileMapping[f.identifier] = f
        if fileID is None:
            files = self.fileMapping.values()
            files.sort()
            return files
        return self.fileMapping[fileID]
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
    @staticmethod
    def _construct(mapping):
        u'''Construct a dataset given the information in the ``mapping``.'''
        identifier = mapping[u'id']
        name = mapping.get(u'DatasetName', u'UNKNOWN')
        metadata = {}
        for key, value in mapping.iteritems():
            if isinstance(value, list) and not isinstance(value, basestring):
                metadata[key] = value
        return LabCASDataset(identifier, name, metadata)
    @staticmethod
    def get(collectionName):
        u'''Get the LabCAS datasets belonging to the collection with the given
        ``collectionName``.
        '''
        backend = getUtility(IBackend)
        response = backend.getSearchEngine(u'datasets').select(
            q='*:*',
            fields=None,
            highlight=None,
            score=True,
            sort=['DatasetName'],
            fq=[u'CollectionName:{}'.format(collectionName.replace(u':', u'\\:'))],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        return [LabCASDataset._construct(item) for item in response.results]


class LabCASFile(object):
    u'''A file stored in a LabCASProduct'''
    def __init__(self, identifier, name, physicalLocation, size, contentType, metadata):
        self.identifier = identifier
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
    @staticmethod
    def _construct(mapping):
        u'''Construct a LabCASFile with info in the ``mapping``.'''
        identifier = mapping[u'id']
        name = mapping[u'FileName']
        physicalLocation = mapping[u'FileLocation']
        size = mapping[u'FileSize']
        contentType = mapping.get(u'ContentType', u'application/octet-stream')
        metadata = {}
        for key, values in mapping.iteritems():
            if key not in _metadataToIgnore and not key.startswith(u'CAS.'):
                metadata[key] = values
        return LabCASFile(identifier, name, physicalLocation, size, contentType, metadata)
    @staticmethod
    def get(datasetID):
        u'''Get the files belonging to the dataset with the given ``datasetID``
        '''
        backend = getUtility(IBackend)
        response = backend.getSearchEngine(u'files').select(
            q='*:*',
            fields=None,
            highlight=None,
            score=True,
            sort=['FileName'],
            fq=[u'DatasetId:{}'.format(datasetID.replace(u':', u'\\:'))],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        return [LabCASFile._construct(item) for item in response.results]


class LabCASProduct(object):
    u'''A product stored within LabCAS.'''
    def __init__(self, identifier, name, versions, pi, organSite, cg, public):
        self.identifier, self.name, self.versions, self.pi, self.organSite = identifier, name, versions, pi, organSite
        self.cg, self.public = cg, public
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
        response = backend.getSearchEngine().select(
            q='*:*',
            fields=None,
            highlight=None,
            score=True,
            sort=None,
            fq=['DatasetId:{}'.format(name.replace(u':', u'\\:'))],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        versions, public = {}, False  # versions = version → [files]
        for item in response.results:
            public = item.get(u'QAState', None) == [u'Public']
            _logger.debug(u'QA State = %s, so public = %r', item.get(u'QAState', u'UNKNOWN'), public)
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
        if SUPER_GROUP in principals or not principals.isdisjoint(owners) or public:
            return LabCASProduct(productID, datasetName, versions, pi, organ, cg, public)
        else:
            _logger.info('Not returning product "%s"; principals = %r, public = %r', productID, principals, public)
            return None


class LabCASWorkflow(object):
    u'''A workflow we can execute within LabCAS.'''
    def __init__(self, identifier, name, conditions, tasks):
        self.identifier, self.name, self.conditions, self.tasks = identifier, name, conditions, tasks
        self.order = max([i.get(u'configuration', {}).get(u'workflow.order', 0) for i in tasks])
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
    def __hash__(self):
        return hash(self.identifier)


def computeCollaborativeGroupURL(product):
    return COLLABORATIVE_GROUPS.get(product.cg)


# Sincere gratitude to http://jmrware.com/articles/2009/uri_regexp/URI_regex.html
re_python_rfc3986_URI_reference = re.compile(r""" ^
    # RFC-3986 URI component: URI-reference
    (?:                                                               # (
      [A-Za-z][A-Za-z0-9+\-.]* :                                      # URI
      (?: //
        (?: (?:[A-Za-z0-9\-._~!$&'()*+,;=:]|%[0-9A-Fa-f]{2})* @)?
        (?:
          \[
          (?:
            (?:
              (?:                                                    (?:[0-9A-Fa-f]{1,4}:){6}
              |                                                   :: (?:[0-9A-Fa-f]{1,4}:){5}
              | (?:                            [0-9A-Fa-f]{1,4})? :: (?:[0-9A-Fa-f]{1,4}:){4}
              | (?: (?:[0-9A-Fa-f]{1,4}:){0,1} [0-9A-Fa-f]{1,4})? :: (?:[0-9A-Fa-f]{1,4}:){3}
              | (?: (?:[0-9A-Fa-f]{1,4}:){0,2} [0-9A-Fa-f]{1,4})? :: (?:[0-9A-Fa-f]{1,4}:){2}
              | (?: (?:[0-9A-Fa-f]{1,4}:){0,3} [0-9A-Fa-f]{1,4})? ::    [0-9A-Fa-f]{1,4}:
              | (?: (?:[0-9A-Fa-f]{1,4}:){0,4} [0-9A-Fa-f]{1,4})? ::
              ) (?:
                  [0-9A-Fa-f]{1,4} : [0-9A-Fa-f]{1,4}
                | (?: (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?) \.){3}
                      (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)
                )
            |   (?: (?:[0-9A-Fa-f]{1,4}:){0,5} [0-9A-Fa-f]{1,4})? ::    [0-9A-Fa-f]{1,4}
            |   (?: (?:[0-9A-Fa-f]{1,4}:){0,6} [0-9A-Fa-f]{1,4})? ::
            )
          | [Vv][0-9A-Fa-f]+\.[A-Za-z0-9\-._~!$&'()*+,;=:]+
          )
          \]
        | (?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}
             (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)
        | (?:[A-Za-z0-9\-._~!$&'()*+,;=]|%[0-9A-Fa-f]{2})*
        )
        (?: : [0-9]* )?
        (?:/ (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})* )*
      | /
        (?:    (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})+
          (?:/ (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})* )*
        )?
      |        (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})+
          (?:/ (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})* )*
      |
      )
      (?:\? (?:[A-Za-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9A-Fa-f]{2})* )?
      (?:\# (?:[A-Za-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9A-Fa-f]{2})* )?
    | (?: //                                                          # / relative-ref
        (?: (?:[A-Za-z0-9\-._~!$&'()*+,;=:]|%[0-9A-Fa-f]{2})* @)?
        (?:
          \[
          (?:
            (?:
              (?:                                                    (?:[0-9A-Fa-f]{1,4}:){6}
              |                                                   :: (?:[0-9A-Fa-f]{1,4}:){5}
              | (?:                            [0-9A-Fa-f]{1,4})? :: (?:[0-9A-Fa-f]{1,4}:){4}
              | (?: (?:[0-9A-Fa-f]{1,4}:){0,1} [0-9A-Fa-f]{1,4})? :: (?:[0-9A-Fa-f]{1,4}:){3}
              | (?: (?:[0-9A-Fa-f]{1,4}:){0,2} [0-9A-Fa-f]{1,4})? :: (?:[0-9A-Fa-f]{1,4}:){2}
              | (?: (?:[0-9A-Fa-f]{1,4}:){0,3} [0-9A-Fa-f]{1,4})? ::    [0-9A-Fa-f]{1,4}:
              | (?: (?:[0-9A-Fa-f]{1,4}:){0,4} [0-9A-Fa-f]{1,4})? ::
              ) (?:
                  [0-9A-Fa-f]{1,4} : [0-9A-Fa-f]{1,4}
                | (?: (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?) \.){3}
                      (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)
                )
            |   (?: (?:[0-9A-Fa-f]{1,4}:){0,5} [0-9A-Fa-f]{1,4})? ::    [0-9A-Fa-f]{1,4}
            |   (?: (?:[0-9A-Fa-f]{1,4}:){0,6} [0-9A-Fa-f]{1,4})? ::
            )
          | [Vv][0-9A-Fa-f]+\.[A-Za-z0-9\-._~!$&'()*+,;=:]+
          )
          \]
        | (?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}
             (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)
        | (?:[A-Za-z0-9\-._~!$&'()*+,;=]|%[0-9A-Fa-f]{2})*
        )
        (?: : [0-9]* )?
        (?:/ (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})* )*
      | /
        (?:    (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})+
          (?:/ (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})* )*
        )?
      |        (?:[A-Za-z0-9\-._~!$&'()*+,;=@] |%[0-9A-Fa-f]{2})+
          (?:/ (?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})* )*
      |
      )
      (?:\? (?:[A-Za-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9A-Fa-f]{2})* )?
      (?:\# (?:[A-Za-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9A-Fa-f]{2})* )?
    )                                                                       # )
    $ """, re.VERBOSE)
