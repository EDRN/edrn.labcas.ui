# encoding: utf-8

u'''EDRN LabCAS UI — Setup tests'''

from edrn.labcas.ui.testing import EDRN_LABCAS_UI_INTEGRATION_TESTING
import plone.api
import unittest2 as unittest

class SetupTest(unittest.TestCase):
    layer = EDRN_LABCAS_UI_INTEGRATION_TESTING
    def setUp(self):
        super(SetupTest, self).setUp()
        self.portal = self.layer['portal']
    # def testDependencies(self):
    #     u'''Make sure our dependent packages get installed'''
    #     qi = plone.api.portal.get_tool('portal_quickinstaller')
    #     for i in ('edrn.theme',):
    #         self.assertTrue(qi.isProductInstalled(i), u'Expected {} to be installed'.format(i))
    # def testDependencies(self):
    #     '''Make sure our dependent packages get installed.'''
    #     qi = getToolByName(self.portal, 'portal_quickinstaller')
    #     for i in (
    #         'quintagroup.theme.sunrain',  'Products.Carousel', 'quintagroup.portlet.static',
    #         'whiteriversite.pcornet', 'quintagroup.plonecaptchas'
    #     ):
    #         self.failUnless(qi.isProductInstalled(i), 'Package "%s" not installed, should be' % i)
    #     try:
    #         import z3c.jbot
    #         z3c.jbot # silence pyflakes
    #     except ImportError:
    #         self.fail('z3c.jbot not available, should be')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
