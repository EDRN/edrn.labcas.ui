# encoding: utf-8
# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from setuptools import setup, find_packages
import os.path

# Package data
# ------------

_name            = 'edrn.labcas.ui'
_version         = '1.0.1'
_description     = 'User interface for LabCAS, for EDRN'
_author          = 'Sean Kelly'
_authorEmail     = 'sean.kelly@jpl.nasa.gov'
_maintainer      = 'Sean Kelly'
_maintainerEmail = 'sean.kelly@jpl.nasa.gov'
_license         = 'ALv2'
_namespaces      = ['edrn', 'edrn.labcas']
_zipSafe         = False
_keywords        = 'web edrn cancer biomarkers lab laboratory catalog archive'
_testSuite       = 'edrn.labcas.ui.tests.test_suite'
_entryPoints     = {
    'paste.app_factory': ['main=edrn.labcas.ui:main'],
    'console_scripts': ['update-vocabularies=edrn.labcas.ui.vocabularies:main']
}
_extras = {
}
_externalRequirements = [
    'setuptools',
    'deform >= 2.0a1',
    'humanize',
    'M2Crypto',
    'pyramid',
    'pyramid_beaker',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'pyramid_ldap',
    'rdflib',
    'six',
    'solrpy',
    'waitress',
    'zope.component',
    'zope.interface',
]
_classifiers = [
    'Development Status :: 3 - Alpha',
    'Environment :: Web Environment',
    'Framework :: Pyramid',
    'Intended Audience :: Healthcare Industry',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

# Setup Metadata
# --------------


def _read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

_header = '*' * len(_name) + '\n' + _name + '\n' + '*' * len(_name)
_longDescription = _header + '\n\n' + _read('README.rst') + '\n\n' + _read('docs', 'INSTALL.txt') + '\n\n' \
    + _read('docs', 'HISTORY.txt') + '\n'
open('doc.txt', 'w').write(_longDescription)


setup(
    author=_author,
    author_email=_authorEmail,
    classifiers=_classifiers,
    description=_description,
    entry_points=_entryPoints,
    extras_require=_extras,
    include_package_data=True,
    install_requires=_externalRequirements,
    keywords=_keywords,
    license=_license,
    long_description=_longDescription,
    maintainer=_maintainer,
    maintainer_email=_maintainerEmail,
    name=_name,
    namespace_packages=_namespaces,
    packages=find_packages('src', exclude=['ez_setup', 'bootstrap']),
    package_dir={'': 'src'},
    url='https://github.com/EDRN/' + _name,
    version=_version,
    zip_safe=_zipSafe,
)
