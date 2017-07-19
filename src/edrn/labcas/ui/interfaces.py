# encoding: utf-8

from zope.interface import Interface


class IBackend(Interface):
    u'''What a LabCAS backend looks like.'''
    def getFileMgr():
        u'''Retrieves the file manager'''
    def getWorkflowMgr():
        u'''Retrieves the workflow manager'''
    def getStagingDirectory():
        u'''Retrieves the path to the LabCAS staging directory'''
    def getArchiveDirectory():
        u'''Retrieves the path to the LabCAS archive directory'''
    def getSearchEngine(kind):
        u'''Retrieves the SOLR search API for the given ``kind`` of data.'''


class IVocabularies(Interface):
    u'''What the vocabulary manager resembles.'''
    def getPeople():
        u'''Returns a sequence of people working on EDRN'''
    def getProtocols():
        u'''Returns a sequence of EDRN protocol names'''
    def getSites():
        u'''Returns a sequence of EDRN or MCL site names'''
    def getOrgans():
        u'''Returns a sequence of EDRN or MCL organs (body systems)'''
    def getDisciplines():
        u'''Returns a sequence of MCL disciplines.'''
    def getSpecies():
        u'''Return a sequence of species, like left shark or human.'''
    def getSpecimenTypes():
        u'''Return a sequence of types of specimens, like blood.'''


class ILabCASSettings(Interface):
    u'''Various settings for LabCAS'''
    def getProgram():
        u'''Returns either EDRN or MCL'''
    def setProgram(program):
        u'''Set whether this is for EDRN or MCL'''
    def getSpecimenTypeRDFURL():
        u'''Get the URL to specimen type information'''
    def setSpecimenTypeRDFURL(url):
        u'''Set the URL to specimen type information'''
    def getSpeciesRDFURL():
        u'''Get the URL to Species information'''
    def setSpeciesRDFURL(url):
        u'''Set the URL to Species information'''
    def getSiteRDFURL():
        u'''Get the URL to site information'''
    def setSiteRDFURL(url):
        u'''Set the URL to site information'''
    def getProtocolRDFURL():
        u'''Get the URL to Protocol information'''
    def setProtocolRDFURL(url):
        u'''Set the URL to Protocol information'''
    def getPeopleRDFURL():
        u'''Get the URL to People information'''
    def setPeopleRDFURL(url):
        u'''Set the URL to People information'''
    def getOrganRDFURL():
        u'''Get the URL to Organ information'''
    def setOrganRDFURL(url):
        u'''Set the URL to Organ information'''
    def getDisciplineRDFURL():
        u'''Get the URL to Discipline information'''
    def setDisciplineRDFURL(url):
        u'''Set the URL to Discipline information'''
    def getMetadataElements():
        u'''Return a mapping of element identifiers to MetadataElement instances'''
    def deleteMetadataElement(identifier):
        u'''Delete the metadata element with the given identifier'''
    def addMetadataElement(element):
        u'''Add the given metadata element; if such an element has the same identifier as an existing, it's replaced'''
    def getDataTypes():
        u'''Return a mapping of data type identifiers to DataType instances'''
    def deleteDataType(identifier):
        u'''Delete the data type with the given identifier'''
    def addDataType(datatype):
        u'''Add the given data type; if such an type has the same identifier as an existing, it's replaced'''
    def getSuperGroup():
        u'''Get the LDAP group for the super users'''
    def setSuperGroup(group):
        u'''Set the super group'''
