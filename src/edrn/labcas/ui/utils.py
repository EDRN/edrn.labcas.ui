# encoding: utf-8
# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from zope.component import getUtility
from edrn.labcas.ui.interfaces import IBackend
from urlparse import urlparse
import urllib, re, datetime


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
            response = backend.getSearchEngine().query('*:*', fq=['DatasetId:{}'.format(name.replace(u':', u'\\:'))], start=0)
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


