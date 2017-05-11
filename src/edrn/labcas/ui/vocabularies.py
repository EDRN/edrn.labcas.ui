# encoding: utf-8
# Copyright 2016 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

u'''EDRN LabCAS User Interface: vocabularies'''

from .interfaces import IVocabularies, ILabCASSettings
from .utils import UTC, Settings
from zope.interface import implements
from zope.component import getUtility, provideUtility
import os.path, cPickle, datetime, rdflib, ConfigParser, argparse, os, sys, urlparse, logging

_logger = logging.getLogger(__name__)


_surnamePredicateURI   = rdflib.term.URIRef(u'http://xmlns.com/foaf/0.1/surname')
_givenNamePredicateURI = rdflib.term.URIRef(u'http://xmlns.com/foaf/0.1/givenname')
_dcTitlePredicateURI   = rdflib.term.URIRef(u'http://purl.org/dc/terms/title')
_personTypes = (
    rdflib.term.URIRef(u'http://cancer.jpl.nasa.gov/rdf/types.rdf#Person'),
    rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Person')
)
_protocolTypes = (
    rdflib.term.URIRef(u'http://cancer.jpl.nasa.gov/rdf/types.rdf#Protocol'),
    rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Protocol')
)
_siteTypes = (
    rdflib.term.URIRef(u'https://cancer.jpl.nasa.gov/rdf/types.rdf#FundedSite'),
    rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Site')
)
_organTypes = (
    rdflib.term.URIRef(u'https://cancer.jpl.nasa.gov/rdf/types.rdf#Organ'),
    rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#BodySystem')
)
_disciplineTypes = (
    rdflib.term.URIRef(u'https://cancer.jpl.nasa.gov/rdf/types.rdf#Discipline'),
)
_speciesTypes = (
    rdflib.term.URIRef(u'https://cancer.jpl.nasa.gov/rdf/types.rdf#Species'),
)
_specimenTypesTypes = (
    rdflib.term.URIRef(u'https://cancer.jpl.nasa.gov/rdf/types.rdf#SpecimenType'),
)


class Vocabularies(object):
    u'''Vocabularies.'''
    implements(IVocabularies)
    def __init__(self, vocabDir):
        self.vocabDir = vocabDir
        self.peopleTimestamp = self.protocolsTimestamp = self.sitesTimestamp = self.organsTimestamp \
            = self.speciesTimestamp = self.disciplinesTimestamp = self.specimenTypesTimestamp \
            = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0, UTC)
    def _loadVocabulary(self, vocabName):
        vocabFile = os.path.join(self.vocabDir, vocabName)
        _logger.info(u'Loading vocabulary from %s', vocabFile)
        with open(vocabFile, 'rb') as f:
            return cPickle.load(f)
    def _getLastUpdate(self, vocabName):
        timestampFile = os.path.join(self.vocabDir, vocabName + u'.timestamp')
        with open(timestampFile, 'rb') as f:
            return cPickle.load(f)
    def getPeople(self):
        timestamp = self._getLastUpdate(u'people')
        if timestamp > self.peopleTimestamp:
            self.people = self._loadVocabulary(u'people')
            self.peopleTimestamp = timestamp
        return self.people
    def getProtocols(self):
        timestamp = self._getLastUpdate(u'protocols')
        if timestamp > self.protocolsTimestamp:
            self.protocols = self._loadVocabulary(u'protocols')
            self.protocolsTimestamp = timestamp
        return self.protocols
    def getSites(self):
        timestamp = self._getLastUpdate(u'sites')
        if timestamp > self.sitesTimestamp:
            self.sites = self._loadVocabulary(u'sites')
            self.sitesTimestamp = timestamp
        return self.sites
    def getOrgans(self):
        timestamp = self._getLastUpdate(u'organs')
        if timestamp > self.organsTimestamp:
            self.organs = self._loadVocabulary(u'organs')
            self.organsTimestamp = timestamp
        return self.organs
    def getSpecies(self):
        timestamp = self._getLastUpdate(u'species')
        if timestamp > self.speciesTimestamp:
            self.species = self._loadVocabulary(u'species')
            self.speciesTimestamp = timestamp
        return self.species
    def getDisciplines(self):
        timestamp = self._getLastUpdate(u'disciplines')
        if timestamp > self.disciplinesTimestamp:
            self.disciplines = self._loadVocabulary(u'disciplines')
            self.disciplinesTimestamp = timestamp
        return self.disciplines
    def getSpecimenTypes(self):
        timestamp = self._getLastUpdate(u'specimenTypes')
        if timestamp > self.specimenTypesTimestamp:
            self.specimenTypes = self._loadVocabulary(u'specimenTypes')
            self.specimenTypesTimestamp = timestamp
        return self.specimenTypes


def _parseRDF(graph):
    u'''Convert an RDF graph into a mapping of {s→{p→[o]}} where s is a subject
    URI, p is a predicate URI, and o is a list of objects which may be literals
    or URI references.
    '''
    statements = {}
    for s, p, o in graph:
        predicates = statements.get(s, {})
        statements[s] = predicates
        objects = predicates.get(p, [])
        predicates[p] = objects
        objects.append(o)
    return statements


def _getStatements(url):
    u'''Return a mapping of statements to predicates to objects for the RDF at url.'''
    g = rdflib.Graph()
    g.load(url)
    return _parseRDF(g)


