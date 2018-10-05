# encoding: utf-8
# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from .interfaces import IBackend, ILabCASSettings, IVocabularies, ILabCASSettings
from pyramid_ldap import get_ldap_connector
from zope.component import getUtility
from zope.interface import implements
import colander, re, datetime, logging, deform, cPickle, csv, codecs, os.path

# Logging
_logger = logging.getLogger(__name__)

# Handy constants
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

# Current collaborative groups for widget vocabulary
_collaborativeGroups = [
    u'N/A',
    u'Breast and Gynecologic Cancers Research Group',
    u'G.I. and Other Associated Cancers Research Group',
    u'Lung and Upper Aerodigestive Cancers Research Group',
    u'Prostate and Urologic Cancers Research Group'
]

# Capture the common name (cn) at the front of an LDAP distinguished name (dn)
_cnHunter = re.compile(ur'^cn=([^,]+),')

# Capture the ID number in parentheses at the end of a "Name name name (ID number)" string
ID_NUMBER_HUNTER = re.compile(ur'\((\d+)\)$')

# Capture the field name and meta-meta item of a metadata item from the LabCAS backend
_fieldGrabber = re.compile(ur'^input\.dataset\.([^.]+)\.([^.]+)')

# Metadata we ignore in LabCAS files in addition to anything starting
# with "CAS."
_metadataToIgnore = frozenset((
    u'_version_',
    u'CollectionId',
    u'CollectionName',
    u'DatasetId',
    u'DatasetName',
    u'DatasetVersion',
    u'FileDownloadId',
    u'FileLocation',
    u'FileName',
    u'FileSize',
    u'FileThumbnailUrl',
    u'id',
    u'LeadPI',
    u'OwnerPrincipal',
    u'ParentDatasetId',
    u'score',
    u'Version',
))

# Default settings
_defaultMetadata = {
}
_defaultDatatypes = {
}
DEFAULT_SITE_RDF_URL       = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/sites/@@rdf'
DEFAULT_PROTOCOL_RDF_URL   = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'
DEFAULT_PEOPLE_RDF_URL     = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/registered-person/@@rdf'
DEFAULT_ORGAN_RDF_URL      = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/body-systems/@@rdf'
DEFAULT_DISCIPLINE_RDF_URL = u'https://mcl.jpl.nasa.gov/ksdb/publishrdf/?filterby=program&filterval=1&rdftype=discipline'
DEFAULT_SPECIES_RDF_URL    = u'https://mcl.jpl.nasa.gov/ksdb/publishrdf/?filterby=program&filterval=1&rdftype=species'
DEFAULT_SPEC_TYPES_RDF_URL = u'https://mcl.jpl.nasa.gov/ksdb/publishrdf/?filterby=program&filterval=1&rdftype=specimentype'
DEFAULT_SUPER_GROUP        = u'cn=Super User,dc=edrn,dc=jpl,dc=nasa,dc=gov'
DEFAULT_ZIP_FILE_LIMIT     = 250
DEFAULT_TMP_DIR            = u'/data/tmp'
DEFAULT_ANALYTICS          = u''


# Functions
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


def computeCollaborativeGroupURL(product):
    return COLLABORATIVE_GROUPS.get(product.cg)


