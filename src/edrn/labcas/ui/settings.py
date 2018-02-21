# encoding: utf-8

from .interfaces import ILabCASSettings
from .utils import Settings, DEFAULT_ZIP_FILE_LIMIT, DEFAULT_TMP_DIR, DEFAULT_SUPER_GROUP
from zope.interface import implements
from zope.component import getUtility, provideUtility
import os.path, cPickle, datetime, rdflib, ConfigParser, argparse, os, sys, urlparse, logging, click

_logger = logging.getLogger(__name__)


def _validateProgram(context, parameter, value):
    if value not in (u'EDRN', u'MCL'):
        raise click.BadParameter('Program must be either EDRN or MCL')
    return value

@click.command()
@click.option('--tmp', help='Set the path to the temporary directory', default=DEFAULT_TMP_DIR)
@click.option('--zip', help='Set the limit (in megabytes) for ZIP archives', default=DEFAULT_ZIP_FILE_LIMIT)
@click.option('--program', help='Set the program to either MCL or EDRN', callback=_validateProgram, default='EDRN')
@click.option('--super', help='Set the DN of the Super User group', default=DEFAULT_SUPER_GROUP)
def main(tmp, zip, program, super):
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
        with open(settingsFile, 'rb') as f:
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
