# encoding: utf-8

u'''EDRN LabCAS UI — Functional tests'''

from edrn.labcas.ui.testing import EDRN_LABCAS_UI_FUNCTIONAL_TESTING as LAYER
from plone.testing import layered
import doctest
import unittest2 as unittest

optionFlags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE | doctest.REPORT_ONLY_FIRST_FAILURE)


def test_suite():
    return unittest.TestSuite([
        layered(doctest.DocFileSuite('README.rst', package='edrn.labcas.ui', optionflags=optionFlags), LAYER),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
