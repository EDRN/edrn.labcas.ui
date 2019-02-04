# encoding: utf-8

from zope.interface import implements
from .interfaces import ILabCASSettings
import logging, cPickle, sys, os, codecs, string, random, pkg_resources


logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)


# Default settings
_defaultMetadata = {
}
_defaultDatatypes = {
}
DEFAULT_SOLR_URL           = u'http://labcas-backend:8983/solr'
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


class Settings(object):
    implements(ILabCASSettings)
    program            = u'EDRN'
    metadata           = _defaultMetadata
    datatypes          = _defaultDatatypes
    solrURL            = DEFAULT_SOLR_URL
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
    def getSolrURL(self):
        return self.solrURL
    def setSolrURL(self, solrURL):
        if self.solrURL != solrURL:
            self.solrURL = solrURL
            self.update()
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


_tokenChars = string.ascii_letters + string.digits


def _generateToken():
    return u''.join(random.choice(_tokenChars) for i in range(4))


def main():
    try:
        # First our post-start mutable LabCAS settings
        _logger.info('Creating LabCAS settings')
        print >>sys.stderr, '=========== HERE ========='
        settings = Settings('/app/persistence/settings')
        settings.setTmpDir(os.environ['LabCAS_TMP_Dir'])
        settings.setZipFileLimit(int(os.environ['LabCAS_ZIP_File_Limit']))
        settings.setSuperGroup(os.environ['LabCAS_LDAP_Super_Group'])
        settings.setProgram(os.environ['LabCAS_Program'])

        # Now our Pyramid start-up settings
        values = {
            'secrets_session': _generateToken(),
            'secrets_authorization': _generateToken(),
            'ldap_manager_dn': os.environ['LabCAS_LDAP_Manager_DN'],
            'secrets_ldap_manager_password': os.environ['LabCAS_LDAP_Manager_Auth'],
            'ldap_user_base': os.environ['LabCAS_LDAP_User_Base'],
            'ldap_group_base': os.environ['LabCAS_LDAP_Group_Base']
        }
        _logger.info('Creating Pyramid settings')
        fn = pkg_resources.resource_filename(__name__, 'templates/paste.cfg')
        with codecs.open(fn, encoding='utf-8') as f:
            source = string.Template(f.read())
            with codecs.open('/app/persistence/paste.cfg', encoding='utf-8', mode='w') as out:
                out.write(source.substitute(values))
    except Exception as ex:
        _logger.critical('Settings setup failed!')
        _logger.exception('Exception detail follows')
        return -1
    return 0


if __name__ == '__main__':
    sys.exit(main())
