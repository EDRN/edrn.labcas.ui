# encoding: utf-8

import unittest
from pyramid import testing


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_my_view(self):
        from edrn.labcas.ui.views import my_view
        request = testing.DummyRequest()
        info = my_view(request)
        self.assertEqual('doom!', info['project'])


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
