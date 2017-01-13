# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import IBackend
from edrn.labcas.ui.utils import LabCASWorkflow
from pyramid.view import view_config, view_defaults
from zope.component import getUtility


@view_defaults(renderer=PACKAGE_NAME + ':templates/start.pt')
class StartView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='start', permission='upload')
    def __call__(self):
        backend = getUtility(IBackend)
        workflows = []
        for availableWorkflow in backend.getWorkflowMgr().getWorkflows():
            # Include only workflows that have a task with order 1:
            tasks = availableWorkflow.get('tasks', [])
            for task in tasks:
                if task.get('order', '-1') == '1':
                    workflow = LabCASWorkflow(
                        availableWorkflow.get('id', u'unknown'),
                        availableWorkflow.get('name', u'unknown'),
                        availableWorkflow.get('conditions', []),
                        tasks
                    )
                    if not workflow.uploadFiles:
                        workflows.append(workflow)
        workflows.sort(lambda a, b: cmp(a.order, b.order))
        return {u'hasWorkflows': len(workflows) > 0, u'workflows': workflows}
