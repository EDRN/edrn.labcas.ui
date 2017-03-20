# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import ILabCASSettings
from edrn.labcas.ui.utils import LabCASWorkflow
from pyramid.view import view_config, view_defaults
from zope.component import getUtility
import colander, deform


@view_defaults(renderer=PACKAGE_NAME + ':templates/manage.pt')
class ManageView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='manage', permission='manage')
    def __call__(self):
        settings = getUtility(ILabCASSettings)
        schema = colander.SchemaNode(colander.Mapping())
        schema.add(colander.SchemaNode(
            colander.String(),
            name='siteName',
            title=u'Site Name',
            description=u'The name of this LabCAS installation.',
            validator=colander.Length(min=1),
            default=settings.getSiteName()
        ))
        form = deform.Form(schema, buttons=('submit',))
        if 'submit' in self.request.params:
            try:
                metadataAppstruct = form.validate(self.request.POST.items())
                siteName = metadataAppstruct['siteName']
                if siteName != settings.getSiteName():
                    settings.setSiteName(siteName)
                    self.request.session.flash(u'Changes saved.', 'info')
                else:
                    self.request.session.flash(u'No changes made.', 'info')
            except deform.ValidationFailure as ex:
                self.request.session.flash(u"Some required fields are missing or don't make sense.", 'info')
                return {
                    'form': ex.render(),
                    'widgetResources': form.get_widget_resources()
                }
        return {
            'form': form.render(),
            'widgetResources': form.get_widget_resources()
        }
