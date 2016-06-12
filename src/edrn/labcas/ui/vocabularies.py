# encoding: utf-8
# Copyright 2016 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

u'''EDRN LabCAS User Interface: vocabularies'''

from .interfaces import IVocabularies
from .utils import UTC
from zope.interface import implements
import os.path, cPickle, datetime, rdflib, ConfigParser, argparse, os, os.path, sys, urlparse, logging

_logger = logging.getLogger(__name__)


_peopleRDF             = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/registered-person/@@rdf'
_personType            = rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Person')
_surnamePredicateURI   = rdflib.term.URIRef(u'http://xmlns.com/foaf/0.1/surname')
_givenNamePredicateURI = rdflib.term.URIRef(u'http://xmlns.com/foaf/0.1/givenname')
_protocolsRDF          = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'
_protocolType          = rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Protocol')
_dcTitlePredicateURI   = rdflib.term.URIRef(u'http://purl.org/dc/terms/title')


class Vocabularies(object):
    u'''Vocabularies.'''
    implements(IVocabularies)
    def __init__(self, vocabDir):
        self.vocabDir = vocabDir
        self.peopleTimestamp = self.protocolsTimestamp = datetime.datetime(
            datetime.MINYEAR, 1, 1, 0, 0, 0, 0, UTC
        )
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
    dest = os.path.join(vocabDir, name)
    with open(dest, 'wb') as f:
        cPickle.dump(obj, f)
    tsFile = os.path.join(vocabDir, name + u'.timestamp')
    with open(tsFile, 'wb') as f:
        cPickle.dump(datetime.datetime.now(UTC), f)


def _dumpPeople(vocabDir):
    people = {}
    statements = _getStatements(_peopleRDF)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType != _personType: continue
        givenName = unicode(predicates.get(_givenNamePredicateURI, [u''])[0])
        surname = unicode(predicates.get(_surnamePredicateURI, [u''])[0])
        personID = os.path.basename(urlparse.urlparse(subjectURI).path)
        name = u'{}, {} ({})'.format(surname, givenName, personID)
        people[personID] = name
    _dumpFile(vocabDir, people, u'people')


def _dumpProtocols(vocabDir):
    protocols = {}
    statements = _getStatements(_protocolsRDF)
    for subjectURI, predicates in statements.iteritems():
        objectType = predicates[rdflib.RDF.type][0]
        if objectType != _protocolType: continue
        title = predicates.get(_dcTitlePredicateURI, None)
        if not title: continue
        protocolID = os.path.basename(urlparse.urlparse(subjectURI).path)
        name = u'{} ({})'.format(unicode(title[0]), protocolID)
        protocols[protocolID] = name
    _dumpFile(vocabDir, protocols, u'protocols')


def main():
    parser = argparse.ArgumentParser(description=u'Update the LabCAS UI vocabulary files')
    parser.add_argument('config', help=u'Path to LabCAS UI "Paste" configuration file')
    args = parser.parse_args()
    config = ConfigParser.SafeConfigParser()
    config.read(args.config)
    vocabDir = config.get('app:main', 'labcas.vocabularies')
    if not os.path.isdir(vocabDir):
        os.makedirs(vocabDir)
    _dumpPeople(vocabDir)
    _dumpProtocols(vocabDir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