def createSchema(workflow, request):
    # Find the task with order 1:
    schema = colander.SchemaNode(colander.Mapping())
    for task in workflow.tasks:
        if task.get('order', '-1') == '1':
            # build the form
            conf = task.get('configuration', {})
            fieldNames = []
            for k, v in conf.iteritems():
                matches = _fieldGrabber.search(k)
                if matches and matches.group(2) == u'order':
                    fieldNames.append((matches.group(1), int(v)))
            fieldNames.sort(lambda a, b: cmp(a[1], b[1]))
            for fieldName in [i[0] for i in fieldNames]:
                # CA-1394, LabCAS UI will generate dataset IDs
                if fieldName == 'DatasetId': continue
                visible = conf.get(u'input.dataset.{}.visible'.format(fieldName), u'true') == u'true'
                if not visible: continue
                title = conf.get(u'input.dataset.{}.title'.format(fieldName), u'Unknown Field')
                description = conf.get(u'input.dataset.{}.description'.format(fieldName), u'Not sure what to put here.')
                dataType = conf.get(u'input.dataset.{}.type'.format(fieldName), u'http://www.w3.org/2001/XMLSchema/string')
                missing = colander.required if conf.get(u'input.dataset.{}.required'.format(fieldName)) == u'true' else None
                if missing is colander.required:
                    title = u'🔴 ' + title  # There's a red circle (U+1F534) and a no-break space U+00A0 in there
                # FIXME:
                if dataType in (
                    u'http://www.w3.org/2001/XMLSchema/string',
                ):
                    # Check for enumerated values
                    if u'input.dataset.{}.value.1'.format(fieldName) in conf:
                        # Collect the values
                        exp = re.compile(u'input.dataset.{}.value.[0-9]+'.format(fieldName))
                        values = []
                        for key, val in conf.items():
                            if exp.match(key) is not None:
                                values.append((val, val))
                        values.sort()
                        schema.add(colander.SchemaNode(
                            colander.String(),
                            name=fieldName,
                            title=title,
                            description=description,
                            validator=colander.OneOf([i[0] for i in values]),
                            widget=deform.widget.RadioChoiceWidget(values=values, inline=True),
                            missing=missing
                        ))
                    else:
                        schema.add(colander.SchemaNode(
                            colander.String(),
                            name=fieldName,
                            title=title,
                            description=description,
                            missing=missing
                        ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#text':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.TextAreaWidget(rows=6)
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#nistDatasetId':
                    # Skip this; we generated this dataset ID based on other fields
                    pass
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#participatingSiteId':
                    # Skip this; we'll capture it based on the "http://…#participatingSite" value
                    pass
                elif dataType == u'http://edrn.nci.nih.gov/xml/schema/types.xml#nistDatasetId':
                    # Skip this; it's generated based on other fields
                    pass
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#participatingSite':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.AutocompleteInputWidget(values=request.route_url('sites'))
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#organ':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.AutocompleteInputWidget(values=request.route_url('organs'))
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#discipline':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.AutocompleteInputWidget(values=request.route_url('disciplines'))
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#species':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.AutocompleteInputWidget(values=request.route_url('species'))
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#currentLogin':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        default=request.authenticated_userid.split(u',')[0][4:]
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#collaborativeGroup':
                    # CA-1356 ugly fix but I'm in a hurry and these groups haven't changed in 10 years.
                    # FIXME: correct solution: use IVocabularies
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        validator=colander.OneOf(_collaborativeGroups),
                        widget=deform.widget.RadioChoiceWidget(values=[(i, i) for i in _collaborativeGroups])
                    ))
                elif dataType == u'urn:ldap:attributes:dn':
                    principals = [
                        _cnHunter.match(i).group(1).strip() for i in request.effective_principals
                        if i.startswith(u'cn=')
                    ]
                    principals.sort()
                    c = get_ldap_connector(request)
                    ldapGroups = [
                        _cnHunter.match(i).group(1).strip() for i, attrs in c.user_groups(u'uid=*')
                        if i.startswith(u'cn=')
                    ]
                    group = colander.SchemaNode(
                        colander.String(),
                        widget=deform.widget.AutocompleteInputWidget(values=request.route_url('ldapGroups')),
                        name='group',
                        title=u'Group',
                        description=u'Name of an EDRN group that should be able to access this data'
                    )
                    groups = colander.SchemaNode(
                        colander.Sequence(),
                        group,
                        validator=colander.ContainsOnly(ldapGroups),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        default=principals
                    )
                    schema.add(groups)
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#principalInvestigator':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.AutocompleteInputWidget(values=request.route_url('people'))
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#protocolName':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.AutocompleteInputWidget(values=request.route_url('protocols'))
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#qaState':
                    values = (('Public', 'Public'), ('Under Review', 'Under Review'))
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.RadioChoiceWidget(values=values, inline=True)
                    ))
                elif dataType == u'http://cancer.jpl.nasa.gov/xml/schema/types.xml#specimenType':
                    values = [(i, i) for i in getUtility(IVocabularies).getSpecimenTypes().values()]
                    values.sort()
                    schema.add(colander.SchemaNode(
                        colander.Set(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        widget=deform.widget.CheckboxChoiceWidget(values=values, inline=True)
                    ))
                elif dataType == u'http://www.w3.org/2001/XMLSchema/url':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        validator=colander.url
                    ))
                elif dataType == u'http://www.w3.org/2001/XMLSchema/integer':
                    schema.add(colander.SchemaNode(
                        colander.Int(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing
                    ))
                elif dataType == u'http://www.w3.org/2001/XMLSchema/boolean':
                    schema.add(colander.SchemaNode(
                        colander.Boolean(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing
                    ))
                elif dataType == u'http://www.w3.org/2001/XMLSchema/anyURI':
                    schema.add(colander.SchemaNode(
                        colander.String(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing,
                        validator=colander.Regex(re_python_rfc3986_URI_reference)
                    ))
                elif dataType == u'http://www.w3.org/2001/XMLSchema/date':
                    schema.add(colander.SchemaNode(
                        colander.Date(),
                        name=fieldName,
                        title=title,
                        description=description,
                        missing=missing
                    ))
                else:
                    _logger.warn(u'Unknown data type "%s" for field "%s"', dataType, fieldName)
            break
    return schema


def addIdentifiersForStringFields(metadata):
    u'''For those fields which are entered by name, add their matching identifiers.'''
    # CA-1354 ugly kludge
    protocolName = metadata.get('ProtocolName', None)
    if protocolName:
        match = ID_NUMBER_HUNTER.search(protocolName)
        if match:
            metadata['ProtocolId'] = match.group(1)
    # More ugly kludges
    organName = metadata.get('Organ', None)
    if organName:
        match = ID_NUMBER_HUNTER.search(organName)
        if match:
            metadata['OrganId'] = match.group(1)
    leadPI = metadata.get('LeadPI', None)
    if leadPI:
        match = ID_NUMBER_HUNTER.search(leadPI)
        if match:
            metadata['LeadPIId'] = match.group(1)
    institution = metadata.get('Institution', None)
    if institution:
        match = ID_NUMBER_HUNTER.search(institution)
        if match:
            metadata['InstitutionId'] = match.group(1)
    # CA-1533
    species = metadata.get('Species', None)
    if species:
        match = ID_NUMBER_HUNTER.search(species)
        if match:
            metadata['SpeciesId'] = match.group(1)


# Classes
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
    def __init__(self, identifier, qaState, owners, name, title, description, leadPIs, organs, metadata):
        self.identifier = identifier
        self.qaState = qaState
        self.owners = owners
        self.name = name
        self.title = title
        self.description = description
        self.leadPIs = leadPIs
        self.organs = organs
        self.metadata = metadata
        self.datasetMapping = None
    def isPublic(self):
        return self.qaState == u'Public'
    def getMetadata(self):
        metadata = self.metadata.items()
        metadata.sort(lambda a, b: cmp(a[0], b[0]))
        return metadata
    def datasets(self, includeChildren=False, datasetID=None):
        _logger.info('LabCASCollection.datasets called with datasetID="%s", my collectionID="%s", children=%d',
            datasetID, self.identifier, includeChildren)
        if self.datasetMapping is None:
            self.datasetMapping = {}
            datasets = LabCASDataset.get(self.identifier, includeChildren=includeChildren)
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
        superGroup = getUtility(ILabCASSettings).getSuperGroup()
        if superGroup in principals or not principals.isdisjoint(owners) or public:
            # The logged in user is allowed access to this collection
            identifier = mapping[u'id']
            name = mapping.get(u'CollectionName', u'UNKNOWN')
            title = _getSingleValue(u'Title', mapping, u'UNKNOWN')
            description = mapping.get(u'CollectionDescription', u'UNKNOWN')
            leadPIs = _getMultipleValues(u'LeadPI', mapping, u'UNKNOWN')
            organs = _getMultipleValues(u'Organ', mapping, [])
            metadata = {}
            for key, values in mapping.iteritems():
                if key in (u'CollectionName', u'Title', u'CollectionDescription', u'LeadPI', u'Organ'): continue
                if key in _metadataToIgnore: continue
                if not isinstance(values, list) and not isinstance(values, basestring):
                    values = [values]
                metadata[key] = [unicode(i) for i in values]
            return LabCASCollection(identifier, qaState, owners, name, title, description, leadPIs, organs, metadata)
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
        _logger.info('Retrieving collection with identifier "%s"', identifier)
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
    def __init__(self, identifier, name, description, metadata, children=[], parentID=None):
        self.identifier, self.name, self.description, self.metadata = identifier, name, description, metadata
        self.parentID = parentID
        self.children = children
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
        _logger.info('Dataset identifier is %s', identifier)
        name = mapping.get(u'DatasetName', u'UNKNOWN')
        metadata = {}
        description = parentID = None
        for key, value in mapping.iteritems():
            if key == u'OwnerPrincipal': continue
            if key == u'DatasetDescription' and value is not None:
                description = value
            if key == u'DatasetParentId' and value is not None:
                parentID = value
            if isinstance(value, list) and not isinstance(value, basestring):
                metadata[key] = value
        # Get the kids
        backend = getUtility(IBackend)
        response = backend.getSearchEngine(u'datasets').select(
            q='*:*',
            fields=None,
            highlight=None,
            score=True,
            sort=['DatasetName'],
            fq=[u'DatasetParentId:{}'.format(identifier.replace(u':', u'\\:'))],
            start=0,
            rows=99999  # FIXME: support pagination
        )
        children = [LabCASDataset._construct(item) for item in response.results]
        return LabCASDataset(identifier, name, description, metadata, children, parentID)
    @staticmethod
    def getByDatasetID(datasetID):
        u'''Get the LabCAS dataset with the matching ID'''
        _logger.info('Retreiving dataset for datasetID "%s"', datasetID)
        backend = getUtility(IBackend)
        response = backend.getSearchEngine(u'datasets').select(
            q='*:*',
            fields=None,
            highlight=None,
            score=True,
            sort=['DatasetName'],
            fq=[u'id:{}'.format(datasetID.replace(u':', u'\\:'))],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        return LabCASDataset._construct(response.results[0])
    @staticmethod
    def get(collectionID, includeChildren=False):
        u'''Get the LabCAS datasets belonging to the collection with the given
        ``collectionName``.
        '''
        _logger.info('Retrieving datasets for collectionID "%s"', collectionID)
        backend = getUtility(IBackend)
        response = backend.getSearchEngine(u'datasets').select(
            q='*:*',
            fields=None,
            highlight=None,
            score=True,
            sort=['DatasetName'],
            fq=[u'CollectionId:{}'.format(collectionID.replace(u':', u'\\:'))],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        if includeChildren:
            return [LabCASDataset._construct(item) for item in response.results]
        else:
            return [LabCASDataset._construct(item) for item in response.results if item.get('DatasetParentId') is None]
    # What uses this ``getByParentDataset`` method? Nothing so far as I can tell.
    @staticmethod
    def getByParentDataset(datasetID):
        u'''Get the LabCAS datasets that have the given datasetID as a parent.'''
        backend = getUtility(IBackend)
        response = backend.getSearchEngine(u'datasets').select(
            q='*:*',
            fields=None,
            highlight=None,
            score=True,
            sort=['DatasetName'],
            fq=[u'DatasetParentId:{}'.format(datasetID.replace(u':', u'\\:'))],
            start=0,
            rows=99999  # FIXME: we should support pagination
        )
        return [LabCASDataset._construct(item) for item in response.results]


class LabCASFile(object):
    u'''A file stored in a LabCASDataset'''
    def __init__(self, identifier, name, fileID, size, contentType, directory, metadata, description, thumbnailURL):
        self.identifier = identifier
        self.name, self.fileID, self.size, self.contentType, self.directory = name, fileID, size, contentType, directory
        self.description, self.thumbnailURL = description, thumbnailURL
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
        fileID = mapping[u'FileDownloadId']
        size = mapping[u'FileSize']
        directory = mapping[u'FileLocation']
        contentType = mapping.get(u'FileType', [u'application/octet-stream'])[0]
        thumbnailURL = mapping.get(u'FileThumbnailUrl', [None])[0]
        description = None
        if u'Description' in mapping:
            seq = mapping[u'Description']
            del mapping[u'Description']
            if seq:
                description = seq[0]
        metadata = {}
        for key, values in mapping.iteritems():
            if key not in _metadataToIgnore and not key.startswith(u'CAS.'):
                metadata[key] = values
        return LabCASFile(identifier, name, fileID, size, contentType, directory, metadata, description, thumbnailURL)
    @staticmethod
    def get(datasetID):
        u'''Get the files belonging to the dataset with the given ``datasetID``
        '''
        _logger.info('Retrieving files for datasetID "%s"', datasetID)
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


class LabCASWorkflow(object):
    u'''A workflow we can execute within LabCAS.'''
    def __init__(self, identifier, name, conditions, tasks):
        self.identifier, self.name, self.conditions, self.tasks = identifier, name, conditions, tasks
        self.order = max([i.get(u'configuration', {}).get(u'workflow.order', 0) for i in tasks])
        self.collectionName = None
        self.uploadFiles = False
        for task in tasks:
            order = task.get('order', '-1')
            if order == '1':
                self.collectionName = task['configuration'].get('CollectionName', None)
                self.uploadFiles = task['configuration'].get('UploadFiles', False) == 'true'
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
    def __hash__(self):
        return hash(self.identifier)


class Settings(object):
    implements(ILabCASSettings)
    program            = u'EDRN'
    metadata           = _defaultMetadata
    datatypes          = _defaultDatatypes
    siteRDFURL         = DEFAULT_SITE_RDF_URL
    protocolRDFURL     = DEFAULT_PROTOCOL_RDF_URL
    peopleRDFURL       = DEFAULT_PEOPLE_RDF_URL
    organRDFURL        = DEFAULT_ORGAN_RDF_URL
    disciplineRDFURL   = DEFAULT_DISCIPLINE_RDF_URL
    speciesRDFURL      = DEFAULT_SPECIES_RDF_URL
    specimenTypeRDFURL = DEFAULT_SPEC_TYPES_RDF_URL
    superGroup         = DEFAULT_SUPER_GROUP
    zipFileLimit       = DEFAULT_ZIP_FILE_LIMIT
    tmpDir             = DEFAULT_TMP_DIR
    analytics          = DEFAULT_ANALYTICS
    def __init__(self, settingsPath):
        self.settingsPath = settingsPath
        _logger.info(u'Settings object CREATED with path %s', settingsPath)
    def getAnalytics(self):
        return self.analytics
    def setAnalytics(self, analytics):
        if self.analytics != analytics:
            self.analytics = analytics
            self.update()
    def getTmpDir(self):
        return self.tmpDir
    def setTmpDir(self, tmpDir):
        if self.tmpDir != tmpDir:
            self.tmpDir = tmpDir
            self.update()
    def getZipFileLimit(self):
        return self.zipFileLimit
    def setZipFileLimit(self, megabytes):
        if self.zipFileLimit != megabytes:
            self.zipFileLimit = megabytes
            self.update()
    def getSuperGroup(self):
        return self.superGroup
    def setSuperGroup(self, group):
        if self.superGroup != group:
            self.superGroup = group
            self.update()
    def getProgram(self):
        return self.program
    def setProgram(self, program):
        if program != self.program:
            self.program = program
            self.update()
    def getSpecimenTypeRDFURL(self):
        return self.specimenTypeRDFURL
    def setSpecimenTypeRDFURL(self, url):
        if url != self.specimenTypeRDFURL:
            self.specimenTypeRDFURL = url
            self.update()
    def getSpeciesRDFURL(self):
        return self.speciesRDFURL
    def setSpeciesRDFURL(self, url):
        if url != self.speciesRDFURL:
            self.speciesRDFURL = url
            self.update()
    def getDisciplineRDFURL(self):
        return self.disciplineRDFURL
    def setDisciplineRDFURL(self, url):
        if url != self.disciplineRDFURL:
            self.disciplineRDFURL = url
            self.update()
    def getSiteRDFURL(self):
        return self.siteRDFURL
    def setSiteRDFURL(self, url):
        if url != self.siteRDFURL:
            self.siteRDFURL = url
            self.update()
    def getOrganRDFURL(self):
        return self.organRDFURL
    def setOrganRDFURL(self, url):
        if url != self.organRDFURL:
            self.organRDFURL = url
            self.update()
    def getProtocolRDFURL(self):
        return self.protocolRDFURL
    def setProtocolRDFURL(self, url):
        if url != self.protocolRDFURL:
            self.protocolRDFURL = url
            self.update()
    def getPeopleRDFURL(self):
        return self.peopleRDFURL
    def setPeopleRDFURL(self, url):
        if url != self.peopleRDFURL:
            self.peopleRDFURL = url
            self.update()
    def getMetadataElements(self):
        return self.metadata
    def deleteMetadataElement(self, identifier):
        try:
            del self.metadata[identifier]
            self.update()
        except KeyError:
            pass
    def addMetadataElement(self, element):
        self.metadata[element.identifier] = element
        self.update()
    def getDataTypes(self):
        return self.datatypes
    def deleteDataType(self, identifier):
        try:
            del self.datatypes[identifier]
            self.update()
        except KeyError:
            pass
    def addDataType(self, datatype):
        self.datatypes[datatype.identifier] = datatype
        self.update()
    def update(self):
        _logger.info(u'Settings object saving itself to %s', self.settingsPath)
        with open(self.settingsPath, 'wb') as f:
            cPickle.dump(self, f)


class DataType(object):
    def __init__(self, identifier):
        self.identifier = identifier
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
    def __repr__(self):
        return u'{}:{}'.format(self.__class__.__name__, self.identifier)


class MetadataElement(object):
    def __init__(self, identifier):
        self.identifier = identifier
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
    def __repr__(self):
        return u'{}:{}'.format(self.__class__.__name__, self.identifier)


# Courtesy of https://docs.python.org/2/library/csv.html#module-csv
class UTF8Recoder(object):
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)
    def __iter__(self):
        return self
    def next(self):
        return self.reader.next().encode('utf-8')


class UnicodeReader(object):
    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)
    def next(self):
        row = self.reader.next()
        return [unicode(s, 'utf-8') for s in row]
    def __iter__(self):
        return self


def _readMimeTypes():
    mimes = {}
    with open(os.path.join(os.path.dirname(__file__), 'static', 'mimes.csv'), 'rb') as f:
        reader = UnicodeReader(f)
        for row in reader:
            contentType, description = row[0], row[1]
            mimes[contentType] = description
    return mimes


def _readExtensions():
    extensions = {}
    with open(os.path.join(os.path.dirname(__file__), 'static', 'mimes.csv'), 'rb') as f:
        reader = UnicodeReader(f)
        for row in reader:
            extension, description = row[2], row[1]
            extensions[extension] = description
    return extensions


MIME_TYPES = _readMimeTypes()
EXTENSIONS = _readExtensions()


def computeHumanReadableContentType(fileName, contentType):
    desc = MIME_TYPES.get(contentType)
    if not desc or contentType == u'application/octet-stream':
        fn, ext = os.path.splitext(fileName)
        desc = EXTENSIONS.get(ext)
        if not desc:
            desc = 'Binary Data'
    return desc


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
