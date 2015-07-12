# encoding: utf-8

from setuptools import setup, find_packages
import os.path

# Package data
# ------------

_name            = 'edrn.labcas.ui'
_version         = '0.0.0'
_description     = 'ui package for EDRN LabCAS'
_url             = 'https://github.com/EDRN/' + _name
_downloadURL     = 'https://github.com/EDRN/' + _name + '/downloads'
_author          = 'Sean Kelly'
_authorEmail     = 'sean.kelly@jpl.nasa.gov'
_maintainer      = 'Sean Kelly'
_maintainerEmail = 'sean.kelly@jpl.nasa.gov'
_license         = 'ALv2'
_namespaces      = ['edrn', 'edrn.labcas']
_zipSafe         = False
_keywords        = 'plone zope site website ui edrn labcas edrn labcas science cancer detection'
_testSuite       = 'edrn.labcas.ui.tests.test_suite'
_extras = {
    'test': ['plone.app.testing'],
}
_entryPoints = {
    'z3c.autoinclude.plugin': ['target=plone'],
}
_requirements = [
    'setuptools',
    'Products.CMFPlone',
    'z3c.autoinclude',
    'Products.CMFPlacefulWorkflow',
    'plone.api',
    'plone.app.dexterity[grok,relations]',
    'anyjson',
    'lxml',
]
_classifiers = [
    'Development Status :: 2 - Pre-Alpha',
    'Environment :: Web Environment',
    'Framework :: Plone',
    'License :: Other/Proprietary License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

# Setup Metadata
# --------------
#
# Nothing below here should require updating.

def _read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

_header = '*' * len(_name) + '\n' + _name + '\n' + '*' * len(_name)
_longDescription = _header + '\n\n' + _read('README.rst') + '\n\n' + _read('docs', 'INSTALL.txt') + '\n\n' \
    + _read('docs', 'HISTORY.txt') + '\n\n' + _read('docs', 'LICENSE.txt')
open('doc.txt', 'w').write(_longDescription)

setup(
    author=_author,
    author_email=_authorEmail,
    classifiers=_classifiers,
    description=_description,
    download_url=_downloadURL,
    entry_points=_entryPoints,
    extras_require=_extras,
    include_package_data=True,
    install_requires=_requirements,
    keywords=_keywords,
    license=_license,
    long_description=_longDescription,
    maintainer=_maintainer,
    maintainer_email=_maintainerEmail,
    name=_name,
    namespace_packages=_namespaces,
    packages=find_packages('src', exclude=['ez_setup', 'bootstrap']),
    package_dir={'': 'src'},
    test_suite=_testSuite,
    url=_url,
    version=_version,
    zip_safe=_zipSafe,
)