def _dumpFile(vocabDir, obj, name):
    dest = os.path.join(vocabDir, name + '.dump')
    with open(dest, 'wb') as f:
        cPickle.dump(obj, f)
    os.rename(dest, os.path.join(vocabDir, name))
    tsFile = os.path.join(vocabDir, name + u'.timestamp')
    with open(tsFile, 'wb') as f:
        cPickle.dump(datetime.datetime.now(UTC), f)


def _getID(url):
    u'''Get the identifying numeric component from an MCL- or EDRN-specific RDF subject URI.'''
    last, query = os.path.basename(urlparse.urlparse(url).path), urlparse.urlparse(url).query
    if query.startswith(u'id='):
        return query[3:]
    else:
        return last


def _dumpPeople(vocabDir):
    settings = getUtility(ILabCASSettings)
    people = {}
    url = settings.getPeopleRDFURL()
    _logger.info('Dumping people from %s', url)
    statements = _getStatements(url)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType not in _personTypes: continue
        givenName = unicode(predicates.get(_givenNamePredicateURI, [u''])[0])
        surname = unicode(predicates.get(_surnamePredicateURI, [u''])[0])
        personID = _getID(subjectURI)
        name = u'{}, {} ({})'.format(surname, givenName, personID)
        people[personID] = name
    _dumpFile(vocabDir, people, u'people')


def _dumpProtocols(vocabDir):
    settings = getUtility(ILabCASSettings)
    protocols = {}
    url = settings.getProtocolRDFURL()
    _logger.info('Dumping protocols from %s', url)
    statements = _getStatements(url)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType not in _protocolTypes: continue
        title = predicates.get(_dcTitlePredicateURI, None)
        if not title: continue
        protocolID = _getID(subjectURI)
        name = u'{} ({})'.format(unicode(title[0]), protocolID)
        protocols[protocolID] = name
    _dumpFile(vocabDir, protocols, u'protocols')


def _dumpSites(vocabDir):
    settings = getUtility(ILabCASSettings)
    sites = {}
    url = settings.getSiteRDFURL()
    _logger.info('Dumping sites from %s', url)
    statements = _getStatements(url)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType not in _siteTypes: continue
        title = predicates.get(_dcTitlePredicateURI, None)
        if not title: continue
        siteID = _getID(subjectURI)
        name = u'{} ({})'.format(unicode(title[0]), siteID)
        sites[siteID] = name
    _dumpFile(vocabDir, sites, u'sites')


def _dumpOrgans(vocabDir):
    settings = getUtility(ILabCASSettings)
    organs = {}
    url = settings.getOrganRDFURL()
    _logger.info('Dumping organs from %s', url)
    statements = _getStatements(url)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType not in _organTypes: continue
        title = predicates.get(_dcTitlePredicateURI, None)
        if not title: continue
        organID = _getID(subjectURI)
        name = u'{} ({})'.format(unicode(title[0]), organID)
        organs[organID] = name
    _dumpFile(vocabDir, organs, u'organs')


def _dumpDisciplines(vocabDir):
    settings = getUtility(ILabCASSettings)
    disciplines = {}
    url = settings.getDisciplineRDFURL()
    _logger.info('Dumping disciplines from %s', url)
    statements = _getStatements(url)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType not in _disciplineTypes: continue
        title = predicates.get(_dcTitlePredicateURI, None)
        if not title: continue
        discID = _getID(subjectURI)
        name = u'{} ({})'.format(unicode(title[0]), discID)
        disciplines[discID] = name
    _dumpFile(vocabDir, disciplines, u'disciplines')


def _dumpSpecies(vocabDir):
    settings = getUtility(ILabCASSettings)
    species = {}
    url = settings.getSpeciesRDFURL()
    _logger.info('Dumping species from %s', url)
    statements = _getStatements(url)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType not in _speciesTypes: continue
        title = predicates.get(_dcTitlePredicateURI, None)
        if not title: continue
        specID = _getID(subjectURI)
        name = u'{} ({})'.format(unicode(title[0]), specID)
        species[specID] = name
    _dumpFile(vocabDir, species, u'species')


def _dumpSpecimenTypes(vocabDir):
    settings = getUtility(ILabCASSettings)
    specs = {}
    url = settings.getSpecimenTypeRDFURL()
    _logger.info('Dumping specimen types from %s', url)
    statements = _getStatements(url)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType not in _specimenTypesTypes: continue
        title = predicates.get(_dcTitlePredicateURI, None)
        if not title: continue
        specID = _getID(subjectURI)
        name = u'{} ({})'.format(unicode(title[0]), specID)
        specs[specID] = name
    _dumpFile(vocabDir, specs, u'specimenTypes')


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=u'Update the LabCAS UI vocabulary files')
    parser.add_argument('config', help=u'Path to LabCAS UI "Paste" configuration file')
    args = parser.parse_args()
    config = ConfigParser.SafeConfigParser()
    config.read(args.config)
    vocabDir = config.get('app:main', 'labcas.vocabularies')
    settingsFile = config.get('app:main',  'labcas.settings')
    if not os.path.isdir(vocabDir):
        os.makedirs(vocabDir)
    try:
        with open(config.get(settingsFile, 'rb')) as f:
            labCASSettings = cPickle.load(f)
    except:
        labCASSettings = Settings(settingsFile)
        labCASSettings.update()
    provideUtility(labCASSettings)
    _dumpPeople(vocabDir)
    _dumpProtocols(vocabDir)
    _dumpSites(vocabDir)
    _dumpOrgans(vocabDir)
    _dumpDisciplines(vocabDir)
    _dumpSpecies(vocabDir)
    _dumpSpecimenTypes(vocabDir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
