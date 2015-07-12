# encoding: utf-8

u'''EDRN LabCAS: user interface testing fixtures and layers'''

from plone.app.testing import PloneSandboxLayer, IntegrationTesting, FunctionalTesting, PLONE_FIXTURE
import plone.api

class EDRNLabCASUI(PloneSandboxLayer):
    u'''LabCAS sandbox layer'''
    defaultBases = (PLONE_FIXTURE,)
    def setUpZope(self, app, configurationContext):
        import edrn.labcas.ui
        self.loadZCML(package=edrn.labcas.ui)
    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'edrn.labcas.ui:default')
        wf = plone.api.portal.get_tool('portal_workflow')
        wf.setDefaultChain('plone_workflow')


EDRN_LABCAS_UI = EDRNLabCASUI()
EDRN_LABCAS_UI_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EDRN_LABCAS_UI,), name='EDRNLabCASUI:Integration'
)
EDRN_LABCAS_UI_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EDRN_LABCAS_UI,), name='EDRNLabCASUI:Functional'
)
